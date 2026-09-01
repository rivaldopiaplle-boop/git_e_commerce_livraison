"""La reservation de stock d'une commande — un seul endroit, D-15.

Ce fichier existe a cause d'un vrai defaut : le stock etait reserve **deux
fois** pour une meme commande, une fois a sa creation
(`decoupage._creer_commande`) et une fois a l'ouverture du paiement. Deux
reservations, une seule liberation : chaque commande payee laissait derriere
elle une reserve fantome qui rendait des articles invendables pour toujours.

La lecon est plus generale que le bug : **un compteur partage ne doit avoir
qu'un seul auteur.** D'ou ce module, et le drapeau `stock_reserve_pose` porte
par la commande. Poser une reservation deja posee ne fait rien ; en relacher
une qui ne l'est pas non plus. Les trois operations sont donc rejouables sans
degat, ce qui est exactement ce qu'exige un webhook de paiement (D-12) : les
fournisseurs reessaient quand ils doutent d'avoir ete recus.

Les trois moments de la vie d'une reservation :

  · **poser** — a la creation de la commande, puis a chaque nouvelle tentative
    de paiement apres un abandon ;
  · **relacher** — paiement refuse, abandonne, ou commande annulee ; le stock
    repart a la vente sans qu'aucun mouvement n'ait ete invente, puisque rien
    n'est jamais sorti ;
  · **consommer** — le paiement est capture : la reserve devient une sortie
    reelle, avec son `MouvementStock` (scenario 4.4). Un stock qui baisse sans
    mouvement est un stock qu'on ne saura pas expliquer le lendemain.
"""
from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from catalogue.models import MouvementStock, Produit, TypeMouvement

# Une reservation ne dure pas eternellement : au-dela, le stock revient a la
# vente. Sans expiration, un panier abandonne bloquerait un article pour
# toujours, et le catalogue afficherait « epuise » sans que personne ne
# comprenne pourquoi. Dix minutes est le delai qu'affichent les billetteries :
# assez pour payer sans se presser, assez court pour ne pas geler une vente.
DUREE_MINUTES = 10


def _lignes(commande):
    for sous_commande in commande.sous_commandes.all():
        for ligne in sous_commande.lignes.all():
            if ligne.produit_id:
                yield ligne


def _besoins(commande):
    """Ce que la commande demande, produit par produit.

    On agrege : rien n'interdit au meme produit d'apparaitre dans deux
    sous-commandes, et verrouiller deux fois la meme ligne pour l'ajuster deux
    fois est le genre de detail qui finit en compteur faux.
    """
    besoins = {}
    for ligne in _lignes(commande):
        besoins[ligne.produit_id] = besoins.get(ligne.produit_id, 0) + ligne.quantite
    return besoins


@transaction.atomic
def poser(commande):
    """Mettre le stock de cote. Rend la liste de ce qui manque — vide si tout va bien.

    `select_for_update` sur les produits n'est pas un exces : deux clients qui
    paient le dernier exemplaire au meme instant, c'est le cas normal d'une
    vente flash. Sans verrou, les deux passent et l'un des deux ne sera jamais
    livre.
    """
    if commande.stock_reserve_pose:
        return []

    besoins = _besoins(commande)
    if not besoins:
        return []

    # On verrouille AVANT de verifier : verifier puis verrouiller laisse la
    # place a une autre transaction entre les deux.
    produits = {
        produit.id: produit
        for produit in Produit.objects.select_for_update().filter(id__in=besoins)
    }

    manquants = [
        {
            "produit": produits[identifiant].nom,
            "demande": quantite,
            "disponible": produits[identifiant].stock_commandable,
        }
        for identifiant, quantite in besoins.items()
        if identifiant in produits and produits[identifiant].stock_commandable < quantite
    ]
    if manquants:
        return manquants

    for identifiant, quantite in besoins.items():
        Produit.objects.filter(pk=identifiant).update(
            stock_reserve=F("stock_reserve") + quantite
        )

    commande.stock_reserve_pose = True
    commande.save(update_fields=["stock_reserve_pose"])
    return []


@transaction.atomic
def relacher(commande):
    """Rendre a la vente ce qui avait ete mis de cote. Vrai si quelque chose a bouge."""
    if not commande.stock_reserve_pose:
        return False

    for identifiant, quantite in _besoins(commande).items():
        Produit.objects.filter(
            pk=identifiant, stock_reserve__gte=quantite
        ).update(stock_reserve=F("stock_reserve") - quantite)

    commande.stock_reserve_pose = False
    commande.save(update_fields=["stock_reserve_pose"])
    return True


@transaction.atomic
def consommer(commande, auteur=None):
    """La reserve devient une sortie reelle, avec sa trace. Vrai si elle etait posee.

    Refuser de consommer une reservation absente est ce qui rend la
    confirmation de paiement rejouable : le deuxieme appel du webhook ne
    decremente rien.
    """
    if not commande.stock_reserve_pose:
        return False

    for identifiant, quantite in _besoins(commande).items():
        Produit.objects.filter(pk=identifiant).update(
            stock_disponible=F("stock_disponible") - quantite,
            stock_reserve=F("stock_reserve") - quantite,
        )
        produit = Produit.objects.get(pk=identifiant)
        MouvementStock.objects.create(
            produit=produit,
            auteur=auteur if auteur is not None and auteur.is_authenticated else None,
            type=TypeMouvement.VENTE,
            quantite=-quantite,
            motif=f"Commande {commande.numero_commande}",
            stock_apres=produit.stock_disponible,
        )

    commande.stock_reserve_pose = False
    commande.save(update_fields=["stock_reserve_pose"])
    return True


@transaction.atomic
def liberer_les_expirees(minutes=DUREE_MINUTES):
    """Rendre a la vente ce que des paniers abandonnes retiennent encore.

    Elle est appelee au demarrage du projet et par la commande de peuplement,
    faute d'ordonnanceur. C'est volontairement le choix le plus simple qui
    marche : une tache planifiee demanderait un service de plus a heberger,
    pour un projet qui doit tourner sur une offre gratuite (D-19).

    Rend le nombre de commandes liberees.
    """
    from .models import Commande, StatutCommande

    limite = timezone.now() - timedelta(minutes=minutes)
    expirees = Commande.objects.filter(
        stock_reserve_pose=True,
        statut_actuel=StatutCommande.EN_ATTENTE_PAIEMENT,
        date_commande__lt=limite,
    ).prefetch_related("sous_commandes__lignes")

    liberees = 0
    for commande in expirees:
        if relacher(commande):
            liberees += 1
    return liberees
