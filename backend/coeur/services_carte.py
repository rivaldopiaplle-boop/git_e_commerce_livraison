"""La carte et les itineraires, derriere une interface — D-18, D-142.

Ta demande, bloc N-5 : *« je veux une vraie API de carte sophistiquee, dis-moi
quelle cle prendre pour le meilleur resultat. »*

Il y a **deux services distincts** derriere le mot « carte », et les confondre
mene a payer deux fois pour un seul besoin :

  1. **le fond de carte** — les tuiles, le dessin des rues. Il vit dans le
     navigateur, pas ici. Voir `frontend-web/src/composants/Carte.vue` ;
  2. **l'itineraire** — le trace routier, la distance reelle et la duree.
     C'est un calcul serveur, et c'est ce fichier.

Les deux suivent D-18 : une interface, un simulateur, un vrai fournisseur
choisi par une variable d'environnement.

Le simulateur n'est pas un bouche-trou. Le projet calcule deja les distances a
vol d'oiseau en local (D-25) : c'est **suffisant pour les frais de livraison et
le rayon Express**, et cela ne demande ni cle ni reseau. Ce que l'itineraire
reel apporte, c'est la **duree** — un livreur a velo ne traverse pas la Saone a
la nage — et le **trace**, qui est ce qu'on affiche sur la carte.
"""
import json
import logging
import os
from dataclasses import dataclass, field
from urllib.request import Request, urlopen

from .geographie import distance_km

logger = logging.getLogger(__name__)


# Les vitesses moyennes en ville, par mode. Ce ne sont pas des vitesses de
# pointe : elles integrent les feux, les arrets et le stationnement, parce
# qu'une estimation optimiste est pire qu'une estimation absente — le client
# la voit passer, et il ne fait plus confiance a la suivante.
VITESSES_KMH = {
    "velo": 15.0,       # livreur Express, en ville
    "voiture": 22.0,    # camionnette de tournee, arrets compris
    "pieton": 4.5,
}

# Le detour moyen entre le vol d'oiseau et la route reelle en milieu urbain.
# Mesure classique en logistique : une rue ne va jamais tout droit.
FACTEUR_DETOUR = 1.35


@dataclass
class Itineraire:
    """Un trajet, quel que soit celui qui l'a calcule."""

    distance_km: float
    duree_minutes: int
    #: La suite de points [longitude, latitude] — l'ordre de GeoJSON, pas
    #: l'inverse. C'est la confusion la plus courante avec les cartes, et elle
    #: ne se voit qu'a l'ecran, quand le trace part en Somalie.
    trace: list = field(default_factory=list)
    simule: bool = True


class ItineraireSimule:
    """Vol d'oiseau, majore du detour urbain. Sans cle et sans reseau.

    Ce n'est pas une approximation grossiere : sur un trajet urbain de quelques
    kilometres, le facteur de detour donne une distance a 10-15 % de la
    distance routiere reelle. Assez pour une estimation affichee, pas assez
    pour guider quelqu'un — et c'est justement pour cela qu'on ne guide pas :
    le bouton « M'y conduire » passe la main a l'application de navigation du
    telephone, qui le fait mieux que nous et gratuitement.
    """

    nom = "simulateur"

    def calculer(self, points, profil="voiture"):
        """`points` : [(lat, lon), (lat, lon), ...] dans l'ordre de passage."""
        points = [(float(lat), float(lon)) for lat, lon in points if lat is not None]
        if len(points) < 2:
            return Itineraire(distance_km=0.0, duree_minutes=0, trace=[], simule=True)

        total = 0.0
        for (lat1, lon1), (lat2, lon2) in zip(points, points[1:], strict=False):
            total += distance_km(lat1, lon1, lat2, lon2) or 0.0
        total *= FACTEUR_DETOUR

        vitesse = VITESSES_KMH.get(profil, VITESSES_KMH["voiture"])
        return Itineraire(
            distance_km=round(total, 2),
            duree_minutes=max(1, round(total / vitesse * 60)),
            # Le trace du simulateur est la ligne brisee entre les points. La
            # carte le dessine en pointilles : un trait plein ferait croire a
            # un itineraire routier calcule.
            trace=[[lon, lat] for lat, lon in points],
            simule=True,
        )


class ItineraireParApi:
    """OpenRouteService : vrai reseau routier, vraie duree, vrai trace.

    **Pourquoi celui-la** et pas Google, Mapbox ou HERE : c'est le seul des
    quatre dont le palier gratuit ne demande **aucune carte bancaire** —
    2 000 requetes par jour, largement au-dessus de ce qu'une demonstration
    consomme. Les trois autres exigent un moyen de paiement pour delivrer une
    cle, ce qui est une mauvaise idee sur un projet qu'on met en ligne pour le
    montrer et qu'on oublie ensuite.

    Il est bati sur OpenStreetMap, donc les rues sont les vraies rues, et il
    connait le profil velo — ce qui compte ici, puisque la moitie des courses
    sont des livraisons Express a velo.

    Comme partout ailleurs, **toute panne retombe sur le simulateur** : cle
    expiree, quota depasse, reseau coupe. Une carte sans trace vaut mieux
    qu'un ecran en erreur.
    """

    nom = "openrouteservice"

    ADRESSE = "https://api.openrouteservice.org/v2/directions/{profil}/geojson"

    # Le vocabulaire d'OpenRouteService, traduit depuis le notre. Le garder
    # ici plutot que dans les vues evite que le nom du fournisseur remonte
    # jusqu'aux ecrans.
    PROFILS = {
        "velo": "cycling-regular",
        "voiture": "driving-car",
        "pieton": "foot-walking",
    }

    DELAI_SECONDES = 8

    def __init__(self, cle):
        self.cle = cle
        self.repli = ItineraireSimule()

    def calculer(self, points, profil="voiture"):
        points = [(float(lat), float(lon)) for lat, lon in points if lat is not None]
        if len(points) < 2:
            return self.repli.calculer(points, profil)

        corps = json.dumps({
            # GeoJSON attend [longitude, latitude]. L'inversion est LA erreur
            # classique des cartes, et elle ne se voit qu'a l'affichage.
            "coordinates": [[lon, lat] for lat, lon in points],
            "instructions": False,
        }).encode()

        requete = Request(
            self.ADRESSE.format(profil=self.PROFILS.get(profil, "driving-car")),
            data=corps, method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/geo+json",
                "Authorization": self.cle,
            },
        )
        try:
            with urlopen(requete, timeout=self.DELAI_SECONDES) as reponse:
                charge = json.loads(reponse.read())
            trajet = charge["features"][0]
            resume = trajet["properties"]["summary"]
            return Itineraire(
                distance_km=round(resume["distance"] / 1000, 2),
                duree_minutes=max(1, round(resume["duration"] / 60)),
                trace=trajet["geometry"]["coordinates"],
                simule=False,
            )
        except Exception as souci:  # noqa: BLE001 — tout echec mene au repli
            logger.warning("Itineraire indisponible (%s) : repli sur le calcul local.",
                           type(souci).__name__)
            return self.repli.calculer(points, profil)


def service_itineraire():
    """Le calculateur en service : le vrai s'il y a une cle, le local sinon.

    Poser `CLE_ITINERAIRE` suffit ; la retirer suffit a revenir au calcul
    local. Aucun autre reglage, aucun drapeau (D-18).
    """
    cle = os.environ.get("CLE_ITINERAIRE", "").strip()
    return ItineraireParApi(cle) if cle else ItineraireSimule()
