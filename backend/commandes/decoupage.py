"""Le decoupage du panier en commandes — decision D-10.

C'est la piece la plus structurante du projet, et la regle tient en trois
lignes :

1. On groupe les lignes du panier **par vendeur**.
2. Chaque vendeur **Express** devient sa propre commande, livree seule.
3. Tous les vendeurs **Standard** sont regroupes en **une** commande
   multi-vendeur, qui se decompose en sous-commandes a la preparation.

Un panier mixte donne donc N commandes Express plus, eventuellement, une
commande Standard — et un seul paiement pour le client.

Pourquoi ce n'est pas negociable : une commande Express est portee par un
livreur unique depuis une seule boutique. Deux restaurants dans une meme
commande, ce serait un livreur qui attend deux cuisines. Les colis Standard,
eux, transitent par un entrepot : les regrouper est justement l'interet du
circuit.
"""
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from comptes.models import TypeService

from . import reservation
from .models import (
    Commande,
    LigneCommande,
    Panier,
    SousCommande,
    StatutCommande,
    StatutPanier,
)


class PanierInvalide(Exception):
    """Le panier ne peut pas devenir une commande. Le message est pour l'humain."""


def numero_commande():
    """Lisible par un humain au telephone, et impossible a deviner.

    Le jour et une part aleatoire : un numero sequentiel dirait a chacun
    combien de commandes la plateforme recoit.
    """
    return f"RD-{timezone.now():%y%m%d}-{secrets.token_hex(3).upper()}"


def frais_livraison_centimes(type_service, montant_produits_centimes, zone=None):
    """Frais par bandes, jamais au metre pres — decision D-11.

    Express : quasi fixe dans le rayon couvert, la boutique disparaissant du
    catalogue au-dela. Standard : frais par zone, offerts au-dela d'un seuil,
    pour pousser a grouper les achats sans jamais l'imposer.
    """
    if type_service == TypeService.EXPRESS:
        return 290

    base = zone.frais_base_centimes if zone else 490
    seuil = zone.seuil_gratuite_centimes if zone else 5000
    if seuil and montant_produits_centimes >= seuil:
        return 0
    return base


def probleme_de_ligne(ligne):
    """Ce qui empeche CETTE ligne d'etre commandee, ou None.

    Rendue publique parce que trois appelants en ont besoin : l'apercu, la
    creation de commande, et la route qui nettoie le panier.
    """
    produit = ligne.produit
    if not produit.est_visible or produit.vendeur.statut_validation != "VALIDE":
        return {
            "code": "retire",
            "message": f"« {produit.nom} » a ete retire de la vente.",
        }
    if produit.stock_commandable <= 0:
        return {
            "code": "rupture",
            "message": f"« {produit.nom} » est en rupture de stock.",
        }
    if produit.stock_commandable < ligne.quantite:
        return {
            "code": "stock_insuffisant",
            "message": (f"« {produit.nom} » : il ne reste que "
                        f"{produit.stock_commandable} exemplaire(s)."),
            "disponible": produit.stock_commandable,
        }
    return None


def lignes_bloquantes(panier):
    """Les lignes du panier qu'on ne peut pas commander, avec leur raison."""
    bloquees = []
    for ligne in panier.lignes.select_related("produit", "produit__vendeur").order_by("id"):
        souci = probleme_de_ligne(ligne)
        if souci:
            bloquees.append({
                "id_ligne": ligne.id,
                "id_produit": ligne.produit_id,
                "nom": ligne.produit.nom,
                "quantite": ligne.quantite,
                **souci,
            })
    return bloquees


def _apercu_groupes(panier, strict=True):
    """Groupe les lignes par vendeur.

    `strict=True` refuse le panier des la premiere ligne fautive : c'est ce
    qu'il faut au moment de creer la commande, ou l'on ne veut rien facturer
    d'indisponible. `strict=False` ignore ces lignes et rend ce qui reste
    commandable : c'est ce qu'il faut a l'apercu, pour montrer au client
    quatorze articles valides et UN probleme, plutot qu'un mur.
    """
    lignes = list(
        panier.lignes.select_related("produit", "produit__vendeur").order_by("id")
    )
    if not lignes:
        raise PanierInvalide("Votre panier est vide.")

    groupes = {}
    for ligne in lignes:
        souci = probleme_de_ligne(ligne)
        if souci:
            if strict:
                raise PanierInvalide(souci["message"])
            continue
        produit = ligne.produit
        groupes.setdefault(produit.vendeur_id, {"vendeur": produit.vendeur, "lignes": []})
        groupes[produit.vendeur_id]["lignes"].append(ligne)
    return groupes


def apercu(panier):
    """Ce que le panier donnera, AVANT de valider quoi que ce soit.

    Le client doit savoir qu'il s'apprete a creer trois commandes livrees
    separement — le decouvrir apres le paiement serait une mauvaise surprise.
    """
    groupes = _apercu_groupes(panier, strict=False)
    commandes = []

    express = [g for g in groupes.values() if g["vendeur"].type_activite == TypeService.EXPRESS]
    standard = [g for g in groupes.values() if g["vendeur"].type_activite == TypeService.STANDARD]

    for groupe in express:
        produits = sum(
            ligne.produit.prix_unitaire_centimes * ligne.quantite for ligne in groupe["lignes"]
        )
        commandes.append({
            "type_service": TypeService.EXPRESS,
            "boutiques": [groupe["vendeur"].nom_boutique],
            "articles": sum(ligne.quantite for ligne in groupe["lignes"]),
            "montant_produits_centimes": produits,
            "montant_livraison_centimes": frais_livraison_centimes(TypeService.EXPRESS, produits),
        })

    if standard:
        produits = sum(
            ligne.produit.prix_unitaire_centimes * ligne.quantite
            for groupe in standard
            for ligne in groupe["lignes"]
        )
        commandes.append({
            "type_service": TypeService.STANDARD,
            "boutiques": sorted(groupe["vendeur"].nom_boutique for groupe in standard),
            "articles": sum(
                ligne.quantite for groupe in standard for ligne in groupe["lignes"]
            ),
            "montant_produits_centimes": produits,
            "montant_livraison_centimes": frais_livraison_centimes(TypeService.STANDARD, produits),
        })

    total = sum(c["montant_produits_centimes"] + c["montant_livraison_centimes"] for c in commandes)
    # Les lignes ecartees partent avec l'apercu : l'ecran doit pouvoir dire
    # LESQUELLES posent probleme, et proposer de les retirer.
    return {
        "commandes": commandes,
        "total_centimes": total,
        "lignes_bloquantes": lignes_bloquantes(panier),
    }


@transaction.atomic
def decouper(panier: Panier, client, adresse):
    """Transforme le panier en commandes. Tout ou rien.

    La transaction est indispensable : creer deux commandes sur trois, puis
    echouer, laisserait un panier a moitie converti que personne ne saurait
    rattraper.
    """
    groupes = _apercu_groupes(panier)
    creees = []

    express = [g for g in groupes.values() if g["vendeur"].type_activite == TypeService.EXPRESS]
    standard = [g for g in groupes.values() if g["vendeur"].type_activite == TypeService.STANDARD]

    for groupe in express:
        creees.append(_creer_commande(panier, client, adresse, TypeService.EXPRESS, [groupe]))
    if standard:
        creees.append(_creer_commande(panier, client, adresse, TypeService.STANDARD, standard))

    panier.statut = StatutPanier.CONVERTI
    panier.save(update_fields=["statut"])
    return creees


def _creer_commande(panier, client, adresse, type_service, groupes):
    zone = getattr(adresse, "zone", None)
    montant_produits = 0

    commande = Commande.objects.create(
        numero_commande=numero_commande(),
        client=client,
        adresse_livraison=adresse,
        panier_origine=panier,
        type_service=type_service,
        statut_actuel=StatutCommande.EN_ATTENTE_PAIEMENT,
        date_livraison_estimee=timezone.now()
        + (timedelta(minutes=45) if type_service == TypeService.EXPRESS else timedelta(days=2)),
    )

    for groupe in groupes:
        vendeur = groupe["vendeur"]
        sous_commande = SousCommande.objects.create(commande=commande, vendeur=vendeur)
        part_vendeur = 0

        for ligne in groupe["lignes"]:
            produit = ligne.produit
            sous_total = produit.prix_unitaire_centimes * ligne.quantite
            part_vendeur += sous_total
            montant_produits += sous_total

            # Le nom et le prix sont RECOPIES : une commande passee ne change
            # plus, meme si le produit est renomme ou reevalue.
            LigneCommande.objects.create(
                sous_commande=sous_commande,
                produit=produit,
                nom_produit_capture=produit.nom,
                prix_unitaire_centimes=produit.prix_unitaire_centimes,
                quantite=ligne.quantite,
                sous_total_centimes=sous_total,
            )


        commission = round(part_vendeur * float(vendeur.taux_commission))
        sous_commande.montant_vendeur_centimes = part_vendeur - commission
        sous_commande.montant_commission_centimes = commission
        sous_commande.save(
            update_fields=["montant_vendeur_centimes", "montant_commission_centimes"]
        )

    livraison = frais_livraison_centimes(type_service, montant_produits, zone)
    commande.montant_produits_centimes = montant_produits
    commande.montant_livraison_centimes = livraison
    commande.montant_total_centimes = montant_produits + livraison
    commande.save(
        update_fields=[
            "montant_produits_centimes",
            "montant_livraison_centimes",
            "montant_total_centimes",
        ]
    )

    # Reservation courte, le temps du paiement (D-15) : le stock n'est pas
    # decremente, il est mis de cote. Un seul module en est l'auteur, sans
    # quoi la meme commande finit reservee deux fois.
    reservation.poser(commande)
    return commande
