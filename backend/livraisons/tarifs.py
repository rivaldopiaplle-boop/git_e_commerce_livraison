"""Ce que gagne un livreur, et d'où ça sort — O-5.

**Ton reproche** : *« la distance du trajet et le prix pour vous ne sont pas
vraiment calculés ou mis par l'admin, ça sort de nulle part »*.

Il était exact, et à deux titres :

  · la **distance** était tirée au hasard entre 0,8 et 7,5 km par le jeu de
    démonstration. Elle ne correspondait à rien — ni à la boutique, ni à
    l'adresse de livraison ;
  · la **rémunération** suivait une formule enfouie dans le peuplement, et
    aucune commande créée en vrai n'avait de livraison du tout.

Deux corrections, et la seconde compte autant que la première :

1. **la distance est calculée** — de la boutique (Express) ou de l'entrepôt
   (Standard) jusqu'à l'adresse du client, par la formule de haversine
   (D-25), puis majorée du détour urbain comme partout ailleurs (D-142) ;
2. **le tarif est publié**. Il vit ici, en clair, il est le même pour tout le
   monde, et l'écran du livreur peut l'afficher : « 2,50 € de base + 0,60 €/km
   × 3,2 km = 4,42 € ». Un livreur doit pouvoir vérifier ce qu'on lui doit.

Pourquoi une table de constantes plutôt qu'un réglage en base ? Parce qu'un
tarif de course est une **décision de la plateforme**, pas un paramètre qu'on
change à la volée : le versionner avec le code laisse une trace de qui l'a
changé et quand, ce qu'un champ modifiable en base ne donne pas. Le jour où il
faut le rendre modifiable par un administrateur, la fonction reste, seule sa
source change.
"""
from coeur.geographie import distance_km

# Le détour urbain : une rue ne va jamais tout droit. Même facteur que la
# carte (D-142), et pour la même raison — deux facteurs différents feraient
# afficher deux distances différentes pour le même trajet.
FACTEUR_DETOUR = 1.35

# Le barème, par mode. Ce sont les deux seules lignes qui décident de ce que
# gagne un livreur, et elles sont ici, lisibles.
BAREME = {
    "EXPRESS": {
        # Une course Express est courte et urgente : la part fixe pèse plus que
        # le kilométrage, sinon les courses de proximité ne valent pas le
        # déplacement et personne ne les prend.
        "base_centimes": 250,
        "par_km_centimes": 60,
        "minimum_centimes": 300,
    },
    "STANDARD": {
        # Un arrêt de tournée se paie à l'arrêt : le livreur en enchaîne
        # quinze, et la distance entre deux d'entre eux est faible.
        "base_centimes": 150,
        "par_km_centimes": 35,
        "minimum_centimes": 180,
    },
}


def distance_de_course(depart, arrivee):
    """La distance réelle d'une course, en kilomètres, ou None.

    `depart` et `arrivee` sont des adresses. Sans coordonnées des deux côtés,
    on rend None plutôt qu'un chiffre inventé : une distance fausse sur une
    fiche de paie est pire qu'une distance absente.
    """
    if depart is None or arrivee is None:
        return None
    vol = distance_km(depart.latitude, depart.longitude, arrivee.latitude, arrivee.longitude)
    if vol is None:
        return None
    return round(vol * FACTEUR_DETOUR, 2)


def remuneration(mode, distance):
    """Ce que la course rapporte, et le détail du calcul.

    Rend un couple `(centimes, detail)`. Le détail est une phrase que l'écran
    affiche telle quelle : c'est elle qui répond à « ça sort d'où ».
    """
    bareme = BAREME.get(mode, BAREME["STANDARD"])
    if distance is None:
        # Sans distance connue, on paie la base : ne rien payer serait pire, et
        # inventer un kilométrage serait malhonnête.
        return bareme["minimum_centimes"], (
            f"{bareme['minimum_centimes'] / 100:.2f} EUR — forfait minimum, "
            f"la distance n'a pas pu etre calculee."
        )

    brut = bareme["base_centimes"] + int(round(float(distance) * bareme["par_km_centimes"]))
    montant = max(brut, bareme["minimum_centimes"])
    detail = (
        f"{bareme['base_centimes'] / 100:.2f} EUR de base "
        f"+ {bareme['par_km_centimes'] / 100:.2f} EUR/km x {distance} km "
        f"= {montant / 100:.2f} EUR"
    )
    if montant != brut:
        detail += f" (releve au minimum de {bareme['minimum_centimes'] / 100:.2f} EUR)"
    return montant, detail
