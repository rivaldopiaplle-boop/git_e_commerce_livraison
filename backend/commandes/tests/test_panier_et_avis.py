"""Le parcours d'achat, et l'avis qui le clot — defauts trouves au bloc K.

Deux defauts reproduits de bout en bout avant d'etre corriges :

  · **« le bouton passer la commande ne fonctionne pas »**. La cause n'etait
    pas le bouton : une SEULE ligne devenue indisponible faisait echouer tout
    l'apercu en 409. L'ecran affichait « votre panier est vide » alors que le
    panneau lateral montrait quinze articles, et rien ne disait quoi enlever ;

  · **« le client ne peut pas donner son avis »** : la table existait, aucune
    route ne l'alimentait.
"""
import pytest
from django.urls import reverse

from catalogue.models import Produit
from commandes.decoupage import decouper
from commandes.models import Commande, LignePanier, Panier, StatutCommande
from comptes.models import (
    Adresse,
    Client,
    StatutCompte,
    StatutValidation,
    TypeService,
    Utilisateur,
    Vendeur,
)
from engagement.models import Avis, CibleAvis

MOT_DE_PASSE = "UnMotDePasseSolide!2026"


def entete(client, email):
    jeton = client.post(
        reverse("connexion"), {"email": email, "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json",
    ).json()["data"]["acces"]
    return {"Authorization": f"Bearer {jeton}"}


@pytest.fixture
def boutique(db):
    utilisateur = Utilisateur.objects.create_user(
        email="sophie@exemple.fr", password=MOT_DE_PASSE, nom="Leroy", prenom="Sophie",
        role="VENDEUR", statut_compte=StatutCompte.ACTIF,
    )
    return Vendeur.objects.create(
        utilisateur=utilisateur, nom_boutique="TechSophie",
        type_activite=TypeService.STANDARD, statut_validation=StatutValidation.VALIDE,
    )


@pytest.fixture
def acheteuse(db):
    utilisateur = Utilisateur.objects.create_user(
        email="lea@exemple.fr", password=MOT_DE_PASSE, nom="Martin", prenom="Lea",
        role="CLIENT", statut_compte=StatutCompte.ACTIF,
    )
    profil = Client.objects.create(utilisateur=utilisateur)
    adresse = Adresse.objects.create(
        rue="8 rue Victor Hugo", code_postal="69002", ville="Lyon", libelle="Domicile"
    )
    profil.adresses.through.objects.create(
        client=profil, adresse=adresse, est_principale=True
    )
    return profil


@pytest.fixture
def panier_mixte(boutique, acheteuse):
    """Un panier de trois articles dont UN seul est indisponible."""
    bon = Produit.objects.create(
        vendeur=boutique, nom="Casque", prix_unitaire_centimes=18900, stock_disponible=5
    )
    autre_bon = Produit.objects.create(
        vendeur=boutique, nom="Clavier", prix_unitaire_centimes=8900, stock_disponible=3
    )
    retire = Produit.objects.create(
        vendeur=boutique, nom="Tarte du jour", prix_unitaire_centimes=620,
        stock_disponible=4, est_visible=False,
    )

    panier = Panier.objects.create(client=acheteuse)
    for produit in (bon, autre_bon, retire):
        LignePanier.objects.create(
            panier=panier, produit=produit, quantite=1,
            prix_capture_centimes=produit.prix_unitaire_centimes,
        )
    return panier


# ── Le panier ne se bloque plus tout entier ──────────────────────────────

@pytest.mark.django_db
def test_l_apercu_montre_ce_qui_bloque_au_lieu_de_tout_refuser(client, panier_mixte):
    reponse = client.get(
        reverse("apercu-commandes"), headers=entete(client, "lea@exemple.fr")
    )
    assert reponse.status_code == 200, "un seul article retire ne doit pas tout bloquer"

    donnees = reponse.json()["data"]
    assert donnees["commandes"], "le reste du panier reste commandable"
    assert [ligne["nom"] for ligne in donnees["lignes_bloquantes"]] == ["Tarte du jour"]
    assert donnees["lignes_bloquantes"][0]["code"] == "retire"
    # Et le total ne compte pas ce qu'on ne peut pas acheter. La livraison
    # est offerte : 278 EUR depassent le seuil de gratuite Standard (D-11).
    assert donnees["total_centimes"] == 18900 + 8900


@pytest.mark.django_db
def test_retirer_les_indisponibles_debloque_la_commande(client, panier_mixte):
    entetes = entete(client, "lea@exemple.fr")

    nettoyage = client.post(reverse("nettoyer-panier"), headers=entetes)
    assert nettoyage.status_code == 200
    assert [ligne["nom"] for ligne in nettoyage.json()["data"]["retirees"]] == ["Tarte du jour"]
    assert nettoyage.json()["data"]["nombre_articles"] == 2

    creation = client.post(
        reverse("creer-commandes"),
        {"adresse": {"rue": "8 rue Victor Hugo", "code_postal": "69002", "ville": "Lyon"}},
        content_type="application/json", headers=entetes,
    )
    assert creation.status_code == 201
    assert Commande.objects.count() == 1


@pytest.mark.django_db
def test_la_creation_reste_stricte_meme_si_l_apercu_est_tolerant(client, panier_mixte):
    """Tolerer a l'apercu ne veut pas dire facturer n'importe quoi."""
    reponse = client.post(
        reverse("creer-commandes"),
        {"adresse": {"rue": "8 rue Victor Hugo", "code_postal": "69002", "ville": "Lyon"}},
        content_type="application/json", headers=entete(client, "lea@exemple.fr"),
    )
    assert reponse.status_code == 409
    assert "Tarte du jour" in reponse.json()["erreur"]["message"]
    assert Commande.objects.count() == 0


# ── L'avis ───────────────────────────────────────────────────────────────

@pytest.fixture
def commande_livree(client, panier_mixte, acheteuse):
    LignePanier.objects.filter(produit__est_visible=False).delete()
    adresse = acheteuse.adresses.first()
    commande = decouper(panier_mixte, acheteuse, adresse)[0]
    commande.statut_actuel = StatutCommande.LIVREE
    commande.save(update_fields=["statut_actuel"])
    return commande


@pytest.mark.django_db
def test_un_client_note_la_boutique_et_les_produits_recus(client, commande_livree):
    entetes = entete(client, "lea@exemple.fr")

    possibles = client.get(
        reverse("avis-commande", args=[commande_livree.id]), headers=entetes
    ).json()["data"]
    assert possibles["livree"] is True
    cibles = {element["cible"] for element in possibles["elements"]}
    assert CibleAvis.VENDEUR in cibles and CibleAvis.PRODUIT in cibles

    boutique = next(e for e in possibles["elements"] if e["cible"] == CibleAvis.VENDEUR)
    reponse = client.post(
        reverse("avis-commande", args=[commande_livree.id]),
        {"cible": boutique["cible"], "id_cible": boutique["id_cible"],
         "note": 4, "commentaire": "Emballage soigne."},
        content_type="application/json", headers=entetes,
    )
    assert reponse.status_code == 200
    avis = Avis.objects.get(commande=commande_livree, cible=CibleAvis.VENDEUR)
    assert avis.note == 4


@pytest.mark.django_db
def test_on_ne_note_que_ce_qu_on_a_recu(client, panier_mixte, acheteuse):
    """R-06 : autoriser un avis avant livraison ouvrirait la porte aux faux."""
    LignePanier.objects.filter(produit__est_visible=False).delete()
    commande = decouper(panier_mixte, acheteuse, acheteuse.adresses.first())[0]

    reponse = client.post(
        reverse("avis-commande", args=[commande.id]),
        {"cible": CibleAvis.VENDEUR, "id_cible": 1, "note": 5},
        content_type="application/json", headers=entete(client, "lea@exemple.fr"),
    )
    assert reponse.status_code == 409
    assert reponse.json()["erreur"]["code"] == "pas_encore_livree"
    assert not Avis.objects.exists()


@pytest.mark.django_db
def test_on_ne_note_pas_une_cible_absente_de_la_commande(client, commande_livree):
    """Sans cette verification, changer un identifiant suffirait a noter
    n'importe quelle boutique de la plateforme."""
    reponse = client.post(
        reverse("avis-commande", args=[commande_livree.id]),
        {"cible": CibleAvis.VENDEUR, "id_cible": 9999, "note": 1},
        content_type="application/json", headers=entete(client, "lea@exemple.fr"),
    )
    assert reponse.status_code == 400
    assert reponse.json()["erreur"]["code"] == "cible_hors_commande"


@pytest.mark.django_db
def test_on_ne_note_pas_la_commande_d_un_autre(client, commande_livree):
    Utilisateur.objects.create_user(
        email="marc@exemple.fr", password=MOT_DE_PASSE, nom="Dubois", prenom="Marc",
        role="CLIENT", statut_compte=StatutCompte.ACTIF,
    )
    Client.objects.create(utilisateur=Utilisateur.objects.get(email="marc@exemple.fr"))

    reponse = client.post(
        reverse("avis-commande", args=[commande_livree.id]),
        {"cible": CibleAvis.VENDEUR, "id_cible": 1, "note": 1},
        content_type="application/json", headers=entete(client, "marc@exemple.fr"),
    )
    assert reponse.status_code == 404
