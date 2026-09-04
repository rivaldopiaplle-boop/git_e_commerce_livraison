"""Une commande prête devient une livraison — O-5.

**Le trou le plus grave du bloc O**, et il ne se voyait pas : *rien* ne créait
de `Livraison` en dehors du jeu de démonstration. Une commande payée pour de
vrai, préparée pour de vrai, marquée prête pour de vrai… n'arrivait chez aucun
livreur. Toutes les courses qu'on voyait dans l'application venaient du
peuplement.

C'est ce que tu décrivais de trois façons différentes :

  · *« je n'ai pas vu de commande à livrer disponible quand le livreur est
    libre »* ;
  · *« la distance du trajet et le prix pour vous ne sont pas vraiment
    calculés, ça sort de nulle part »* ;
  · *« je ne comprends pas d'où sort la tournée du livreur »*.

Ce module est le chaînon manquant. Il est appelé **au moment où la commande
passe à `PRETE`**, c'est-à-dire quand toutes ses boutiques ont fini, et il est
idempotent : une commande qui repasse par là ne crée pas une deuxième course.
"""
import random

from django.db import transaction

from coeur.evenements import Evenement, emettre
from comptes.models import TypeService

from .models import Livraison, StatutLivraison
from .tarifs import distance_de_course, remuneration


def _code_de_remise():
    """Quatre chiffres, remis par le client au livreur.

    Ni signature ni photo : quatre chiffres que le client lit sur son écran
    suffisent à prouver que le bon colis est arrivé à la bonne personne, et
    n'exposent rien si on les entend dans un couloir.
    """
    return f"{random.randint(1000, 9999)}"


def entrepot_pour(adresse):
    """L'entrepôt qui dessert cette adresse : le plus proche, tout simplement.

    Le choix se faisait… nulle part. `SousCommande.entrepot` n'était renseigné
    que par le jeu de démonstration, si bien qu'une vraie commande Standard
    n'était rattachée à aucun entrepôt : l'écran des colis restait vide, et la
    distance de la course ne pouvait pas se calculer.

    Le plus proche à vol d'oiseau, et non une table de correspondance par code
    postal : une table est juste le jour où on l'écrit et fausse dès qu'un
    entrepôt ouvre.
    """
    from coeur.geographie import distance_km

    from .models import Entrepot

    entrepots = list(
        Entrepot.objects.filter(est_actif=True).select_related("adresse")
    )
    if not entrepots:
        return None
    if adresse is None:
        return entrepots[0]

    def ecart(entrepot):
        if entrepot.adresse is None:
            return 10_000
        valeur = distance_km(
            adresse.latitude, adresse.longitude,
            entrepot.adresse.latitude, entrepot.adresse.longitude,
        )
        return 10_000 if valeur is None else valeur

    return min(entrepots, key=ecart)


def _depart_de(commande):
    """D'où part la course.

    Express : de la boutique — il n'y en a qu'une, c'est la règle du découpage
    (D-10). Standard : de l'entrepôt, puisque le colis y transite.
    """
    premiere = commande.sous_commandes.select_related(
        "vendeur__adresse", "entrepot__adresse"
    ).first()
    if premiere is None:
        return None
    if commande.type_service == TypeService.EXPRESS:
        return premiere.vendeur.adresse

    entrepot = premiere.entrepot or entrepot_pour(commande.adresse_livraison)
    return entrepot.adresse if entrepot else None


@transaction.atomic
def creer_livraison(commande):
    """Créer la course d'une commande prête, si elle n'existe pas déjà.

    Rend la `Livraison`, créée ou retrouvée. Idempotente : `_synchroniser_commande`
    peut appeler cette fonction plusieurs fois — un vendeur qui refait passer sa
    part de PRETE à PRETE ne doit pas engendrer une deuxième course.
    """
    existante = Livraison.objects.filter(commande=commande).first()
    if existante is not None:
        return existante

    depart = _depart_de(commande)
    arrivee = commande.adresse_livraison
    distance = distance_de_course(depart, arrivee)
    montant, detail = remuneration(commande.type_service, distance)

    livraison = Livraison.objects.create(
        commande=commande,
        adresse_livraison=arrivee,
        # **Express : la course part au pot commun**, et le premier livreur
        # disponible la prend (D-60). Standard : elle attend qu'un
        # gestionnaire la range dans une tournée — personne ne prend un colis
        # d'entrepôt à la volée.
        statut_livraison=StatutLivraison.A_ATTRIBUER,
        distance_km=distance,
        frais_calcules_centimes=commande.montant_livraison_centimes,
        remuneration_livreur_centimes=montant,
        code_confirmation=_code_de_remise(),
        date_estimee=commande.date_livraison_estimee,
    )

    # Prévenir le client : le code de remise vient d'exister, et c'est lui
    # qu'on lui demandera à la porte (O-5).
    emettre(Evenement(
        nom="LIVRAISON_CREEE", type_objet="LIVRAISON", id_objet=livraison.id,
        titre=f"Votre commande {commande.numero_commande} part en livraison",
        message=f"Code a donner au livreur : {livraison.code_confirmation}.",
        lien="/espace/commandes",
        apres={"statut_livraison": livraison.statut_livraison,
               "remuneration_detail": detail},
        destinataires=[commande.client.utilisateur],
    ))
    return livraison


@transaction.atomic
def recalculer_depuis_entrepot(commande, entrepot):
    """Refaire la distance et la rémunération une fois l'entrepôt connu.

    L'ordre des choses le rend nécessaire. Une course Standard naît quand la
    commande passe à `PRETE`, c'est-à-dire **avant** que le vendeur l'expédie —
    donc avant qu'un entrepôt soit rattaché. À ce moment-là, on ne sait que
    deviner l'entrepôt le plus proche du client.

    Quand le colis arrive réellement, l'entrepôt n'est plus une hypothèse. On
    reprend donc le calcul, et cette fois il est juste. Il ne bouge plus
    ensuite : une rémunération qui change après coup est le meilleur moyen de
    perdre la confiance d'un livreur.
    """
    livraison = Livraison.objects.filter(commande=commande).first()
    if livraison is None or livraison.livreur_id is not None:
        # Une course deja attribuee ne change plus de prix sous les pieds de
        # celui qui l'a acceptee.
        return livraison

    distance = distance_de_course(entrepot.adresse if entrepot else None,
                                  commande.adresse_livraison)
    if distance is None:
        return livraison

    montant, _ = remuneration(commande.type_service, distance)
    livraison.distance_km = distance
    livraison.remuneration_livreur_centimes = montant
    livraison.save(update_fields=["distance_km", "remuneration_livreur_centimes"])
    return livraison
