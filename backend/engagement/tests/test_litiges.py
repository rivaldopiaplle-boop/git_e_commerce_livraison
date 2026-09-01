"""Le cycle complet d'un litige — D-94.

Ce qui est verifie ici n'est pas « l'endpoint repond 200 » mais la procedure
elle-meme : **on n'ouvre pas un litige sur une commande en cours, on ne tranche
pas sans avoir entendu le vendeur, et l'argent suit la decision.**

Le fil directeur, en une phrase : un litige est une procedure contradictoire,
pas un formulaire de reclamation.
"""
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from catalogue.models import Produit
from commandes.models import Commande, StatutCommande
from comptes.models import (
    Administrateur,
    Adresse,
    AdresseClient,
    Client,
    StatutCompte,
    StatutValidation,
    TypeService,
    Utilisateur,
    Vendeur,
)
from engagement.models import Litige, StatutLitige
from paiements.models import Paiement, Remboursement, RepartitionVendeur

MOT_DE_PASSE = "UnMotDePasseSolide!2026"
SESSION = "session-litige"
DESCRIPTION = "Le colis est arrive ouvert et deux articles manquaient a l appel."
REPONSE = "Le colis est parti scelle, la photo de preparation en fait foi."


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
        vendeur=boutique, nom="Ramen", prix_unitaire_centimes=1290, stock_disponible=20
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


@pytest.fixture
def patronne(db):
    compte = Utilisateur.objects.create_user(
        email="admin@exemple.fr", password=MOT_DE_PASSE, nom="Diallo", prenom="Awa",
        role="ADMIN", statut_compte=StatutCompte.ACTIF,
    )
    return Administrateur.objects.create(utilisateur=compte)


def connecter(client, email):
    reponse = client.post(
        reverse("connexion"), {"email": email, "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json", headers={"X-Panier-Session": SESSION},
    )
    return {"Authorization": f"Bearer {reponse.json()['data']['acces']}"}


def commande_livree(client, produit, quantite=2):
    """Une commande payee puis livree : le seul etat ou un litige s'ouvre."""
    entetes = connecter(client, "lea@exemple.fr")
    client.post(
        reverse("ajouter-ligne"), {"produit": produit.id, "quantite": quantite},
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

    Commande.objects.filter(pk=commande.id).update(statut_actuel=StatutCommande.LIVREE)
    commande.refresh_from_db()
    return commande, entetes


def ouvrir_litige(client, commande, entetes, **surcharge):
    corps = {"motif": "INCOMPLET", "description": DESCRIPTION}
    corps.update(surcharge)
    return client.post(reverse("ouvrir-litige", args=[commande.id]), corps,
                       content_type="application/json", headers=entetes)


# ── 1. L'ouverture ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_le_client_ouvre_un_litige_sur_une_commande_livree(client, lea, produit):
    commande, entetes = commande_livree(client, produit)

    reponse = ouvrir_litige(client, commande, entetes)

    assert reponse.status_code == 201
    dossier = reponse.json()["data"]
    assert dossier["statut"] == StatutLitige.OUVERT
    assert dossier["libelle_motif"] == "Commande incomplete"
    # Le delai court des l'ouverture : sans date limite, l'instruction
    # n'aurait pas de fin.
    assert dossier["date_limite_reponse"] is not None
    assert dossier["arbitrable"] is False


@pytest.mark.django_db
def test_on_ne_conteste_pas_une_commande_encore_en_cours(client, lea, produit):
    """Le suivi repond a « ou est ma commande ? ». Un litige, non."""
    commande, entetes = commande_livree(client, produit)
    Commande.objects.filter(pk=commande.id).update(
        statut_actuel=StatutCommande.EN_PREPARATION
    )

    reponse = ouvrir_litige(client, commande, entetes)

    assert reponse.status_code == 409
    assert reponse.json()["erreur"]["code"] == "commande_non_contestable"


@pytest.mark.django_db
def test_un_seul_litige_ouvert_par_commande(client, lea, produit):
    """Deux dossiers concurrents donneraient deux decisions, sans dire laquelle compte."""
    commande, entetes = commande_livree(client, produit)
    ouvrir_litige(client, commande, entetes)

    reponse = ouvrir_litige(client, commande, entetes)

    assert reponse.status_code == 409
    assert reponse.json()["erreur"]["code"] == "litige_deja_ouvert"
    assert Litige.objects.count() == 1


@pytest.mark.django_db
def test_une_description_vide_est_refusee(client, lea, produit):
    """C'est ce que le vendeur et l'administrateur liront pour trancher."""
    commande, entetes = commande_livree(client, produit)

    reponse = ouvrir_litige(client, commande, entetes, description="cassé")

    assert reponse.status_code == 400
    assert reponse.json()["erreur"]["code"] == "description_trop_courte"


@pytest.mark.django_db
def test_ouvrir_un_litige_gele_le_versement_au_vendeur(client, lea, produit):
    """Verser puis reprendre n'est pas une operation qui existe."""
    commande, entetes = commande_livree(client, produit)
    assert RepartitionVendeur.objects.get(
        sous_commande__commande=commande
    ).statut == "TRANSFERE"

    ouvrir_litige(client, commande, entetes)

    assert RepartitionVendeur.objects.get(
        sous_commande__commande=commande
    ).statut == "BLOQUE"


@pytest.mark.django_db
def test_on_n_ouvre_pas_de_litige_sur_la_commande_d_un_autre(client, lea, produit):
    """404 et non 403 : un 403 confirmerait que la commande existe."""
    commande, _ = commande_livree(client, produit)
    autre = Utilisateur.objects.create_user(
        email="marc@exemple.fr", password=MOT_DE_PASSE, nom="Marc", prenom="Test",
        role="CLIENT", statut_compte=StatutCompte.ACTIF,
    )
    Client.objects.create(utilisateur=autre)

    reponse = ouvrir_litige(client, commande, connecter(client, "marc@exemple.fr"))

    assert reponse.status_code == 404


# ── 2. La reponse du vendeur ─────────────────────────────────────────────

@pytest.mark.django_db
def test_le_vendeur_voit_le_litige_qui_le_concerne(client, lea, produit, boutique):
    commande, entetes = commande_livree(client, produit)
    ouvrir_litige(client, commande, entetes)

    reponse = client.get(reverse("litiges-vendeur"),
                         headers=connecter(client, "karim@exemple.fr"))

    dossiers = reponse.json()["data"]
    assert len(dossiers) == 1
    assert dossiers[0]["commande"] == commande.numero_commande
    # Il doit lire ce qu'on lui reproche, sinon il ne peut pas repondre.
    assert DESCRIPTION in dossiers[0]["description"]


@pytest.mark.django_db
def test_le_vendeur_donne_sa_version_et_le_dossier_passe_en_examen(client, lea, produit):
    commande, entetes = commande_livree(client, produit)
    dossier = ouvrir_litige(client, commande, entetes).json()["data"]

    reponse = client.post(
        reverse("repondre-litige", args=[dossier["id"]]), {"reponse": REPONSE},
        content_type="application/json", headers=connecter(client, "karim@exemple.fr"),
    )

    assert reponse.status_code == 200
    donnees = reponse.json()["data"]
    assert donnees["statut"] == StatutLitige.EN_COURS
    assert donnees["reponse_vendeur"] == REPONSE
    assert donnees["arbitrable"] is True, "les deux versions sont la"


@pytest.mark.django_db
def test_le_vendeur_ne_repond_qu_une_fois(client, lea, produit):
    """Ce n'est pas une messagerie : un echange sans fin retarde la decision."""
    commande, entetes = commande_livree(client, produit)
    dossier = ouvrir_litige(client, commande, entetes).json()["data"]
    vendeur = connecter(client, "karim@exemple.fr")
    client.post(reverse("repondre-litige", args=[dossier["id"]]), {"reponse": REPONSE},
                content_type="application/json", headers=vendeur)

    reponse = client.post(
        reverse("repondre-litige", args=[dossier["id"]]), {"reponse": "Je me suis trompe."},
        content_type="application/json", headers=vendeur,
    )

    assert reponse.status_code == 409
    assert reponse.json()["erreur"]["code"] == "deja_repondu"


@pytest.mark.django_db
def test_un_autre_vendeur_ne_voit_pas_le_dossier(client, lea, produit):
    commande, entetes = commande_livree(client, produit)
    dossier = ouvrir_litige(client, commande, entetes).json()["data"]
    intrus = Utilisateur.objects.create_user(
        email="amel@exemple.fr", password=MOT_DE_PASSE, nom="Amel", prenom="Test",
        role="VENDEUR", statut_compte=StatutCompte.ACTIF,
    )
    Vendeur.objects.create(
        utilisateur=intrus, nom_boutique="Chez Amel", type_activite=TypeService.EXPRESS,
        statut_validation=StatutValidation.VALIDE,
    )

    reponse = client.post(
        reverse("repondre-litige", args=[dossier["id"]]), {"reponse": REPONSE},
        content_type="application/json", headers=connecter(client, "amel@exemple.fr"),
    )

    assert reponse.status_code == 404


# ── 3. L'arbitrage ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_on_ne_tranche_pas_avant_d_avoir_entendu_le_vendeur(client, lea, produit, patronne):
    """Sans ce garde-fou, la procedure contradictoire n'est qu'un decor."""
    commande, entetes = commande_livree(client, produit)
    dossier = ouvrir_litige(client, commande, entetes).json()["data"]

    reponse = client.post(
        reverse("arbitrer-litige", args=[dossier["id"]]),
        {"decision": "REMBOURSER", "motivation": "Le client a raison."},
        content_type="application/json", headers=connecter(client, "admin@exemple.fr"),
    )

    assert reponse.status_code == 409
    assert reponse.json()["erreur"]["code"] == "vendeur_pas_encore_entendu"


@pytest.mark.django_db
def test_le_delai_passe_l_administrateur_tranche_avec_ce_qu_il_a(client, lea, produit, patronne):
    """Un vendeur silencieux ne doit pas bloquer un client indefiniment."""
    commande, entetes = commande_livree(client, produit)
    dossier = ouvrir_litige(client, commande, entetes).json()["data"]
    Litige.objects.filter(pk=dossier["id"]).update(
        date_limite_reponse=timezone.now() - timedelta(hours=1)
    )

    reponse = client.post(
        reverse("arbitrer-litige", args=[dossier["id"]]),
        {"decision": "REMBOURSER", "motivation": "La boutique n a pas repondu dans les temps."},
        content_type="application/json", headers=connecter(client, "admin@exemple.fr"),
    )

    assert reponse.status_code == 200
    assert reponse.json()["data"]["statut"] == StatutLitige.RESOLU


@pytest.mark.django_db
def test_une_decision_sans_motivation_est_refusee(client, lea, produit, patronne):
    """Une decision sans motif ne s'explique pas six mois plus tard."""
    commande, entetes = commande_livree(client, produit)
    dossier = ouvrir_litige(client, commande, entetes).json()["data"]
    client.post(reverse("repondre-litige", args=[dossier["id"]]), {"reponse": REPONSE},
                content_type="application/json", headers=connecter(client, "karim@exemple.fr"))

    reponse = client.post(
        reverse("arbitrer-litige", args=[dossier["id"]]), {"decision": "REFUSER"},
        content_type="application/json", headers=connecter(client, "admin@exemple.fr"),
    )

    assert reponse.status_code == 400
    assert reponse.json()["erreur"]["code"] == "motivation_requise"


@pytest.mark.django_db
def test_rembourser_ecrit_un_remboursement_et_solde_la_commande(client, lea, produit, patronne):
    commande, entetes = commande_livree(client, produit)
    dossier = ouvrir_litige(client, commande, entetes).json()["data"]
    client.post(reverse("repondre-litige", args=[dossier["id"]]), {"reponse": REPONSE},
                content_type="application/json", headers=connecter(client, "karim@exemple.fr"))

    reponse = client.post(
        reverse("arbitrer-litige", args=[dossier["id"]]),
        {"decision": "REMBOURSER", "motivation": "Deux articles manquants, photo a l appui."},
        content_type="application/json", headers=connecter(client, "admin@exemple.fr"),
    )

    assert reponse.status_code == 200
    paiement = Paiement.objects.get(commande=commande)
    remboursement = Remboursement.objects.get(paiement=paiement)
    assert remboursement.montant_centimes == paiement.montant_centimes
    assert remboursement.type == "TOTAL"

    commande.refresh_from_db()
    assert commande.statut_actuel == StatutCommande.REMBOURSEE
    assert RepartitionVendeur.objects.get(
        sous_commande__commande=commande
    ).statut == "REMBOURSE"


@pytest.mark.django_db
def test_un_remboursement_partiel_ne_solde_pas_la_commande(client, lea, produit, patronne):
    """Un article manquant sur cinq ne renverse pas toute la vente."""
    commande, entetes = commande_livree(client, produit)
    dossier = ouvrir_litige(client, commande, entetes).json()["data"]
    client.post(reverse("repondre-litige", args=[dossier["id"]]), {"reponse": REPONSE},
                content_type="application/json", headers=connecter(client, "karim@exemple.fr"))

    reponse = client.post(
        reverse("arbitrer-litige", args=[dossier["id"]]),
        {"decision": "REMBOURSER", "montant_centimes": 1290,
         "motivation": "Un seul article manquait sur les deux."},
        content_type="application/json", headers=connecter(client, "admin@exemple.fr"),
    )

    assert reponse.json()["data"]["montant_rembourse_centimes"] == 1290
    assert Remboursement.objects.get().type == "PARTIEL"
    commande.refresh_from_db()
    assert commande.statut_actuel == StatutCommande.LIVREE, "la vente tient encore"


@pytest.mark.django_db
def test_on_ne_rembourse_pas_plus_que_ce_qui_a_ete_paye(client, lea, produit, patronne):
    commande, entetes = commande_livree(client, produit)
    dossier = ouvrir_litige(client, commande, entetes).json()["data"]
    client.post(reverse("repondre-litige", args=[dossier["id"]]), {"reponse": REPONSE},
                content_type="application/json", headers=connecter(client, "karim@exemple.fr"))

    reponse = client.post(
        reverse("arbitrer-litige", args=[dossier["id"]]),
        {"decision": "REMBOURSER", "montant_centimes": 999_999,
         "motivation": "Une tentative de remboursement fantaisiste."},
        content_type="application/json", headers=connecter(client, "admin@exemple.fr"),
    )

    assert reponse.status_code == 400
    assert reponse.json()["erreur"]["code"] == "montant_invalide"
    assert not Remboursement.objects.exists()


@pytest.mark.django_db
def test_refuser_rend_le_versement_au_vendeur(client, lea, produit, patronne):
    """Un litige rejete doit debloquer l'argent, sinon il reste gele pour rien."""
    commande, entetes = commande_livree(client, produit)
    dossier = ouvrir_litige(client, commande, entetes).json()["data"]
    client.post(reverse("repondre-litige", args=[dossier["id"]]), {"reponse": REPONSE},
                content_type="application/json", headers=connecter(client, "karim@exemple.fr"))

    reponse = client.post(
        reverse("arbitrer-litige", args=[dossier["id"]]),
        {"decision": "REFUSER", "motivation": "La photo de preparation montre le colis complet."},
        content_type="application/json", headers=connecter(client, "admin@exemple.fr"),
    )

    assert reponse.json()["data"]["statut"] == StatutLitige.REJETE
    assert RepartitionVendeur.objects.get(
        sous_commande__commande=commande
    ).statut == "TRANSFERE"
    assert not Remboursement.objects.exists()


@pytest.mark.django_db
def test_un_dossier_tranche_ne_se_retranche_pas(client, lea, produit, patronne):
    commande, entetes = commande_livree(client, produit)
    dossier = ouvrir_litige(client, commande, entetes).json()["data"]
    client.post(reverse("repondre-litige", args=[dossier["id"]]), {"reponse": REPONSE},
                content_type="application/json", headers=connecter(client, "karim@exemple.fr"))
    admin = connecter(client, "admin@exemple.fr")
    client.post(reverse("arbitrer-litige", args=[dossier["id"]]),
                {"decision": "REFUSER", "motivation": "Le colis etait complet au depart."},
                content_type="application/json", headers=admin)

    reponse = client.post(
        reverse("arbitrer-litige", args=[dossier["id"]]),
        {"decision": "REMBOURSER", "motivation": "Revirement."},
        content_type="application/json", headers=admin,
    )

    assert reponse.status_code == 409
    assert reponse.json()["erreur"]["code"] == "litige_clos"


@pytest.mark.django_db
def test_un_client_ne_peut_pas_arbitrer_son_propre_litige(client, lea, produit, patronne):
    commande, entetes = commande_livree(client, produit)
    dossier = ouvrir_litige(client, commande, entetes).json()["data"]

    reponse = client.post(
        reverse("arbitrer-litige", args=[dossier["id"]]),
        {"decision": "REMBOURSER", "motivation": "Je me rembourse moi-meme."},
        content_type="application/json", headers=entetes,
    )

    assert reponse.status_code == 403


# ── 4. Les deux parties sont prevenues ───────────────────────────────────

@pytest.mark.django_db
def test_les_deux_parties_recoivent_la_meme_decision(client, lea, produit, boutique, patronne):
    """N'en prevenir qu'une est la facon la plus sure de creer un second litige."""
    from engagement.models import Notification

    commande, entetes = commande_livree(client, produit)
    dossier = ouvrir_litige(client, commande, entetes).json()["data"]
    client.post(reverse("repondre-litige", args=[dossier["id"]]), {"reponse": REPONSE},
                content_type="application/json", headers=connecter(client, "karim@exemple.fr"))
    client.post(reverse("arbitrer-litige", args=[dossier["id"]]),
                {"decision": "REMBOURSER", "motivation": "Deux articles manquaient."},
                content_type="application/json", headers=connecter(client, "admin@exemple.fr"))

    tranchees = Notification.objects.filter(type="LITIGE_TRANCHE")
    destinataires = {notification.utilisateur_id for notification in tranchees}
    assert lea.utilisateur_id in destinataires
    assert boutique.utilisateur_id in destinataires


@pytest.mark.django_db
def test_le_vendeur_est_prevenu_de_l_ouverture(client, lea, produit, boutique):
    """Sans notification, le delai de 48 heures courrait a son insu."""
    from engagement.models import Notification

    commande, entetes = commande_livree(client, produit)
    ouvrir_litige(client, commande, entetes)

    notification = Notification.objects.get(type="LITIGE_OUVERT")
    assert notification.utilisateur_id == boutique.utilisateur_id
    assert "48" in notification.contenu
