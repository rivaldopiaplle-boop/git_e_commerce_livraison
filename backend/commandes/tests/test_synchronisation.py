"""Le vendeur et son personnel voient ce que l'autre a fait — D-80.

**Ta formulation, L-3** : *« le vendeur et le gestionnaire se marchent sur les
pieds, ne sont pas complementaires, et les actions de l'un ne sont pas mises a
jour chez l'autre »*.

Verifie, et le defaut etait double :

  1. la file etait la meme pour les deux, et **aucun ne disait qui avait
     agi** : impossible de savoir si l'employe avait deja pris la commande ;
  2. la trace de preparation etait enregistree sur la **commande** et non sur
     la sous-commande. Sur une commande Standard a trois boutiques, trois
     vendeurs y ecrivaient trois statuts de preparation sans rapport entre
     eux, et rien ne disait lequel concernait qui.
"""
import pytest
from django.urls import reverse

from catalogue.models import Produit
from commandes.models import (
    Commande,
    HistoriqueStatut,
    SousCommande,
    StatutCommande,
    StatutPreparation,
    TypeObjetSuivi,
)
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
SESSION = "session-synchro"


def creer_vendeur(nom, email, service=TypeService.STANDARD):
    compte = Utilisateur.objects.create_user(
        email=email, password=MOT_DE_PASSE, nom=nom, prenom="Test",
        role="VENDEUR", statut_compte=StatutCompte.ACTIF,
    )
    return Vendeur.objects.create(
        utilisateur=compte, nom_boutique=nom, type_activite=service,
        statut_validation=StatutValidation.VALIDE, taux_commission=0.15,
    )


@pytest.fixture
def sophie(db):
    return creer_vendeur("TechSophie", "sophie@exemple.fr")


@pytest.fixture
def leo(db):
    return creer_vendeur("LivresLeo", "leo@exemple.fr")


@pytest.fixture
def nadia(sophie):
    compte = Utilisateur.objects.create_user(
        email="nadia@exemple.fr", password=MOT_DE_PASSE, nom="Nadia", prenom="Test",
        role="GESTIONNAIRE", statut_compte=StatutCompte.ACTIF,
    )
    return Gestionnaire.objects.create(
        utilisateur=compte, vendeur=sophie, type_gestionnaire="STAFF_VENDEUR"
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


def commande_payee(client, boutiques):
    """Une commande Standard, payee, qui porte une sous-commande par boutique."""
    entetes = connecter(client, "lea@exemple.fr")
    for boutique in boutiques:
        produit = Produit.objects.create(
            vendeur=boutique, nom=f"Article {boutique.nom_boutique}",
            prix_unitaire_centimes=1500, stock_disponible=10,
        )
        client.post(
            reverse("ajouter-ligne"), {"produit": produit.id, "quantite": 1},
            content_type="application/json", headers=entetes,
        )
    reponse = client.post(reverse("creer-commandes"), {}, content_type="application/json",
                          headers=entetes)
    commande = Commande.objects.get(pk=reponse.json()["data"][0]["id"])
    intention = client.post(reverse("ouvrir-intention", args=[commande.id]), {},
                            content_type="application/json", headers=entetes)
    client.post(reverse("confirmer-paiement"),
                {"reference": intention.json()["data"]["reference"]},
                content_type="application/json")
    commande.refresh_from_db()
    return commande


def avancer(client, sous_commande, statut, email):
    return client.patch(
        reverse("avancer-preparation", args=[sous_commande.id]), {"statut": statut},
        content_type="application/json", headers=connecter(client, email),
    )


# ── La trace appartient a la sous-commande ───────────────────────────────

@pytest.mark.django_db
def test_la_preparation_se_trace_sur_la_sous_commande(client, lea, sophie):
    commande = commande_payee(client, [sophie])
    sous = commande.sous_commandes.get()

    avancer(client, sous, StatutPreparation.EN_PREPARATION, "sophie@exemple.fr")

    trace = HistoriqueStatut.objects.get(
        type_objet=TypeObjetSuivi.SOUS_COMMANDE, id_objet=sous.id
    )
    assert trace.statut_apres == StatutPreparation.EN_PREPARATION
    assert trace.utilisateur.email == "sophie@exemple.fr"


@pytest.mark.django_db
def test_deux_boutiques_ne_melangent_plus_leurs_avancements(client, lea, sophie, leo):
    """Le defaut d'origine : trois vendeurs ecrivaient sur la MEME commande."""
    commande = commande_payee(client, [sophie, leo])
    part_sophie = commande.sous_commandes.get(vendeur=sophie)
    part_leo = commande.sous_commandes.get(vendeur=leo)

    avancer(client, part_sophie, StatutPreparation.EN_PREPARATION, "sophie@exemple.fr")
    avancer(client, part_leo, StatutPreparation.EN_PREPARATION, "leo@exemple.fr")

    # Chaque trace pointe vers SA sous-commande : on sait laquelle concerne qui.
    assert HistoriqueStatut.objects.filter(
        type_objet=TypeObjetSuivi.SOUS_COMMANDE, id_objet=part_sophie.id
    ).count() == 1
    assert HistoriqueStatut.objects.filter(
        type_objet=TypeObjetSuivi.SOUS_COMMANDE, id_objet=part_leo.id
    ).count() == 1


@pytest.mark.django_db
def test_la_commande_qui_suit_ses_boutiques_le_dit_dans_son_historique(client, lea, sophie):
    """« Jamais de statut modifie en silence » (D-95) : cela valait aussi ici."""
    commande = commande_payee(client, [sophie])
    sous = commande.sous_commandes.get()

    avancer(client, sous, StatutPreparation.EN_PREPARATION, "sophie@exemple.fr")

    commande.refresh_from_db()
    assert commande.statut_actuel == StatutCommande.EN_PREPARATION
    trace = HistoriqueStatut.objects.filter(
        type_objet=TypeObjetSuivi.COMMANDE, id_objet=commande.id,
        statut_apres=StatutCommande.EN_PREPARATION,
    ).first()
    assert trace is not None, "le client doit pouvoir expliquer ce changement"


# ── Chacun voit ce que l'autre a fait ────────────────────────────────────

@pytest.mark.django_db
def test_la_file_dit_qui_a_agi_en_dernier(client, lea, sophie, nadia):
    """Sans cela, les deux prenaient la meme commande sans le savoir."""
    commande = commande_payee(client, [sophie])
    sous = commande.sous_commandes.get()
    avancer(client, sous, StatutPreparation.EN_PREPARATION, "nadia@exemple.fr")

    reponse = client.get(reverse("commandes-recues"),
                         headers=connecter(client, "sophie@exemple.fr"))

    ligne = reponse.json()["data"][0]
    assert ligne["dernier_acte"]["qui"] == "Test Nadia"
    assert ligne["dernier_acte"]["statut"] == StatutPreparation.EN_PREPARATION


@pytest.mark.django_db
def test_une_commande_jamais_touchee_n_a_pas_de_dernier_acte(client, lea, sophie):
    commande_payee(client, [sophie])

    reponse = client.get(reverse("commandes-recues"),
                         headers=connecter(client, "sophie@exemple.fr"))

    assert reponse.json()["data"][0]["dernier_acte"] is None


@pytest.mark.django_db
def test_le_vendeur_voit_l_activite_de_chaque_employe(client, lea, sophie, nadia):
    """Le vendeur avait un employe et aucun moyen de savoir ce qu'il faisait."""
    commande = commande_payee(client, [sophie])
    sous = commande.sous_commandes.get()
    avancer(client, sous, StatutPreparation.EN_PREPARATION, "nadia@exemple.fr")

    produit = Produit.objects.filter(vendeur=sophie).first()
    client.patch(
        reverse("modifier-stock", args=[produit.id]),
        {"nouvelle_quantite": 4, "motif": "Inventaire du soir."},
        content_type="application/json", headers=connecter(client, "nadia@exemple.fr"),
    )

    reponse = client.get(reverse("mon-personnel"),
                         headers=connecter(client, "sophie@exemple.fr"))

    membre = reponse.json()["data"]["personnel"][0]
    assert membre["commandes_preparees"] == 1
    assert membre["ajustements_stock"] == 1
    assert membre["derniere_action"] is not None


@pytest.mark.django_db
def test_l_activite_ne_melange_pas_deux_boutiques(client, lea, sophie, leo, nadia):
    """Chaque compteur est cloisonne comme l'ecran qu'il resume."""
    autre = Utilisateur.objects.create_user(
        email="pierre@exemple.fr", password=MOT_DE_PASSE, nom="Pierre", prenom="Test",
        role="GESTIONNAIRE", statut_compte=StatutCompte.ACTIF,
    )
    Gestionnaire.objects.create(utilisateur=autre, vendeur=leo,
                                type_gestionnaire="STAFF_VENDEUR")
    commande = commande_payee(client, [sophie, leo])
    avancer(client, commande.sous_commandes.get(vendeur=leo),
            StatutPreparation.EN_PREPARATION, "pierre@exemple.fr")

    reponse = client.get(reverse("mon-personnel"),
                         headers=connecter(client, "sophie@exemple.fr"))

    personnel = reponse.json()["data"]["personnel"]
    assert len(personnel) == 1, "Sophie ne voit que SON personnel"
    assert personnel[0]["commandes_preparees"] == 0


@pytest.mark.django_db
def test_un_vendeur_ne_fait_pas_avancer_la_part_d_une_autre_boutique(client, lea, sophie, leo):
    commande = commande_payee(client, [sophie, leo])
    part_leo = commande.sous_commandes.get(vendeur=leo)

    reponse = avancer(client, part_leo, StatutPreparation.EN_PREPARATION,
                      "sophie@exemple.fr")

    assert reponse.status_code == 404
    part_leo.refresh_from_db()
    assert part_leo.statut_preparation == StatutPreparation.A_PREPARER


@pytest.mark.django_db
def test_la_commande_ne_passe_prete_que_lorsque_TOUTES_les_parts_le_sont(
    client, lea, sophie, leo,
):
    """Une commande Standard part quand le dernier colis est pret, pas le premier."""
    commande = commande_payee(client, [sophie, leo])
    part_sophie = commande.sous_commandes.get(vendeur=sophie)
    part_leo = commande.sous_commandes.get(vendeur=leo)

    for statut in (StatutPreparation.EN_PREPARATION, StatutPreparation.PRETE):
        avancer(client, part_sophie, statut, "sophie@exemple.fr")
    commande.refresh_from_db()
    assert commande.statut_actuel != StatutCommande.PRETE, "LivresLeo n'a pas fini"

    for statut in (StatutPreparation.EN_PREPARATION, StatutPreparation.PRETE):
        avancer(client, part_leo, statut, "leo@exemple.fr")
    commande.refresh_from_db()
    assert commande.statut_actuel == StatutCommande.PRETE


@pytest.mark.django_db
def test_preparer_fait_descendre_la_pastille_des_deux_cotes(client, lea, sophie, nadia):
    """Les deux files se rafraichissent seules : agir chez l'un se voit chez l'autre."""
    commande = commande_payee(client, [sophie])
    sous = SousCommande.objects.get(commande=commande)

    avant = client.get(reverse("mes-compteurs"),
                       headers=connecter(client, "nadia@exemple.fr")).json()["data"]
    assert avant["vendeur-commandes"] == 1

    avancer(client, sous, StatutPreparation.EN_PREPARATION, "sophie@exemple.fr")

    apres = client.get(reverse("mes-compteurs"),
                       headers=connecter(client, "nadia@exemple.fr")).json()["data"]
    assert "vendeur-commandes" not in apres
