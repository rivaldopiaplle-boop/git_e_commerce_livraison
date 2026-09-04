"""L'annulation d'une part de commande par son vendeur — D-07, D-81, D-144.

Ce que faisait l'ecran avant : un bouton « Annuler » qui posait le statut
`ANNULEE` sur la sous-commande, et rien d'autre.

Autrement dit, quand un restaurant annulait :

  · **le client n'etait prevenu de rien.** Sa commande restait « payee » ;
  · **son argent restait pris.** Aucun remboursement, aucune trace ;
  · **le stock ne revenait pas a la vente**, alors que la vente n'avait pas eu
    lieu — trois plats disparaissaient du compteur pour toujours ;
  · **aucun motif n'etait demande**, alors que D-07 l'exige depuis le debut.

C'est exactement ce que tu appelais *« la chaine n'est pas comme dans la
realite »* (D-81) : les etiquettes changeaient, le metier ne suivait pas.

Ce module fait le travail complet, en une transaction. Il est appele par la
vue, et par elle seule : une annulation ecrite a deux endroits finirait par
diverger, et c'est celle qui en fait le moins qui gagnerait.
"""
from django.db import transaction
from django.db.models import F

from catalogue.models import MouvementStock, Produit, TypeMouvement
from coeur.evenements import Evenement, emettre
from coeur.services_externes import fournisseur_de_paiement
from paiements.models import Paiement, Remboursement, RepartitionVendeur, TypeRemboursement

from .models import (
    HistoriqueStatut,
    StatutCommande,
    StatutPreparation,
    TypeObjetSuivi,
)

# Les motifs qu'un vendeur peut invoquer. Une liste fermee plutot qu'un champ
# libre seul : « annule » sans raison est ce qui remplit les litiges, et un
# motif classe se compte — on peut voir qu'une boutique annule six fois par
# semaine pour rupture, ce qu'un texte libre ne dirait jamais.
MOTIFS = {
    "RUPTURE": "Produit finalement indisponible",
    "FERMETURE": "Boutique fermee ou service interrompu",
    "ERREUR_PRIX": "Erreur de prix ou de description",
    "CLIENT": "A la demande du client",
    "AUTRE": "Autre raison",
}

# Le texte libre reste obligatoire : c'est lui que le client lit, et un motif
# classe seul (« RUPTURE ») ne dit pas QUEL produit ni pourquoi.
LONGUEUR_MINIMALE = 15


class AnnulationRefusee(Exception):
    """Levee avec un code et un message destines a l'ecran."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def _rendre_le_stock(sous_commande, auteur):
    """Ce qui n'est pas vendu retourne a la vente, avec sa trace.

    Le stock a deja ete decremente a la capture du paiement
    (`reservation.consommer`). Une annulation apres paiement doit donc
    **remonter** le compteur, et laisser un mouvement : un stock qui remonte
    sans explication est aussi inexplicable qu'un stock qui baisse sans
    explication (scenario 4.4).
    """
    for ligne in sous_commande.lignes.select_related("produit"):
        if not ligne.produit_id:
            continue
        Produit.objects.filter(pk=ligne.produit_id).update(
            stock_disponible=F("stock_disponible") + ligne.quantite
        )
        produit = Produit.objects.get(pk=ligne.produit_id)
        MouvementStock.objects.create(
            produit=produit,
            auteur=auteur if auteur is not None and auteur.is_authenticated else None,
            type=TypeMouvement.ANNULATION,
            quantite=ligne.quantite,
            motif=f"Annulation de {sous_commande.commande.numero_commande} "
                  f"par {sous_commande.vendeur.nom_boutique}",
            stock_apres=produit.stock_disponible,
        )


def _rembourser(sous_commande, texte, auteur):
    """Rendre au client ce qu'il a paye pour CETTE part, et rien de plus.

    Sur une commande Standard a trois boutiques, une seule annule : les deux
    autres livrent, et le client ne doit etre rembourse que du tiers concerne.
    Rembourser la totalite serait aussi faux que ne rien rembourser.

    Les frais de livraison ne sont pas rendus tant qu'une part subsiste : la
    tournee a lieu quand meme. Si toute la commande tombe, ils le sont — c'est
    traite par l'appelant, qui voit l'ensemble.
    """
    paiement = Paiement.objects.filter(
        commande=sous_commande.commande, statut_paiement="CAPTURE"
    ).first()
    if paiement is None:
        return 0

    deja = sum(remboursement.montant_centimes
               for remboursement in paiement.remboursements.all())
    plafond = paiement.montant_centimes - deja
    montant = min(sous_commande.montant_vendeur_centimes
                  + sous_commande.montant_commission_centimes, plafond)
    if montant <= 0:
        return 0

    reference = fournisseur_de_paiement().rembourser(paiement.reference_stripe, montant)
    Remboursement.objects.create(
        paiement=paiement,
        montant_centimes=montant,
        motif=texte[:200],
        type=(TypeRemboursement.TOTAL if montant + deja >= paiement.montant_centimes
              else TypeRemboursement.PARTIEL),
        declenche_par=auteur if auteur is not None and auteur.is_authenticated else None,
        reference_stripe=str(reference),
    )
    # Le vendeur qui annule n'est pas paye. C'est evident et c'etait pourtant
    # le cas : sa repartition restait « a transferer ».
    RepartitionVendeur.objects.filter(sous_commande=sous_commande).update(statut="ANNULE")
    return montant


@transaction.atomic
def annuler(sous_commande, motif, texte, auteur):
    """Annuler une part de commande, entierement.

    Rend le montant rembourse, en centimes. Leve `AnnulationRefusee` si le
    motif manque ou si l'etape ne le permet plus.
    """
    if sous_commande.statut_preparation not in (
        StatutPreparation.A_PREPARER, StatutPreparation.EN_PREPARATION
    ):
        raise AnnulationRefusee(
            "trop_tard",
            "Cette part est deja prete ou expediee : elle ne s'annule plus ici. "
            "Le client peut ouvrir un litige, qui sera arbitre.",
        )

    if motif not in MOTIFS:
        raise AnnulationRefusee("motif_invalide", "Choisissez un motif dans la liste.")

    texte = str(texte or "").strip()
    if len(texte) < LONGUEUR_MINIMALE:
        raise AnnulationRefusee(
            "explication_trop_courte",
            "Expliquez en une phrase ce qui s'est passe : c'est ce texte que le "
            "client lira, et c'est ce qui evite qu'il ouvre un litige.",
        )

    commande = sous_commande.commande
    avant = sous_commande.statut_preparation
    sous_commande.statut_preparation = StatutPreparation.ANNULEE
    sous_commande.save(update_fields=["statut_preparation"])

    HistoriqueStatut.objects.create(
        type_objet=TypeObjetSuivi.SOUS_COMMANDE, id_objet=sous_commande.id,
        statut_avant=avant, statut_apres=StatutPreparation.ANNULEE, utilisateur=auteur,
        commentaire=f"{MOTIFS[motif]} — {texte}"[:255],
    )

    _rendre_le_stock(sous_commande, auteur)
    montant = _rembourser(sous_commande, f"{MOTIFS[motif]} — {texte}", auteur)

    # Toutes les parts annulees : la commande entiere tombe.
    restantes = commande.sous_commandes.exclude(
        statut_preparation=StatutPreparation.ANNULEE
    ).exists()
    if not restantes:
        precedent = commande.statut_actuel
        commande.statut_actuel = (
            StatutCommande.REMBOURSEE if montant else StatutCommande.ANNULEE
        )
        commande.save(update_fields=["statut_actuel"])
        HistoriqueStatut.objects.create(
            type_objet=TypeObjetSuivi.COMMANDE, id_objet=commande.id,
            statut_avant=precedent, statut_apres=commande.statut_actuel,
            utilisateur=auteur,
            commentaire="Toutes les boutiques ont annule",
        )

    # **La notification forte de D-07.** Le client apprenait avant... rien du
    # tout. Le message dit qui annule, pourquoi, ce qui reste, et ce qui a ete
    # rendu — les quatre questions qu'il se pose dans cet ordre.
    reste = "Le reste de votre commande suit son cours." if restantes else ""
    rendu = (f"{montant / 100:.2f} EUR vous sont rembourses." if montant
             else "Aucun montant n'avait ete debite.")
    emettre(Evenement(
        nom="SOUS_COMMANDE_ANNULEE",
        type_objet="SOUS_COMMANDE", id_objet=sous_commande.id,
        titre=f"{sous_commande.vendeur.nom_boutique} a annule sa part de "
              f"{commande.numero_commande}",
        message=f"{MOTIFS[motif]} : {texte} {rendu} {reste}".strip(),
        lien="/espace/commandes",
        avant={"statut_preparation": avant},
        apres={"statut_preparation": StatutPreparation.ANNULEE,
               "montant_rembourse_centimes": montant},
        destinataires=[commande.client.utilisateur],
    ))
    return montant
