"""Le cycle complet d'un litige — D-94.

Quatre temps, et chacun a une raison d'exister :

  1. **le client ouvre** un litige sur une commande qu'il a recue. Pas avant :
     on ne conteste pas une livraison qui n'a pas eu lieu ;
  2. **le vendeur repond**, sous quarante-huit heures. Trancher sur la seule
     parole du client serait injuste, et c'est ce que fait la moitie des
     places de marche ;
  3. **l'administrateur arbitre**, avec les deux versions sous les yeux. Il ne
     peut pas trancher avant que le vendeur ait eu son tour — sauf si le delai
     est passe, auquel cas il tranche avec ce qu'il a, et l'ecran le dit ;
  4. **l'argent suit la decision** : un remboursement est ecrit, le paiement du
     vendeur est ajuste, et les deux parties sont prevenues.

Ce qui bloque pendant l'instruction : **le versement au vendeur**. Payer un
vendeur pendant qu'un litige porte sur sa livraison reviendrait a devoir lui
reprendre l'argent ensuite, ce qu'aucune plateforme ne sait faire proprement.
La `RepartitionVendeur` passe donc en `BLOQUE` a l'ouverture et n'en sort
qu'a la decision.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from coeur.evenements import Evenement, emettre
from coeur.services_externes import fournisseur_de_paiement
from commandes.models import Commande, StatutCommande
from comptes.permissions import EstAdmin
from paiements.models import Paiement, Remboursement, RepartitionVendeur, TypeRemboursement

from .models import Litige, MotifLitige, StatutLitige

# Le vendeur a deux jours pour donner sa version. Assez pour qu'un artisan qui
# ne consulte pas ses messages tous les jours ne soit pas condamne par defaut,
# assez court pour qu'un client ne reste pas un mois sans reponse.
DELAI_REPONSE_HEURES = 48

# Un litige ne s'ouvre que sur une commande dont l'histoire est finie : on ne
# conteste pas une livraison qui est encore en cours.
STATUTS_CONTESTABLES = [
    StatutCommande.LIVREE,
    StatutCommande.ECHEC_LIVRAISON,
]


def _refus(code, message, statut=status.HTTP_409_CONFLICT):
    return Response(
        {"erreur": {"code": code, "message": message, "details": {}}}, status=statut
    )


def _en_dictionnaire(dossier, pour=""):
    """La forme d'un litige, identique pour les trois roles.

    Une seule fonction plutot que trois : trois representations divergentes du
    meme objet finissent toujours par se contredire, et c'est l'ecran qui
    ment.
    """
    return {
        "id": dossier.id,
        "motif": dossier.motif,
        "libelle_motif": dossier.get_motif_display(),
        "description": dossier.description,
        "statut": dossier.statut,
        "libelle_statut": dossier.get_statut_display(),
        "resolution": dossier.resolution,
        "montant_rembourse_centimes": dossier.montant_rembourse_centimes,
        "date_ouverture": dossier.date_ouverture,
        "date_resolution": dossier.date_resolution,
        "reponse_vendeur": dossier.reponse_vendeur,
        "date_reponse_vendeur": dossier.date_reponse_vendeur,
        "date_limite_reponse": dossier.date_limite_reponse,
        "delai_expire": dossier.delai_expire,
        "arbitrable": dossier.arbitrable,
        "client": f"{dossier.client.utilisateur.prenom} "
                  f"{dossier.client.utilisateur.nom}".strip(),
        "commande": dossier.commande.numero_commande,
        "id_commande": dossier.commande_id,
        "montant_commande_centimes": dossier.commande.montant_total_centimes,
        "boutiques": [
            sous.vendeur.nom_boutique for sous in dossier.commande.sous_commandes.all()
        ],
        "pour": pour,
    }


def _vendeurs_concernes(commande):
    return [sous.vendeur for sous in commande.sous_commandes.select_related("vendeur__utilisateur")]


# ═══════════════════════════════════════════════════════════════════════════
#  1. Le client ouvre
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def ouvrir(requete, identifiant):
    """Ouvrir un litige sur une de ses commandes.

    Un seul litige ouvert par commande : deux dossiers concurrents sur la meme
    livraison donneraient deux decisions, et rien ne dirait laquelle compte.
    """
    profil = getattr(requete.user, "profil_client", None)
    commande = (
        Commande.objects.filter(pk=identifiant, client=profil)
        .prefetch_related("sous_commandes__vendeur__utilisateur")
        .first()
    )
    if commande is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if commande.statut_actuel not in STATUTS_CONTESTABLES:
        return _refus(
            "commande_non_contestable",
            "Un litige s'ouvre une fois la commande arrivee a son terme. "
            "Tant qu'elle est en cours, le suivi vous dit ou elle en est.",
        )

    if Litige.objects.filter(
        commande=commande, statut__in=[StatutLitige.OUVERT, StatutLitige.EN_COURS]
    ).exists():
        return _refus("litige_deja_ouvert", "Un litige est deja en cours sur cette commande.")

    motif = str(requete.data.get("motif", "")).strip()
    if motif not in MotifLitige.values:
        return _refus("motif_invalide", "Choisissez un motif dans la liste.",
                      status.HTTP_400_BAD_REQUEST)

    description = str(requete.data.get("description", "")).strip()
    if len(description) < 20:
        return _refus(
            "description_trop_courte",
            "Decrivez ce qui s'est passe en quelques phrases : c'est ce que le "
            "vendeur et l'administrateur liront pour trancher.",
            status.HTTP_400_BAD_REQUEST,
        )

    dossier = Litige.objects.create(
        commande=commande,
        client=profil,
        motif=motif,
        description=description,
        preuves_urls=str(requete.data.get("preuves", "")).strip(),
        statut=StatutLitige.OUVERT,
        date_limite_reponse=timezone.now() + timedelta(hours=DELAI_REPONSE_HEURES),
    )

    # Le versement au vendeur est gele le temps de l'instruction : le lui
    # verser puis le lui reprendre n'est pas une operation qui existe.
    RepartitionVendeur.objects.filter(sous_commande__commande=commande).update(statut="BLOQUE")

    emettre(Evenement(
        nom="LITIGE_OUVERT", type_objet="LITIGE", id_objet=dossier.id,
        titre=f"Litige ouvert sur la commande {commande.numero_commande}",
        message=f"{dossier.get_motif_display()}. Vous avez {DELAI_REPONSE_HEURES} heures "
                f"pour donner votre version.",
        lien="/espace/litiges",
        apres={"statut": dossier.statut, "motif": dossier.motif},
        destinataires=[vendeur.utilisateur for vendeur in _vendeurs_concernes(commande)],
    ))

    return Response({"data": _en_dictionnaire(dossier, pour="client")},
                    status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mes_litiges(requete):
    """Ses propres dossiers, ouverts d'abord."""
    profil = getattr(requete.user, "profil_client", None)
    if profil is None:
        return Response({"data": []})

    dossiers = (
        Litige.objects.filter(client=profil)
        .select_related("client__utilisateur", "commande")
        .prefetch_related("commande__sous_commandes__vendeur")
    )
    return Response({"data": [_en_dictionnaire(d, pour="client") for d in dossiers]})


# ═══════════════════════════════════════════════════════════════════════════
#  2. Le vendeur repond
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def litiges_du_vendeur(requete):
    """Les litiges qui portent sur ses commandes.

    Ouverts en premier, et ceux dont le delai court en tete : c'est le seul
    ordre utile pour quelqu'un qui a deux jours pour repondre.
    """
    vendeur = getattr(requete.user, "profil_vendeur", None)
    if vendeur is None:
        vendeur = getattr(getattr(requete.user, "profil_gestionnaire", None), "vendeur", None)
    if vendeur is None:
        return Response({"data": []})

    dossiers = (
        Litige.objects.filter(commande__sous_commandes__vendeur=vendeur)
        .select_related("client__utilisateur", "commande")
        .prefetch_related("commande__sous_commandes__vendeur")
        .distinct()
        .order_by("date_reponse_vendeur", "-date_ouverture")
    )
    return Response({"data": [_en_dictionnaire(d, pour="vendeur") for d in dossiers]})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def repondre(requete, identifiant):
    """Donner sa version des faits.

    Une seule reponse : ce n'est pas une messagerie. Un echange sans fin
    retarderait la decision, et c'est la decision que les deux parties
    attendent.
    """
    vendeur = getattr(requete.user, "profil_vendeur", None)
    if vendeur is None:
        return _refus("reserve_au_vendeur",
                      "Seul le proprietaire de la boutique repond a un litige.",
                      status.HTTP_403_FORBIDDEN)

    dossier = (
        Litige.objects.select_for_update()
        .filter(pk=identifiant, commande__sous_commandes__vendeur=vendeur)
        .select_related("client__utilisateur", "commande")
        .first()
    )
    if dossier is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if dossier.statut not in (StatutLitige.OUVERT, StatutLitige.EN_COURS):
        return _refus("litige_clos", "Ce dossier est deja tranche.")
    if dossier.date_reponse_vendeur:
        return _refus("deja_repondu", "Vous avez deja donne votre version de ce litige.")

    reponse = str(requete.data.get("reponse", "")).strip()
    if len(reponse) < 20:
        return _refus(
            "reponse_trop_courte",
            "Expliquez votre version en quelques phrases : une reponse vide "
            "revient a ne pas repondre.",
            status.HTTP_400_BAD_REQUEST,
        )

    dossier.reponse_vendeur = reponse
    dossier.date_reponse_vendeur = timezone.now()
    dossier.statut = StatutLitige.EN_COURS
    dossier.save(update_fields=["reponse_vendeur", "date_reponse_vendeur", "statut"])

    emettre(Evenement(
        nom="LITIGE_REPONSE_VENDEUR", type_objet="LITIGE", id_objet=dossier.id,
        titre=f"La boutique a repondu a votre litige n° {dossier.id}",
        message="Un administrateur va trancher avec les deux versions.",
        lien="/mes-commandes",
        apres={"statut": dossier.statut},
        destinataires=[dossier.client.utilisateur],
    ))

    return Response({"data": _en_dictionnaire(dossier, pour="vendeur")})


# ═══════════════════════════════════════════════════════════════════════════
#  3. L'administrateur arbitre
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["POST"])
@permission_classes([EstAdmin])
@transaction.atomic
def arbitrer(requete, identifiant):
    """Trancher : rembourser tout, une partie, ou refuser.

    Trois garde-fous, et chacun repare un abus reel :

      · **on ne tranche pas avant que le vendeur ait pu repondre**, sauf delai
        expire. Sinon la procedure contradictoire est un decor ;
      · **une decision est toujours motivee**, meme favorable au client. Une
        decision sans motif ne s'explique pas six mois plus tard ;
      · **on ne rembourse pas plus que ce qui a ete paye**, remboursements
        anterieurs compris.
    """
    dossier = (
        Litige.objects.select_for_update()
        .filter(pk=identifiant)
        .select_related("client__utilisateur", "commande")
        .prefetch_related("commande__sous_commandes__vendeur__utilisateur")
        .first()
    )
    if dossier is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if dossier.statut in (StatutLitige.RESOLU, StatutLitige.REJETE):
        return _refus("litige_clos", "Ce dossier a deja ete tranche.")
    if not dossier.arbitrable:
        return _refus(
            "vendeur_pas_encore_entendu",
            f"La boutique a jusqu'au {dossier.date_limite_reponse:%d/%m/%Y a %Hh%M} "
            f"pour donner sa version. Trancher avant reviendrait a lui refuser la parole.",
        )

    decision = str(requete.data.get("decision", "")).strip().upper()
    if decision not in ("REMBOURSER", "REFUSER"):
        return _refus("decision_invalide", "La decision est « rembourser » ou « refuser ».",
                      status.HTTP_400_BAD_REQUEST)

    motivation = str(requete.data.get("motivation", "")).strip()
    if len(motivation) < 10:
        return _refus(
            "motivation_requise",
            "Une decision se motive : les deux parties la liront, et elle doit "
            "s'expliquer six mois plus tard.",
            status.HTTP_400_BAD_REQUEST,
        )

    commande = dossier.commande
    paiement = Paiement.objects.filter(commande=commande).first()
    montant = 0

    if decision == "REMBOURSER":
        if paiement is None:
            return _refus("aucun_paiement",
                          "Cette commande n'a jamais ete payee : il n'y a rien a rembourser.")

        deja = sum(r.montant_centimes for r in paiement.remboursements.all())
        plafond = paiement.montant_centimes - deja
        demande = requete.data.get("montant_centimes")
        montant = plafond if demande in (None, "") else int(demande)

        if montant <= 0 or montant > plafond:
            return _refus(
                "montant_invalide",
                f"Le remboursement doit tenir entre 1 centime et {plafond} centimes "
                f"— c'est ce qui reste remboursable sur ce paiement.",
                status.HTTP_400_BAD_REQUEST,
            )

        reference = fournisseur_de_paiement().rembourser(paiement.reference_stripe, montant)
        Remboursement.objects.create(
            paiement=paiement,
            montant_centimes=montant,
            motif=motivation[:200],
            type=(TypeRemboursement.TOTAL if montant == paiement.montant_centimes
                  else TypeRemboursement.PARTIEL),
            declenche_par=requete.user,
            reference_stripe=str(reference),
        )
        # Un remboursement total renverse la vente : la commande le dit.
        if montant + deja >= paiement.montant_centimes:
            commande.statut_actuel = StatutCommande.REMBOURSEE
            commande.save(update_fields=["statut_actuel"])

    # Le versement au vendeur reprend son cours, dans un sens ou dans l'autre.
    RepartitionVendeur.objects.filter(sous_commande__commande=commande).update(
        statut="REMBOURSE" if decision == "REMBOURSER" else "TRANSFERE"
    )

    avant = dossier.statut
    dossier.statut = StatutLitige.RESOLU if decision == "REMBOURSER" else StatutLitige.REJETE
    dossier.resolution = motivation
    dossier.montant_rembourse_centimes = montant
    dossier.date_resolution = timezone.now()
    dossier.admin_traitant = getattr(requete.user, "profil_admin", None)
    dossier.save(update_fields=[
        "statut", "resolution", "montant_rembourse_centimes",
        "date_resolution", "admin_traitant",
    ])

    # Les deux parties sont prevenues de la MEME decision. N'en prevenir
    # qu'une seule est la facon la plus sure de creer un second litige.
    destinataires = [dossier.client.utilisateur]
    destinataires += [v.utilisateur for v in _vendeurs_concernes(commande)]
    emettre(Evenement(
        nom="LITIGE_TRANCHE", type_objet="LITIGE", id_objet=dossier.id,
        titre=f"Litige n° {dossier.id} : {dossier.get_statut_display().lower()}",
        message=(f"Remboursement de {montant / 100:.2f} EUR. {motivation}"
                 if montant else motivation),
        lien="/espace/litiges",
        avant={"statut": avant},
        apres={"statut": dossier.statut, "montant_rembourse_centimes": montant},
        destinataires=destinataires,
    ))

    return Response({"data": _en_dictionnaire(dossier, pour="admin")})
