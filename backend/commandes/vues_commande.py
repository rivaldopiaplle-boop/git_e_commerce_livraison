"""Passer commande, suivre ses commandes, preparer celles qu'on recoit."""
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from coeur.adresses import VENDEUR, adresse_pour
from comptes.models import Adresse, AdresseClient
from comptes.permissions import EstClient, EstVendeurOuSonPersonnel

from .decoupage import PanierInvalide, apercu, decouper
from .models import (
    Commande,
    HistoriqueStatut,
    SousCommande,
    StatutCommande,
    StatutPreparation,
    TypeObjetSuivi,
)
from .serializers_commande import CommandeSerializer, SousCommandeSerializer
from .services import panier_courant

# Ce qu'un vendeur peut faire avancer, et rien d'autre. Un menu libre de
# statuts laisserait passer « livree » depuis « en attente de paiement ».
SUITE_PREPARATION = {
    StatutPreparation.A_PREPARER: [StatutPreparation.EN_PREPARATION, StatutPreparation.ANNULEE],
    StatutPreparation.EN_PREPARATION: [StatutPreparation.PRETE, StatutPreparation.ANNULEE],
    StatutPreparation.PRETE: [StatutPreparation.EXPEDIEE],
    StatutPreparation.EXPEDIEE: [],
    StatutPreparation.ANNULEE: [],
}


@api_view(["GET"])
@permission_classes([AllowAny])
def apercu_commandes(requete):
    """Ce que le panier donnera, avant tout engagement.

    Le client doit savoir qu'il s'apprete a creer trois commandes livrees
    separement (D-10) — le decouvrir apres le paiement serait une mauvaise
    surprise.
    """
    panier = panier_courant(requete.user, requete.META.get("HTTP_X_PANIER_SESSION", "")[:64],
                            creer=False)
    if panier is None:
        return Response({"data": {"commandes": [], "total_centimes": 0}})

    try:
        return Response({"data": apercu(panier)})
    except PanierInvalide as refus:
        return Response(
            {"erreur": {"code": "panier", "message": str(refus), "details": {}}},
            status=status.HTTP_409_CONFLICT,
        )


@api_view(["POST"])
@permission_classes([EstClient])
@transaction.atomic
def creer_commandes(requete):
    """Le compte n'est exige qu'ici : on regarde et on remplit son panier sans
    lui, on ne commande pas sans (D-03)."""
    profil = getattr(requete.user, "profil_client", None)
    if profil is None:
        return Response(
            {"erreur": {"code": "profil_absent", "message": "Aucun profil client.",
                        "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    panier = panier_courant(requete.user, "", creer=False)
    if panier is None or not panier.lignes.exists():
        return Response(
            {"erreur": {"code": "panier_vide", "message": "Votre panier est vide.",
                        "details": {}}},
            status=status.HTTP_409_CONFLICT,
        )

    adresse = _adresse_de_livraison(requete, profil)
    if adresse is None:
        return Response(
            {"erreur": {"code": "adresse_absente",
                        "message": "Indiquez une adresse de livraison.", "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        commandes = decouper(panier, profil, adresse)
    except PanierInvalide as refus:
        return Response(
            {"erreur": {"code": "panier", "message": str(refus), "details": {}}},
            status=status.HTTP_409_CONFLICT,
        )

    for commande in commandes:
        HistoriqueStatut.objects.create(
            type_objet="COMMANDE", id_objet=commande.id, statut_avant="",
            statut_apres=commande.statut_actuel, utilisateur=requete.user,
            commentaire="Commande creee",
        )

    return Response(
        {"data": CommandeSerializer(commandes, many=True, context={"request": requete}).data},
        status=status.HTTP_201_CREATED,
    )


def _adresse_de_livraison(requete, profil):
    """Celle demandee, celle du carnet, ou celle qu'on vient de saisir."""
    identifiant = requete.data.get("id_adresse")
    if identifiant:
        return Adresse.objects.filter(pk=identifiant, clients=profil).first()

    nouvelle = requete.data.get("adresse")
    if nouvelle:
        rue = str(nouvelle.get("rue", "")).strip()
        ville = str(nouvelle.get("ville", "")).strip()
        code_postal = str(nouvelle.get("code_postal", "")).strip()
        complement = str(nouvelle.get("complement", "")).strip()

        # On REUTILISE une adresse identique deja au carnet plutot que d'en
        # creer une copie. Sans cela, commander trois fois chez soi remplissait
        # le carnet de trois lignes rigoureusement identiques : le client ne
        # savait plus laquelle choisir, et le tunnel de commande devenait
        # illisible au bout de quelques achats.
        adresse = Adresse.objects.filter(
            clients=profil, rue__iexact=rue, ville__iexact=ville,
            code_postal=code_postal, complement__iexact=complement,
        ).first()

        if adresse is None:
            adresse = Adresse.objects.create(
                libelle=nouvelle.get("libelle", "Livraison"),
                rue=rue,
                complement=complement,
                ville=ville,
                code_postal=code_postal,
                instructions_livraison=nouvelle.get("instructions_livraison", ""),
            )
        AdresseClient.objects.get_or_create(
            client=profil, adresse=adresse,
            defaults={"est_principale": not profil.adresses.exists()},
        )
        return adresse

    lien = AdresseClient.objects.filter(client=profil).order_by("-est_principale").first()
    return lien.adresse if lien else None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mes_commandes(requete):
    profil = getattr(requete.user, "profil_client", None)
    if profil is None:
        return Response({"data": []})

    commandes = (
        Commande.objects.filter(client=profil)
        .prefetch_related("sous_commandes__lignes", "sous_commandes__vendeur")
        .select_related("adresse_livraison")
    )
    return Response({"data": CommandeSerializer(
        commandes, many=True, context={"request": requete}
    ).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def detail_commande(requete, identifiant):
    commande = get_object_or_404(
        Commande.objects.prefetch_related("sous_commandes__lignes"), pk=identifiant
    )

    # Chaque role ne voit que ce qui le concerne — et le controle est ici, pas
    # dans l'interface (scenario 14.1).
    utilisateur = requete.user
    autorise = (
        getattr(utilisateur, "profil_client", None) == commande.client
        or utilisateur.role == "ADMIN"
        or commande.sous_commandes.filter(
            vendeur__utilisateur=utilisateur
        ).exists()
    )
    if not autorise:
        return Response(status=status.HTTP_404_NOT_FOUND)

    historique = HistoriqueStatut.objects.filter(type_objet="COMMANDE", id_objet=commande.id)
    return Response({"data": {
        **CommandeSerializer(commande, context={"request": requete}).data,
        "historique": [
            {
                "statut": ligne.statut_apres,
                "commentaire": ligne.commentaire,
                "date": ligne.date_changement,
            }
            for ligne in historique
        ],
    }})


@api_view(["GET"])
@permission_classes([EstVendeurOuSonPersonnel])
def commandes_recues(requete):
    """La file du vendeur : ce qu'il doit preparer, dans l'ordre d'arrivee."""
    utilisateur = requete.user
    profil = getattr(utilisateur, "profil_vendeur", None)
    identifiant = profil.id if profil else getattr(
        getattr(utilisateur, "profil_gestionnaire", None), "vendeur_id", None
    )
    if identifiant is None:
        return Response({"data": []})

    sous_commandes = (
        SousCommande.objects.filter(vendeur_id=identifiant)
        .select_related("commande", "vendeur", "commande__adresse_livraison")
        .prefetch_related("lignes")
        .order_by("-commande__date_commande")
    )

    # Le dernier changement de statut de chaque sous-commande, en UNE requete.
    # Une par ligne serait invisible sur cinq commandes et insupportable sur
    # trois cents.
    derniers_actes = {}
    for entree in (
        HistoriqueStatut.objects.filter(
            type_objet="SOUS_COMMANDE",
            id_objet__in=[sous.id for sous in sous_commandes],
        )
        .select_related("utilisateur")
        .order_by("id_objet", "-date_changement")
    ):
        derniers_actes.setdefault(entree.id_objet, {
            "qui": (f"{entree.utilisateur.prenom} {entree.utilisateur.nom}".strip()
                    if entree.utilisateur else "le systeme"),
            "quand": entree.date_changement,
            "statut": entree.statut_apres,
        })

    return Response({"data": [
        {
            **SousCommandeSerializer(sous, context={"request": requete}).data,
            "numero_commande": sous.commande.numero_commande,
            "type_service": sous.commande.type_service,
            "date_commande": sous.commande.date_commande,
            "statut_commande": sous.commande.statut_actuel,
            "suites_possibles": SUITE_PREPARATION.get(sous.statut_preparation, []),
            # Ou part le colis (D-74). Le vendeur ne savait meme pas dans quelle
            # ville il expediait : ni la rue ni les instructions, il prepare un
            # colis, il n'a pas a connaitre l'etage de quelqu'un.
            "destination": adresse_pour(VENDEUR, sous.commande.adresse_livraison),
            # Qui a fait avancer cette commande, et quand (D-80). Le vendeur et
            # son personnel travaillaient sur la meme file sans jamais savoir
            # lequel des deux avait deja agi.
            "dernier_acte": derniers_actes.get(sous.id),
        }
        for sous in sous_commandes
    ]})


@api_view(["PATCH"])
@permission_classes([EstVendeurOuSonPersonnel])
def avancer_preparation(requete, identifiant):
    """Le statut avance d'un cran, jamais de deux, jamais a rebours.

    L'API renvoie elle-meme les suites possibles : le front n'a pas a
    connaitre la machine a etats, il affiche les boutons qu'on lui donne.
    """
    utilisateur = requete.user
    profil = getattr(utilisateur, "profil_vendeur", None)
    id_vendeur = profil.id if profil else getattr(
        getattr(utilisateur, "profil_gestionnaire", None), "vendeur_id", None
    )
    sous = SousCommande.objects.filter(pk=identifiant, vendeur_id=id_vendeur).first()
    if sous is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    vise = requete.data.get("statut")
    if vise not in SUITE_PREPARATION.get(sous.statut_preparation, []):
        return Response(
            {"erreur": {"code": "transition_interdite",
                        "message": f"Impossible de passer de « {sous.get_statut_preparation_display()} »"
                                   f" a ce statut.", "details": {}}},
            status=status.HTTP_409_CONFLICT,
        )

    avant = sous.statut_preparation
    sous.statut_preparation = vise
    sous.save(update_fields=["statut_preparation"])

    # La trace porte sur la SOUS-commande : c'est elle qui a un statut de
    # preparation. L'ecrire sur la commande melangeait les avancements de trois
    # boutiques differentes sur une commande Standard multi-vendeur.
    HistoriqueStatut.objects.create(
        type_objet=TypeObjetSuivi.SOUS_COMMANDE, id_objet=sous.id,
        statut_avant=avant, statut_apres=vise, utilisateur=utilisateur,
        commentaire=f"Preparation chez {sous.vendeur.nom_boutique}",
    )

    # La commande suit quand toutes ses parts sont pretes : c'est ce qui
    # declenchera l'attribution d'un livreur.
    _synchroniser_commande(sous.commande, utilisateur)

    return Response({"data": {
        **SousCommandeSerializer(sous, context={"request": requete}).data,
        "suites_possibles": SUITE_PREPARATION.get(sous.statut_preparation, []),
    }})


def _synchroniser_commande(commande, utilisateur=None):
    """La commande suit ses sous-commandes, et le dit dans son historique.

    Le changement etait applique en silence : le client voyait sa commande
    passer de « payee » a « prete » sans qu'aucune ligne d'historique ne
    l'explique. « Jamais de statut modifie en silence » est pourtant la
    premiere phrase du modele (D-95).
    """
    statuts = set(commande.sous_commandes.values_list("statut_preparation", flat=True))
    if statuts <= {StatutPreparation.PRETE, StatutPreparation.EXPEDIEE}:
        nouveau = StatutCommande.PRETE
    elif StatutPreparation.EN_PREPARATION in statuts:
        nouveau = StatutCommande.EN_PREPARATION
    else:
        return

    if commande.statut_actuel == nouveau:
        return

    avant = commande.statut_actuel
    commande.statut_actuel = nouveau
    commande.save(update_fields=["statut_actuel"])
    HistoriqueStatut.objects.create(
        type_objet=TypeObjetSuivi.COMMANDE, id_objet=commande.id,
        statut_avant=avant, statut_apres=nouveau, utilisateur=utilisateur,
        commentaire="Suit l'avancement des boutiques",
    )
