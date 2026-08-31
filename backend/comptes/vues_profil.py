"""Le profil et les parametres — deux ecrans distincts (D-76).

Le modele est celui du projet banque, et il tient en une phrase : **l'identite
ne se change pas seul**. Nom, prenom et date de naissance sont geles ; les
corriger passe par une demande motivee qu'un administrateur arbitre (D-77).
Les coordonnees — courriel, telephone — se modifient directement.

Pourquoi c'est juste ici aussi : sur une place de marche, l'identite engage.
Un vendeur valide sur un nom ne doit pas pouvoir en changer seul apres coup.
"""
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    ChampDemande,
    ChampSensible,
    DemandeModification,
    Preferences,
    StatutDemande,
)
from .permissions import EstAdmin

# Ce qu'on peut corriger soi-meme, et rien d'autre. La liste est ici et non
# dans un serializer : c'est une regle metier, pas une contrainte de format.
CHAMPS_LIBRES = ("email", "telephone")

# Le nom de l'attribut derriere chaque champ sensible.
ATTRIBUTS = {
    ChampSensible.NOM: "nom",
    ChampSensible.PRENOM: "prenom",
    ChampSensible.DATE_NAISSANCE: "date_naissance",
}


def _serialiser_demande(demande):
    return {
        "id": demande.id,
        "statut": demande.statut,
        "libelle_statut": demande.get_statut_display(),
        "motif": demande.motif,
        "commentaire_decision": demande.commentaire_decision,
        "date_demande": demande.date_demande,
        "date_decision": demande.date_decision,
        "demandeur": {
            "id": demande.utilisateur_id,
            "nom": f"{demande.utilisateur.prenom} {demande.utilisateur.nom}".strip(),
            "email": demande.utilisateur.email,
            "role": demande.utilisateur.role,
        },
        "champs": [
            {
                "champ": champ.champ,
                "libelle": champ.get_champ_display(),
                "valeur_actuelle": champ.valeur_actuelle,
                "valeur_demandee": champ.valeur_demandee,
            }
            for champ in demande.champs.all()
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Le profil
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def mon_profil(requete):
    """Ce que je suis, et ce que je peux corriger seul."""
    utilisateur = requete.user

    if requete.method == "PATCH":
        # Un champ gele envoye ici est refuse explicitement plutot qu'ignore
        # en silence : sans message, on croit que la modification a marche.
        geles = [
            champ for champ in ("nom", "prenom", "date_naissance")
            if champ in requete.data
        ]
        if geles:
            return Response(
                {"erreur": {
                    "code": "champ_gele",
                    "message": "Votre identite ne se modifie que par une demande validee.",
                    "details": {champ: ["Champ gele."] for champ in geles},
                }},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for champ in CHAMPS_LIBRES:
            if champ in requete.data:
                setattr(utilisateur, champ, str(requete.data[champ]).strip())
        try:
            utilisateur.full_clean(exclude=["password"])
        except ValidationError as refus:
            return Response(
                {"erreur": {"code": "validation", "message": "Informations invalides.",
                            "details": refus.message_dict}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        utilisateur.save(update_fields=list(CHAMPS_LIBRES))

    demandes = utilisateur.demandes_modification.prefetch_related("champs")
    return Response({"data": {
        "identite": {
            "nom": utilisateur.nom,
            "prenom": utilisateur.prenom,
            "role": utilisateur.role,
            "libelle_role": utilisateur.get_role_display(),
            "statut_compte": utilisateur.statut_compte,
            "date_inscription": utilisateur.date_inscription,
        },
        "coordonnees": {
            "email": utilisateur.email,
            "telephone": utilisateur.telephone,
        },
        # L'ecran n'a rien a deviner : le serveur dit ce qui est gele.
        "champs_geles": [
            {"champ": valeur, "libelle": libelle}
            for valeur, libelle in ChampSensible.choices
        ],
        "demandes": [_serialiser_demande(demande) for demande in demandes],
        "demandes_en_attente": demandes.filter(statut=StatutDemande.EN_ATTENTE).count(),
    }})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def demander_modification(requete):
    """Demander la correction d'un champ d'identite.

    Le motif est obligatoire : sans lui, l'administrateur arbitrerait a
    l'aveugle, ce qui revient a tout accepter.
    """
    champs = requete.data.get("champs") or {}
    motif = str(requete.data.get("motif", "")).strip()

    demandes = {
        cle: str(valeur).strip()
        for cle, valeur in champs.items()
        if cle in ChampSensible.values and str(valeur).strip()
    }
    if not demandes:
        return Response(
            {"erreur": {"code": "aucun_champ",
                        "message": "Indiquez au moins un champ a corriger.", "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not motif:
        return Response(
            {"erreur": {"code": "motif_obligatoire",
                        "message": "Expliquez pourquoi cette correction est necessaire.",
                        "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if requete.user.demandes_modification.filter(statut=StatutDemande.EN_ATTENTE).exists():
        return Response(
            {"erreur": {"code": "demande_en_cours",
                        "message": "Une demande est deja en attente de decision.",
                        "details": {}}},
            status=status.HTTP_409_CONFLICT,
        )

    demande = DemandeModification.objects.create(utilisateur=requete.user, motif=motif)
    for champ, valeur in demandes.items():
        ChampDemande.objects.create(
            demande=demande,
            champ=champ,
            valeur_actuelle=str(getattr(requete.user, ATTRIBUTS[champ], "") or ""),
            valeur_demandee=valeur,
        )

    return Response({"data": _serialiser_demande(demande)}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def changer_mot_de_passe(requete):
    """Changer son mot de passe, en prouvant qu'on connait l'ancien.

    Demander l'ancien n'est pas une formalite : sans lui, une session laissee
    ouverte suffirait a prendre le compte definitivement.
    """
    ancien = str(requete.data.get("ancien", ""))
    nouveau = str(requete.data.get("nouveau", ""))

    if not requete.user.check_password(ancien):
        return Response(
            {"erreur": {"code": "mot_de_passe_incorrect",
                        "message": "Votre mot de passe actuel est incorrect.", "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        validate_password(nouveau, requete.user)
    except ValidationError as refus:
        return Response(
            {"erreur": {"code": "mot_de_passe_faible",
                        "message": " ".join(refus.messages), "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    requete.user.set_password(nouveau)
    requete.user.save(update_fields=["password"])
    update_session_auth_hash(requete, requete.user)
    return Response({"data": {"change": True}})


# ═══════════════════════════════════════════════════════════════════════════
#  Les parametres
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def mes_parametres(requete):
    preferences, _ = Preferences.objects.get_or_create(utilisateur=requete.user)

    if requete.method == "PATCH":
        booleens = (
            "notifications_email", "notifications_push",
            "courriels_promotionnels", "masquer_montants",
        )
        for champ in booleens:
            if champ in requete.data:
                setattr(preferences, champ, bool(requete.data[champ]))
        if requete.data.get("densite") in ("COMPACTE", "NORMALE"):
            preferences.densite = requete.data["densite"]
        preferences.save()

    return Response({"data": {
        "notifications_email": preferences.notifications_email,
        "notifications_push": preferences.notifications_push,
        "courriels_promotionnels": preferences.courriels_promotionnels,
        "densite": preferences.densite,
        "masquer_montants": preferences.masquer_montants,
        # Le canal dans l'application ne se coupe pas : une information
        # critique n'a jamais un canal unique (scenario 12.1).
        "canal_in_app_toujours_actif": True,
    }})


# ═══════════════════════════════════════════════════════════════════════════
#  L'arbitrage, cote administrateur
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["GET"])
@permission_classes([EstAdmin])
def demandes_a_arbitrer(requete):
    demandes = (
        DemandeModification.objects.select_related("utilisateur")
        .prefetch_related("champs")
        .order_by("statut", "-date_demande")
    )
    return Response({"data": {
        "demandes": [_serialiser_demande(demande) for demande in demandes[:100]],
        "en_attente": demandes.filter(statut=StatutDemande.EN_ATTENTE).count(),
    }})


@api_view(["POST"])
@permission_classes([EstAdmin])
def arbitrer_demande(requete, identifiant):
    """Accepter ou refuser une demande. Accepter APPLIQUE la correction.

    Une acceptation qui n'appliquerait pas la modification obligerait
    l'administrateur a la recopier a la main — et il finirait par se tromper.
    """
    demande = (
        DemandeModification.objects.filter(pk=identifiant)
        .prefetch_related("champs")
        .select_related("utilisateur")
        .first()
    )
    if demande is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if demande.statut != StatutDemande.EN_ATTENTE:
        return Response(
            {"erreur": {"code": "deja_arbitree",
                        "message": "Cette demande a deja ete tranchee.", "details": {}}},
            status=status.HTTP_409_CONFLICT,
        )

    accepter = bool(requete.data.get("accepter"))
    commentaire = str(requete.data.get("commentaire", "")).strip()
    if not accepter and not commentaire:
        return Response(
            {"erreur": {"code": "motif_obligatoire",
                        "message": "Un refus s'explique.", "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if accepter:
        utilisateur = demande.utilisateur
        modifies = []
        for champ in demande.champs.all():
            attribut = ATTRIBUTS.get(champ.champ)
            if attribut and hasattr(utilisateur, attribut):
                setattr(utilisateur, attribut, champ.valeur_demandee)
                modifies.append(attribut)
        if modifies:
            utilisateur.save(update_fields=modifies)

    demande.statut = StatutDemande.ACCEPTEE if accepter else StatutDemande.REFUSEE
    demande.commentaire_decision = commentaire
    demande.decide_par = requete.user
    demande.date_decision = timezone.now()
    demande.save(update_fields=["statut", "commentaire_decision", "decide_par", "date_decision"])

    return Response({"data": _serialiser_demande(demande)})
