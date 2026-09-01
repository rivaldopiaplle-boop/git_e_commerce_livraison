"""Ce que chaque role voit d'une adresse de livraison — D-74.

**Ta question, L-2** : *« mes adresses : ces informations ne sont pas utilisees
par le vendeur, l'entrepot, le gestionnaire ni le livreur, pourquoi ? »*

Elle etait juste. Le client saisissait une adresse et des instructions
(« code portail 4512, 3e etage »), et **personne ne les voyait ensuite**. Le
vendeur ne savait meme pas dans quelle ville partait son colis.

Le cloisonnement n'est pas une pudeur administrative : une adresse complete
diffusee a toute la chaine est une donnee personnelle exposee sans necessite.
Chacun recoit **ce dont son metier a besoin**, et rien de plus :

| Qui | Ce qu'il voit | Pourquoi pas plus |
|---|---|---|
| Vendeur, son personnel | ville, code postal | il prepare un colis, il n'a pas a connaitre l'etage de quelqu'un |
| Gestionnaire d'entrepot | rue, ville, code postal, zone | il ORDONNE des arrets : sans la rue, il ne peut pas |
| Livreur | tout, instructions comprises | c'est lui qui sonne a la porte |
| Admin | tout | il arbitre les litiges, avec les deux versions |

La seule nuance par rapport a la redaction d'origine de D-74 : l'entrepot voit
la **rue**. Monter une tournee sans les rues reviendrait a ordonner des arrets
au hasard. Il ne voit pas les **instructions** — elles ne servent qu'a celui
qui se presente devant la porte.

Une seule fonction, appelee par toutes les vues. Trois cloisonnements ecrits
separement finissent toujours par diverger, et c'est celui qui en dit le plus
qui fait foi.
"""

VENDEUR = "vendeur"
ENTREPOT = "entrepot"
LIVREUR = "livreur"
ADMIN = "admin"


def adresse_pour(role, adresse):
    """La forme d'une adresse telle que `role` a le droit de la lire.

    Rend `None` si l'adresse manque : une commande sans adresse ne devrait pas
    exister, mais un ecran ne doit pas tomber pour autant.
    """
    if adresse is None:
        return None

    # Le socle, que tout le monde voit : sans la ville, un vendeur ne sait meme
    # pas s'il expedie a cote ou a l'autre bout du pays.
    vue = {
        "ville": adresse.ville,
        "code_postal": adresse.code_postal,
    }

    if role == VENDEUR:
        return vue

    if role == ENTREPOT:
        return {
            **vue,
            "rue": adresse.rue,
            "zone": adresse.zone.nom if adresse.zone_id else None,
        }

    # Livreur et admin : tout, instructions comprises.
    return {
        **vue,
        "id": adresse.id,
        "libelle": adresse.libelle,
        "rue": adresse.rue,
        "complement": adresse.complement,
        "instructions": adresse.instructions_livraison,
        "latitude": float(adresse.latitude) if adresse.latitude is not None else None,
        "longitude": float(adresse.longitude) if adresse.longitude is not None else None,
    }


def resume(adresse, role=LIVREUR):
    """L'adresse en une ligne, pour une liste — jamais pour un ecran de detail."""
    vue = adresse_pour(role, adresse)
    if vue is None:
        return ""
    if "rue" in vue:
        return f"{vue['rue']}, {vue['code_postal']} {vue['ville']}"
    return f"{vue['code_postal']} {vue['ville']}"
