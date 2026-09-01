"""Donne une histoire a la plateforme : des commandes dans tous leurs etats.

    python manage.py seed_activite

`seed_demo` cree les comptes, `seed_catalogue` les produits. Il manquait la
troisieme chose, et c'est celle qui se voit : **la vie**. Un tableau de bord
qui n'affiche que des zeros ne se demontre pas, et un ecran de commandes vide
ne prouve pas qu'il sait afficher une commande.

Le principe : chaque etat que le modele sait representer existe ici au moins
une fois. Pas pour faire du volume, mais pour qu'aucun ecran ne soit jamais
confronte a un cas qu'il n'a jamais vu.

  commande     en attente de paiement, payee, en preparation, prete,
               expediee vers l'entrepot, recue, en tournee, en livraison,
               livree, annulee, echec de livraison
  livraison    a attribuer, attribuee, recuperee, en route, livree, echouee
  tournee      brouillon, prete, affectee, en cours, terminee
  stock        rupture, seuil d'alerte, reservation en cours, historique
  engagement   avis publies et signales, litiges ouverts et resolus,
               notifications lues et non lues

La commande est **idempotente** : elle reconnait son propre travail au
prefixe des numeros de commande et ne le refait pas.
"""
import datetime
import random

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction
from django.utils import timezone

from catalogue.models import MouvementStock, Produit, TypeMouvement
from commandes import reservation
from commandes.models import (
    Commande,
    HistoriqueStatut,
    LigneCommande,
    SousCommande,
    StatutCommande,
    StatutPreparation,
    TypeObjetSuivi,
)
from comptes.models import Client, Gestionnaire, Livreur, TypeService, Vendeur
from engagement.models import (
    Avis,
    CanalNotification,
    CibleAvis,
    Litige,
    MotifLitige,
    Notification,
    StatutLitige,
    StatutModeration,
)
from livraisons.models import (
    ArretTournee,
    Entrepot,
    Livraison,
    ResultatTentative,
    StatutArret,
    StatutLivraison,
    StatutTournee,
    TentativeLivraison,
    Tournee,
)
from paiements.models import (
    Facture,
    Paiement,
    Promotion,
    RepartitionVendeur,
    StatutPaiement,
    TypeReduction,
)

# Les commandes de demonstration se reconnaissent a ce prefixe. C'est ce qui
# rend la commande rejouable sans dupliquer une histoire deja ecrite.
PREFIXE = "RD-DEMO-"


class Command(BaseCommand):
    help = "Cree des commandes, livraisons, tournees, avis et litiges de demonstration."

    def add_arguments(self, analyseur):
        analyseur.add_argument(
            "--refaire", action="store_true", dest="refaire",
            help="Efface l'activite de demonstration existante et la recree.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_activite ne s'execute qu'en developpement.")

        if options["refaire"]:
            self._effacer()

        # La remise en ordre des compteurs de reservation tourne AVANT le
        # garde d'idempotence : c'est une reparation, pas un peuplement. Un
        # essai de paiement interrompu la veille laisse du stock immobilise,
        # et relancer la commande de peuplement doit suffire a le rendre.
        self._reparer_reservations()

        if Commande.objects.filter(numero_commande__startswith=PREFIXE).exists():
            self.stdout.write(self.style.SUCCESS("Activite de demonstration deja en place."))
            return

        # Une graine fixe : le meme jeu de donnees a chaque peuplement. Une
        # demonstration qui change de chiffres a chaque lancement ne se
        # prepare pas.
        self.hasard = random.Random(2026)
        self.compteur = 0

        acteurs = self._rassembler()
        if acteurs is None:
            return

        self._promotions(acteurs)
        commandes = self._commandes(acteurs)
        self._livraisons(acteurs, commandes)
        self._tournees(acteurs, commandes)
        self._engagement(acteurs, commandes)
        self._mouvements_de_stock(acteurs)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Activite : {len(commandes)} commandes, "
            f"{Livraison.objects.count()} livraisons, "
            f"{Tournee.objects.count()} tournees, "
            f"{Avis.objects.count()} avis, {Litige.objects.count()} litiges."
        ))
        self.stdout.write("")

    # ── Preparation ──────────────────────────────────────────────────────

    def _effacer(self):
        commandes = Commande.objects.filter(numero_commande__startswith=PREFIXE)
        Tournee.objects.filter(livraisons__commande__in=commandes).delete()
        Litige.objects.filter(commande__in=commandes).delete()
        Avis.objects.filter(commande__in=commandes).delete()
        Facture.objects.filter(commande__in=commandes).delete()
        Paiement.objects.filter(commande__in=commandes).delete()
        commandes.delete()
        Notification.objects.filter(type__startswith="DEMO_").delete()
        self.stdout.write("Activite de demonstration effacee.")

    def _reparer_reservations(self):
        """Recalculer le stock reserve a partir des commandes qui en tiennent une.

        Cette methode disait autrefois : « aucune reservation n'est legitime
        tant que le paiement n'existe pas », et remettait tout a zero. Le
        paiement existe maintenant, et une commande en attente de paiement
        tient une reservation parfaitement valable (D-15) : l'effacer ferait
        vendre deux fois le meme exemplaire.

        On ne devine donc plus : on **recompte**. La somme des lignes des
        commandes dont le drapeau `stock_reserve_pose` est leve fait foi, et
        tout ce qui depasse est un residu d'une execution interrompue.
        """
        # D'abord rendre ce qu'un panier abandonne retient encore : sans quoi
        # on recompterait des reservations qui n'ont plus lieu d'etre.
        expirees = reservation.liberer_les_expirees()
        if expirees:
            self.stdout.write(
                f"  {expirees} commande(s) jamais payee(s) : stock rendu a la vente."
            )

        attendu = {}
        commandes = Commande.objects.filter(stock_reserve_pose=True).prefetch_related(
            "sous_commandes__lignes"
        )
        for commande in commandes:
            for sous_commande in commande.sous_commandes.all():
                for ligne in sous_commande.lignes.all():
                    if ligne.produit_id:
                        attendu[ligne.produit_id] = (
                            attendu.get(ligne.produit_id, 0) + ligne.quantite
                        )

        corriges = 0
        for produit in Produit.objects.filter(
            models.Q(stock_reserve__gt=0) | models.Q(id__in=attendu)
        ):
            juste = min(attendu.get(produit.id, 0), produit.stock_disponible)
            if produit.stock_reserve != juste:
                Produit.objects.filter(pk=produit.id).update(stock_reserve=juste)
                corriges += 1

        if corriges:
            self.stdout.write(
                f"  {corriges} compteur(s) de reservation recalcule(s) "
                f"depuis les commandes en attente de paiement."
            )

    def _rassembler(self):
        """Les acteurs de l'histoire, ou un message clair s'ils manquent."""
        boutiques = {v.nom_boutique: v for v in Vendeur.objects.select_related("adresse")}
        clients = {
            c.utilisateur.email: c
            for c in Client.objects.select_related("utilisateur").prefetch_related("adresses")
        }
        if not boutiques or not clients:
            self.stdout.write(self.style.WARNING(
                "Aucune boutique ou aucun client : lance d'abord `python manage.py seed_demo`."
            ))
            return None

        return {
            "boutiques": boutiques,
            "clients": clients,
            "livreurs": {
                liv.utilisateur.email: liv
                for liv in Livreur.objects.select_related("utilisateur")
            },
            "entrepots": {e.nom: e for e in Entrepot.objects.all()},
            "gestionnaires": {
                g.utilisateur.email: g
                for g in Gestionnaire.objects.select_related("utilisateur")
            },
            "produits": {
                (p.vendeur.nom_boutique, p.nom): p
                for p in Produit.objects.select_related("vendeur")
            },
        }

    # ── Promotions (D-45) ────────────────────────────────────────────────

    def _promotions(self, acteurs):
        aujourdhui = timezone.localdate()
        Promotion.objects.get_or_create(
            code="BIENVENUE10",
            defaults={
                "vendeur": None,  # promotion de la plateforme
                "type_reduction": TypeReduction.POURCENTAGE,
                "valeur": 10,
                "montant_minimum_centimes": 1500,
                "date_debut": aujourdhui - datetime.timedelta(days=30),
                "date_fin": aujourdhui + datetime.timedelta(days=60),
                "quantite_max": 500,
                "quantite_utilisee": 137,
            },
        )
        karim = acteurs["boutiques"].get("Chez Karim")
        if karim:
            Promotion.objects.get_or_create(
                code="MIDIKARIM",
                defaults={
                    "vendeur": karim,  # promotion de boutique
                    "type_reduction": TypeReduction.MONTANT,
                    "valeur": 2,
                    "montant_minimum_centimes": 2000,
                    "date_debut": aujourdhui - datetime.timedelta(days=7),
                    "date_fin": aujourdhui + datetime.timedelta(days=7),
                    "quantite_max": 100,
                    "quantite_utilisee": 12,
                },
            )
        # Une promotion expiree : les ecrans doivent savoir l'afficher comme
        # telle plutot que de la proposer encore.
        Promotion.objects.get_or_create(
            code="RENTREE24",
            defaults={
                "vendeur": None,
                "type_reduction": TypeReduction.FRAIS_LIVRAISON,
                "valeur": 0,
                "date_debut": aujourdhui - datetime.timedelta(days=200),
                "date_fin": aujourdhui - datetime.timedelta(days=140),
                "quantite_max": 200,
                "quantite_utilisee": 200,
            },
        )

    # ── Les commandes ────────────────────────────────────────────────────

    def _numero(self, quand):
        self.compteur += 1
        return f"{PREFIXE}{quand:%y%m%d}-{self.compteur:03d}"

    def _adresse(self, client):
        return client.adresses.first()

    def _creer(self, acteurs, courriel_client, service, statut, paniers, il_y_a_heures,
               preparation=StatutPreparation.A_PREPARER, frais=490, annulee_par=""):
        """Une commande complete : lignes, sous-commandes, paiement, historique.

        `paniers` est une liste de (nom_boutique, nom_produit, quantite). Le
        decoupage par vendeur reproduit celui de `CommandeSplitter` (D-10) :
        une sous-commande par vendeur, une commande Standard qui peut en
        contenir plusieurs.
        """
        client = acteurs["clients"].get(courriel_client)
        adresse = self._adresse(client) if client else None
        if client is None or adresse is None:
            return None

        quand = timezone.now() - datetime.timedelta(hours=il_y_a_heures)
        commande = Commande.objects.create(
            numero_commande=self._numero(quand),
            client=client,
            adresse_livraison=adresse,
            type_service=service,
            statut_actuel=statut,
            montant_livraison_centimes=frais,
        )
        # `date_commande` est en auto_now_add : seule une mise a jour directe
        # peut la faire remonter dans le passe.
        Commande.objects.filter(pk=commande.pk).update(
            date_commande=quand,
            date_livraison_estimee=quand + datetime.timedelta(
                minutes=35 if service == TypeService.EXPRESS else 60 * 48
            ),
        )

        total_produits = 0
        par_vendeur = {}
        for nom_boutique, nom_produit, quantite in paniers:
            produit = acteurs["produits"].get((nom_boutique, nom_produit))
            if produit is None:
                continue
            par_vendeur.setdefault(produit.vendeur, []).append((produit, quantite))

        for vendeur, lignes in par_vendeur.items():
            montant = sum(p.prix_unitaire_centimes * q for p, q in lignes)
            total_produits += montant
            commission = int(montant * float(vendeur.taux_commission))
            sous_commande = SousCommande.objects.create(
                commande=commande,
                vendeur=vendeur,
                statut_preparation=preparation,
                montant_vendeur_centimes=montant - commission,
                montant_commission_centimes=commission,
                entrepot=(acteurs["entrepots"].get("Entrepot Lyon-Est")
                          if service == TypeService.STANDARD else None),
            )
            if preparation in (StatutPreparation.EXPEDIEE,):
                SousCommande.objects.filter(pk=sous_commande.pk).update(
                    date_expedition_entrepot=quand + datetime.timedelta(hours=3)
                )
            for produit, quantite in lignes:
                LigneCommande.objects.create(
                    sous_commande=sous_commande,
                    produit=produit,
                    nom_produit_capture=produit.nom,
                    prix_unitaire_centimes=produit.prix_unitaire_centimes,
                    quantite=quantite,
                    sous_total_centimes=produit.prix_unitaire_centimes * quantite,
                )

        commande.montant_produits_centimes = total_produits
        commande.montant_total_centimes = total_produits + frais
        commande.save(update_fields=["montant_produits_centimes", "montant_total_centimes"])

        # Le paiement suit l'etat de la commande : une commande livree qui
        # n'aurait jamais ete payee serait une incoherence visible a l'ecran.
        if statut != StatutCommande.EN_ATTENTE_PAIEMENT:
            paye = statut not in (StatutCommande.ANNULEE, StatutCommande.REMBOURSEE)
            paiement = Paiement.objects.create(
                commande=commande,
                montant_centimes=commande.montant_total_centimes,
                statut_paiement=(StatutPaiement.CAPTURE if paye else StatutPaiement.REMBOURSE),
                reference_stripe=f"pi_demo_{commande.pk:06d}",
                date_paiement=quand + datetime.timedelta(minutes=2),
            )
            for sous_commande in commande.sous_commandes.all():
                RepartitionVendeur.objects.create(
                    paiement=paiement,
                    sous_commande=sous_commande,
                    vendeur=sous_commande.vendeur,
                    montant_vendeur_centimes=sous_commande.montant_vendeur_centimes,
                    montant_commission_centimes=sous_commande.montant_commission_centimes,
                    reference_transfert_stripe=f"tr_demo_{sous_commande.pk:06d}",
                    statut="TRANSFERE" if paye else "ANNULE",
                )
            if statut == StatutCommande.LIVREE:
                Facture.objects.create(
                    commande=commande,
                    numero_facture=f"F-{commande.numero_commande[8:]}",
                    montant_ht_centimes=int(commande.montant_total_centimes / 1.2),
                    montant_ttc_centimes=commande.montant_total_centimes,
                )

        self._historique(commande, statut, quand, annulee_par)
        return commande

    def _historique(self, commande, statut_final, depart, annulee_par=""):
        """Le chemin parcouru, pas seulement le point d'arrivee.

        Un ecran de suivi qui n'affiche que le statut courant ne dit rien :
        c'est la suite des etapes qui rassure un client.
        """
        chemins = {
            TypeService.EXPRESS: [
                StatutCommande.EN_ATTENTE_PAIEMENT, StatutCommande.PAYEE,
                StatutCommande.EN_PREPARATION, StatutCommande.PRETE,
                StatutCommande.EN_LIVRAISON, StatutCommande.LIVREE,
            ],
            TypeService.STANDARD: [
                StatutCommande.EN_ATTENTE_PAIEMENT, StatutCommande.PAYEE,
                StatutCommande.EN_PREPARATION, StatutCommande.PRETE,
                StatutCommande.EXPEDIEE_ENTREPOT, StatutCommande.RECUE_ENTREPOT,
                StatutCommande.EN_TOURNEE, StatutCommande.LIVREE,
            ],
        }
        chemin = chemins[commande.type_service]
        etapes = []
        for etape in chemin:
            etapes.append(etape)
            if etape == statut_final:
                break
        else:
            # Statut hors du chemin nominal : annulation, echec, remboursement.
            etapes = chemin[:3] + [statut_final]

        precedent = ""
        for index, etape in enumerate(etapes):
            trace = HistoriqueStatut.objects.create(
                type_objet=TypeObjetSuivi.COMMANDE,
                id_objet=commande.pk,
                statut_avant=precedent,
                statut_apres=etape,
                commentaire=annulee_par if etape == StatutCommande.ANNULEE else "",
            )
            HistoriqueStatut.objects.filter(pk=trace.pk).update(
                date_changement=depart + datetime.timedelta(minutes=index * 12)
            )
            precedent = etape

    def _commandes(self, acteurs):
        """Une commande par etat, et un panier mixte qui en produit deux (D-10)."""
        E, S = TypeService.EXPRESS, TypeService.STANDARD
        creees = []

        scenarios = [
            # -- Ce qui attend Karim, maintenant --------------------------
            ("lea@exemple.fr", E, StatutCommande.PAYEE,
             [("Chez Karim", "Bol de ramen maison", 1), ("Chez Karim", "Salade de saison", 1)],
             1, StatutPreparation.A_PREPARER, 390, ""),
            ("theo@exemple.fr", E, StatutCommande.EN_PREPARATION,
             [("Chez Karim", "Pizza napolitaine", 2)],
             2, StatutPreparation.EN_PREPARATION, 390, ""),
            ("awa@exemple.fr", E, StatutCommande.PRETE,
             [("Chez Karim", "Assiette du chef", 1)],
             3, StatutPreparation.PRETE, 390, ""),

            # -- Le Fournil, pour que la deuxieme boutique Express vive ----
            ("lea@exemple.fr", E, StatutCommande.EN_LIVRAISON,
             [("Le Fournil d a cote", "Pain au levain", 2),
              ("Le Fournil d a cote", "Croissant au beurre", 4)],
             4, StatutPreparation.PRETE, 290, ""),
            ("awa@exemple.fr", E, StatutCommande.LIVREE,
             [("Le Fournil d a cote", "Flan patissier", 2)],
             28, StatutPreparation.EXPEDIEE, 290, ""),

            # -- Le circuit Standard, de bout en bout ---------------------
            ("lea@exemple.fr", S, StatutCommande.EXPEDIEE_ENTREPOT,
             [("TechSophie", "Casque a reduction de bruit", 1)],
             30, StatutPreparation.EXPEDIEE, 590, ""),
            ("theo@exemple.fr", S, StatutCommande.RECUE_ENTREPOT,
             [("Maison Perrin", "Cafe en grains, torrefaction artisanale", 2)],
             40, StatutPreparation.EXPEDIEE, 590, ""),
            ("awa@exemple.fr", S, StatutCommande.EN_TOURNEE,
             [("TechSophie", "Montre connectee", 1)],
             52, StatutPreparation.EXPEDIEE, 590, ""),
            ("lea@exemple.fr", S, StatutCommande.LIVREE,
             [("TechSophie", "Telephone reconditionne", 1)],
             120, StatutPreparation.EXPEDIEE, 0, ""),
            ("awa@exemple.fr", S, StatutCommande.LIVREE,
             [("Maison Perrin", "Miel de montagne", 3),
              ("Maison Perrin", "Huile d olive premiere pression", 1)],
             150, StatutPreparation.EXPEDIEE, 590, ""),

            # -- Une commande Standard multi-vendeur : la preuve que
            #    l'entrepot regroupe plusieurs boutiques ------------------
            ("theo@exemple.fr", S, StatutCommande.EN_PREPARATION,
             [("TechSophie", "Enceinte portable", 1),
              ("Maison Perrin", "Coffret d epices", 1)],
             6, StatutPreparation.A_PREPARER, 590, ""),

            # -- Ce qui a mal tourne, et qui doit s'afficher aussi ---------
            ("theo@exemple.fr", E, StatutCommande.ANNULEE,
             [("Chez Karim", "Tarte du jour", 2)],
             72, StatutPreparation.ANNULEE, 390,
             "Rupture de stock non detectee a temps."),
            ("marc@exemple.fr", S, StatutCommande.ECHEC_LIVRAISON,
             [("TechSophie", "Sac a dos urbain", 1)],
             96, StatutPreparation.EXPEDIEE, 690, ""),
            ("ines.client@exemple.fr", S, StatutCommande.REMBOURSEE,
             [("TechSophie", "Ordinateur portable 14 pouces", 1)],
             200, StatutPreparation.EXPEDIEE, 690, ""),

            # -- Un panier abandonne avant le paiement --------------------
            ("marc@exemple.fr", S, StatutCommande.EN_ATTENTE_PAIEMENT,
             [("Maison Perrin", "Huile d olive premiere pression", 2)],
             1, StatutPreparation.A_PREPARER, 690, ""),
        ]

        for courriel, service, statut, panier, heures, preparation, frais, motif in scenarios:
            commande = self._creer(
                acteurs, courriel, service, statut, panier, heures, preparation, frais, motif
            )
            if commande is not None:
                creees.append(commande)

        return creees

    # ── Livraisons ───────────────────────────────────────────────────────

    def _livraisons(self, acteurs, commandes):
        """Une livraison par commande payee, dans l'etat qui suit la commande."""
        correspondance = {
            StatutCommande.PAYEE: StatutLivraison.A_ATTRIBUER,
            StatutCommande.EN_PREPARATION: StatutLivraison.A_ATTRIBUER,
            StatutCommande.PRETE: StatutLivraison.ATTRIBUEE,
            StatutCommande.EN_LIVRAISON: StatutLivraison.EN_ROUTE,
            StatutCommande.EXPEDIEE_ENTREPOT: StatutLivraison.A_ATTRIBUER,
            StatutCommande.RECUE_ENTREPOT: StatutLivraison.A_ATTRIBUER,
            StatutCommande.EN_TOURNEE: StatutLivraison.EN_ROUTE,
            StatutCommande.LIVREE: StatutLivraison.LIVREE,
            StatutCommande.ECHEC_LIVRAISON: StatutLivraison.ECHOUEE,
            StatutCommande.ANNULEE: StatutLivraison.ANNULEE,
            StatutCommande.REMBOURSEE: StatutLivraison.LIVREE,
        }
        amine = acteurs["livreurs"].get("amine@exemple.fr")
        sonia = acteurs["livreurs"].get("sonia@exemple.fr")
        julien = acteurs["livreurs"].get("julien@exemple.fr")

        for commande in commandes:
            statut = correspondance.get(commande.statut_actuel)
            if statut is None:
                continue

            express = commande.type_service == TypeService.EXPRESS
            livreur = None
            if statut in (StatutLivraison.ATTRIBUEE, StatutLivraison.RECUPEREE,
                          StatutLivraison.EN_ROUTE, StatutLivraison.LIVREE,
                          StatutLivraison.ECHOUEE):
                livreur = (sonia if express and commande.pk % 2 else amine) if express else julien

            distance = round(self.hasard.uniform(0.8, 7.5), 2)
            # La remuneration du livreur est ce qu'il lit dans son
            # application (D-29) : elle doit exister meme au jeu de demo.
            remuneration = 250 + int(distance * 60)

            livraison = Livraison.objects.create(
                commande=commande,
                livreur=livreur,
                adresse_livraison=commande.adresse_livraison,
                statut_livraison=statut,
                distance_km=distance,
                frais_calcules_centimes=commande.montant_livraison_centimes,
                remuneration_livreur_centimes=remuneration,
                code_confirmation=f"{self.hasard.randint(1000, 9999)}",
                date_attribution=(commande.date_commande + datetime.timedelta(minutes=8)
                                  if livreur else None),
                date_estimee=commande.date_livraison_estimee,
                date_reelle=(commande.date_commande + datetime.timedelta(minutes=42)
                             if statut == StatutLivraison.LIVREE else None),
            )

            if statut == StatutLivraison.LIVREE:
                TentativeLivraison.objects.create(
                    livraison=livraison, numero_tentative=1,
                    resultat=ResultatTentative.LIVREE,
                    commentaire="Remis en main propre.",
                )
            elif statut == StatutLivraison.ECHOUEE:
                # Deux tentatives, puis retour (D-23) : le cas doit exister
                # pour que l'ecran sache l'afficher.
                for numero in (1, 2):
                    TentativeLivraison.objects.create(
                        livraison=livraison, numero_tentative=numero,
                        resultat=ResultatTentative.CLIENT_ABSENT,
                        commentaire="Personne a l'adresse, avis de passage depose.",
                    )

    # ── Tournees (D-44) ──────────────────────────────────────────────────

    def _tournees(self, acteurs, commandes):
        """Des tournees dans chacun de leurs etats, avec leurs arrets ordonnes.

        L'ordre des arrets n'est pas decoratif : une tournee dont les arrets
        ne sont pas ordonnes n'est pas une tournee, c'est une liste.
        """
        entrepot = acteurs["entrepots"].get("Entrepot Lyon-Est")
        rachid = acteurs["gestionnaires"].get("rachid@exemple.fr")
        julien = acteurs["livreurs"].get("julien@exemple.fr")
        if entrepot is None:
            return

        a_livrer = [
            livraison for livraison in Livraison.objects.select_related("commande")
            .filter(commande__type_service=TypeService.STANDARD, tournee__isnull=True)
            .order_by("pk")
        ]
        if not a_livrer:
            return

        def monter(livraisons, statut, livreur, debut_il_y_a=None):
            if not livraisons:
                return None
            tournee = Tournee.objects.create(
                entrepot=entrepot, livreur=livreur, cree_par=rachid,
                zone=entrepot.zones.first(), statut=statut,
                nombre_arrets=len(livraisons),
                distance_totale_km=round(sum(float(x.distance_km or 0) for x in livraisons), 2),
                date_debut=(timezone.now() - datetime.timedelta(hours=debut_il_y_a)
                            if debut_il_y_a else None),
            )
            for ordre, livraison in enumerate(livraisons, start=1):
                livraison.tournee = tournee
                livraison.save(update_fields=["tournee"])
                ArretTournee.objects.create(
                    tournee=tournee, livraison=livraison, ordre=ordre,
                    statut=(StatutArret.LIVRE
                            if livraison.statut_livraison == StatutLivraison.LIVREE
                            else StatutArret.ECHOUE
                            if livraison.statut_livraison == StatutLivraison.ECHOUEE
                            else StatutArret.A_FAIRE),
                    heure_estimee=timezone.now() + datetime.timedelta(minutes=25 * ordre),
                )
            return tournee

        # Une tournee terminee, une en cours, une prete a partir, et un
        # brouillon que le gestionnaire d'entrepot doit encore completer.
        terminees = [x for x in a_livrer if x.statut_livraison == StatutLivraison.LIVREE]
        en_cours = [x for x in a_livrer if x.statut_livraison == StatutLivraison.EN_ROUTE]
        restantes = [x for x in a_livrer if x not in terminees and x not in en_cours]

        monter(terminees[:3], StatutTournee.TERMINEE, julien, debut_il_y_a=26)
        monter(en_cours[:2], StatutTournee.EN_COURS, julien, debut_il_y_a=2)
        monter(restantes[:2], StatutTournee.PRETE, None)
        monter(restantes[2:3], StatutTournee.BROUILLON, None)

    # ── Avis, litiges, notifications ─────────────────────────────────────

    def _engagement(self, acteurs, commandes):
        livrees = [c for c in commandes if c.statut_actuel == StatutCommande.LIVREE]

        textes = [
            (5, "Commande arrivee chaude et en avance, rien a redire."),
            (4, "Tres bon produit, emballage un peu leger."),
            (5, "Le livreur a prevenu par telephone avant d'arriver, parfait."),
            (2, "Colis abime a la reception, le contenu est intact mais bon."),
        ]

        for index, commande in enumerate(livrees):
            note, texte = textes[index % len(textes)]
            sous_commande = commande.sous_commandes.first()
            if sous_commande is None:
                continue
            Avis.objects.get_or_create(
                client=commande.client, commande=commande,
                cible=CibleAvis.VENDEUR, id_cible=sous_commande.vendeur_id,
                defaults={"note": note, "commentaire": texte,
                          "statut_moderation": StatutModeration.PUBLIE},
            )
            livraison = getattr(commande, "livraison", None)
            if livraison and livraison.livreur_id:
                Avis.objects.get_or_create(
                    client=commande.client, commande=commande,
                    cible=CibleAvis.LIVREUR, id_cible=livraison.livreur_id,
                    defaults={"note": min(5, note + 1),
                              "commentaire": "Livraison rapide et polie."},
                )

        # Un avis signale : la moderation admin doit avoir de quoi travailler.
        if livrees:
            sous_commande = livrees[0].sous_commandes.first()
            if sous_commande:
                Avis.objects.get_or_create(
                    client=livrees[0].client, commande=livrees[0],
                    cible=CibleAvis.PRODUIT,
                    id_cible=sous_commande.lignes.first().produit_id,
                    defaults={"note": 1, "commentaire": "Avis signale par la boutique.",
                              "statut_moderation": StatutModeration.SIGNALE},
                )

        # Les CINQ etats d'un litige, pour que chaque case de la procedure
        # (D-94) soit visible a l'ecran sans avoir a la fabriquer a la main :
        #
        #   1. ouvert, le delai court        -> le vendeur doit repondre,
        #                                       l'admin ne peut PAS trancher
        #   2. ouvert, delai depasse         -> l'admin tranche sans la
        #                                       seconde version
        #   3. en cours, vendeur entendu     -> pret a etre arbitre
        #   4. resolu, remboursement partiel -> la vente tient encore
        #   5. rejete                        -> le versement a repris son cours
        #
        # On pioche dans les commandes dont l'histoire est FINIE : un litige ne
        # s'ouvre pas sur une livraison en cours. Une premiere version prenait
        # les commandes livrees par leur rang dans la liste, et le cinquieme
        # etat disparaissait silencieusement des qu'il y en avait moins de
        # quatre. Le compte est desormais verifie, et un manque se dit.
        maintenant = timezone.now()
        terminees = [
            commande for commande in commandes
            if commande.statut_actuel in (
                StatutCommande.LIVREE,
                StatutCommande.ECHEC_LIVRAISON,
                StatutCommande.ANNULEE,
                StatutCommande.REMBOURSEE,
            )
        ]

        etats = [
            {
                "motif": MotifLitige.INCOMPLET,
                "description": "Deux articles manquants sur les trois commandes.",
                "statut": StatutLitige.OUVERT,
                "date_limite_reponse": maintenant + datetime.timedelta(hours=31),
            },
            {
                "motif": MotifLitige.ENDOMMAGE,
                "description": "Le bocal est arrive brise, tout le contenu s'est "
                               "repandu dans le carton.",
                "statut": StatutLitige.OUVERT,
                # Le delai est passe : l'administrateur peut trancher seul.
                "date_limite_reponse": maintenant - datetime.timedelta(hours=6),
            },
            {
                "motif": MotifLitige.NON_CONFORME,
                "description": "J'ai recu un modele different de celui de la fiche "
                               "produit.",
                "statut": StatutLitige.EN_COURS,
                "date_limite_reponse": maintenant + datetime.timedelta(hours=12),
                "reponse_vendeur": "La photo de la fiche a ete mise a jour la semaine "
                                   "derniere, l'ancienne reference n'est plus en stock.",
                "date_reponse_vendeur": maintenant - datetime.timedelta(hours=3),
            },
            {
                "motif": MotifLitige.INCOMPLET,
                "description": "Il manquait un article sur les quatre de ma commande.",
                "statut": StatutLitige.RESOLU,
                "date_limite_reponse": maintenant - datetime.timedelta(days=3),
                "reponse_vendeur": "Effectivement, une reference etait en rupture au "
                                   "moment de la preparation.",
                "date_reponse_vendeur": maintenant - datetime.timedelta(days=3, hours=4),
                "resolution": "Article manquant confirme par la boutique : "
                              "remboursement de la seule ligne concernee.",
                # Partiel : la vente tient encore, la commande reste LIVREE.
                "montant_rembourse_centimes": 1500,
                "date_resolution": maintenant - datetime.timedelta(days=2),
            },
            {
                "motif": MotifLitige.NON_RECU,
                "description": "Je n'ai rien recu ce jour-la.",
                "statut": StatutLitige.REJETE,
                "date_limite_reponse": maintenant - datetime.timedelta(days=5),
                "reponse_vendeur": "Preuve de remise signee par le client a 18h12, "
                                   "photo du colis devant la porte a l'appui.",
                "date_reponse_vendeur": maintenant - datetime.timedelta(days=5, hours=6),
                "resolution": "Preuve de remise signee : la reclamation ne peut pas "
                              "prosperer.",
                "date_resolution": maintenant - datetime.timedelta(days=4),
            },
        ]

        if len(terminees) < len(etats):
            self.stdout.write(self.style.WARNING(
                f"  {len(etats) - len(terminees)} etat(s) de litige sans commande "
                f"terminee ou se poser : l'ecran d'arbitrage sera incomplet."
            ))

        for commande, details in zip(terminees, etats, strict=False):
            details = dict(details)
            if details.get("montant_rembourse_centimes"):
                details["montant_rembourse_centimes"] = min(
                    details["montant_rembourse_centimes"], commande.montant_total_centimes
                )
            dossier, cree = Litige.objects.get_or_create(
                commande=commande, client=commande.client, defaults=details,
            )
            if not cree:
                continue
            # Le versement au vendeur suit l'etat du dossier, sinon l'ecran des
            # paiements raconterait une autre histoire que celui des litiges.
            if dossier.statut in (StatutLitige.OUVERT, StatutLitige.EN_COURS):
                etat = "BLOQUE"
            elif dossier.montant_rembourse_centimes:
                etat = "REMBOURSE"
            else:
                etat = "TRANSFERE"
            RepartitionVendeur.objects.filter(
                sous_commande__commande=commande
            ).update(statut=etat)

        # Des notifications, lues et non lues : une cloche qui n'a jamais
        # rien a montrer ne prouve rien.
        for commande in commandes[:6]:
            Notification.objects.get_or_create(
                utilisateur=commande.client.utilisateur,
                type="DEMO_STATUT_COMMANDE",
                titre=f"Commande {commande.numero_commande}",
                defaults={
                    "contenu": f"Son statut est passe a "
                               f"« {commande.get_statut_actuel_display()} ».",
                    "lien_action": f"/mes-commandes/{commande.pk}",
                    "canal": CanalNotification.IN_APP,
                    "date_lecture": (timezone.now() if commande.pk % 2 else None),
                },
            )

    # ── Mouvements de stock ──────────────────────────────────────────────

    def _mouvements_de_stock(self, acteurs):
        """Un historique de stock credible, sans toucher aux quantites.

        Les mouvements sont ecrits directement plutot que par `ajuster_stock` :
        on reconstitue un passe, on ne rejoue pas des ajustements qui
        videraient les etageres.
        """
        karim = acteurs["boutiques"].get("Chez Karim")
        sophie = acteurs["boutiques"].get("TechSophie")
        auteurs = {
            "Chez Karim": karim.utilisateur if karim else None,
            "TechSophie": sophie.utilisateur if sophie else None,
        }

        modeles = [
            (TypeMouvement.REAPPRO, 20, "Livraison du matin"),
            (TypeMouvement.VENTE, -3, ""),
            (TypeMouvement.AJUSTEMENT, -2, "Casse constatee a l'inventaire"),
            (TypeMouvement.VENTE, -5, ""),
            (TypeMouvement.RETOUR, 1, "Retour client, produit intact"),
        ]

        for produit in Produit.objects.select_related("vendeur").order_by("pk")[:12]:
            if produit.mouvements.exists():
                continue
            stock = produit.stock_disponible
            for index, (type_mouvement, quantite, motif) in enumerate(reversed(modeles)):
                # On remonte le temps : le stock d'avant est celui d'apres
                # moins le mouvement.
                mouvement = MouvementStock.objects.create(
                    produit=produit,
                    auteur=auteurs.get(produit.vendeur.nom_boutique) or produit.vendeur.utilisateur,
                    type=type_mouvement,
                    quantite=quantite,
                    motif=motif,
                    stock_apres=max(0, stock),
                )
                MouvementStock.objects.filter(pk=mouvement.pk).update(
                    date_mouvement=timezone.now() - datetime.timedelta(hours=6 * (index + 1))
                )
                stock -= quantite
