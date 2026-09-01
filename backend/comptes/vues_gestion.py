"""La gestion cote administration — D-93.

**Ta remarque, L-7** : *« boutiques et livreurs : tu n'as pensé qu'à la
consultation »*. Verifie : aucune route ne permettait de suspendre une
boutique, d'en refuser une avec motif, ni de rattacher un livreur a un
entrepot. L'administration lisait, elle n'administrait pas.

Chaque action ici :

  · **se propage** — elle emet un evenement, qui ecrit le journal d'audit et
    previent la personne concernee (D-62) ;
  · **s'explique** — un refus ou une suspension exige un motif, sans quoi la
    personne recoit une decision sans savoir quoi corriger ;
  · **se rejoue en sens inverse** — on suspend, on ne supprime jamais (D-61).
"""
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from coeur.evenements import Evenement, emettre

from .models import (
    Gestionnaire,
    Livreur,
    StatutCompte,
    StatutValidation,
    Utilisateur,
    Vendeur,
)
from .permissions import EstAdmin, EstVendeur


def _motif(requete):
    return str(requete.data.get("motif", "")).strip()


def _exige_un_motif():
    return Response(
        {"erreur": {"code": "motif_obligatoire",
                    "message": "Une decision qui touche un compte s'explique.",
                    "details": {}}},
        status=status.HTTP_400_BAD_REQUEST,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Les boutiques
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["POST"])
@permission_classes([EstAdmin])
def decider_vendeur(requete, identifiant):
    """Valider, refuser, suspendre ou reactiver une boutique.

    Une seule route pour quatre decisions : elles partagent leurs effets de
    bord — trace, notification, statut du compte — et les separer aurait
    duplique trois fois la meme chose.
    """
    boutique = (
        Vendeur.objects.select_related("utilisateur").filter(pk=identifiant).first()
    )
    if boutique is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    decision = requete.data.get("decision")
    motif = _motif(requete)
    avant = {
        "statut_validation": boutique.statut_validation,
        "statut_compte": boutique.utilisateur.statut_compte,
    }

    if decision == "valider":
        boutique.statut_validation = StatutValidation.VALIDE
        boutique.utilisateur.statut_compte = StatutCompte.ACTIF
        titre = "Votre boutique est validee"
        message = (f"« {boutique.nom_boutique} » est en ligne : vos produits sont "
                   f"desormais visibles au catalogue.")

    elif decision == "refuser":
        if not motif:
            return _exige_un_motif()
        boutique.statut_validation = StatutValidation.REJETE
        boutique.utilisateur.statut_compte = StatutCompte.EN_ATTENTE
        titre = "Votre dossier n'a pas ete retenu"
        message = f"Motif : {motif}. Vous pouvez corriger et redeposer votre dossier."

    elif decision == "suspendre":
        if not motif:
            return _exige_un_motif()
        boutique.statut_validation = StatutValidation.SUSPENDU
        boutique.utilisateur.statut_compte = StatutCompte.SUSPENDU
        titre = "Votre boutique est suspendue"
        message = (f"Motif : {motif}. Vos produits ne sont plus visibles ; vos commandes "
                   f"en cours restent a honorer.")

    elif decision == "reactiver":
        boutique.statut_validation = StatutValidation.VALIDE
        boutique.utilisateur.statut_compte = StatutCompte.ACTIF
        titre = "Votre boutique est reactivee"
        message = "Vos produits sont de nouveau visibles au catalogue."

    elif decision == "revalider":
        # Utilise quand le SIRET ou le type d'activite change (D-84) : la
        # boutique repasse en examen sans que ses produits disparaissent.
        boutique.statut_validation = StatutValidation.EN_ATTENTE
        titre = "Votre dossier repasse en verification"
        message = (motif or "Une information administrative a change et doit etre "
                            "reverifiee. Votre boutique reste en ligne pendant l'examen.")

    else:
        return Response(
            {"erreur": {"code": "decision_inconnue",
                        "message": "Decision attendue : valider, refuser, suspendre, "
                                   "reactiver ou revalider.",
                        "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    boutique.save(update_fields=["statut_validation"])
    boutique.utilisateur.save(update_fields=["statut_compte"])

    emettre(Evenement(
        nom=f"BOUTIQUE_{decision.upper()}",
        acteur=requete.user,
        type_objet="VENDEUR",
        id_objet=boutique.id,
        titre=titre,
        message=message,
        lien="/espace",
        motif=motif,
        avant=avant,
        apres={"statut_validation": boutique.statut_validation,
               "statut_compte": boutique.utilisateur.statut_compte},
        destinataires=[boutique.utilisateur],
    ))

    return Response({"data": {
        "id": boutique.id,
        "nom_boutique": boutique.nom_boutique,
        "statut_validation": boutique.statut_validation,
        "statut_compte": boutique.utilisateur.statut_compte,
    }})


# ═══════════════════════════════════════════════════════════════════════════
#  Les livreurs
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["POST"])
@permission_classes([EstAdmin])
def decider_livreur(requete, identifiant):
    """Valider, refuser, suspendre, reactiver — et rattacher a un entrepot.

    Le rattachement est ici et non dans un ecran a part : un livreur Standard
    sans entrepot ne recevra jamais de tournee, ce qui en fait un compte
    valide mais inutilisable — le genre de trou qu'on ne voit qu'en
    production.
    """
    from livraisons.models import Entrepot

    livreur = Livreur.objects.select_related("utilisateur").filter(pk=identifiant).first()
    if livreur is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    decision = requete.data.get("decision")
    motif = _motif(requete)
    avant = {
        "statut_validation": livreur.statut_validation,
        "statut_compte": livreur.utilisateur.statut_compte,
        "entrepot": livreur.entrepot_id,
    }

    if decision == "valider":
        livreur.statut_validation = StatutValidation.VALIDE
        livreur.utilisateur.statut_compte = StatutCompte.ACTIF
        titre = "Votre compte livreur est valide"
        message = "Vous pouvez accepter des courses depuis l'application mobile."

    elif decision == "refuser":
        if not motif:
            return _exige_un_motif()
        livreur.statut_validation = StatutValidation.REJETE
        livreur.utilisateur.statut_compte = StatutCompte.EN_ATTENTE
        titre = "Votre candidature n'a pas ete retenue"
        message = f"Motif : {motif}."

    elif decision == "suspendre":
        if not motif:
            return _exige_un_motif()
        livreur.statut_validation = StatutValidation.SUSPENDU
        livreur.utilisateur.statut_compte = StatutCompte.SUSPENDU
        titre = "Votre compte livreur est suspendu"
        message = f"Motif : {motif}."

    elif decision == "reactiver":
        livreur.statut_validation = StatutValidation.VALIDE
        livreur.utilisateur.statut_compte = StatutCompte.ACTIF
        titre = "Votre compte livreur est reactive"
        message = "Vous pouvez de nouveau accepter des courses."

    elif decision == "rattacher":
        entrepot = Entrepot.objects.filter(pk=requete.data.get("id_entrepot")).first()
        if entrepot is None:
            return Response(
                {"erreur": {"code": "entrepot_inconnu",
                            "message": "Cet entrepot n'existe pas.", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        livreur.entrepot = entrepot
        livreur.save(update_fields=["entrepot"])
        titre = "Vous etes rattache a un entrepot"
        message = f"Vos tournees partiront de « {entrepot.nom} »."
        emettre(Evenement(
            nom="LIVREUR_RATTACHE", acteur=requete.user, type_objet="LIVREUR",
            id_objet=livreur.id, titre=titre, message=message, lien="/espace/courses",
            avant=avant, apres={"entrepot": entrepot.id},
            destinataires=[livreur.utilisateur],
        ))
        return Response({"data": _resume_livreur(livreur)})

    else:
        return Response(
            {"erreur": {"code": "decision_inconnue",
                        "message": "Decision attendue : valider, refuser, suspendre, "
                                   "reactiver ou rattacher.",
                        "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    livreur.save(update_fields=["statut_validation"])
    livreur.utilisateur.save(update_fields=["statut_compte"])

    emettre(Evenement(
        nom=f"LIVREUR_{decision.upper()}",
        acteur=requete.user,
        type_objet="LIVREUR",
        id_objet=livreur.id,
        titre=titre,
        message=message,
        lien="/espace",
        motif=motif,
        avant=avant,
        apres={"statut_validation": livreur.statut_validation,
               "statut_compte": livreur.utilisateur.statut_compte},
        destinataires=[livreur.utilisateur],
    ))

    return Response({"data": _resume_livreur(livreur)})


def _resume_livreur(livreur):
    return {
        "id": livreur.id,
        "nom": f"{livreur.utilisateur.prenom} {livreur.utilisateur.nom}".strip(),
        "statut_validation": livreur.statut_validation,
        "statut_compte": livreur.utilisateur.statut_compte,
        "entrepot": livreur.entrepot.nom if livreur.entrepot_id else "",
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Les comptes
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["POST"])
@permission_classes([EstAdmin])
def basculer_compte(requete, identifiant):
    """Suspendre ou reactiver un compte, avec motif et notification.

    Remplace l'ancienne bascule muette : elle changeait un statut sans rien
    dire a personne, et la personne suspendue decouvrait son sort en voyant
    ses ecrans se vider.
    """
    compte = Utilisateur.objects.filter(pk=identifiant).first()
    if compte is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if compte.role == "ADMIN":
        return Response(
            {"erreur": {"code": "non_autorise",
                        "message": "Un administrateur ne se suspend pas depuis cet ecran.",
                        "details": {}}},
            status=status.HTTP_403_FORBIDDEN,
        )

    suspendre = compte.statut_compte != StatutCompte.SUSPENDU
    motif = _motif(requete)
    if suspendre and not motif:
        return _exige_un_motif()

    avant = {"statut_compte": compte.statut_compte}
    compte.statut_compte = StatutCompte.SUSPENDU if suspendre else StatutCompte.ACTIF
    compte.save(update_fields=["statut_compte"])

    emettre(Evenement(
        nom="COMPTE_SUSPENDU" if suspendre else "COMPTE_REACTIVE",
        acteur=requete.user,
        type_objet="UTILISATEUR",
        id_objet=compte.id,
        titre="Votre compte est suspendu" if suspendre else "Votre compte est reactive",
        message=(f"Motif : {motif}." if suspendre
                 else "Vous retrouvez l'acces a votre espace."),
        lien="/",
        motif=motif,
        avant=avant,
        apres={"statut_compte": compte.statut_compte},
        destinataires=[compte],
    ))

    return Response({"data": {
        "id": compte.id,
        "statut_compte": compte.statut_compte,
        "date_decision": timezone.now(),
    }})


@api_view(["POST"])
@permission_classes([EstVendeur])
@transaction.atomic
def basculer_employe(requete, identifiant):
    """Suspendre ou reactiver un compte de son propre personnel — D-04.

    Le vendeur cree deja des comptes pour ses employes, mais il n'avait aucun
    moyen d'en retirer un. Un employe qui part gardait donc son acces aux
    commandes et au stock de la boutique, indefiniment. C'est le genre de trou
    qu'on ne remarque que le jour ou il coute cher.

    **Suspendre plutot que supprimer** : les ajustements de stock qu'il a
    signes doivent rester attribuables (D-13, D-95). Un compte efface
    laisserait un journal d'audit plein de trous.
    """
    vendeur = getattr(requete.user, "profil_vendeur", None)
    employe = (
        Gestionnaire.objects.filter(pk=identifiant, vendeur=vendeur)
        .select_related("utilisateur")
        .first()
    )
    if employe is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    compte = employe.utilisateur
    avant = compte.statut_compte
    suspendre = avant == StatutCompte.ACTIF

    if suspendre and not str(requete.data.get("motif", "")).strip():
        return Response(
            {"erreur": {
                "code": "motif_requis",
                "message": "Dites pourquoi ce compte est suspendu : la personne le lira, "
                           "et le journal le gardera.",
                "details": {},
            }},
            status=status.HTTP_400_BAD_REQUEST,
        )

    compte.statut_compte = StatutCompte.SUSPENDU if suspendre else StatutCompte.ACTIF
    compte.save(update_fields=["statut_compte"])

    motif = str(requete.data.get("motif", "")).strip()
    emettre(Evenement(
        nom="EMPLOYE_SUSPENDU" if suspendre else "EMPLOYE_REACTIVE",
        type_objet="UTILISATEUR", id_objet=compte.id,
        titre=("Votre acces a la boutique est suspendu" if suspendre
               else "Votre acces a la boutique est retabli"),
        message=motif or "Vous pouvez de nouveau preparer les commandes et ajuster le stock.",
        lien="/espace",
        avant={"statut_compte": avant},
        apres={"statut_compte": compte.statut_compte},
        motif=motif,
        acteur=requete.user,
        destinataires=[compte],
    ))

    return Response({"data": {
        "id": employe.id,
        "statut_compte": compte.statut_compte,
        "actif": compte.statut_compte == StatutCompte.ACTIF,
    }})
