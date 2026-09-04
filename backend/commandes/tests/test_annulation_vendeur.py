"""L'annulation d'une part de commande par son vendeur — D-07, D-81, D-144.

Le bouton « Annuler » posait le statut `ANNULEE` sur la sous-commande, et rien
d'autre. Quand un restaurant annulait :

  · le client n'etait prevenu de rien, et sa commande restait « payee » ;
  · son argent restait pris ;
  · le stock ne revenait pas a la vente ;
  · aucun motif n'etait demande, alors que D-07 l'exige depuis le debut.

Chacun de ces quatre points a son test. Ils echouent tous sur l'ancien code.
"""
import pytest
from django.urls import reverse

from catalogue.models import MouvementStock, Produit, TypeMouvement
from commandes.models import (
    Commande,
    LigneCommande,
    SousCommande,
    StatutCommande,
    StatutPreparation,
)
from comptes.models import Adresse, Client, StatutCompte, Utilisateur, Vendeur
from engagement.models import Notification
from paiements.models import Paiement, Remboursement, RepartitionVendeur, StatutPaiement

MOT_DE_PASSE = "Demonstration!2026"


def _utilisateur(email, role, **extra):
    return Utilisateur.objects.create_user(
        email=email, password=MOT_DE_PASSE, nom="Essai", prenom=email.split("@")[0],
        role=role, statut_compte=StatutCompte.ACTIF, **extra,
    )


@pytest.fixture
def scene(db):
    """Une commande payee, deux boutiques, chacune sa part."""
    adresse = Adresse.objects.create(
        libelle="Domicile", rue="8 rue Victor Hugo", code_postal="69002",
        ville="Lyon", latitude=45.755, longitude=4.832,
    )
    client = Client.objects.create(utilisateur=_utilisateur("cliente@exemple.fr", "CLIENT"))

    boutiques, produits = [], []
    for rang, nom in enumerate(("Chez Karim", "TechSophie"), start=1):
        vendeur = Vendeur.objects.create(
            utilisateur=_utilisateur(f"vendeur{rang}@exemple.fr", "VENDEUR"),
            nom_boutique=nom, type_activite="STANDARD", statut_validation="VALIDE",
            adresse=adresse,
        )
        boutiques.append(vendeur)
        produits.append(Produit.objects.create(
            vendeur=vendeur, nom=f"Produit {rang}", description="x",
            prix_unitaire_centimes=1000, stock_disponible=10, seuil_alerte=1,
        ))

    commande = Commande.objects.create(
        numero_commande="RD-TEST-000001", client=client, adresse_livraison=adresse,
        type_service="STANDARD", statut_actuel=StatutCommande.PAYEE,
        montant_produits_centimes=4000, montant_livraison_centimes=0,
        montant_total_centimes=4000,
    )
    paiement = Paiement.objects.create(
        commande=commande, montant_centimes=4000,
        statut_paiement=StatutPaiement.CAPTURE, reference_stripe="pi_sim_essai",
    )

    parts = []
    for vendeur, produit in zip(boutiques, produits, strict=True):
        sous = SousCommande.objects.create(
            commande=commande, vendeur=vendeur,
            statut_preparation=StatutPreparation.A_PREPARER,
            montant_vendeur_centimes=1700, montant_commission_centimes=300,
        )
        LigneCommande.objects.create(
            sous_commande=sous, produit=produit, nom_produit_capture=produit.nom,
            prix_unitaire_centimes=1000, quantite=2, sous_total_centimes=2000,
        )
        RepartitionVendeur.objects.create(
            paiement=paiement, sous_commande=sous, vendeur=vendeur,
            montant_vendeur_centimes=1700, montant_commission_centimes=300,
        )
        parts.append(sous)

    return {"commande": commande, "client": client, "parts": parts,
            "produits": produits, "boutiques": boutiques, "paiement": paiement}


def connecte(client_http, utilisateur):
    reponse = client_http.post(
        reverse("connexion"), {"email": utilisateur.email, "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {reponse.json()['data']['acces']}"}


def annuler(client_http, entetes, sous, **corps):
    return client_http.patch(
        reverse("avancer-preparation", args=[sous.id]),
        {"statut": "ANNULEE", **corps}, content_type="application/json", **entetes,
    )


class TestLeMotifEstObligatoire:
    """D-07 l'exigeait depuis le debut du projet. Il n'existait pas."""

    def test_sans_motif_c_est_refuse(self, client, scene):
        entetes = connecte(client, scene["boutiques"][0].utilisateur)

        reponse = annuler(client, entetes, scene["parts"][0])

        assert reponse.status_code == 400
        assert reponse.json()["erreur"]["code"] == "motif_invalide"
        scene["parts"][0].refresh_from_db()
        assert scene["parts"][0].statut_preparation == StatutPreparation.A_PREPARER

    def test_un_motif_hors_liste_est_refuse(self, client, scene):
        """Une liste fermee se compte : « annule » en texte libre ne dit rien."""
        entetes = connecte(client, scene["boutiques"][0].utilisateur)

        reponse = annuler(client, entetes, scene["parts"][0],
                          motif="PARCE_QUE", explication="Une explication assez longue.")

        assert reponse.status_code == 400
        assert reponse.json()["erreur"]["code"] == "motif_invalide"

    def test_une_explication_trop_courte_est_refusee(self, client, scene):
        """C'est ce texte que le client lit : « rupture » ne lui apprend rien."""
        entetes = connecte(client, scene["boutiques"][0].utilisateur)

        reponse = annuler(client, entetes, scene["parts"][0],
                          motif="RUPTURE", explication="rupture")

        assert reponse.status_code == 400
        assert reponse.json()["erreur"]["code"] == "explication_trop_courte"


@pytest.fixture
def annulee(client, scene):
    """Une premiere part annulee dans les regles."""
    entetes = connecte(client, scene["boutiques"][0].utilisateur)
    reponse = annuler(client, entetes, scene["parts"][0], motif="RUPTURE",
                      explication="Il ne me reste plus ce produit, desole.")
    assert reponse.status_code == 200, reponse.json()
    return reponse


class TestCeQueLAnnulationDeclenche:
    def test_le_client_est_rembourse_de_SA_part_seulement(self, annulee, scene):
        """Deux boutiques, une seule annule : rembourser tout serait aussi faux
        que ne rien rembourser."""
        remboursements = Remboursement.objects.filter(paiement=scene["paiement"])

        assert remboursements.count() == 1
        assert remboursements.first().montant_centimes == 2000
        assert annulee.json()["data"]["montant_rembourse_centimes"] == 2000

    def test_le_stock_revient_a_la_vente_avec_sa_trace(self, annulee, scene):
        """Un stock qui remonte sans explication est aussi inexplicable qu'un
        stock qui baisse sans explication (scenario 4.4)."""
        produit = scene["produits"][0]
        produit.refresh_from_db()

        assert produit.stock_disponible == 12
        mouvement = MouvementStock.objects.get(produit=produit)
        assert mouvement.type == TypeMouvement.ANNULATION
        assert mouvement.quantite == 2
        assert mouvement.stock_apres == 12
        assert scene["commande"].numero_commande in mouvement.motif

    def test_le_client_est_prevenu_avec_l_explication_du_vendeur(self, annulee, scene):
        """La notification forte de D-07. Le client n'apprenait rien du tout."""
        notification = Notification.objects.filter(
            utilisateur=scene["client"].utilisateur
        ).order_by("-id").first()

        assert notification is not None
        assert "Chez Karim" in notification.titre
        assert "Il ne me reste plus ce produit" in notification.contenu
        assert "20.00 EUR" in notification.contenu
        # Ce qui reste compte autant que ce qui tombe.
        assert "suit son cours" in notification.contenu

    def test_le_vendeur_qui_annule_n_est_pas_paye(self, annulee, scene):
        """Evident, et pourtant sa repartition restait « a transferer »."""
        repartition = RepartitionVendeur.objects.get(sous_commande=scene["parts"][0])

        assert repartition.statut == "ANNULE"
        # Celle de l'autre boutique ne bouge pas : elle livre.
        assert RepartitionVendeur.objects.get(
            sous_commande=scene["parts"][1]
        ).statut == "EN_ATTENTE"

    def test_l_autre_boutique_n_est_pas_touchee(self, annulee, scene):
        autre = scene["parts"][1]
        autre.refresh_from_db()
        scene["produits"][1].refresh_from_db()

        assert autre.statut_preparation == StatutPreparation.A_PREPARER
        assert scene["produits"][1].stock_disponible == 10

    def test_la_commande_ne_tombe_pas_tant_qu_une_part_subsiste(self, annulee, scene):
        scene["commande"].refresh_from_db()

        assert scene["commande"].statut_actuel == StatutCommande.PAYEE

    def test_l_annulation_est_tracee_avec_son_motif(self, annulee, scene):
        from commandes.models import HistoriqueStatut, TypeObjetSuivi

        trace = HistoriqueStatut.objects.filter(
            type_objet=TypeObjetSuivi.SOUS_COMMANDE, id_objet=scene["parts"][0].id,
            statut_apres=StatutPreparation.ANNULEE,
        ).first()

        assert trace is not None
        assert "Produit finalement indisponible" in trace.commentaire
        assert trace.utilisateur == scene["boutiques"][0].utilisateur


class TestQuandToutTombe:
    def test_la_derniere_annulation_fait_tomber_la_commande(self, client, scene, annulee):
        entetes = connecte(client, scene["boutiques"][1].utilisateur)

        reponse = annuler(client, entetes, scene["parts"][1], motif="FERMETURE",
                          explication="Nous sommes fermes cette semaine.")

        assert reponse.status_code == 200
        scene["commande"].refresh_from_db()
        assert scene["commande"].statut_actuel == StatutCommande.REMBOURSEE

    def test_on_ne_rembourse_jamais_plus_que_ce_qui_a_ete_paye(self, client, scene, annulee):
        entetes = connecte(client, scene["boutiques"][1].utilisateur)
        annuler(client, entetes, scene["parts"][1], motif="FERMETURE",
                explication="Nous sommes fermes cette semaine.")

        total = sum(
            remboursement.montant_centimes
            for remboursement in Remboursement.objects.filter(paiement=scene["paiement"])
        )

        assert total <= scene["paiement"].montant_centimes


class TestCeQuiNeSAnnulePlus:
    def test_une_part_prete_ne_s_annule_pas_ici(self, client, scene):
        """Le colis est fait : c'est un litige, pas une annulation."""
        sous = scene["parts"][0]
        sous.statut_preparation = StatutPreparation.PRETE
        sous.save(update_fields=["statut_preparation"])
        entetes = connecte(client, scene["boutiques"][0].utilisateur)

        reponse = annuler(client, entetes, sous, motif="RUPTURE",
                          explication="Il ne me reste plus ce produit, desole.")

        # La machine a etats refuse deja la transition PRETE -> ANNULEE.
        assert reponse.status_code == 409
        sous.refresh_from_db()
        assert sous.statut_preparation == StatutPreparation.PRETE

    def test_annuler_deux_fois_ne_rembourse_pas_deux_fois(self, client, scene, annulee):
        entetes = connecte(client, scene["boutiques"][0].utilisateur)

        annuler(client, entetes, scene["parts"][0], motif="RUPTURE",
                explication="Il ne me reste plus ce produit, desole.")

        assert Remboursement.objects.filter(paiement=scene["paiement"]).count() == 1
        assert MouvementStock.objects.filter(produit=scene["produits"][0]).count() == 1


class TestLeVocabulaireSuitLeCircuit:
    """D-81 : un restaurant et un expediteur de colis ne font pas le meme geste."""

    def _libelles(self, client, scene, type_service):
        commande = scene["commande"]
        commande.type_service = type_service
        commande.save(update_fields=["type_service"])
        entetes = connecte(client, scene["boutiques"][0].utilisateur)
        reponse = client.get(reverse("commandes-recues"), **entetes)
        return next(
            entree for entree in reponse.json()["data"]
            if entree["id"] == scene["parts"][0].id
        )

    def test_un_restaurant_met_en_preparation(self, client, scene):
        ligne = self._libelles(client, scene, "EXPRESS")

        assert ligne["libelles_suites"]["EN_PREPARATION"] == "Mettre en preparation"

    def test_un_expediteur_prepare_un_colis(self, client, scene):
        ligne = self._libelles(client, scene, "STANDARD")

        assert ligne["libelles_suites"]["EN_PREPARATION"] == "Preparer le colis"

    def test_le_temps_d_attente_est_donne_avec_son_delai(self, client, scene):
        """Une file ou tout se ressemble se traite dans le desordre."""
        ligne = self._libelles(client, scene, "EXPRESS")

        assert ligne["attente"]["minutes"] is not None
        assert ligne["attente"]["delai_minutes"] == 20
        assert ligne["attente"]["en_retard"] is False

    def test_une_part_terminee_n_attend_plus(self, client, scene):
        """Compter le temps d'attente d'un colis expedie n'a pas de sens."""
        sous = scene["parts"][0]
        sous.statut_preparation = StatutPreparation.EXPEDIEE
        sous.save(update_fields=["statut_preparation"])

        ligne = self._libelles(client, scene, "STANDARD")

        assert ligne["attente"]["minutes"] is None
        assert ligne["attente"]["en_retard"] is False
