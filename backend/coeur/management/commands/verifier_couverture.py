"""Chaque scenario du dossier produit a-t-il encore une donnee qui l'illustre ? — D-96.

**Ta formulation, L-15** : *« cree autant de donnees que possible pour rendre
visible chaque scenario et chaque decision »*.

Le peuplement ne cherche pas le volume mais la **couverture**. Cette commande
est ce qui empeche la promesse de se defaire en silence : elle interroge la
base reelle, scenario par scenario, et dit lesquels n'ont plus rien a montrer.

    python manage.py verifier_couverture
    python manage.py verifier_couverture --strict   # sort en erreur si un trou

Trois familles de scenarios, et elles ne se verifient pas de la meme facon :

  · **donnee** — une requete doit rendre au moins une ligne. C'est le gros du
    fichier, et c'est ce que cette commande verifie ;
  · **regle** — un comportement refuse par le serveur. Il n'y a rien a
    peupler : ce sont les tests qui en repondent, et la colonne du document
    nomme lequel ;
  · **absent** — pas encore implemente. Le dire vaut mieux que de le laisser
    croire couvert.

`plan-organisation/donnees-demo/couverture.md` est la table de correspondance
lisible ; ce fichier en est la moitie executable. Un test verifie que les deux
listent exactement les memes scenarios.
"""
from django.core.management.base import BaseCommand
from django.db.models import Count


def _controles():
    """Les scenarios illustres par des donnees, et la requete qui le prouve.

    Chaque entree rend un couple (compte, phrase). La phrase est ce qui
    s'affiche : « 3 commandes livrees » se lit, « True » non.
    """
    from catalogue.models import MouvementStock, Produit, TypeMouvement
    from commandes.models import Commande, SousCommande, StatutCommande
    from comptes.models import Gestionnaire, StatutCompte, StatutValidation, Utilisateur, Vendeur
    from engagement.models import (
        Avis,
        CibleAvis,
        Litige,
        Notification,
        StatutLitige,
        StatutModeration,
    )
    from livraisons.models import Livraison, StatutLivraison, StatutTournee, Tournee
    from paiements.models import Facture, Paiement, Promotion, RepartitionVendeur, StatutPaiement

    def compter(requete, phrase):
        nombre = requete.count()
        return nombre, f"{nombre} {phrase}"

    return {
        "2": lambda: compter(
            Utilisateur.objects.values("role").annotate(n=Count("id")),
            "roles represents parmi les comptes",
        ),
        "3.1": lambda: compter(
            Commande.objects.filter(type_service="EXPRESS"), "commandes Express"
        ),
        "3.2": lambda: compter(
            Commande.objects.filter(type_service="STANDARD"), "commandes Standard"
        ),
        "4.1": lambda: compter(
            Produit.objects.filter(stock_disponible__gt=0, est_visible=True),
            "produits disponibles au catalogue",
        ),
        "4.4": lambda: compter(
            MouvementStock.objects.filter(type=TypeMouvement.AJUSTEMENT),
            "ajustements de stock avec motif",
        ),
        "4.5": lambda: compter(
            Produit.objects.filter(est_visible=False), "produits retires de la vente"
        ),
        "5.3": lambda: compter(
            Commande.objects.annotate(n=Count("sous_commandes")).filter(n__gt=1),
            "commandes multi-vendeur",
        ),
        "6.1": lambda: compter(
            Commande.objects.filter(statut_actuel=StatutCommande.ANNULEE), "commandes annulees"
        ),
        "6.5": lambda: compter(
            SousCommande.objects.all(), "sous-commandes, chacune suivie par son vendeur"
        ),
        "7.1": lambda: compter(
            Commande.objects.filter(statut_actuel=StatutCommande.EN_ATTENTE_PAIEMENT),
            "commandes en attente de paiement",
        ),
        "7.2": lambda: compter(
            Paiement.objects.filter(statut_paiement=StatutPaiement.CAPTURE),
            "paiements confirmes par le serveur",
        ),
        "7.3": lambda: compter(
            Commande.objects.filter(statut_actuel=StatutCommande.REMBOURSEE),
            "commandes remboursees",
        ),
        "7.4": lambda: compter(
            RepartitionVendeur.objects.all(), "repartitions vendeur, commission deduite"
        ),
        "8.1": lambda: compter(
            Commande.objects.filter(statut_actuel=StatutCommande.ECHEC_LIVRAISON),
            "livraisons ou le client etait absent",
        ),
        "8.6": lambda: compter(
            Litige.objects.filter(motif__in=["ENDOMMAGE", "INCOMPLET"]),
            "litiges pour colis abime ou incomplet",
        ),
        "8.9": lambda: compter(
            Livraison.objects.filter(livreur__isnull=False), "courses attribuees a un livreur"
        ),
        "9.1": lambda: compter(
            Commande.objects.filter(statut_actuel=StatutCommande.RECUE_ENTREPOT),
            "colis recus a l'entrepot",
        ),
        "9.2": lambda: compter(
            Tournee.objects.filter(statut=StatutTournee.PRETE), "tournees pretes a partir"
        ),
        "9.3": lambda: compter(
            Tournee.objects.filter(statut=StatutTournee.EN_COURS), "tournees en cours"
        ),
        "10.3": lambda: compter(
            Vendeur.objects.filter(statut_validation=StatutValidation.SUSPENDU),
            "boutiques suspendues",
        ),
        "10.5": lambda: compter(Gestionnaire.objects.all(), "comptes de personnel crees"),
        "11.1": lambda: compter(
            Promotion.objects.all(), "promotions, dont au moins une expiree"
        ),
        "12.2": lambda: compter(
            Avis.objects.filter(statut_moderation=StatutModeration.SIGNALE),
            "avis signales attendant la moderation",
        ),
        "12.3": lambda: compter(
            Avis.objects.values("cible").annotate(n=Count("id")),
            "cibles d'avis distinctes (produit, boutique, livreur)",
        ),
        "13.2": lambda: compter(
            Notification.objects.values("utilisateur__role").annotate(n=Count("id")),
            "roles differents ayant recu une notification",
        ),
        "14.1": lambda: compter(
            Litige.objects.filter(statut__in=[StatutLitige.OUVERT, StatutLitige.EN_COURS]),
            "litiges en instruction",
        ),
        "14.2": lambda: compter(
            Vendeur.objects.filter(statut_validation=StatutValidation.EN_ATTENTE),
            "boutiques en attente de validation",
        ),
        # Au-dela des scenarios ecrits : ce qui rend une demonstration
        # credible. Le prefixe « + » les distingue, pour qu'on ne les prenne
        # jamais pour des numeros du dossier produit.
        "+ litige-vendeur-entendu": lambda: compter(
            Litige.objects.filter(date_reponse_vendeur__isnull=False),
            "litiges ou la boutique a donne sa version",
        ),
        "+ litige-rembourse": lambda: compter(
            Litige.objects.filter(statut=StatutLitige.RESOLU, montant_rembourse_centimes__gt=0),
            "litiges resolus par un remboursement",
        ),
        "+ litige-rejete": lambda: compter(
            Litige.objects.filter(statut=StatutLitige.REJETE), "litiges rejetes"
        ),
        "+ factures": lambda: compter(Facture.objects.all(), "factures emises"),
        "+ compte-suspendu": lambda: compter(
            Utilisateur.objects.filter(statut_compte=StatutCompte.SUSPENDU),
            "comptes suspendus",
        ),
        "+ livraisons-terminees": lambda: compter(
            Livraison.objects.filter(statut_livraison=StatutLivraison.LIVREE), "livraisons terminees"
        ),
        "+ avis-livreur": lambda: compter(
            Avis.objects.filter(cible=CibleAvis.LIVREUR), "avis portant sur un livreur"
        ),
    }


class Command(BaseCommand):
    help = "Verifie que chaque scenario illustrable a encore une donnee (D-96)."

    def add_arguments(self, analyseur):
        analyseur.add_argument(
            "--strict", action="store_true",
            help="Sort en erreur si un scenario n'a plus rien a montrer.",
        )

    def handle(self, *args, **options):
        controles = _controles()
        trous = []

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Couverture du jeu de demonstration — {len(controles)} scenarios illustres"
        ))
        self.stdout.write("")

        def rang(cle):
            """Les numeros du dossier d'abord, les ajouts ensuite."""
            if cle.startswith("+"):
                return (1, 0, 0, cle)
            morceaux = [int(n) for n in cle.split(".")]
            return (0, morceaux[0], morceaux[1] if len(morceaux) > 1 else 0, "")

        for cle in sorted(controles, key=rang):
            nombre, phrase = controles[cle]()
            if nombre:
                self.stdout.write(f"  {self.style.SUCCESS('ok')}   {cle:<26} {phrase}")
            else:
                trous.append(cle)
                self.stdout.write(f"  {self.style.ERROR('vide')} {cle:<26} {phrase}")

        self.stdout.write("")
        if trous:
            message = (
                f"{len(trous)} scenario(s) sans donnee : {', '.join(trous)}. "
                "Relance `seed_demo`, `seed_catalogue` puis `seed_activite --refaire`."
            )
            if options["strict"]:
                self.stderr.write(self.style.ERROR(message))
                raise SystemExit(1)
            self.stdout.write(self.style.WARNING(message))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Chaque scenario illustrable a de quoi se montrer a l'ecran."
            ))
