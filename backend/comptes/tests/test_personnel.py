"""Le personnel d'une boutique — D-04, D-93.

Le vendeur creait des comptes pour ses employes, mais il n'avait aucun moyen
d'en retirer un. Un employe qui partait gardait donc son acces aux commandes et
au stock de la boutique, indefiniment. C'est le genre de trou qu'on ne remarque
que le jour ou il coute cher.

Ce qui est verifie ici : **suspendre bloque vraiment l'entree**, **on suspend
sans jamais supprimer**, et **un vendeur ne touche qu'a son propre personnel**.
"""
import pytest
from django.urls import reverse

from comptes.models import (
    Gestionnaire,
    StatutCompte,
    StatutValidation,
    TypeService,
    Utilisateur,
    Vendeur,
)
from engagement.models import JournalAudit, Notification

MOT_DE_PASSE = "UnMotDePasseSolide!2026"


def creer_vendeur(nom, email):
    compte = Utilisateur.objects.create_user(
        email=email, password=MOT_DE_PASSE, nom=nom, prenom="Test",
        role="VENDEUR", statut_compte=StatutCompte.ACTIF,
    )
    return Vendeur.objects.create(
        utilisateur=compte, nom_boutique=nom, type_activite=TypeService.EXPRESS,
        statut_validation=StatutValidation.VALIDE,
    )


@pytest.fixture
def karim(db):
    return creer_vendeur("Chez Karim", "karim@exemple.fr")


@pytest.fixture
def employe(karim):
    compte = Utilisateur.objects.create_user(
        email="rachid@exemple.fr", password=MOT_DE_PASSE, nom="Rachid", prenom="Test",
        role="GESTIONNAIRE", statut_compte=StatutCompte.ACTIF,
    )
    return Gestionnaire.objects.create(
        utilisateur=compte, vendeur=karim, type_gestionnaire="STAFF_VENDEUR"
    )


def connecter(client, email):
    reponse = client.post(
        reverse("connexion"), {"email": email, "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json",
    )
    return reponse


def entetes(client, email):
    return {"Authorization": f"Bearer {connecter(client, email).json()['data']['acces']}"}


def basculer(client, employe, email="karim@exemple.fr", motif="Fin de contrat."):
    return client.post(
        reverse("basculer-employe", args=[employe.id]), {"motif": motif},
        content_type="application/json", headers=entetes(client, email),
    )


@pytest.mark.django_db
def test_la_liste_dit_qui_peut_encore_entrer(client, karim, employe):
    """Sans ce champ, un compte suspendu ressemblait a un compte actif."""
    reponse = client.get(reverse("mon-personnel"), headers=entetes(client, "karim@exemple.fr"))

    membre = reponse.json()["data"]["personnel"][0]
    assert membre["actif"] is True
    assert membre["statut_compte"] == StatutCompte.ACTIF


@pytest.mark.django_db
def test_suspendre_un_employe_lui_ferme_vraiment_la_porte(client, karim, employe):
    """Masquer un menu ne suffit pas : c'est la connexion qui doit echouer."""
    assert basculer(client, employe).status_code == 200

    employe.utilisateur.refresh_from_db()
    assert employe.utilisateur.statut_compte == StatutCompte.SUSPENDU

    refus = connecter(client, "rachid@exemple.fr")
    assert refus.status_code == 403
    assert refus.json()["erreur"]["code"] == "compte_bloque"


@pytest.mark.django_db
def test_on_suspend_sans_jamais_supprimer(client, karim, employe):
    """Les ajustements de stock qu'il a signes doivent rester attribuables (D-13, D-95)."""
    basculer(client, employe)

    assert Gestionnaire.objects.filter(pk=employe.pk).exists()
    assert Utilisateur.objects.filter(pk=employe.utilisateur_id).exists()


@pytest.mark.django_db
def test_reactiver_lui_rend_son_acces(client, karim, employe):
    basculer(client, employe)

    reponse = basculer(client, employe, motif="")

    assert reponse.json()["data"]["actif"] is True
    assert connecter(client, "rachid@exemple.fr").status_code == 200


@pytest.mark.django_db
def test_suspendre_exige_un_motif(client, karim, employe):
    """La personne le lira, et le journal le gardera."""
    reponse = basculer(client, employe, motif="")

    assert reponse.status_code == 400
    assert reponse.json()["erreur"]["code"] == "motif_requis"
    employe.utilisateur.refresh_from_db()
    assert employe.utilisateur.statut_compte == StatutCompte.ACTIF


@pytest.mark.django_db
def test_l_employe_est_prevenu_et_le_journal_garde_la_trace(client, karim, employe):
    """Une decision subie sans explication est une decision qu'on ne peut pas corriger."""
    basculer(client, employe, motif="Fin de contrat au 31 aout.")

    notification = Notification.objects.get(utilisateur=employe.utilisateur)
    assert "Fin de contrat" in notification.contenu

    entree = JournalAudit.objects.filter(action="EMPLOYE_SUSPENDU").first()
    assert entree is not None
    assert entree.donnees_avant["statut_compte"] == StatutCompte.ACTIF
    assert entree.donnees_apres["statut_compte"] == StatutCompte.SUSPENDU


@pytest.mark.django_db
def test_un_vendeur_ne_touche_pas_au_personnel_d_une_autre_boutique(client, karim, employe):
    """404 et non 403 : un 403 confirmerait que ce compte existe."""
    creer_vendeur("Chez Amel", "amel@exemple.fr")

    reponse = basculer(client, employe, email="amel@exemple.fr")

    assert reponse.status_code == 404
    employe.utilisateur.refresh_from_db()
    assert employe.utilisateur.statut_compte == StatutCompte.ACTIF


@pytest.mark.django_db
def test_un_employe_ne_suspend_pas_ses_collegues(client, karim, employe):
    """Le droit de gerer le personnel appartient au proprietaire de la boutique (D-04)."""
    reponse = client.post(
        reverse("basculer-employe", args=[employe.id]), {"motif": "Tentative."},
        content_type="application/json", headers=entetes(client, "rachid@exemple.fr"),
    )

    assert reponse.status_code == 403
