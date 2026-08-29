"""Ce que chaque role a le droit de voir, verifie cote serveur.

Le bloc J a mis au jour trois defauts qui se ressemblaient tous :

  · le gestionnaire staff recevait un **403 sur la liste des produits**, donc
    son ecran de stock — le seul de son metier — ne s'ouvrait pas ;
  · le meme gestionnaire recevait le **chiffre d'affaires** de la boutique
    dans le tableau de bord, alors que D-04 le lui interdit. L'interface le
    masquait ; masquer n'est pas une permission ;
  · le catalogue vendeur recevait la vignette du client, sans `est_visible` ni
    stock exact, ce qui rendait impossible de remettre en vente un produit
    masque.

Chacun a maintenant son test.
"""
import pytest
from django.urls import reverse

from catalogue.models import MouvementStock, Produit, TypeMouvement
from comptes.models import (
    Gestionnaire,
    StatutCompte,
    StatutValidation,
    TypeGestionnaire,
    TypeService,
    Utilisateur,
    Vendeur,
)

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
        email="karim@exemple.fr", password=MOT_DE_PASSE, nom="Benali", prenom="Karim",
        role="VENDEUR", statut_compte=StatutCompte.ACTIF,
    )
    return Vendeur.objects.create(
        utilisateur=utilisateur, nom_boutique="Chez Karim",
        type_activite=TypeService.EXPRESS, statut_validation=StatutValidation.VALIDE,
    )


@pytest.fixture
def personnel(boutique):
    utilisateur = Utilisateur.objects.create_user(
        email="nadia@exemple.fr", password=MOT_DE_PASSE, nom="Sow", prenom="Nadia",
        role="GESTIONNAIRE", statut_compte=StatutCompte.ACTIF,
    )
    return Gestionnaire.objects.create(
        utilisateur=utilisateur, type_gestionnaire=TypeGestionnaire.STAFF_VENDEUR,
        vendeur=boutique,
    )


@pytest.fixture
def produit(boutique):
    return Produit.objects.create(
        vendeur=boutique, nom="Ramen", prix_unitaire_centimes=1290,
        stock_disponible=10, seuil_alerte=5,
    )


# ── Le catalogue du vendeur ──────────────────────────────────────────────

@pytest.mark.django_db
def test_le_catalogue_vendeur_expose_ce_que_le_client_ne_voit_pas(client, produit):
    """Sans `est_visible` ni stock exact, l'ecran ne peut pas faire son travail."""
    reponse = client.get(
        reverse("mes-produits"), headers=entete(client, "karim@exemple.fr")
    )
    assert reponse.status_code == 200
    ligne = reponse.json()["data"][0]
    for champ in ("est_visible", "stock_disponible", "stock_reserve",
                  "stock_commandable", "est_en_rupture", "seuil_alerte"):
        assert champ in ligne, f"« {champ} » manque au catalogue du vendeur"


@pytest.mark.django_db
def test_le_personnel_peut_lister_les_produits_de_sa_boutique(client, produit, personnel):
    """Il recevait un 403 : son ecran de stock ne s'ouvrait pas du tout."""
    reponse = client.get(
        reverse("mes-produits"), headers=entete(client, "nadia@exemple.fr")
    )
    assert reponse.status_code == 200
    assert [ligne["nom"] for ligne in reponse.json()["data"]] == ["Ramen"]


@pytest.mark.django_db
def test_le_personnel_ne_publie_pas_de_produit(client, boutique, personnel):
    """Publier est une decision commerciale : elle reste au vendeur (D-04)."""
    reponse = client.post(
        reverse("mes-produits"),
        {"nom": "Nouveau plat", "prix_unitaire_centimes": 900},
        content_type="application/json",
        headers=entete(client, "nadia@exemple.fr"),
    )
    assert reponse.status_code == 403
    assert not Produit.objects.filter(nom="Nouveau plat").exists()


# ── Le tableau de bord ───────────────────────────────────────────────────

@pytest.mark.django_db
def test_le_chiffre_d_affaires_ne_quitte_pas_le_serveur_pour_le_personnel(
    client, produit, personnel
):
    """D-04 : le personnel n'a jamais acces au chiffre d'affaires.

    Le masquer dans l'interface ne suffirait pas — il ne doit pas figurer
    dans la reponse.
    """
    du_vendeur = client.get(
        reverse("tableau-vendeur"), headers=entete(client, "karim@exemple.fr")
    ).json()["data"]
    du_personnel = client.get(
        reverse("tableau-vendeur"), headers=entete(client, "nadia@exemple.fr")
    ).json()["data"]

    assert "revenu_centimes" in du_vendeur
    assert "revenu_centimes" not in du_personnel
    # Il garde en revanche ce qui releve de son metier.
    assert "a_preparer" in du_personnel
    assert "stock_bas" in du_personnel


@pytest.mark.django_db
def test_les_statistiques_sont_refusees_au_personnel(client, produit, personnel):
    assert client.get(
        reverse("statistiques-vendeur"), headers=entete(client, "nadia@exemple.fr")
    ).status_code == 403
    assert client.get(
        reverse("mon-personnel"), headers=entete(client, "nadia@exemple.fr")
    ).status_code == 403


# ── Le stock : quantite absolue et rupture ───────────────────────────────

@pytest.mark.django_db
def test_une_quantite_absolue_calcule_l_ecart(client, produit):
    """La maquette demande « Nouvelle quantite » : on compte l'etagere."""
    reponse = client.patch(
        reverse("modifier-stock", args=[produit.id]),
        {"nouvelle_quantite": 4, "type": TypeMouvement.AJUSTEMENT, "motif": "Inventaire"},
        content_type="application/json",
        headers=entete(client, "karim@exemple.fr"),
    )
    assert reponse.status_code == 200
    produit.refresh_from_db()
    assert produit.stock_disponible == 4

    mouvement = MouvementStock.objects.get(produit=produit)
    assert mouvement.quantite == -6, "l'ecart doit etre deduit, pas recopie"
    assert mouvement.stock_apres == 4
    assert mouvement.motif == "Inventaire"


@pytest.mark.django_db
def test_declarer_une_rupture_gele_le_produit_sans_le_masquer(client, produit):
    """D-06 : le produit reste au catalogue, son bouton est gele."""
    client.patch(
        reverse("modifier-stock", args=[produit.id]),
        {"nouvelle_quantite": 0, "type": TypeMouvement.AJUSTEMENT,
         "motif": "Rupture constatee en boutique"},
        content_type="application/json",
        headers=entete(client, "karim@exemple.fr"),
    )
    produit.refresh_from_db()
    assert produit.stock_disponible == 0
    assert produit.est_en_rupture
    assert produit.est_visible, "une rupture ne retire pas le produit du catalogue"

    # Et le client le voit toujours, marque indisponible.
    public = client.get(reverse("detail-produit", args=[produit.id])).json()["data"]
    assert public["disponible"] is False


@pytest.mark.django_db
def test_une_quantite_identique_est_refusee_avec_un_message_clair(client, produit):
    reponse = client.patch(
        reverse("modifier-stock", args=[produit.id]),
        {"nouvelle_quantite": 10, "type": TypeMouvement.AJUSTEMENT, "motif": "Inventaire"},
        content_type="application/json",
        headers=entete(client, "karim@exemple.fr"),
    )
    assert reponse.status_code == 400
    assert "deja a 10" in reponse.json()["erreur"]["message"]


# ── Remettre en vente ────────────────────────────────────────────────────

@pytest.fixture
def produit_standard(db):
    """Une boutique Standard : elle n'est pas soumise au filtrage par rayon.

    Un produit Express sans adresse geocodee n'apparait jamais au catalogue
    d'un visiteur sans position (D-22) — il masquerait ici ce que le test
    cherche a verifier.
    """
    utilisateur = Utilisateur.objects.create_user(
        email="sophie@exemple.fr", password=MOT_DE_PASSE, nom="Leroy", prenom="Sophie",
        role="VENDEUR", statut_compte=StatutCompte.ACTIF,
    )
    boutique = Vendeur.objects.create(
        utilisateur=utilisateur, nom_boutique="TechSophie",
        type_activite=TypeService.STANDARD, statut_validation=StatutValidation.VALIDE,
    )
    return Produit.objects.create(
        vendeur=boutique, nom="Casque", prix_unitaire_centimes=18900,
        stock_disponible=4, seuil_alerte=2,
    )


@pytest.mark.django_db
def test_un_produit_masque_peut_etre_remis_en_vente(client, produit_standard):
    """L'ecran ne savait que masquer : l'action n'avait pas d'inverse."""
    produit = produit_standard
    entetes = entete(client, "sophie@exemple.fr")

    client.patch(
        reverse("modifier-produit", args=[produit.id]),
        {"est_visible": False}, content_type="application/json", headers=entetes,
    )
    produit.refresh_from_db()
    assert not produit.est_visible
    assert produit.id not in [
        ligne["id"] for ligne in client.get(reverse("liste-produits")).json()["data"]
    ]

    client.patch(
        reverse("modifier-produit", args=[produit.id]),
        {"est_visible": True}, content_type="application/json", headers=entetes,
    )
    produit.refresh_from_db()
    assert produit.est_visible
    assert produit.id in [
        ligne["id"] for ligne in client.get(reverse("liste-produits")).json()["data"]
    ]
