"""Les pastilles de la barre laterale — L-3.

La barre laterale listait des noms d'ecrans, et rien de plus : il fallait
ouvrir chacun pour decouvrir qu'il y avait trois commandes a preparer.

Ce qui est verifie ici tient en trois phrases : **chaque role recoit ce qui le
concerne**, **un zero n'est pas envoye** — une pastille qui ne descend jamais a
zero cesse d'etre lue —, et **le personnel ne recoit pas ce qui appartient au
proprietaire de la boutique** (D-04).
"""
import pytest
from django.urls import reverse

from catalogue.models import Produit
from commandes.models import Commande, StatutCommande
from comptes.models import (
    Adresse,
    AdresseClient,
    Client,
    Gestionnaire,
    StatutCompte,
    StatutValidation,
    TypeService,
    Utilisateur,
    Vendeur,
)

MOT_DE_PASSE = "UnMotDePasseSolide!2026"
SESSION = "session-compteurs"


@pytest.fixture
def boutique(db):
    compte = Utilisateur.objects.create_user(
        email="karim@exemple.fr", password=MOT_DE_PASSE, nom="Karim", prenom="Test",
        role="VENDEUR", statut_compte=StatutCompte.ACTIF,
    )
    return Vendeur.objects.create(
        utilisateur=compte, nom_boutique="Chez Karim", type_activite=TypeService.EXPRESS,
        statut_validation=StatutValidation.VALIDE, taux_commission=0.15,
    )


@pytest.fixture
def produit(boutique):
    return Produit.objects.create(
        vendeur=boutique, nom="Ramen", prix_unitaire_centimes=1290,
        stock_disponible=20, seuil_alerte=5,
    )


@pytest.fixture
def lea(db):
    compte = Utilisateur.objects.create_user(
        email="lea@exemple.fr", password=MOT_DE_PASSE, nom="Martin", prenom="Lea",
        role="CLIENT", statut_compte=StatutCompte.ACTIF,
    )
    profil = Client.objects.create(utilisateur=compte)
    adresse = Adresse.objects.create(rue="8 rue Victor Hugo", ville="Lyon", code_postal="69002")
    AdresseClient.objects.create(client=profil, adresse=adresse, est_principale=True)
    return profil


def connecter(client, email):
    reponse = client.post(
        reverse("connexion"), {"email": email, "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json", headers={"X-Panier-Session": SESSION},
    )
    return {"Authorization": f"Bearer {reponse.json()['data']['acces']}"}


def compteurs(client, email):
    return client.get(reverse("mes-compteurs"), headers=connecter(client, email)).json()["data"]


def commander(client, produit, entetes):
    client.post(
        reverse("ajouter-ligne"), {"produit": produit.id, "quantite": 1},
        content_type="application/json", headers=entetes,
    )
    return client.post(reverse("creer-commandes"), {}, content_type="application/json",
                       headers=entetes)


@pytest.mark.django_db
def test_un_compte_sans_rien_en_attente_ne_recoit_aucune_pastille(client, lea):
    """Une pastille a zero n'est pas une pastille : on ne l'envoie pas."""
    assert compteurs(client, "lea@exemple.fr") == {}


@pytest.mark.django_db
def test_le_client_voit_ses_commandes_a_payer(client, lea, produit):
    """C'est la pastille la plus utile du projet : une commande impayee gele du stock."""
    entetes = connecter(client, "lea@exemple.fr")
    commander(client, produit, entetes)

    donnees = compteurs(client, "lea@exemple.fr")

    assert donnees["mes-commandes"] == 1
    assert donnees["paiement"] == 1


@pytest.mark.django_db
def test_la_pastille_descend_quand_le_travail_est_fait(client, lea, produit):
    """Une pastille qui ne descend jamais cesse d'etre lue au bout de deux jours."""
    entetes = connecter(client, "lea@exemple.fr")
    reponse = commander(client, produit, entetes)
    commande = Commande.objects.get(pk=reponse.json()["data"][0]["id"])

    intention = client.post(reverse("ouvrir-intention", args=[commande.id]), {},
                            content_type="application/json", headers=entetes)
    client.post(reverse("confirmer-paiement"),
                {"reference": intention.json()["data"]["reference"]},
                content_type="application/json")

    assert "mes-commandes" not in compteurs(client, "lea@exemple.fr")


@pytest.mark.django_db
def test_le_vendeur_voit_ce_qu_il_doit_preparer(client, lea, produit, boutique):
    entetes = connecter(client, "lea@exemple.fr")
    reponse = commander(client, produit, entetes)
    commande = Commande.objects.get(pk=reponse.json()["data"][0]["id"])
    intention = client.post(reverse("ouvrir-intention", args=[commande.id]), {},
                            content_type="application/json", headers=entetes)
    client.post(reverse("confirmer-paiement"),
                {"reference": intention.json()["data"]["reference"]},
                content_type="application/json")

    assert compteurs(client, "karim@exemple.fr")["vendeur-commandes"] == 1


@pytest.mark.django_db
def test_le_vendeur_est_alerte_sur_son_stock_bas(client, produit):
    """Il doit reapprovisionner AVANT de perdre une vente, pas apres."""
    Produit.objects.filter(pk=produit.id).update(stock_disponible=2, seuil_alerte=5)

    assert compteurs(client, "karim@exemple.fr")["vendeur-catalogue"] == 1


@pytest.mark.django_db
def test_le_personnel_ne_recoit_pas_les_litiges_de_la_boutique(client, produit, boutique):
    """Un litige se repond par le proprietaire, pas par l'employe (D-04)."""
    compte = Utilisateur.objects.create_user(
        email="nadia@exemple.fr", password=MOT_DE_PASSE, nom="Nadia", prenom="Test",
        role="GESTIONNAIRE", statut_compte=StatutCompte.ACTIF,
    )
    Gestionnaire.objects.create(
        utilisateur=compte, vendeur=boutique, type_gestionnaire="STAFF_VENDEUR"
    )
    Produit.objects.filter(pk=produit.id).update(stock_disponible=2, seuil_alerte=5)

    donnees = compteurs(client, "nadia@exemple.fr")

    # Le stock, oui : c'est son travail.
    assert donnees["vendeur-catalogue"] == 1
    assert "vendeur-litiges" not in donnees


@pytest.mark.django_db
def test_un_visiteur_ne_peut_pas_demander_de_compteurs(client):
    assert client.get(reverse("mes-compteurs")).status_code == 401


@pytest.mark.django_db
def test_le_vendeur_ne_voit_pas_les_commandes_d_une_autre_boutique(client, lea, produit):
    """Chaque pastille est cloisonnee comme l'ecran qu'elle annonce."""
    entetes = connecter(client, "lea@exemple.fr")
    reponse = commander(client, produit, entetes)
    commande = Commande.objects.get(pk=reponse.json()["data"][0]["id"])
    intention = client.post(reverse("ouvrir-intention", args=[commande.id]), {},
                            content_type="application/json", headers=entetes)
    client.post(reverse("confirmer-paiement"),
                {"reference": intention.json()["data"]["reference"]},
                content_type="application/json")

    autre = Utilisateur.objects.create_user(
        email="amel@exemple.fr", password=MOT_DE_PASSE, nom="Amel", prenom="Test",
        role="VENDEUR", statut_compte=StatutCompte.ACTIF,
    )
    Vendeur.objects.create(
        utilisateur=autre, nom_boutique="Chez Amel", type_activite=TypeService.EXPRESS,
        statut_validation=StatutValidation.VALIDE,
    )

    assert "vendeur-commandes" not in compteurs(client, "amel@exemple.fr")


@pytest.mark.django_db
def test_l_admin_voit_les_dossiers_a_valider(client):
    from comptes.models import Administrateur

    compte = Utilisateur.objects.create_user(
        email="fatou@exemple.fr", password=MOT_DE_PASSE, nom="Diallo", prenom="Fatou",
        role="ADMIN", statut_compte=StatutCompte.ACTIF,
    )
    Administrateur.objects.create(utilisateur=compte)

    candidat = Utilisateur.objects.create_user(
        email="camille@exemple.fr", password=MOT_DE_PASSE, nom="Roux", prenom="Camille",
        role="VENDEUR", statut_compte=StatutCompte.EN_ATTENTE,
    )
    Vendeur.objects.create(
        utilisateur=candidat, nom_boutique="L Atelier Camille",
        type_activite=TypeService.STANDARD, statut_validation=StatutValidation.EN_ATTENTE,
    )

    assert compteurs(client, "fatou@exemple.fr")["admin-validations"] == 1


@pytest.mark.django_db
def test_l_admin_ne_compte_que_les_litiges_qu_il_a_le_droit_de_trancher(client, lea, produit):
    """Compter un dossier ou le vendeur a encore la parole afficherait un
    travail que l'administrateur n'a pas le droit de faire (D-103)."""
    from comptes.models import Administrateur

    compte = Utilisateur.objects.create_user(
        email="fatou@exemple.fr", password=MOT_DE_PASSE, nom="Diallo", prenom="Fatou",
        role="ADMIN", statut_compte=StatutCompte.ACTIF,
    )
    Administrateur.objects.create(utilisateur=compte)

    entetes = connecter(client, "lea@exemple.fr")
    reponse = commander(client, produit, entetes)
    commande = Commande.objects.get(pk=reponse.json()["data"][0]["id"])
    intention = client.post(reverse("ouvrir-intention", args=[commande.id]), {},
                            content_type="application/json", headers=entetes)
    client.post(reverse("confirmer-paiement"),
                {"reference": intention.json()["data"]["reference"]},
                content_type="application/json")
    Commande.objects.filter(pk=commande.id).update(statut_actuel=StatutCommande.LIVREE)

    client.post(
        reverse("ouvrir-litige", args=[commande.id]),
        {"motif": "INCOMPLET", "description": "Il manquait un article a l arrivee."},
        content_type="application/json", headers=entetes,
    )

    # Le delai court encore : rien a arbitrer.
    assert "admin-litiges" not in compteurs(client, "fatou@exemple.fr")

    client.post(
        reverse("repondre-litige", args=[1]),
        {"reponse": "Le colis est parti complet, photo a l appui."},
        content_type="application/json", headers=connecter(client, "karim@exemple.fr"),
    )

    assert compteurs(client, "fatou@exemple.fr")["admin-litiges"] == 1
