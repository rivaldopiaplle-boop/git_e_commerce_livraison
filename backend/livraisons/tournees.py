"""La tournée se calcule, au lieu de sortir de nulle part — O-5.

**Ta remarque** : *« les tournées doivent se calculer seules en fonction des
commandes — je crois que c'est le gestionnaire qui demande le calcul en
fonction de ce qui est à sa disposition, et peut le refaire quand il veut, et
le résultat peut différer après le départ ou la réception des colis. Et le
gestionnaire doit attribuer à un livreur juste, confirmer la réception des
colis. Donc je ne comprends pas d'où sort la tournée du livreur. »*

Elle ne sortait de nulle part : **seul le jeu de démonstration créait des
tournées**. Aucun bouton, nulle part, n'en montait une.

## Ce que fait le calcul, et ce qu'il ne fait pas

Il **ordonne**, il ne décide pas. Le gestionnaire garde la main sur trois
choses : quand il calcule, à qui il attribue, et quand la tournée part. C'est
volontaire — une optimisation qui déciderait à sa place lui ferait perdre le
contrôle de sa journée sans qu'il comprenne pourquoi.

L'ordre est obtenu par **le plus proche voisin** : on part de l'entrepôt, on va
au colis le plus proche, puis au plus proche de celui-là, et ainsi de suite.

Pourquoi celui-là et pas mieux ? Parce que le problème du voyageur de commerce
n'a pas de solution exacte praticable au-delà d'une vingtaine d'arrêts, et que
le plus proche voisin donne un trajet **de 20 à 25 % plus long que l'optimal**
pour un coût de calcul nul. Sur une tournée de quinze arrêts en ville, cela
représente quelques minutes. Une heure de calcul pour les gagner n'aurait aucun
sens, et une bibliothèque d'optimisation serait une dépendance de plus pour un
gain que personne ne verrait.

## Recalculable, et c'est le point important

Le calcul est **idempotent sur une tournée en brouillon** : il vide et refait.
C'est ce que tu décrivais — *« le résultat peut différer après le départ ou la
réception des colis »*. Une tournée déjà partie, elle, ne se recalcule pas : on
ne réordonne pas les arrêts de quelqu'un qui roule.
"""
from django.db import transaction
from django.utils import timezone

from coeur.evenements import Evenement, emettre
from coeur.geographie import distance_km
from commandes.models import StatutPreparation

from .models import ArretTournee, Livraison, StatutLivraison, StatutTournee, Tournee


class CalculRefuse(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def livraisons_en_attente(entrepot):
    """Les colis reçus à cet entrepôt qui n'ont pas encore de tournée.

    Deux conditions, et la première est celle qu'on oublie : **le colis doit
    être arrivé**. Charger dans une tournée un colis que le vendeur n'a pas
    encore expédié enverrait le livreur chercher du vide.
    """
    return list(
        Livraison.objects.filter(
            statut_livraison=StatutLivraison.A_ATTRIBUER,
            tournee__isnull=True,
            commande__type_service="STANDARD",
            commande__sous_commandes__entrepot=entrepot,
            commande__sous_commandes__statut_preparation=StatutPreparation.EXPEDIEE,
        )
        .select_related("commande", "adresse_livraison")
        .distinct()
    )


def ordonner(depart, livraisons):
    """Le plus proche voisin, en partant de l'entrepôt.

    Rend la liste ordonnée et la distance totale. Les livraisons sans
    coordonnées ferment la marche : on ne peut pas les placer, et les mettre au
    milieu casserait l'ordre de toutes les autres.
    """
    situees = [
        livraison for livraison in livraisons
        if livraison.adresse_livraison
        and livraison.adresse_livraison.latitude is not None
    ]
    sans_position = [livraison for livraison in livraisons if livraison not in situees]

    ordre, total = [], 0.0
    courant = depart
    restantes = list(situees)

    while restantes:
        if courant is None:
            ordre.extend(restantes)
            break
        proche = min(
            restantes,
            key=lambda livraison: distance_km(
                courant.latitude, courant.longitude,
                livraison.adresse_livraison.latitude, livraison.adresse_livraison.longitude,
            ) or 10_000,
        )
        pas = distance_km(
            courant.latitude, courant.longitude,
            proche.adresse_livraison.latitude, proche.adresse_livraison.longitude,
        )
        total += pas or 0
        ordre.append(proche)
        restantes.remove(proche)
        courant = proche.adresse_livraison

    return ordre + sans_position, round(total, 2)


@transaction.atomic
def calculer(entrepot, gestionnaire=None, tournee=None):
    """Monter ou refaire une tournée à partir de ce qui est disponible."""
    if tournee is not None and tournee.statut not in (
        StatutTournee.BROUILLON, StatutTournee.PRETE
    ):
        raise CalculRefuse(
            "tournee_partie",
            "Cette tournée est déjà partie : on ne réordonne pas les arrêts de "
            "quelqu'un qui roule.",
        )

    attente = livraisons_en_attente(entrepot)
    if tournee is not None:
        # On récupère aussi ce qui était déjà dans la tournée : refaire le
        # calcul ne doit pas perdre des colis en route.
        attente += list(
            Livraison.objects.filter(tournee=tournee)
            .select_related("commande", "adresse_livraison")
        )
        attente = list({livraison.id: livraison for livraison in attente}.values())

    if not attente:
        raise CalculRefuse(
            "rien_a_charger",
            "Aucun colis reçu n'attend de tournée. Confirmez d'abord la "
            "réception des colis expédiés par les boutiques.",
        )

    ordre, distance = ordonner(entrepot.adresse, attente)

    if tournee is None:
        tournee = Tournee.objects.create(
            entrepot=entrepot, cree_par=gestionnaire, statut=StatutTournee.BROUILLON,
        )

    # On vide et on refait : c'est ce qui rend le calcul rejouable autant de
    # fois qu'on veut, ce qui était toute la demande.
    tournee.arrets.all().delete()
    Livraison.objects.filter(tournee=tournee).update(tournee=None)

    for rang, livraison in enumerate(ordre, start=1):
        livraison.tournee = tournee
        livraison.save(update_fields=["tournee"])
        ArretTournee.objects.create(tournee=tournee, livraison=livraison, ordre=rang)

    tournee.nombre_arrets = len(ordre)
    tournee.distance_totale_km = distance
    tournee.save(update_fields=["nombre_arrets", "distance_totale_km"])
    return tournee


@transaction.atomic
def attribuer(tournee, livreur):
    """Confier la tournée à un livreur Standard, et le prévenir.

    Un livreur Express n'a rien à faire ici : il prend des courses à la volée.
    Confier une tournée à quelqu'un qui n'a pas le véhicule pour, c'est une
    journée perdue pour lui et pour les clients.
    """
    if livreur.mode_livraison != "STANDARD":
        raise CalculRefuse(
            "mauvais_mode",
            f"{livreur.utilisateur.prenom} est livreur Express : il prend des "
            "courses à la volée, pas des tournées.",
        )
    if livreur.statut_validation != "VALIDE":
        raise CalculRefuse(
            "livreur_non_valide",
            "Ce compte de livreur n'a pas encore été validé.",
        )
    if tournee.statut in (StatutTournee.EN_COURS, StatutTournee.TERMINEE):
        raise CalculRefuse("tournee_partie", "Cette tournée est déjà partie.")

    tournee.livreur = livreur
    tournee.statut = StatutTournee.AFFECTEE
    tournee.save(update_fields=["livreur", "statut"])

    Livraison.objects.filter(tournee=tournee).update(
        livreur=livreur,
        statut_livraison=StatutLivraison.ATTRIBUEE,
        date_attribution=timezone.now(),
    )

    emettre(Evenement(
        nom="TOURNEE_ATTRIBUEE", type_objet="TOURNEE", id_objet=tournee.id,
        titre=f"Une tournée de {tournee.nombre_arrets} arrêts vous est confiée",
        message=f"Départ depuis {tournee.entrepot.nom}, "
                f"{tournee.distance_totale_km or 0} km au total.",
        lien="/tournee",
        apres={"statut": tournee.statut},
        destinataires=[livreur.utilisateur],
    ))
    return tournee
