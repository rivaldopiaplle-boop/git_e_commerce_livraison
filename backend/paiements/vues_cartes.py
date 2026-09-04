"""Le carnet de cartes du client, et la répartition de l'argent — O-5.

Deux besoins distincts, réunis ici parce qu'ils répondent à la même remarque :
*« payer est validé sans carte »* et *« l'argent payé, on ne voit pas la
distribution chez les vendeurs, la part du livreur, celle de l'application »*.
"""
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from commandes.models import Commande

from .cartes import CARTES_D_ESSAI, CarteRefusee, MoyenPaiement, valider
from .models import Paiement, RepartitionVendeur, StatutPaiement


def _refus(champ, code, message):
    return Response(
        {"erreur": {"code": code, "message": message, "details": {"champ": champ}}},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def mes_cartes(requete):
    """Le carnet de cartes : le lire, en ajouter une.

    C'est ce qui rend le deuxième paiement instantané. Le coût de saisie est
    payé **une seule fois**, ce qui était ta demande : *« que ça ne prenne pas
    beaucoup de temps »*.
    """
    profil = getattr(requete.user, "profil_client", None)
    if profil is None:
        return Response({"data": {"cartes": [], "cartes_d_essai": []}})

    if requete.method == "POST":
        try:
            marque, quatre, jeton, refusee = valider(
                requete.data.get("numero"),
                requete.data.get("mois"),
                requete.data.get("annee"),
                requete.data.get("cryptogramme"),
            )
        except CarteRefusee as souci:
            return _refus(souci.champ, souci.code, souci.message)

        with transaction.atomic():
            carte, cree = MoyenPaiement.objects.get_or_create(
                jeton=jeton,
                defaults={
                    "client": profil, "marque": marque, "quatre_derniers": quatre,
                    "mois_expiration": int(requete.data.get("mois")),
                    "annee_expiration": _annee(requete.data.get("annee")),
                    # La première carte devient la carte par défaut : personne
                    # ne va cocher une case pour choisir entre une carte et
                    # rien.
                    "par_defaut": not profil.moyens_paiement.exists(),
                },
            )
            if not cree and carte.client_id != profil.id:
                # Deux personnes ne peuvent pas partager un jeton : le carnet
                # est nominatif.
                return _refus("numero", "carte_indisponible",
                              "Cette carte est déjà enregistrée sur un autre compte.")
            if requete.data.get("par_defaut"):
                profil.moyens_paiement.update(par_defaut=False)
                carte.par_defaut = True
                carte.save(update_fields=["par_defaut"])

        return Response({"data": carte.en_dictionnaire()},
                        status=status.HTTP_201_CREATED if cree else status.HTTP_200_OK)

    return Response({"data": {
        "cartes": [carte.en_dictionnaire() for carte in profil.moyens_paiement.all()],
        # La liste des cartes d'essai est SERVIE, pas cachée dans un
        # commentaire : une démonstration qu'on ne sait pas essayer ne se
        # démontre pas.
        "cartes_d_essai": [
            {"numero": numero, "marque": marque,
             "effet": "acceptée" if issue == "accepte" else "refusée"}
            for numero, (marque, issue) in CARTES_D_ESSAI.items()
        ],
    }})


def _annee(valeur):
    annee = int(valeur)
    return annee + 2000 if annee < 100 else annee


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def retirer_carte(requete, identifiant):
    """Retirer une carte du carnet.

    Rien ne se perd : les paiements passés gardent la trace de la carte
    utilisée, puisqu'ils portent leur propre référence. Retirer une carte
    n'efface pas l'histoire, elle cesse seulement d'être proposée.
    """
    profil = getattr(requete.user, "profil_client", None)
    carte = MoyenPaiement.objects.filter(pk=identifiant, client=profil).first()
    if carte is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    etait_par_defaut = carte.par_defaut
    carte.delete()
    if etait_par_defaut:
        suivante = profil.moyens_paiement.first()
        if suivante:
            suivante.par_defaut = True
            suivante.save(update_fields=["par_defaut"])

    return Response({"data": {
        "cartes": [carte.en_dictionnaire() for carte in profil.moyens_paiement.all()],
    }})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def repartition(requete, identifiant):
    """Où va l'argent d'une commande — O-5.

    **Ta remarque** : *« l'argent payé, on ne voit pas la distribution chez les
    vendeurs différents qui interviennent dans la commande, la part du livreur,
    celle de l'application ; rien n'existe réellement, encore moins
    synchronisé »*.

    La répartition existait bien en base (`RepartitionVendeur`), et le vendeur
    voyait sa part. **Personne ne voyait l'ensemble** — ni le client, ni
    l'administrateur. Or c'est précisément ce qui rend une place de marché
    compréhensible : un paiement unique, plusieurs destinataires.

    Les montants ne sont pas recalculés ici : ils sont **lus** là où ils ont
    été écrits au moment du paiement. Un écran qui recalcule finit toujours par
    afficher autre chose que ce qui a été versé.
    """
    profil = getattr(requete.user, "profil_client", None)
    commande = (
        Commande.objects.filter(pk=identifiant, client=profil)
        .prefetch_related("sous_commandes__vendeur", "sous_commandes__repartition")
        .select_related("livraison__livreur__utilisateur")
        .first()
    )
    if commande is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    paiement = Paiement.objects.filter(commande=commande).first()
    parts = []
    commission_totale = 0

    for sous in commande.sous_commandes.all():
        ligne = getattr(sous, "repartition", None)
        montant = (ligne.montant_vendeur_centimes if ligne
                   else sous.montant_vendeur_centimes)
        commission = (ligne.montant_commission_centimes if ligne
                      else sous.montant_commission_centimes)
        commission_totale += commission
        parts.append({
            "qui": sous.vendeur.nom_boutique,
            "role": "VENDEUR",
            "montant_centimes": montant,
            "statut": ligne.statut if ligne else "EN_ATTENTE",
            "detail": f"Sa part de la commande, commission déduite "
                      f"({commission / 100:.2f} EUR).",
        })

    livraison = getattr(commande, "livraison", None)
    if livraison is not None:
        from livraisons.tarifs import remuneration

        livreur = livraison.livreur
        # Le DETAIL du calcul, et pas seulement le montant : ta remarque O-5
        # etait « la distance du trajet et le prix pour vous ne sont pas
        # vraiment calcules, ca sort de nulle part ». Un chiffre qui ne
        # s'explique pas ne se verifie pas.
        _, detail = remuneration(commande.type_service, livraison.distance_km)
        parts.append({
            "qui": (f"{livreur.utilisateur.prenom}" if livreur else "Livreur à attribuer"),
            "role": "LIVREUR",
            "montant_centimes": livraison.remuneration_livreur_centimes,
            "statut": "VERSE" if livraison.statut_livraison == "LIVREE" else "EN_ATTENTE",
            "detail": detail,
        })

    verse = sum(part["montant_centimes"] for part in parts)
    total = commande.montant_total_centimes

    parts.append({
        "qui": "RivDinde",
        "role": "PLATEFORME",
        # Ce qui reste, et non un pourcentage recalculé : la somme des parts
        # affichées doit faire exactement le total payé, sinon l'écran ment
        # d'un centime et on ne lui fait plus confiance.
        "montant_centimes": max(0, total - verse),
        "statut": "ACQUIS" if paiement and paiement.statut_paiement == StatutPaiement.CAPTURE
        else "EN_ATTENTE",
        "detail": "Commission de la place de marché et frais de service.",
    })

    rembourse = sum(
        remboursement.montant_centimes
        for remboursement in (paiement.remboursements.all() if paiement else [])
    )

    return Response({"data": {
        "numero_commande": commande.numero_commande,
        "montant_total_centimes": total,
        "montant_rembourse_centimes": rembourse,
        "statut_paiement": paiement.statut_paiement if paiement else "EN_ATTENTE",
        "parts": parts,
    }})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def repartitions_a_verser(requete):
    """Le même relevé, côté administrateur : ce que la plateforme doit encore.

    Sans lui, « la part de l'application » restait une idée. C'est un chiffre,
    et il se lit.
    """
    from comptes.models import Role

    if getattr(requete.user, "role", None) != Role.ADMIN:
        return Response(status=status.HTTP_403_FORBIDDEN)

    lignes = (
        RepartitionVendeur.objects.select_related("vendeur", "sous_commande__commande")
        .order_by("statut", "-id")[:200]
    )
    par_statut = {}
    for ligne in lignes:
        entree = par_statut.setdefault(ligne.statut, {"nombre": 0, "montant_centimes": 0})
        entree["nombre"] += 1
        entree["montant_centimes"] += ligne.montant_vendeur_centimes

    return Response({"data": {
        "par_statut": par_statut,
        "commission_totale_centimes": sum(
            ligne.montant_commission_centimes for ligne in lignes
        ),
        "lignes": [
            {
                "id": ligne.id,
                "vendeur": ligne.vendeur.nom_boutique,
                "commande": ligne.sous_commande.commande.numero_commande,
                "montant_vendeur_centimes": ligne.montant_vendeur_centimes,
                "montant_commission_centimes": ligne.montant_commission_centimes,
                "statut": ligne.statut,
            }
            for ligne in lignes[:100]
        ],
    }})
