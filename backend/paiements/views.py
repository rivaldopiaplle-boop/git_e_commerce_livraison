"""Le paiement — D-12, D-15, D-18.

Il tourne **sans aucune cle** grace au simulateur (D-18) : le parcours complet
se demontre, echec de paiement compris, et le jour ou une cle Stripe arrive,
`coeur/services_externes.py` bascule sans que ces vues changent.

Deux regles structurent tout ce fichier :

  · **la reservation se pose a la creation de la commande, pas au panier**
    (D-15). Le stock affiche reste le stock reel, identique pour tout le monde,
    y compris pour qui a deja l'article dans son panier : reserver a l'ajout
    produirait une interface incomprehensible — le client croirait epuise
    l'article qu'il tient. Ces vues n'ecrivent jamais le compteur elles-memes,
    elles passent par `commandes.reservation`, seul auteur ;
  · **la confirmation vient du serveur, jamais du navigateur** (D-12). Un
    client qui ferme son onglet ne doit pas empecher une commande payee d'etre
    reconnue comme telle. Elle est donc rejouable de bout en bout.
"""
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from coeur.evenements import Evenement, emettre
from coeur.services_externes import fournisseur_de_paiement
from commandes import reservation
from commandes.models import Commande, HistoriqueStatut, StatutCommande

from .models import Facture, Paiement, RepartitionVendeur, StatutPaiement


def _refus(code, message, statut=status.HTTP_409_CONFLICT):
    return Response(
        {"erreur": {"code": code, "message": message, "details": {}}}, status=statut
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def ouvrir_intention(requete, identifiant):
    """Ouvrir le paiement d'une commande, apres avoir verifie sa reservation.

    La reservation a normalement ete posee a la creation de la commande. Elle
    peut pourtant manquer : le client avait abandonne son paiement, puis il
    revient sur la meme commande. C'est un cas courant, pas une bizarrerie, et
    `reservation.poser` le traite sans effort — poser une reservation deja
    posee ne fait rien, la reposer apres un abandon la retablit.
    """
    profil = getattr(requete.user, "profil_client", None)
    commande = Commande.objects.filter(pk=identifiant, client=profil).first()
    if commande is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if commande.statut_actuel != StatutCommande.EN_ATTENTE_PAIEMENT:
        return _refus("deja_payee", "Cette commande n'attend pas de paiement.")

    manquants = reservation.poser(commande)
    if manquants:
        return Response(
            {"erreur": {
                "code": "stock_insuffisant",
                "message": "Le stock a change pendant que vous prepariez votre commande.",
                "details": {"produits": manquants},
            }},
            status=status.HTTP_409_CONFLICT,
        )

    intention = fournisseur_de_paiement().ouvrir(
        commande.montant_total_centimes, commande.numero_commande
    )

    paiement, _ = Paiement.objects.update_or_create(
        commande=commande,
        defaults={
            "montant_centimes": commande.montant_total_centimes,
            "statut_paiement": StatutPaiement.EN_ATTENTE,
            "reference_stripe": intention.reference,
        },
    )

    return Response({"data": {
        "reference": intention.reference,
        "secret_client": intention.secret_client,
        "montant_centimes": intention.montant_centimes,
        "statut": intention.statut,
        "simule": intention.simule,
        "reservation_expire_dans_minutes": reservation.DUREE_MINUTES,
        "identifiant_paiement": paiement.id,
    }})


@api_view(["POST"])
@permission_classes([AllowAny])
@transaction.atomic
def confirmer(requete):
    """La confirmation serveur — ce que Stripe appellerait un webhook (D-12).

    Elle est **ouverte** : en production, c'est Stripe qui appelle, et Stripe
    n'a pas de jeton de session. La securite vient de la signature du message,
    pas d'une authentification d'utilisateur. En simulation, la reference
    suffit — et le simulateur ne connait que des references qu'il a lui-meme
    fabriquees.
    """
    reference = str(requete.data.get("reference", "")).strip()
    paiement = (
        Paiement.objects.select_for_update()
        .select_related("commande", "commande__client__utilisateur")
        .filter(reference_stripe=reference)
        .first()
    )
    if paiement is None:
        return _refus("paiement_inconnu", "Aucun paiement pour cette reference.",
                      status.HTTP_404_NOT_FOUND)

    # Rejouer un webhook est NORMAL : les fournisseurs reessaient quand ils
    # doutent d'avoir ete recus. Confirmer deux fois ne doit rien decrementer
    # deux fois.
    if paiement.statut_paiement == StatutPaiement.CAPTURE:
        return Response({"data": {"statut": paiement.statut_paiement, "deja_traite": True}})

    resultat = fournisseur_de_paiement().capturer(reference)
    commande = paiement.commande

    if resultat != "CAPTURE":
        paiement.statut_paiement = StatutPaiement.ECHOUE
        paiement.save(update_fields=["statut_paiement"])
        reservation.relacher(commande)
        emettre(Evenement(
            nom="PAIEMENT_ECHOUE", type_objet="COMMANDE", id_objet=commande.id,
            titre="Votre paiement n'a pas abouti",
            message="Aucun montant n'a ete debite. Votre panier vous attend.",
            lien="/commande",
            apres={"statut_paiement": paiement.statut_paiement},
            destinataires=[commande.client.utilisateur],
        ))
        return Response({"data": {"statut": paiement.statut_paiement}})

    # Le paiement est capture : la reserve devient une vraie sortie de stock.
    reservation.consommer(commande, auteur=requete.user)

    paiement.statut_paiement = StatutPaiement.CAPTURE
    paiement.date_paiement = timezone.now()
    paiement.save(update_fields=["statut_paiement", "date_paiement"])

    # La repartition par vendeur : sans cette trace, aucun audit n'est possible
    # sur une commande multi-vendeur.
    for sous_commande in commande.sous_commandes.select_related("vendeur"):
        RepartitionVendeur.objects.update_or_create(
            sous_commande=sous_commande,
            defaults={
                "paiement": paiement,
                "vendeur": sous_commande.vendeur,
                "montant_vendeur_centimes": sous_commande.montant_vendeur_centimes,
                "montant_commission_centimes": sous_commande.montant_commission_centimes,
                "reference_transfert_stripe": f"tr_{paiement.reference_stripe}_"
                                              f"{sous_commande.id}",
                "statut": "TRANSFERE",
            },
        )

    Facture.objects.get_or_create(
        commande=commande,
        defaults={
            "numero_facture": f"F-{commande.numero_commande}",
            "montant_ht_centimes": int(commande.montant_total_centimes / 1.2),
            "montant_ttc_centimes": commande.montant_total_centimes,
        },
    )

    avant = commande.statut_actuel
    commande.statut_actuel = StatutCommande.PAYEE
    commande.save(update_fields=["statut_actuel"])
    HistoriqueStatut.objects.create(
        type_objet="COMMANDE", id_objet=commande.id,
        statut_avant=avant, statut_apres=commande.statut_actuel,
        commentaire="Paiement confirme par le serveur",
    )

    destinataires = [commande.client.utilisateur]
    destinataires += [
        sous.vendeur.utilisateur for sous in commande.sous_commandes.select_related(
            "vendeur__utilisateur"
        )
    ]
    emettre(Evenement(
        nom="COMMANDE_PAYEE", type_objet="COMMANDE", id_objet=commande.id,
        titre=f"Commande {commande.numero_commande} payee",
        message="La preparation peut commencer.",
        lien="/mes-commandes",
        avant={"statut": avant},
        apres={"statut": commande.statut_actuel},
        destinataires=destinataires,
    ))

    return Response({"data": {
        "statut": paiement.statut_paiement,
        "commande": commande.numero_commande,
        "statut_commande": commande.statut_actuel,
    }})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def abandonner(requete, identifiant):
    """Renoncer a payer : la reserve repart a la vente immediatement.

    Sans ce chemin, il faudrait attendre l'expiration — et pendant dix
    minutes, un article resterait invendable pour tout le monde alors que son
    acheteur a deja quitte la page.
    """
    profil = getattr(requete.user, "profil_client", None)
    commande = Commande.objects.filter(pk=identifiant, client=profil).first()
    if commande is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if commande.statut_actuel != StatutCommande.EN_ATTENTE_PAIEMENT:
        return _refus("deja_payee", "Cette commande n'attend plus de paiement.")

    relachee = reservation.relacher(commande)
    Paiement.objects.filter(commande=commande).update(
        statut_paiement=StatutPaiement.ECHOUE
    )
    return Response({"data": {"reservation_relachee": relachee}})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ma_facture(requete, identifiant):
    """La facture d'une commande, pour l'ecran imprimable (D-78).

    Elle s'imprime par le navigateur : une feuille de style dediee et
    `window.print()`. Aucune dependance, aucun travail serveur, et le
    navigateur propose lui-meme « Enregistrer en PDF ».
    """
    profil = getattr(requete.user, "profil_client", None)
    commande = (
        Commande.objects.filter(pk=identifiant, client=profil)
        .prefetch_related("sous_commandes__lignes", "sous_commandes__vendeur")
        .select_related("adresse_livraison", "facture")
        .first()
    )
    if commande is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    facture = getattr(commande, "facture", None)
    return Response({"data": {
        "numero_facture": facture.numero_facture if facture else None,
        "numero_commande": commande.numero_commande,
        "date": commande.date_commande,
        "adresse": str(commande.adresse_livraison),
        "montant_produits_centimes": commande.montant_produits_centimes,
        "montant_livraison_centimes": commande.montant_livraison_centimes,
        "montant_total_centimes": commande.montant_total_centimes,
        "montant_ht_centimes": facture.montant_ht_centimes if facture else None,
        "taux_tva": float(facture.taux_tva) if facture else 0.2,
        "lignes": [
            {
                "boutique": sous.vendeur.nom_boutique,
                "nom": ligne.nom_produit_capture,
                "quantite": ligne.quantite,
                "prix_unitaire_centimes": ligne.prix_unitaire_centimes,
                "sous_total_centimes": ligne.sous_total_centimes,
            }
            for sous in commande.sous_commandes.all()
            for ligne in sous.lignes.all()
        ],
    }})
