"""Le paiement et la reservation de stock — D-12, D-15, D-18.

Ces tests sont nes d'un vrai defaut : le stock etait reserve **deux fois** pour
une meme commande, a sa creation puis a l'ouverture du paiement, et relache une
seule fois. Chaque commande payee laissait donc une reserve fantome, et un
produit finissait par paraitre epuise alors qu'il ne l'etait pas.

Ce qui est verifie ici tient en une phrase : **le compteur de reservation
revient toujours a sa valeur de depart**, quel que soit le chemin — capture,
refus, abandon, webhook rejoue, ou retour du client sur une commande
abandonnee.
"""
import pytest
from django.urls import reverse

from catalogue.models import MouvementStock, Produit, TypeMouvement
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
from paiements.models import Facture, Paiement, RepartitionVendeur, StatutPaiement

MOT_DE_PASSE = "UnMotDePasseSolide!2026"
SESSION = "session-paiement"


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
        vendeur=boutique, nom="Ramen", prix_unitaire_centimes=1290, stock_disponible=10
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


def connecter(client, email="lea@exemple.fr"):
    reponse = client.post(
        reverse("connexion"), {"email": email, "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json", headers={"X-Panier-Session": SESSION},
    )
    return {"Authorization": f"Bearer {reponse.json()['data']['acces']}"}


def commander(client, produit, quantite=1, entetes=None):
    """Un panier, une commande, et les entetes pour la suite."""
    entetes = entetes or connecter(client)
    client.post(
        reverse("ajouter-ligne"), {"produit": produit.id, "quantite": quantite},
        content_type="application/json", headers=entetes,
    )
    reponse = client.post(reverse("creer-commandes"), {}, content_type="application/json",
                          headers=entetes)
    assert reponse.status_code == 201, reponse.json()
    return Commande.objects.get(pk=reponse.json()["data"][0]["id"]), entetes


def ouvrir(client, commande, entetes):
    return client.post(
        reverse("ouvrir-intention", args=[commande.id]), {},
        content_type="application/json", headers=entetes,
    )


def confirmer(client, reference):
    return client.post(
        reverse("confirmer-paiement"), {"reference": reference},
        content_type="application/json",
    )


# ── La reservation n'a qu'un seul auteur ─────────────────────────────────

@pytest.mark.django_db
def test_ouvrir_le_paiement_ne_reserve_pas_une_deuxieme_fois(client, lea, produit):
    """Le defaut d'origine, verrouille pour de bon.

    La commande reserve a sa creation ; ouvrir le paiement ne doit rien
    ajouter. Sans cette garantie, chaque commande immobilise le double de ce
    qu'elle vend.
    """
    commande, entetes = commander(client, produit, quantite=2)
    produit.refresh_from_db()
    assert produit.stock_reserve == 2

    assert ouvrir(client, commande, entetes).status_code == 200

    produit.refresh_from_db()
    assert produit.stock_reserve == 2, "la reservation a ete posee deux fois"
    assert produit.stock_disponible == 10, "rien n'est vendu tant que rien n'est paye"


@pytest.mark.django_db
def test_ouvrir_deux_fois_le_paiement_ne_reserve_toujours_qu_une_fois(client, lea, produit):
    """Le client rafraichit sa page de paiement : cela arrive tout le temps."""
    commande, entetes = commander(client, produit, quantite=2)
    ouvrir(client, commande, entetes)
    ouvrir(client, commande, entetes)

    produit.refresh_from_db()
    assert produit.stock_reserve == 2


@pytest.mark.django_db
def test_le_stock_reserve_n_est_plus_commandable_par_un_autre(client, lea, produit):
    commande, entetes = commander(client, produit, quantite=8)
    ouvrir(client, commande, entetes)

    produit.refresh_from_db()
    assert produit.stock_commandable == 2


# ── La capture ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_la_capture_consomme_la_reserve_et_laisse_un_mouvement(client, lea, produit):
    """Un stock qui baisse sans mouvement est un stock inexplicable (scenario 4.4)."""
    commande, entetes = commander(client, produit, quantite=3)
    reference = ouvrir(client, commande, entetes).json()["data"]["reference"]

    reponse = confirmer(client, reference)

    assert reponse.status_code == 200
    assert reponse.json()["data"]["statut_commande"] == StatutCommande.PAYEE

    produit.refresh_from_db()
    assert produit.stock_disponible == 7
    assert produit.stock_reserve == 0, "la reserve est consommee, pas laissee derriere"

    mouvement = MouvementStock.objects.get(produit=produit)
    assert mouvement.type == TypeMouvement.VENTE
    assert mouvement.quantite == -3
    assert mouvement.stock_apres == 7
    assert commande.numero_commande in mouvement.motif


@pytest.mark.django_db
def test_la_capture_ecrit_la_repartition_et_la_facture(client, lea, produit, boutique):
    """Sans ces deux traces, aucun audit n'est possible sur une commande."""
    commande, entetes = commander(client, produit, quantite=2)
    reference = ouvrir(client, commande, entetes).json()["data"]["reference"]
    confirmer(client, reference)

    repartition = RepartitionVendeur.objects.get(sous_commande__commande=commande)
    assert repartition.vendeur == boutique
    assert repartition.montant_commission_centimes == round(2 * 1290 * 0.15)
    assert (repartition.montant_vendeur_centimes + repartition.montant_commission_centimes
            == 2 * 1290)

    facture = Facture.objects.get(commande=commande)
    assert facture.numero_facture == f"F-{commande.numero_commande}"


@pytest.mark.django_db
def test_rejouer_le_webhook_ne_decremente_rien_deux_fois(client, lea, produit):
    """Les fournisseurs de paiement reessaient quand ils doutent d'avoir ete recus.

    Une confirmation rejouee qui vendrait une deuxieme fois le meme article
    est le genre de defaut qu'on ne decouvre qu'en production, un jour de
    charge.
    """
    commande, entetes = commander(client, produit, quantite=4)
    reference = ouvrir(client, commande, entetes).json()["data"]["reference"]
    confirmer(client, reference)

    reponse = confirmer(client, reference)

    assert reponse.status_code == 200
    assert reponse.json()["data"]["deja_traite"] is True
    produit.refresh_from_db()
    assert produit.stock_disponible == 6
    assert MouvementStock.objects.filter(produit=produit).count() == 1


# ── Les chemins qui echouent ─────────────────────────────────────────────

@pytest.mark.django_db
def test_un_paiement_refuse_rend_le_stock_et_laisse_la_commande_payable(client, lea, produit):
    """Le simulateur sait echouer : sans cela, le chemin d'erreur ne serait jamais teste."""
    commande, entetes = commander(client, produit, quantite=2)
    reference = ouvrir(client, commande, entetes).json()["data"]["reference"]

    # Le simulateur refuse toute reference se terminant par 99 (D-18).
    paiement = Paiement.objects.get(commande=commande)
    paiement.reference_stripe = reference[:-2] + "99"
    paiement.save(update_fields=["reference_stripe"])

    reponse = confirmer(client, paiement.reference_stripe)

    assert reponse.json()["data"]["statut"] == StatutPaiement.ECHOUE
    produit.refresh_from_db()
    assert produit.stock_reserve == 0, "un refus rend le stock a la vente"
    assert produit.stock_disponible == 10, "rien n'est sorti, donc rien ne bouge"
    commande.refresh_from_db()
    assert commande.statut_actuel == StatutCommande.EN_ATTENTE_PAIEMENT, "il peut reessayer"
    assert not MouvementStock.objects.exists(), "aucune vente n'a eu lieu"


@pytest.mark.django_db
def test_abandonner_rend_le_stock_immediatement(client, lea, produit):
    """Sans ce chemin, l'article resterait invendable dix minutes apres le depart du client."""
    commande, entetes = commander(client, produit, quantite=5)
    ouvrir(client, commande, entetes)

    reponse = client.post(reverse("abandonner-paiement", args=[commande.id]), {},
                          content_type="application/json", headers=entetes)

    assert reponse.status_code == 200
    assert reponse.json()["data"]["reservation_relachee"] is True
    produit.refresh_from_db()
    assert produit.stock_reserve == 0


@pytest.mark.django_db
def test_abandonner_deux_fois_ne_rend_pas_le_stock_deux_fois(client, lea, produit):
    """Le miroir du defaut d'origine : relacher est aussi une operation a un seul auteur."""
    commande, entetes = commander(client, produit, quantite=3)
    ouvrir(client, commande, entetes)
    client.post(reverse("abandonner-paiement", args=[commande.id]), {},
                content_type="application/json", headers=entetes)

    reponse = client.post(reverse("abandonner-paiement", args=[commande.id]), {},
                          content_type="application/json", headers=entetes)

    assert reponse.json()["data"]["reservation_relachee"] is False
    produit.refresh_from_db()
    assert produit.stock_reserve == 0


@pytest.mark.django_db
def test_revenir_payer_apres_un_abandon_repose_la_reservation(client, lea, produit):
    """Le client hesite, ferme l'onglet, revient. C'est courant, pas une bizarrerie."""
    commande, entetes = commander(client, produit, quantite=3)
    ouvrir(client, commande, entetes)
    client.post(reverse("abandonner-paiement", args=[commande.id]), {},
                content_type="application/json", headers=entetes)

    assert ouvrir(client, commande, entetes).status_code == 200

    produit.refresh_from_db()
    assert produit.stock_reserve == 3


@pytest.mark.django_db
def test_revenir_payer_quand_le_stock_est_parti_refuse_proprement(client, lea, produit):
    """Il doit apprendre CE qui manque, pas seulement que quelque chose manque."""
    commande, entetes = commander(client, produit, quantite=6)
    ouvrir(client, commande, entetes)
    client.post(reverse("abandonner-paiement", args=[commande.id]), {},
                content_type="application/json", headers=entetes)

    Produit.objects.filter(pk=produit.id).update(stock_disponible=2)

    reponse = ouvrir(client, commande, entetes)

    assert reponse.status_code == 409
    erreur = reponse.json()["erreur"]
    assert erreur["code"] == "stock_insuffisant"
    assert erreur["details"]["produits"] == [
        {"produit": "Ramen", "demande": 6, "disponible": 2}
    ]
    produit.refresh_from_db()
    assert produit.stock_reserve == 0, "un refus ne reserve rien au passage"


@pytest.mark.django_db
def test_on_ne_paie_pas_deux_fois_la_meme_commande(client, lea, produit):
    commande, entetes = commander(client, produit, quantite=1)
    reference = ouvrir(client, commande, entetes).json()["data"]["reference"]
    confirmer(client, reference)

    reponse = ouvrir(client, commande, entetes)

    assert reponse.status_code == 409
    assert reponse.json()["erreur"]["code"] == "deja_payee"


@pytest.mark.django_db
def test_on_ne_paie_pas_la_commande_d_un_autre(client, lea, produit, boutique):
    """Un identifiant devine ne doit rien ouvrir : 404, pas 403.

    Repondre 403 confirmerait que la commande existe — une fuite d'information
    gratuite.
    """
    commande, _ = commander(client, produit, quantite=1)
    autre = Utilisateur.objects.create_user(
        email="marc@exemple.fr", password=MOT_DE_PASSE, nom="Marc", prenom="Test",
        role="CLIENT", statut_compte=StatutCompte.ACTIF,
    )
    Client.objects.create(utilisateur=autre)

    reponse = ouvrir(client, commande, connecter(client, "marc@exemple.fr"))

    assert reponse.status_code == 404


@pytest.mark.django_db
def test_une_reference_inconnue_ne_confirme_rien(client):
    reponse = confirmer(client, "pi_sim_inventee")

    assert reponse.status_code == 404
    assert reponse.json()["erreur"]["code"] == "paiement_inconnu"


# ── La facture ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_la_facture_reprend_les_lignes_et_les_montants(client, lea, produit):
    commande, entetes = commander(client, produit, quantite=2)
    reference = ouvrir(client, commande, entetes).json()["data"]["reference"]
    confirmer(client, reference)

    reponse = client.get(reverse("ma-facture", args=[commande.id]), headers=entetes)

    donnees = reponse.json()["data"]
    assert donnees["numero_facture"] == f"F-{commande.numero_commande}"
    assert len(donnees["lignes"]) == 1
    assert donnees["lignes"][0]["nom"] == "Ramen"
    assert donnees["lignes"][0]["quantite"] == 2
    assert donnees["montant_produits_centimes"] == 2 * 1290


# ── L'expiration ─────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_une_reservation_abandonnee_expire_et_rend_le_stock(client, lea, produit):
    """Un onglet ferme ne doit pas immobiliser un article pour toujours.

    Sans expiration, il suffisait de quelques essais interrompus pour qu'un
    produit parfaitement disponible s'affiche « epuise » au catalogue, sans que
    personne ne puisse expliquer pourquoi.
    """
    from datetime import timedelta

    from django.utils import timezone

    from commandes import reservation

    commande, entetes = commander(client, produit, quantite=4)
    ouvrir(client, commande, entetes)

    # On vieillit la commande plutot que d'attendre dix minutes.
    Commande.objects.filter(pk=commande.id).update(
        date_commande=timezone.now() - timedelta(minutes=reservation.DUREE_MINUTES + 1)
    )

    assert reservation.liberer_les_expirees() == 1

    produit.refresh_from_db()
    assert produit.stock_reserve == 0
    assert produit.stock_disponible == 10, "rien n'a ete vendu, donc rien ne sort"
    commande.refresh_from_db()
    assert commande.stock_reserve_pose is False


@pytest.mark.django_db
def test_une_reservation_recente_ne_expire_pas(client, lea, produit):
    """Le client qui remplit son adresse ne doit pas se faire retirer ses articles."""
    from commandes import reservation

    commande, entetes = commander(client, produit, quantite=4)
    ouvrir(client, commande, entetes)

    assert reservation.liberer_les_expirees() == 0

    produit.refresh_from_db()
    assert produit.stock_reserve == 4


@pytest.mark.django_db
def test_une_commande_payee_n_est_jamais_touchee_par_l_expiration(client, lea, produit):
    """L'expiration ne regarde que ce qui attend un paiement, jamais une vente faite."""
    from datetime import timedelta

    from django.utils import timezone

    from commandes import reservation

    commande, entetes = commander(client, produit, quantite=4)
    reference = ouvrir(client, commande, entetes).json()["data"]["reference"]
    confirmer(client, reference)
    Commande.objects.filter(pk=commande.id).update(
        date_commande=timezone.now() - timedelta(days=3)
    )

    assert reservation.liberer_les_expirees() == 0

    produit.refresh_from_db()
    assert produit.stock_disponible == 6, "le stock vendu ne revient pas par magie"
    assert produit.stock_reserve == 0
