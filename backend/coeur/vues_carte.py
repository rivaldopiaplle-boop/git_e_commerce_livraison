"""Ce que la carte demande au serveur — D-142.

Une seule route, et elle est **fermee aux visiteurs**. La raison n'est pas la
confidentialite du trace : c'est le quota. Une route d'itineraire ouverte est
une facture ouverte, et sur un palier gratuit c'est le service entier qui
tombe pour tout le monde des qu'un robot la trouve.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .services_carte import service_itineraire

# Un itineraire, ce n'est pas une tournee entiere de cent arrets : au-dela,
# c'est un usage qu'on n'a pas prevu, et le fournisseur le refuserait de
# toute facon.
MAXIMUM_POINTS = 25


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def itineraire(requete):
    """Le trajet entre plusieurs points, dans l'ordre donne.

    Le corps attendu :

        {"points": [{"lat": 45.75, "lon": 4.85}, ...], "profil": "velo"}

    L'ordre des points est **celui de l'appelant**. Le serveur ne reordonne
    rien : c'est le gestionnaire d'entrepot qui decide de l'ordre de ses
    arrets, et une optimisation silencieuse lui ferait perdre le controle de
    sa tournee sans qu'il comprenne pourquoi.
    """
    bruts = requete.data.get("points") or []
    if not isinstance(bruts, list):
        bruts = []

    points = []
    for entree in bruts[:MAXIMUM_POINTS]:
        if not isinstance(entree, dict):
            continue
        try:
            points.append((float(entree["lat"]), float(entree["lon"])))
        except (KeyError, TypeError, ValueError):
            continue

    if len(points) < 2:
        return Response(
            {"erreur": {"code": "points_insuffisants",
                        "message": "Un itineraire demande au moins deux points situes.",
                        "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    profil = str(requete.data.get("profil", "voiture"))
    calcul = service_itineraire()
    trajet = calcul.calculer(points, profil)

    return Response({"data": {
        "distance_km": trajet.distance_km,
        "duree_minutes": trajet.duree_minutes,
        "trace": trajet.trace,
        # L'ecran DIT si le trace est reel ou estime, et dessine en pointilles
        # dans le second cas. Faire passer une ligne droite pour un itineraire
        # routier serait le genre de detail qui trahit un travail bacle.
        "simule": trajet.simule,
        "fournisseur": calcul.nom,
    }})
