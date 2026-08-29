"""Les ecrans de logistique : l'entrepot d'un cote, le livreur de l'autre.

Deux roles y travaillent, et ils ne voient pas la meme chose :

  · le **gestionnaire staff entrepot** voit les colis qui arrivent chez lui et
    les tournees qu'il constitue. Jamais un prix, jamais un chiffre d'affaires
    (D-04) — il manipule des colis, pas de l'argent ;
  · le **livreur** voit ses courses et ce qu'elles lui rapportent (D-29), et
    seulement les siennes : l'attribution fait foi (scenario 14.2).

Tout est en lecture pour l'instant. Faire avancer une tournee ou une livraison
appartient a la tranche livraison, qui vient apres le paiement — l'ecrire a
moitie serait pire que de ne pas l'ecrire.
"""
from django.db.models import Count, Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from commandes.models import SousCommande, StatutPreparation
from comptes.models import StatutCompte
from comptes.permissions import EstGestionnaire, EstLivreur

from .models import Livraison, StatutLivraison, StatutTournee, Tournee
from .serializers import LivraisonSerializer, TourneeSerializer


def _entrepot_de(utilisateur):
    """L'entrepot auquel ce compte est rattache, ou None."""
    gestionnaire = getattr(utilisateur, "profil_gestionnaire", None)
    return getattr(gestionnaire, "entrepot", None)


@api_view(["GET"])
@permission_classes([EstGestionnaire])
def colis_recus(requete):
    """Ce qui est arrive a l'entrepot et attend d'etre range puis charge.

    Un colis, ici, c'est une sous-commande expediee par un vendeur Standard.
    L'ecran les groupe par boutique parce que c'est ainsi qu'ils arrivent :
    un vendeur depose son lot du jour, pas un colis a la fois.
    """
    entrepot = _entrepot_de(requete.user)
    if entrepot is None:
        return Response({"data": {"entrepot": None, "groupes": [], "total": 0}})

    colis = (
        SousCommande.objects.filter(
            entrepot=entrepot, statut_preparation=StatutPreparation.EXPEDIEE
        )
        .select_related("vendeur", "commande", "commande__adresse_livraison")
        .order_by("vendeur__nom_boutique", "-date_expedition_entrepot")
    )

    groupes = {}
    for sous_commande in colis:
        entree = groupes.setdefault(sous_commande.vendeur_id, {
            "vendeur": sous_commande.vendeur.nom_boutique,
            "ville": (sous_commande.vendeur.adresse.ville
                      if sous_commande.vendeur.adresse_id else ""),
            "colis": [],
        })
        entree["colis"].append({
            "id": sous_commande.id,
            "numero_commande": sous_commande.commande.numero_commande,
            "destination": (f"{sous_commande.commande.adresse_livraison.code_postal} "
                            f"{sous_commande.commande.adresse_livraison.ville}"),
            "articles": sous_commande.lignes.count(),
            "date_expedition": sous_commande.date_expedition_entrepot,
        })

    return Response({"data": {
        "entrepot": {"id": entrepot.id, "nom": entrepot.nom},
        "groupes": list(groupes.values()),
        "total": colis.count(),
    }})


@api_view(["GET"])
@permission_classes([EstGestionnaire])
def tournees_entrepot(requete):
    """Les tournees de l'entrepot, de leur brouillon a leur cloture."""
    entrepot = _entrepot_de(requete.user)
    if entrepot is None:
        return Response({"data": {"tournees": [], "a_affecter": 0}})

    tournees = (
        Tournee.objects.filter(entrepot=entrepot)
        .select_related("entrepot", "zone", "livreur", "livreur__utilisateur")
        .prefetch_related(
            "arrets__livraison__commande__client__utilisateur",
            "arrets__livraison__commande__sous_commandes__vendeur",
            "arrets__livraison__adresse_livraison",
        )
        .order_by("-date_creation")
    )
    return Response({"data": {
        "tournees": TourneeSerializer(tournees, many=True).data,
        "a_affecter": tournees.filter(
            statut__in=[StatutTournee.BROUILLON, StatutTournee.PRETE]
        ).count(),
        # Ce qui attend une tournee : des livraisons Standard sans arret.
        "en_attente": Livraison.objects.filter(
            commande__type_service="STANDARD", tournee__isnull=True
        ).exclude(
            statut_livraison__in=[StatutLivraison.LIVREE, StatutLivraison.ANNULEE]
        ).count(),
    }})


@api_view(["GET"])
@permission_classes([EstGestionnaire])
def tableau_de_bord_entrepot(requete):
    """Ce que le staff d'entrepot doit voir en arrivant le matin."""
    entrepot = _entrepot_de(requete.user)
    if entrepot is None:
        return Response({"data": {}})

    tournees = Tournee.objects.filter(entrepot=entrepot)
    colis = SousCommande.objects.filter(
        entrepot=entrepot, statut_preparation=StatutPreparation.EXPEDIEE
    )
    return Response({"data": {
        "entrepot": entrepot.nom,
        "colis_recus": colis.count(),
        "boutiques_deposantes": colis.values("vendeur_id").distinct().count(),
        "tournees_a_preparer": tournees.filter(
            statut__in=[StatutTournee.BROUILLON, StatutTournee.PRETE]
        ).count(),
        "tournees_en_cours": tournees.filter(statut=StatutTournee.EN_COURS).count(),
        "livreurs_rattaches": entrepot.livreurs.filter(
            utilisateur__statut_compte=StatutCompte.ACTIF
        ).count(),
    }})


# ═══════════════════════════════════════════════════════════════════════════
#  Le livreur — lecture seule au web, l'action est sur le mobile (D-40)
# ═══════════════════════════════════════════════════════════════════════════

@api_view(["GET"])
@permission_classes([EstLivreur])
def mes_courses(requete):
    """Les courses de CE livreur, et rien d'autre.

    Le filtre par `livreur` n'est pas un confort d'affichage : un livreur ne
    voit et ne valide que ce qui lui est attribue, quoi qu'il declare avoir
    fait physiquement (scenario 14.2).
    """
    profil = getattr(requete.user, "profil_livreur", None)
    if profil is None:
        return Response({"data": {"en_cours": [], "terminees": [], "gains": {}}})

    livraisons = (
        Livraison.objects.filter(livreur=profil)
        .select_related("commande", "commande__client__utilisateur", "adresse_livraison")
        .prefetch_related("commande__sous_commandes__vendeur", "tentatives")
        .order_by("-date_attribution")
    )
    terminees = livraisons.filter(statut_livraison=StatutLivraison.LIVREE)
    en_cours = livraisons.exclude(
        statut_livraison__in=[StatutLivraison.LIVREE, StatutLivraison.ANNULEE]
    )

    tournee = (
        Tournee.objects.filter(livreur=profil, statut=StatutTournee.EN_COURS)
        .select_related("entrepot", "zone", "livreur__utilisateur")
        .prefetch_related(
            "arrets__livraison__commande__client__utilisateur",
            "arrets__livraison__commande__sous_commandes__vendeur",
            "arrets__livraison__adresse_livraison",
        )
        .first()
    )

    return Response({"data": {
        "mode": profil.mode_livraison,
        "disponibilite": profil.statut_disponibilite,
        "en_cours": LivraisonSerializer(en_cours, many=True).data,
        "terminees": LivraisonSerializer(terminees[:20], many=True).data,
        "tournee": TourneeSerializer(tournee).data if tournee else None,
        # Ce que le livreur gagne, parce qu'une plateforme ou l'on ne voit
        # jamais d'argent ne ressemble pas a une plateforme (D-29).
        "gains": {
            "courses_terminees": terminees.count(),
            "total_centimes": terminees.aggregate(
                total=Sum("remuneration_livreur_centimes")
            )["total"] or 0,
            "distance_km": float(
                terminees.aggregate(total=Sum("distance_km"))["total"] or 0
            ),
        },
    }})


@api_view(["GET"])
@permission_classes([EstLivreur])
def tableau_de_bord_livreur(requete):
    profil = getattr(requete.user, "profil_livreur", None)
    if profil is None:
        return Response({"data": {}})

    livraisons = Livraison.objects.filter(livreur=profil)
    terminees = livraisons.filter(statut_livraison=StatutLivraison.LIVREE)
    return Response({"data": {
        "mode": profil.mode_livraison,
        "en_cours": livraisons.exclude(
            statut_livraison__in=[StatutLivraison.LIVREE, StatutLivraison.ANNULEE]
        ).count(),
        "livrees": terminees.count(),
        "echouees": livraisons.filter(statut_livraison=StatutLivraison.ECHOUEE).count(),
        "gains_centimes": terminees.aggregate(
            total=Sum("remuneration_livreur_centimes")
        )["total"] or 0,
    }})


# ═══════════════════════════════════════════════════════════════════════════
#  Vue admin : l'etat logistique de la plateforme
# ═══════════════════════════════════════════════════════════════════════════

def resume_logistique():
    """Utilise par le tableau de bord admin — pas une vue, une fonction."""
    return {
        "livraisons_en_cours": Livraison.objects.exclude(
            statut_livraison__in=[StatutLivraison.LIVREE, StatutLivraison.ANNULEE]
        ).count(),
        "livraisons_echouees": Livraison.objects.filter(
            statut_livraison=StatutLivraison.ECHOUEE
        ).count(),
        "tournees_en_cours": Tournee.objects.filter(statut=StatutTournee.EN_COURS).count(),
        "entrepots": list(
            Tournee.objects.values("entrepot__nom")
            .annotate(nombre=Count("id"))
            .order_by("entrepot__nom")
        ),
        "livreurs_en_activite": Livraison.objects.filter(
            livreur__isnull=False
        ).values("livreur_id").distinct().count(),
    }
