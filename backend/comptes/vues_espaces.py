"""Les ecrans que la maquette prevoit et que l'API ne savait pas encore servir.

Chaque role a, dans `04-maquettes/maquettes.html`, une barre laterale dont
toutes les entrees ne menaient nulle part. Ce module comble ce qui manquait :

  client        son carnet d'adresses (D-21 : l'adresse est une entite partagee)
  vendeur       son personnel (D-04) et ses statistiques (D-29)
  admin         les utilisateurs, les litiges, le journal d'audit

Le decoupage suit la matrice des droits de `01-produit/roles-et-parcours.md`,
et il est verifie **cote serveur** : cacher une entree de menu n'a jamais ete
une permission (scenario 14.1).
"""
from django.db.models import Avg, Count, Max, Q, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Adresse,
    AdresseClient,
    Gestionnaire,
    Livreur,
    Role,
    StatutCompte,
    StatutValidation,
    Utilisateur,
    Vendeur,
)
from .permissions import EstAdmin, EstVendeur
from .serializers import AdresseSerializer, UtilisateurSerializer

# ═══════════════════════════════════════════════════════════════════════════
#  Client — le carnet d'adresses
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def mes_adresses(requete):
    """Le carnet d'adresses du client.

    Une seule adresse peut etre principale : c'est une contrainte de base
    (`une_seule_adresse_principale`), pas une convention. La respecter ici
    evite une erreur d'integrite a la place d'un message lisible.
    """
    profil = getattr(requete.user, "profil_client", None)
    if profil is None:
        return Response({"data": []})

    if requete.method == "POST":
        serializer = AdresseSerializer(data=requete.data)
        serializer.is_valid(raise_exception=True)
        adresse = serializer.save()
        principale = not AdresseClient.objects.filter(client=profil).exists()
        AdresseClient.objects.create(client=profil, adresse=adresse, est_principale=principale)
        return Response({"data": _adresses_de(profil)}, status=status.HTTP_201_CREATED)

    return Response({"data": _adresses_de(profil)})


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def modifier_adresse(requete, identifiant):
    """Modifier une adresse, la rendre principale, ou la retirer du carnet."""
    profil = getattr(requete.user, "profil_client", None)
    lien = AdresseClient.objects.filter(client=profil, adresse_id=identifiant).first()
    if profil is None or lien is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if requete.method == "DELETE":
        if lien.est_principale and AdresseClient.objects.filter(client=profil).count() > 1:
            return Response(
                {"erreur": {"code": "adresse_principale",
                            "message": "Designez d'abord une autre adresse principale.",
                            "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Suppression logique cote carnet : l'adresse elle-meme reste, parce
        # que des commandes passees la referencent (D-13).
        lien.delete()
        return Response({"data": _adresses_de(profil)})

    if requete.data.get("est_principale"):
        AdresseClient.objects.filter(client=profil, est_principale=True).update(
            est_principale=False
        )
        lien.est_principale = True
        lien.save(update_fields=["est_principale"])

    serializer = AdresseSerializer(lien.adresse, data=requete.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"data": _adresses_de(profil)})


def _adresses_de(profil):
    liens = (
        AdresseClient.objects.filter(client=profil)
        .select_related("adresse")
        .order_by("-est_principale", "adresse__libelle")
    )
    return [
        {**AdresseSerializer(lien.adresse).data, "est_principale": lien.est_principale}
        for lien in liens
    ]


# ═══════════════════════════════════════════════════════════════════════════
#  Vendeur — son personnel et ses statistiques
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["GET"])
@permission_classes([EstVendeur])
def mon_personnel(requete):
    """Les gestionnaires employes par cette boutique, et ce qu'ils voient.

    L'ecran affiche explicitement ce a quoi le personnel n'a PAS acces : c'est
    la question que se pose tout commercant avant de creer un compte pour son
    employe, et y repondre dans l'interface evite un appel au support.
    """
    profil = getattr(requete.user, "profil_vendeur", None)
    if profil is None:
        return Response({"data": {"personnel": [], "acces": []}})

    from catalogue.models import MouvementStock
    from commandes.models import HistoriqueStatut

    personnel = Gestionnaire.objects.filter(vendeur=profil).select_related("utilisateur")

    # Ce que chaque employe a REELLEMENT fait (D-80). « Le vendeur et le
    # gestionnaire se marchent sur les pieds, et les actions de l'un ne sont
    # pas mises a jour chez l'autre » : les deux ecrans affichaient les memes
    # compteurs et aucun ne disait QUI avait agi.
    comptes = [gestionnaire.utilisateur_id for gestionnaire in personnel]
    ajustements = dict(
        MouvementStock.objects.filter(auteur_id__in=comptes)
        .values_list("auteur_id")
        .annotate(nombre=Count("id"))
    )
    preparations = dict(
        HistoriqueStatut.objects.filter(
            utilisateur_id__in=comptes, type_objet="SOUS_COMMANDE"
        )
        .values_list("utilisateur_id")
        .annotate(nombre=Count("id"))
    )
    dernieres = dict(
        MouvementStock.objects.filter(auteur_id__in=comptes)
        .values_list("auteur_id")
        .annotate(quand=Max("date_mouvement"))
    )

    return Response({"data": {
        "personnel": [
            {
                "id": gestionnaire.id,
                "utilisateur": UtilisateurSerializer(gestionnaire.utilisateur).data,
                "date_embauche": gestionnaire.date_embauche,
                "commandes_preparees": preparations.get(gestionnaire.utilisateur_id, 0),
                "ajustements_stock": ajustements.get(gestionnaire.utilisateur_id, 0),
                "derniere_action": dernieres.get(gestionnaire.utilisateur_id),
                # L'ecran doit pouvoir dire d'un coup d'oeil qui peut encore
                # entrer. Sans ce champ, un compte suspendu ressemblait a un
                # compte actif, et le vendeur n'avait aucun moyen de le voir.
                "statut_compte": gestionnaire.utilisateur.statut_compte,
                "actif": gestionnaire.utilisateur.statut_compte == StatutCompte.ACTIF,
                "derniere_connexion": gestionnaire.utilisateur.last_login,
            }
            for gestionnaire in personnel
        ],
        "acces": [
            {"libelle": "Preparer les commandes recues", "autorise": True},
            {"libelle": "Ajuster le stock, avec motif", "autorise": True},
            {"libelle": "Voir et modifier les prix", "autorise": False},
            {"libelle": "Voir le chiffre d'affaires", "autorise": False},
            {"libelle": "Publier ou retirer un produit", "autorise": False},
        ],
    }})


@api_view(["GET"])
@permission_classes([EstVendeur])
def statistiques_vendeur(requete):
    """Le chiffre d'affaires, ce qui se vend, et ce qu'on pense de la boutique.

    Reserve au vendeur : le personnel n'a jamais acces au chiffre d'affaires
    (D-04), et cela se verifie ici, pas en masquant une entree de menu.
    """
    from commandes.models import LigneCommande, SousCommande, StatutCommande
    from engagement.models import Avis, CibleAvis

    profil = getattr(requete.user, "profil_vendeur", None)
    if profil is None:
        return Response({"data": {}})

    sous_commandes = SousCommande.objects.filter(vendeur=profil).select_related("commande")
    payees = sous_commandes.exclude(
        commande__statut_actuel__in=[
            StatutCommande.EN_ATTENTE_PAIEMENT, StatutCommande.ANNULEE,
        ]
    )

    # Le chiffre d'affaires des trente derniers jours, jour par jour : c'est
    # la seule forme ou une courbe veut dire quelque chose pour un commercant.
    depuis = timezone.now() - timezone.timedelta(days=30)
    par_jour = {}
    for sous_commande in payees.filter(commande__date_commande__gte=depuis):
        jour = timezone.localtime(sous_commande.commande.date_commande).date().isoformat()
        entree = par_jour.setdefault(jour, {"jour": jour, "commandes": 0, "montant_centimes": 0})
        entree["commandes"] += 1
        entree["montant_centimes"] += sous_commande.montant_vendeur_centimes

    meilleurs = (
        LigneCommande.objects.filter(sous_commande__in=payees)
        .values("nom_produit_capture")
        .annotate(
            quantite=Sum("quantite"),
            montant_centimes=Sum("sous_total_centimes"),
        )
        .order_by("-quantite")[:8]
    )

    avis = Avis.objects.filter(cible=CibleAvis.VENDEUR, id_cible=profil.id)

    return Response({"data": {
        "commandes": payees.count(),
        "revenu_centimes": payees.aggregate(
            total=Sum("montant_vendeur_centimes"))["total"] or 0,
        "commission_centimes": payees.aggregate(
            total=Sum("montant_commission_centimes"))["total"] or 0,
        "taux_commission": float(profil.taux_commission),
        "panier_moyen_centimes": int(
            (payees.aggregate(total=Sum("montant_vendeur_centimes"))["total"] or 0)
            / max(1, payees.count())
        ),
        "par_jour": sorted(par_jour.values(), key=lambda entree: entree["jour"]),
        "meilleurs_produits": list(meilleurs),
        "note_moyenne": round(avis.aggregate(note=Avg("note"))["note"] or 0, 2),
        "nombre_avis": avis.count(),
        "derniers_avis": [
            {
                "note": element.note,
                "commentaire": element.commentaire,
                "date": element.date_avis,
                "statut": element.statut_moderation,
            }
            for element in avis.order_by("-date_avis")[:5]
        ],
    }})


@api_view(["GET"])
@permission_classes([EstVendeur])
def avis_recus(requete):
    """Les avis qui concernent cette boutique, ses produits et ses livraisons."""
    from engagement.models import Avis, CibleAvis

    profil = getattr(requete.user, "profil_vendeur", None)
    if profil is None:
        return Response({"data": []})

    identifiants_produits = list(
        profil.produits.values_list("id", flat=True)
        if hasattr(profil, "produits")
        else []
    )
    avis = (
        Avis.objects.filter(
            Q(cible=CibleAvis.VENDEUR, id_cible=profil.id)
            | Q(cible=CibleAvis.PRODUIT, id_cible__in=identifiants_produits)
        )
        .select_related("client__utilisateur", "commande")
        .order_by("-date_avis")
    )
    return Response({"data": [
        {
            "id": element.id,
            "note": element.note,
            "commentaire": element.commentaire,
            "cible": element.cible,
            "statut_moderation": element.statut_moderation,
            "date": element.date_avis,
            "client": element.client.utilisateur.prenom,
            "commande": element.commande.numero_commande,
        }
        for element in avis
    ]})


# ═══════════════════════════════════════════════════════════════════════════
#  Admin — utilisateurs, litiges, journal
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["GET"])
@permission_classes([EstAdmin])
def utilisateurs(requete):
    """Tous les comptes, filtrables par role et par statut."""
    comptes = Utilisateur.objects.all().order_by("-date_joined")

    if role := requete.query_params.get("role"):
        comptes = comptes.filter(role=role)
    if statut := requete.query_params.get("statut"):
        comptes = comptes.filter(statut_compte=statut)
    if recherche := requete.query_params.get("recherche"):
        comptes = comptes.filter(
            Q(email__icontains=recherche)
            | Q(nom__icontains=recherche)
            | Q(prenom__icontains=recherche)
        )

    return Response({"data": {
        "utilisateurs": [
            {
                **UtilisateurSerializer(compte).data,
                "statut_compte": compte.statut_compte,
                "date_inscription": compte.date_joined,
                "rattachement": _rattachement(compte),
            }
            for compte in comptes[:200]
        ],
        "repartition": list(
            Utilisateur.objects.values("role").annotate(nombre=Count("id")).order_by("role")
        ),
        "total": comptes.count(),
    }})


def _rattachement(compte):
    """En une ligne : la boutique, l'entrepot ou le mode de livraison."""
    if compte.role == Role.VENDEUR:
        profil = getattr(compte, "profil_vendeur", None)
        return f"{profil.nom_boutique} ({profil.get_type_activite_display()})" if profil else ""
    if compte.role == Role.LIVREUR:
        profil = getattr(compte, "profil_livreur", None)
        return profil.get_mode_livraison_display() if profil else ""
    if compte.role == Role.GESTIONNAIRE:
        profil = getattr(compte, "profil_gestionnaire", None)
        if not profil:
            return ""
        return profil.vendeur.nom_boutique if profil.vendeur_id else (
            profil.entrepot.nom if profil.entrepot_id else ""
        )
    return ""


@api_view(["POST"])
@permission_classes([EstAdmin])
def suspendre(requete, identifiant):
    """Suspendre ou reactiver un compte.

    Jamais de suppression : les commandes passees referencent ce compte, et
    une plateforme qui efface ses utilisateurs efface ses preuves (D-13).
    """
    compte = Utilisateur.objects.filter(pk=identifiant).first()
    if compte is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if compte.role == Role.ADMIN:
        return Response(
            {"erreur": {"code": "non_autorise",
                        "message": "Un administrateur ne se suspend pas depuis cet ecran.",
                        "details": {}}},
            status=status.HTTP_403_FORBIDDEN,
        )

    compte.statut_compte = (
        StatutCompte.ACTIF if compte.statut_compte == StatutCompte.SUSPENDU
        else StatutCompte.SUSPENDU
    )
    compte.save(update_fields=["statut_compte"])
    return Response({"data": {"id": compte.id, "statut_compte": compte.statut_compte}})


@api_view(["GET"])
@permission_classes([EstAdmin])
def litiges(requete):
    """Les litiges, ouverts d'abord : c'est ce qui attend un arbitrage.

    La forme d'un dossier vient de `engagement.vues_litiges` et non d'ici :
    trois representations divergentes du meme objet — une par role — finissent
    toujours par se contredire, et c'est l'ecran qui ment.
    """
    from engagement.models import Litige, StatutLitige
    from engagement.vues_litiges import _en_dictionnaire

    dossiers = (
        Litige.objects.select_related("client__utilisateur", "commande")
        .prefetch_related("commande__sous_commandes__vendeur")
        .order_by("-date_ouverture")
    )
    if statut := requete.query_params.get("statut"):
        dossiers = dossiers.filter(statut=statut)

    return Response({"data": {
        "litiges": [_en_dictionnaire(dossier, pour="admin") for dossier in dossiers[:100]],
        "ouverts": Litige.objects.filter(statut=StatutLitige.OUVERT).count(),
        "en_cours": Litige.objects.filter(statut=StatutLitige.EN_COURS).count(),
        "resolus": Litige.objects.filter(statut=StatutLitige.RESOLU).count(),
        # Ce qui attend vraiment une decision : le vendeur a parle, ou son
        # delai est passe. Le reste attend encore la seconde version.
        "a_arbitrer": sum(
            1 for d in Litige.objects.filter(
                statut__in=[StatutLitige.OUVERT, StatutLitige.EN_COURS]
            ) if d.arbitrable
        ),
    }})


@api_view(["GET"])
@permission_classes([EstAdmin])
def journal_audit(requete):
    """Le journal : qui a change quoi, quand, et pourquoi (D-95).

    Il reunit DEUX sources, parce que le systeme trace a deux endroits et que
    l'ecran ne doit pas en montrer un seul :

      · `JournalAudit`      les decisions — valider, suspendre, arbitrer, et
                            tout ce qui passe par le fil d'evenements ;
      · `HistoriqueStatut`  les changements de statut de commande, qu'on relit
                            quand un client conteste.

    Ne montrer que la seconde, comme avant, donnait un journal ou aucune
    decision d'administration n'apparaissait — donc un journal d'audit qui
    n'auditait rien.
    """
    from commandes.models import HistoriqueStatut
    from engagement.models import JournalAudit

    entrees = []

    for trace in JournalAudit.objects.select_related("utilisateur")[:150]:
        apres = trace.donnees_apres or {}
        entrees.append({
            "id": f"audit-{trace.id}",
            "source": "DECISION",
            "type_objet": trace.type_objet,
            "id_objet": trace.id_objet,
            "action": trace.action,
            "statut_avant": str((trace.donnees_avant or {}).get("statut_validation")
                                or (trace.donnees_avant or {}).get("statut_compte") or ""),
            "statut_apres": str(apres.get("statut_validation")
                                or apres.get("statut_compte") or trace.action),
            "commentaire": str(apres.get("motif", "")),
            "date": trace.date_action,
            "par": str(trace.utilisateur) if trace.utilisateur_id else "systeme",
        })

    for trace in HistoriqueStatut.objects.select_related("utilisateur")[:150]:
        entrees.append({
            "id": f"statut-{trace.id}",
            "source": "STATUT",
            "type_objet": trace.type_objet,
            "id_objet": trace.id_objet,
            "action": "CHANGEMENT_STATUT",
            "statut_avant": trace.statut_avant,
            "statut_apres": trace.statut_apres,
            "commentaire": trace.commentaire,
            "date": trace.date_changement,
            "par": str(trace.utilisateur) if trace.utilisateur_id else "systeme",
        })

    entrees.sort(key=lambda entree: entree["date"], reverse=True)
    return Response({"data": entrees[:200]})


@api_view(["GET"])
@permission_classes([EstAdmin])
def boutiques_admin(requete):
    """Toutes les boutiques, quel que soit leur statut de validation.

    L'ecran de validation ne montrait que ce qui attend une decision : on ne
    savait jamais ce qu'un dossier refuse etait devenu.
    """
    boutiques = (
        Vendeur.objects.select_related("utilisateur", "adresse")
        .annotate(
            # `produits` et `commandes` sont deja des relations inverses du
            # modele : une annotation qui reprend leur nom leve une erreur.
            nombre_produits=Count(
                "produits", filter=Q(produits__est_visible=True), distinct=True
            ),
            nombre_commandes=Count("sous_commandes", distinct=True),
        )
        .order_by("statut_validation", "nom_boutique")
    )
    return Response({"data": [
        {
            "id": boutique.id,
            "nom_boutique": boutique.nom_boutique,
            "type_activite": boutique.type_activite,
            "statut_validation": boutique.statut_validation,
            "ville": boutique.adresse.ville if boutique.adresse_id else "",
            "responsable": f"{boutique.utilisateur.prenom} {boutique.utilisateur.nom}".strip(),
            "email": boutique.utilisateur.email,
            "produits": boutique.nombre_produits,
            "commandes": boutique.nombre_commandes,
            "description": boutique.description,
        }
        for boutique in boutiques
    ]})


@api_view(["GET"])
@permission_classes([EstAdmin])
def livreurs_admin(requete):
    """Les livreurs, leur mode, leur entrepot et leur disponibilite."""
    livreurs = Livreur.objects.select_related("utilisateur", "entrepot").order_by(
        "statut_validation", "utilisateur__nom"
    )
    return Response({"data": [
        {
            "id": livreur.id,
            "nom": f"{livreur.utilisateur.prenom} {livreur.utilisateur.nom}".strip(),
            "email": livreur.utilisateur.email,
            "mode_livraison": livreur.mode_livraison,
            "vehicule": livreur.get_vehicule_display(),
            "entrepot": livreur.entrepot.nom if livreur.entrepot_id else "",
            "statut_validation": livreur.statut_validation,
            "statut_disponibilite": livreur.statut_disponibilite,
            "livraisons": livreur.livraisons.count(),
        }
        for livreur in livreurs
    ]})


def _compte_par_statut(modele):
    return {
        statut: modele.objects.filter(statut_validation=statut).count()
        for statut, _ in StatutValidation.choices
    }


@api_view(["GET"])
@permission_classes([EstAdmin])
def resume_validations(requete):
    """Combien de dossiers dans chaque etat, vendeurs et livreurs confondus."""
    return Response({"data": {
        "vendeurs": _compte_par_statut(Vendeur),
        "livreurs": _compte_par_statut(Livreur),
    }})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mes_notifications(requete):
    """La cloche de la navbar. Elle existait sans jamais rien afficher."""
    from engagement.models import Notification

    notifications = Notification.objects.filter(utilisateur=requete.user)[:30]
    return Response({"data": {
        "notifications": [
            {
                "id": notification.id,
                "titre": notification.titre,
                "contenu": notification.contenu,
                "lien": notification.lien_action,
                "date": notification.date_envoi,
                "lue": notification.date_lecture is not None,
            }
            for notification in notifications
        ],
        "non_lues": Notification.objects.filter(
            utilisateur=requete.user, date_lecture__isnull=True
        ).count(),
    }})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def marquer_notifications_lues(requete):
    from engagement.models import Notification

    Notification.objects.filter(utilisateur=requete.user, date_lecture__isnull=True).update(
        date_lecture=timezone.now()
    )
    return Response({"data": {"non_lues": 0}})


# Adresse est importee pour le serializer ; la garder explicite evite un
# import fantome que le prochain lecteur croirait inutile.
__all__ = [
    "Adresse",
    "avis_recus",
    "boutiques_admin",
    "journal_audit",
    "litiges",
    "livreurs_admin",
    "marquer_notifications_lues",
    "mes_adresses",
    "mes_notifications",
    "modifier_adresse",
    "mon_personnel",
    "resume_validations",
    "statistiques_vendeur",
    "suspendre",
    "utilisateurs",
]


# ═══════════════════════════════════════════════════════════════════════════
#  Client — les avis
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def avis_de_commande(requete, identifiant):
    """L'avis du client sur une commande livree.

    Trois regles, toutes tenues cote serveur :

      · **on ne note que ce qu'on a recu** (R-06) : la commande doit etre
        livree. Autoriser un avis avant livraison ouvre la porte aux faux ;
      · **on ne note que ses propres commandes** ;
      · **un seul avis par cible et par commande** — la boutique, le livreur,
        et chaque produit recu.
    """
    from commandes.models import Commande, StatutCommande
    from engagement.models import Avis, CibleAvis

    profil = getattr(requete.user, "profil_client", None)
    if profil is None:
        return Response(status=status.HTTP_403_FORBIDDEN)

    commande = (
        Commande.objects.filter(pk=identifiant, client=profil)
        .prefetch_related("sous_commandes__vendeur", "sous_commandes__lignes__produit")
        .first()
    )
    if commande is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    deja = {
        (avis.cible, avis.id_cible): avis
        for avis in Avis.objects.filter(client=profil, commande=commande)
    }

    if requete.method == "POST":
        if commande.statut_actuel != StatutCommande.LIVREE:
            return Response(
                {"erreur": {"code": "pas_encore_livree",
                            "message": "On ne note que ce qu'on a recu : "
                                       "attendez la livraison.",
                            "details": {}}},
                status=status.HTTP_409_CONFLICT,
            )

        cible = requete.data.get("cible")
        id_cible = requete.data.get("id_cible")
        note = requete.data.get("note")
        if cible not in CibleAvis.values or not id_cible:
            return Response(
                {"erreur": {"code": "cible_invalide",
                            "message": "Precisez ce que vous notez.", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            note = int(note)
        except (TypeError, ValueError):
            note = 0
        if not 1 <= note <= 5:
            return Response(
                {"erreur": {"code": "note_invalide",
                            "message": "La note va de 1 a 5.", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verifier que la cible appartient bien a CETTE commande : sans cela,
        # un client pourrait noter n'importe quelle boutique en changeant un
        # identifiant dans la requete.
        if not _cible_appartient(commande, cible, int(id_cible)):
            return Response(
                {"erreur": {"code": "cible_hors_commande",
                            "message": "Cet element ne fait pas partie de la commande.",
                            "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        avis, _ = Avis.objects.update_or_create(
            client=profil, commande=commande, cible=cible, id_cible=int(id_cible),
            defaults={"note": note,
                      "commentaire": str(requete.data.get("commentaire", ""))[:2000]},
        )
        deja[(avis.cible, avis.id_cible)] = avis

    return Response({"data": _avis_possibles(commande, deja)})


def _cible_appartient(commande, cible, id_cible):
    from engagement.models import CibleAvis

    if cible == CibleAvis.VENDEUR:
        return commande.sous_commandes.filter(vendeur_id=id_cible).exists()
    if cible == CibleAvis.PRODUIT:
        return commande.sous_commandes.filter(lignes__produit_id=id_cible).exists()
    if cible == CibleAvis.LIVREUR:
        livraison = getattr(commande, "livraison", None)
        return bool(livraison and livraison.livreur_id == id_cible)
    return False


def _avis_possibles(commande, deja):
    """Ce que ce client peut noter sur cette commande, et ce qu'il a deja note.

    L'ecran n'a ainsi rien a deviner : il affiche la liste telle quelle.
    """
    from commandes.models import StatutCommande
    from engagement.models import CibleAvis

    elements = []
    for sous_commande in commande.sous_commandes.all():
        elements.append({
            "cible": CibleAvis.VENDEUR,
            "id_cible": sous_commande.vendeur_id,
            "libelle": sous_commande.vendeur.nom_boutique,
            "sous_titre": "La boutique",
        })
        for ligne in sous_commande.lignes.all():
            if ligne.produit_id:
                elements.append({
                    "cible": CibleAvis.PRODUIT,
                    "id_cible": ligne.produit_id,
                    "libelle": ligne.nom_produit_capture,
                    "sous_titre": "Le produit",
                })

    livraison = getattr(commande, "livraison", None)
    if livraison and livraison.livreur_id:
        utilisateur = livraison.livreur.utilisateur
        elements.append({
            "cible": CibleAvis.LIVREUR,
            "id_cible": livraison.livreur_id,
            "libelle": utilisateur.prenom,
            "sous_titre": "Le livreur",
        })

    for element in elements:
        avis = deja.get((element["cible"], element["id_cible"]))
        element["note"] = avis.note if avis else None
        element["commentaire"] = avis.commentaire if avis else ""

    return {
        "livree": commande.statut_actuel == StatutCommande.LIVREE,
        "elements": elements,
    }
