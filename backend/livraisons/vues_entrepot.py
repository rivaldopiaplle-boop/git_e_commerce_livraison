"""Ce que le gestionnaire d'entrepôt FAIT — O-5.

Il consultait. Il ne pouvait rien faire : ni confirmer qu'un colis était
arrivé, ni monter une tournée, ni la confier à un livreur. Les tournées
visibles à l'écran venaient toutes du jeu de démonstration, ce qui est
exactement ta question : *« je ne comprends pas d'où sort la tournée du
livreur »*.

Trois gestes, dans l'ordre où une journée d'entrepôt se déroule :

  1. **confirmer la réception** d'un colis expédié par une boutique ;
  2. **calculer une tournée** avec ce qui est arrivé — autant de fois qu'il
     veut, le résultat pouvant différer d'une fois sur l'autre ;
  3. **la confier à un livreur**, puis la faire partir.
"""
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from commandes.models import (
    HistoriqueStatut,
    SousCommande,
    StatutCommande,
    StatutPreparation,
    TypeObjetSuivi,
)
from comptes.models import Livreur
from comptes.permissions import EstGestionnaireEntrepot

from .attribution import recalculer_depuis_entrepot
from .models import StatutLivraison, StatutTournee, Tournee
from .serializers import TourneeSerializer
from .tournees import CalculRefuse, attribuer, calculer, livraisons_en_attente
from .views import _entrepot_de


def _refus(souci):
    return Response(
        {"erreur": {"code": souci.code, "message": souci.message, "details": {}}},
        status=status.HTTP_409_CONFLICT,
    )


@api_view(["POST"])
@permission_classes([EstGestionnaireEntrepot])
@transaction.atomic
def confirmer_reception(requete, identifiant):
    """« Ce colis est bien arrivé chez nous. »

    Sans ce geste, un colis expédié par une boutique restait « expédié » pour
    toujours, et rien ne distinguait un colis en camion d'un colis sur
    l'étagère. C'est pourtant la seule chose qui autorise à le charger dans une
    tournée.
    """
    entrepot = _entrepot_de(requete.user)
    colis = SousCommande.objects.filter(
        pk=identifiant, entrepot=entrepot,
        statut_preparation=StatutPreparation.EXPEDIEE,
    ).select_related("commande").first()
    if colis is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    commande = colis.commande
    if commande.statut_actuel != StatutCommande.RECUE_ENTREPOT:
        avant = commande.statut_actuel
        commande.statut_actuel = StatutCommande.RECUE_ENTREPOT
        commande.save(update_fields=["statut_actuel"])
        HistoriqueStatut.objects.create(
            type_objet=TypeObjetSuivi.COMMANDE, id_objet=commande.id,
            statut_avant=avant, statut_apres=commande.statut_actuel,
            utilisateur=requete.user,
            commentaire=f"Recu a {entrepot.nom}",
        )

    # L'entrepot n'est plus une hypothese : la course se recalcule sur la vraie
    # distance de depart (O-5).
    livraison = recalculer_depuis_entrepot(commande, entrepot)

    return Response({"data": {
        "id": colis.id,
        "numero_commande": commande.numero_commande,
        "distance_km": livraison.distance_km if livraison else None,
        "remuneration_centimes": (livraison.remuneration_livreur_centimes
                                  if livraison else None),
        "statut_commande": commande.statut_actuel,
        "en_attente_de_tournee": len(livraisons_en_attente(entrepot)),
    }})


@api_view(["POST"])
@permission_classes([EstGestionnaireEntrepot])
def calculer_tournee(requete):
    """Monter une tournée avec ce qui est disponible, ou refaire une existante.

    `id_tournee` permet de **rejouer** le calcul sur un brouillon : c'est
    exactement ce que tu décrivais, *« il peut le refaire quand il veut, et le
    résultat peut différer »*.
    """
    entrepot = _entrepot_de(requete.user)
    if entrepot is None:
        return Response(
            {"erreur": {"code": "sans_entrepot",
                        "message": "Votre compte n'est rattache a aucun entrepot.",
                        "details": {}}},
            status=status.HTTP_409_CONFLICT,
        )

    tournee = None
    if requete.data.get("id_tournee"):
        tournee = Tournee.objects.filter(
            pk=requete.data["id_tournee"], entrepot=entrepot
        ).first()
        if tournee is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        tournee = calculer(
            entrepot, getattr(requete.user, "profil_gestionnaire", None), tournee,
        )
    except CalculRefuse as souci:
        return _refus(souci)

    return Response({"data": TourneeSerializer(
        Tournee.objects.prefetch_related(
            "arrets__livraison__commande__client__utilisateur",
            "arrets__livraison__adresse_livraison",
        ).get(pk=tournee.pk),
        context={"request": requete, "role_adresse": "entrepot"},
    ).data})


@api_view(["POST"])
@permission_classes([EstGestionnaireEntrepot])
def attribuer_tournee(requete, identifiant):
    """Confier la tournée à un livreur Standard."""
    entrepot = _entrepot_de(requete.user)
    tournee = Tournee.objects.filter(pk=identifiant, entrepot=entrepot).first()
    if tournee is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    livreur = Livreur.objects.filter(pk=requete.data.get("id_livreur")).first()
    if livreur is None:
        return Response(
            {"erreur": {"code": "livreur_inconnu",
                        "message": "Choisissez un livreur dans la liste.", "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        attribuer(tournee, livreur)
    except CalculRefuse as souci:
        return _refus(souci)

    return Response({"data": TourneeSerializer(
        tournee, context={"request": requete, "role_adresse": "entrepot"}
    ).data})


@api_view(["POST"])
@permission_classes([EstGestionnaireEntrepot])
@transaction.atomic
def faire_partir(requete, identifiant):
    """La tournée quitte l'entrepôt. À partir de là, elle ne se recalcule plus."""
    entrepot = _entrepot_de(requete.user)
    tournee = Tournee.objects.filter(pk=identifiant, entrepot=entrepot).first()
    if tournee is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if tournee.livreur_id is None:
        return _refus(CalculRefuse(
            "sans_livreur", "Attribuez d'abord cette tournée à un livreur.",
        ))

    tournee.statut = StatutTournee.EN_COURS
    tournee.date_debut = timezone.now()
    tournee.save(update_fields=["statut", "date_debut"])

    for livraison in tournee.livraisons.select_related("commande"):
        livraison.statut_livraison = StatutLivraison.EN_ROUTE
        livraison.date_prise_en_charge = timezone.now()
        livraison.save(update_fields=["statut_livraison", "date_prise_en_charge"])

        commande = livraison.commande
        avant = commande.statut_actuel
        commande.statut_actuel = StatutCommande.EN_TOURNEE
        commande.save(update_fields=["statut_actuel"])
        HistoriqueStatut.objects.create(
            type_objet=TypeObjetSuivi.COMMANDE, id_objet=commande.id,
            statut_avant=avant, statut_apres=commande.statut_actuel,
            utilisateur=requete.user,
            commentaire=f"Partie en tournee depuis {entrepot.nom}",
        )

    return Response({"data": TourneeSerializer(
        tournee, context={"request": requete, "role_adresse": "entrepot"}
    ).data})


@api_view(["GET"])
@permission_classes([EstGestionnaireEntrepot])
def livreurs_disponibles(requete):
    """À qui confier une tournée.

    Seuls les livreurs Standard validés : proposer un livreur Express dans
    cette liste reviendrait à laisser faire une erreur qu'on refuserait
    ensuite.
    """
    entrepot = _entrepot_de(requete.user)
    livreurs = (
        Livreur.objects.filter(mode_livraison="STANDARD", statut_validation="VALIDE")
        .select_related("utilisateur")
        .order_by("utilisateur__prenom")
    )
    return Response({"data": [
        {
            "id": livreur.id,
            "nom": f"{livreur.utilisateur.prenom} {livreur.utilisateur.nom}".strip(),
            "disponibilite": livreur.statut_disponibilite,
            "de_cet_entrepot": livreur.entrepot_id == getattr(entrepot, "id", None),
            "tournees_en_cours": livreur.tournees.filter(
                statut__in=[StatutTournee.AFFECTEE, StatutTournee.EN_COURS]
            ).count(),
        }
        for livreur in livreurs
    ]})
