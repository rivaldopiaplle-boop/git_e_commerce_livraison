"""La carte, la reconfirmation, et ou va l'argent — O-5.

Ton reproche tenait en quatre phrases :

  · *« payer est valide sans carte, pas de demande de carte meme la premiere
    fois, et apres c'est enregistre »* ;
  · *« l'argent est paye sans reconfirmation »* ;
  · *« l'argent paye, on ne voit pas la distribution chez les vendeurs, la part
    du livreur, celle de l'application »* ;
  · *« que ca ne prenne pas beaucoup de temps »*.

Le test le plus important du fichier est celui qui refuse une VRAIE carte : sur
une demonstration, quelqu'un finira par taper la sienne, et il faut l'arreter.
"""
import pytest
from django.urls import reverse

from catalogue.models import Produit
from commandes.models import Commande, StatutCommande
from comptes.models import (
    Adresse,
    AdresseClient,
    Client,
    StatutCompte,
    StatutValidation,
    TypeService,
    Utilisateur,
    Vendeur,
)
from paiements.cartes import MoyenPaiement, luhn, marque_de, valider
from paiements.models import Paiement, StatutPaiement

MOT_DE_PASSE = "Demonstration!2026"
CARTE = {"numero": "4242424242424242", "mois": "12", "annee": "30", "cryptogramme": "123"}


@pytest.fixture
def cliente(db):
    adresse = Adresse.objects.create(
        libelle="Domicile", rue="8 rue Victor Hugo", code_postal="69002", ville="Lyon",
        latitude=45.757, longitude=4.834,
    )
    profil = Client.objects.create(
        utilisateur=Utilisateur.objects.create_user(
            email="lea@exemple.fr", password=MOT_DE_PASSE, nom="Martin", prenom="Lea",
            role="CLIENT", statut_compte=StatutCompte.ACTIF,
        )
    )
    AdresseClient.objects.create(client=profil, adresse=adresse, est_principale=True)
    return profil


@pytest.fixture
def produit(db):
    boutique = Vendeur.objects.create(
        utilisateur=Utilisateur.objects.create_user(
            email="karim@exemple.fr", password=MOT_DE_PASSE, nom="Benali", prenom="Karim",
            role="VENDEUR", statut_compte=StatutCompte.ACTIF,
        ),
        nom_boutique="Chez Karim", type_activite=TypeService.EXPRESS,
        statut_validation=StatutValidation.VALIDE,
        adresse=Adresse.objects.create(
            rue="1 rue du Marche", code_postal="69002", ville="Lyon",
            latitude=45.755, longitude=4.832,
        ),
        rayon_livraison_km=10,
    )
    return Produit.objects.create(
        vendeur=boutique, nom="Ramen", description="x",
        prix_unitaire_centimes=1290, stock_disponible=10, seuil_alerte=1,
    )


def connecter(client, email="lea@exemple.fr"):
    reponse = client.post(
        reverse("connexion"), {"email": email, "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json",
    )
    return {"Authorization": f"Bearer {reponse.json()['data']['acces']}"}


class TestLaValidationSansReseau:
    """La carte est verifiee AVANT le moindre appel : c'est ce qui rend la
    saisie rapide."""

    def test_la_cle_de_luhn_attrape_les_fautes_de_frappe(self):
        assert luhn("4242424242424242") is True
        # Deux chiffres inverses : ce qui arrive tout le temps sur seize
        # chiffres tapes au pouce.
        assert luhn("4242424242424262") is False

    def test_la_marque_se_deduit_du_numero(self):
        assert marque_de("4242424242424242") == "VISA"
        assert marque_de("5555555555554444") == "MASTERCARD"
        assert marque_de("378282246310005") == "AMEX"

    def test_une_amex_veut_quatre_chiffres_de_cryptogramme(self):
        from paiements.cartes import CarteRefusee

        with pytest.raises(CarteRefusee) as souci:
            valider("378282246310005", 12, 30, "123")
        assert souci.value.code == "cryptogramme_invalide"

        marque, quatre, jeton, refus = valider("378282246310005", 12, 30, "1234")
        assert marque == "AMEX"

    def test_la_meme_carte_donne_le_meme_jeton(self):
        """Sinon le carnet se remplirait de doublons de la meme carte."""
        _, _, premier, _ = valider(**{"numero": "4242424242424242", "mois": 12,
                                      "annee": 30, "cryptogramme": "123"})
        _, _, second, _ = valider(**{"numero": "4242 4242 4242 4242", "mois": 12,
                                     "annee": 30, "cryptogramme": "999"})
        assert premier == second

    def test_le_jeton_ne_contient_pas_le_numero(self):
        """Un jeton d'ou l'on peut relire la carte n'est pas un jeton."""
        _, _, jeton, _ = valider("4242424242424242", 12, 30, "123")

        assert "4242424242424242" not in jeton
        assert "424242" not in jeton


@pytest.mark.django_db
class TestLeCarnet:
    def test_une_vraie_carte_est_refusee(self, client, cliente):
        """LE test important de ce fichier.

        Sur une demonstration mise en ligne, quelqu'un finira par taper sa
        vraie carte. Il faut l'arreter, et le lui dire.
        """
        reponse = client.post(
            reverse("mes-cartes"),
            {"numero": "4111111111111111", "mois": "12", "annee": "30",
             "cryptogramme": "123"},
            content_type="application/json", headers=connecter(client),
        )

        assert reponse.status_code == 400
        assert reponse.json()["erreur"]["code"] == "carte_non_test"
        assert "jamais votre vraie carte" in reponse.json()["erreur"]["message"]

    def test_le_numero_ne_touche_jamais_la_base(self, client, cliente):
        client.post(reverse("mes-cartes"), CARTE,
                    content_type="application/json", headers=connecter(client))

        carte = MoyenPaiement.objects.get()
        assert carte.quatre_derniers == "4242"
        # Aucun champ ne contient le numero complet, jeton compris.
        for champ in carte._meta.fields:
            assert "4242424242424242" not in str(getattr(carte, champ.name))

    def test_la_premiere_carte_devient_la_carte_par_defaut(self, client, cliente):
        """Personne ne coche une case pour choisir entre une carte et rien."""
        reponse = client.post(reverse("mes-cartes"), CARTE,
                              content_type="application/json", headers=connecter(client))

        assert reponse.json()["data"]["par_defaut"] is True

    def test_l_erreur_designe_le_champ_fautif(self, client, cliente):
        """« Erreur » en haut du formulaire oblige a relire les quatre champs."""
        reponse = client.post(
            reverse("mes-cartes"),
            {**CARTE, "annee": "20"},
            content_type="application/json", headers=connecter(client),
        )

        assert reponse.json()["erreur"]["details"]["champ"] == "expiration"

    def test_les_cartes_d_essai_sont_servies_pas_cachees(self, client, cliente):
        """Une demonstration qu'on ne sait pas essayer ne se demontre pas."""
        reponse = client.get(reverse("mes-cartes"), headers=connecter(client))

        essais = reponse.json()["data"]["cartes_d_essai"]
        assert any(carte["numero"] == "4242424242424242" for carte in essais)
        assert any(carte["effet"] == "refusée" for carte in essais)


@pytest.mark.django_db
class TestPayerExigeUneCarte:
    def _commander(self, client, produit, entetes):
        client.post(reverse("ajouter-ligne"), {"produit": produit.id, "quantite": 1},
                    content_type="application/json", headers=entetes)
        reponse = client.post(reverse("creer-commandes"), {},
                              content_type="application/json", headers=entetes)
        return Commande.objects.get(pk=reponse.json()["data"][0]["id"])

    def test_sans_carte_le_paiement_est_refuse(self, client, cliente, produit):
        """Le defaut d'origine : le bouton payait sans qu'on ait rien donne."""
        entetes = connecter(client)
        commande = self._commander(client, produit, entetes)

        reponse = client.post(reverse("ouvrir-intention", args=[commande.id]), {},
                              content_type="application/json", headers=entetes)

        assert reponse.status_code == 400
        assert reponse.json()["erreur"]["code"] == "carte_absente"
        commande.refresh_from_db()
        assert commande.statut_actuel == StatutCommande.EN_ATTENTE_PAIEMENT

    def test_avec_une_carte_l_intention_dit_laquelle(self, client, cliente, produit):
        """C'est ce qui permet d'ecrire « payer 12,90 EUR avec Visa 4242 »
        plutot qu'un « Payer » qui ne dit rien (O-5)."""
        entetes = connecter(client)
        commande = self._commander(client, produit, entetes)
        client.post(reverse("mes-cartes"), CARTE,
                    content_type="application/json", headers=entetes)

        reponse = client.post(reverse("ouvrir-intention", args=[commande.id]), {},
                              content_type="application/json", headers=entetes)

        assert reponse.status_code == 200
        assert reponse.json()["data"]["carte"]["libelle"] == "VISA •••• 4242"

    def test_la_carte_utilisee_est_notee_sur_le_paiement(self, client, cliente, produit):
        entetes = connecter(client)
        commande = self._commander(client, produit, entetes)
        client.post(reverse("mes-cartes"), CARTE,
                    content_type="application/json", headers=entetes)
        client.post(reverse("ouvrir-intention", args=[commande.id]), {},
                    content_type="application/json", headers=entetes)

        assert Paiement.objects.get(commande=commande).methode == "VISA-4242"

    def test_une_carte_expiree_est_refusee_au_moment_de_payer(self, client, cliente,
                                                              produit):
        """Une carte valide a l'enregistrement peut expirer avant le paiement."""
        entetes = connecter(client)
        commande = self._commander(client, produit, entetes)
        client.post(reverse("mes-cartes"), CARTE,
                    content_type="application/json", headers=entetes)
        MoyenPaiement.objects.update(annee_expiration=2020, mois_expiration=1)

        reponse = client.post(reverse("ouvrir-intention", args=[commande.id]), {},
                              content_type="application/json", headers=entetes)

        assert reponse.json()["erreur"]["code"] == "carte_expiree"


@pytest.mark.django_db
class TestOuVaLArgent:
    def test_les_parts_font_exactement_le_total_paye(self, client, cliente, produit):
        """Un ecran qui ment d'un centime perd toute sa credibilite."""
        entetes = connecter(client)
        client.post(reverse("ajouter-ligne"), {"produit": produit.id, "quantite": 2},
                    content_type="application/json", headers=entetes)
        creation = client.post(reverse("creer-commandes"), {},
                               content_type="application/json", headers=entetes)
        commande = Commande.objects.get(pk=creation.json()["data"][0]["id"])
        client.post(reverse("mes-cartes"), CARTE,
                    content_type="application/json", headers=entetes)
        intention = client.post(reverse("ouvrir-intention", args=[commande.id]), {},
                                content_type="application/json", headers=entetes)
        client.post(reverse("confirmer-paiement"),
                    {"reference": intention.json()["data"]["reference"]},
                    content_type="application/json")

        donnees = client.get(reverse("repartition-commande", args=[commande.id]),
                             headers=entetes).json()["data"]

        assert sum(part["montant_centimes"] for part in donnees["parts"]) == \
            donnees["montant_total_centimes"]
        assert {part["role"] for part in donnees["parts"]} >= {"VENDEUR", "PLATEFORME"}
        assert donnees["statut_paiement"] == StatutPaiement.CAPTURE

    def test_on_ne_lit_pas_la_repartition_d_un_autre(self, client, cliente, produit, db):
        Utilisateur.objects.create_user(
            email="autre@exemple.fr", password=MOT_DE_PASSE, nom="Autre", prenom="Personne",
            role="CLIENT", statut_compte=StatutCompte.ACTIF,
        )
        entetes = connecter(client)
        client.post(reverse("ajouter-ligne"), {"produit": produit.id, "quantite": 1},
                    content_type="application/json", headers=entetes)
        creation = client.post(reverse("creer-commandes"), {},
                               content_type="application/json", headers=entetes)
        commande = Commande.objects.get(pk=creation.json()["data"][0]["id"])

        reponse = client.get(reverse("repartition-commande", args=[commande.id]),
                             headers=connecter(client, "autre@exemple.fr"))

        assert reponse.status_code == 404
