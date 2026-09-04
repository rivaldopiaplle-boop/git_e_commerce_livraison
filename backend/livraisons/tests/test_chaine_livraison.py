"""D'ou sort une course, et d'ou sort une tournee — O-5.

**Le trou le plus grave du bloc O**, et il ne se voyait pas : rien ne creait de
`Livraison` en dehors du jeu de demonstration. Une commande payee, preparee et
marquee prete n'arrivait chez aucun livreur.

Tes trois formulations du meme defaut :

  · *« je n'ai pas vu de commande a livrer disponible quand le livreur est
    libre »* ;
  · *« la distance du trajet et le prix pour vous ne sont pas vraiment
    calcules, ca sort de nulle part »* ;
  · *« je ne comprends pas d'ou sort la tournee du livreur »*.

Ce fichier suit la chaine complete : le vendeur prepare, l'entrepot recoit,
la tournee se calcule, un livreur la prend.
"""
import pytest
from django.urls import reverse

from catalogue.models import Produit
from commandes.models import (
    Commande,
    LigneCommande,
    SousCommande,
    StatutCommande,
    StatutPreparation,
)
from comptes.models import (
    Adresse,
    AdresseClient,
    Client,
    Gestionnaire,
    Livreur,
    StatutCompte,
    StatutValidation,
    Utilisateur,
    Vendeur,
)
from livraisons.attribution import creer_livraison
from livraisons.models import Entrepot, Livraison, StatutLivraison, StatutTournee, Tournee
from livraisons.tarifs import BAREME, remuneration

MOT_DE_PASSE = "Demonstration!2026"


def _utilisateur(email, role):
    return Utilisateur.objects.create_user(
        email=email, password=MOT_DE_PASSE, nom="Essai", prenom=email.split("@")[0],
        role=role, statut_compte=StatutCompte.ACTIF,
    )


def connecter(client, email):
    reponse = client.post(
        reverse("connexion"), {"email": email, "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json",
    )
    return {"Authorization": f"Bearer {reponse.json()['data']['acces']}"}


@pytest.fixture
def scene(db):
    """Un entrepot, une boutique Standard, une cliente, une commande payee."""
    adresse_entrepot = Adresse.objects.create(
        rue="12 rue de la Logistique", code_postal="69100", ville="Villeurbanne",
        latitude=45.7719, longitude=4.8902,
    )
    entrepot = Entrepot.objects.create(
        nom="Entrepot Lyon-Est", adresse=adresse_entrepot, est_actif=True,
    )
    adresse_client = Adresse.objects.create(
        libelle="Domicile", rue="8 rue Victor Hugo", code_postal="69002", ville="Lyon",
        latitude=45.7545, longitude=4.8480,
    )
    cliente = Client.objects.create(utilisateur=_utilisateur("cliente@exemple.fr", "CLIENT"))
    AdresseClient.objects.create(client=cliente, adresse=adresse_client, est_principale=True)

    boutique = Vendeur.objects.create(
        utilisateur=_utilisateur("boutique@exemple.fr", "VENDEUR"),
        nom_boutique="Maison Perrin", type_activite="STANDARD",
        statut_validation=StatutValidation.VALIDE,
        adresse=Adresse.objects.create(
            rue="3 rue des Artisans", code_postal="69003", ville="Lyon",
            latitude=45.7600, longitude=4.8600,
        ),
    )
    produit = Produit.objects.create(
        vendeur=boutique, nom="Miel", description="x", prix_unitaire_centimes=900,
        stock_disponible=20, seuil_alerte=1,
    )

    gestionnaire = Gestionnaire.objects.create(
        utilisateur=_utilisateur("entrepot@exemple.fr", "GESTIONNAIRE"),
        type_gestionnaire="STAFF_ENTREPOT", entrepot=entrepot,
    )
    livreur = Livreur.objects.create(
        utilisateur=_utilisateur("julien@exemple.fr", "LIVREUR"),
        mode_livraison="STANDARD", statut_validation=StatutValidation.VALIDE,
        entrepot=entrepot,
    )
    express = Livreur.objects.create(
        utilisateur=_utilisateur("amine@exemple.fr", "LIVREUR"),
        mode_livraison="EXPRESS", statut_validation=StatutValidation.VALIDE,
    )

    commande = Commande.objects.create(
        numero_commande="RD-TEST-CHAINE", client=cliente, adresse_livraison=adresse_client,
        type_service="STANDARD", statut_actuel=StatutCommande.PAYEE,
        montant_produits_centimes=1800, montant_livraison_centimes=490,
        montant_total_centimes=2290,
    )
    sous = SousCommande.objects.create(
        commande=commande, vendeur=boutique,
        statut_preparation=StatutPreparation.A_PREPARER,
        montant_vendeur_centimes=1530, montant_commission_centimes=270,
    )
    LigneCommande.objects.create(
        sous_commande=sous, produit=produit, nom_produit_capture=produit.nom,
        prix_unitaire_centimes=900, quantite=2, sous_total_centimes=1800,
    )
    return {"entrepot": entrepot, "commande": commande, "sous": sous,
            "boutique": boutique, "livreur": livreur, "express": express,
            "gestionnaire": gestionnaire, "cliente": cliente}


class TestUneCommandePreteDevientUneCourse:
    def test_marquer_prete_cree_la_livraison(self, client, scene):
        """Le chainon qui manquait : rien ne creait de course en dehors du
        jeu de demonstration."""
        entetes = connecter(client, "boutique@exemple.fr")
        for statut in ("EN_PREPARATION", "PRETE"):
            client.patch(
                reverse("avancer-preparation", args=[scene["sous"].id]),
                {"statut": statut}, content_type="application/json", headers=entetes,
            )

        livraison = Livraison.objects.get(commande=scene["commande"])
        assert livraison.statut_livraison == StatutLivraison.A_ATTRIBUER
        assert livraison.code_confirmation, "le code de remise doit exister"

    def test_la_distance_est_calculee_et_non_tiree_au_hasard(self, scene):
        """« Ca sort de nulle part » : le peuplement tirait un nombre entre
        0,8 et 7,5 km, sans rapport avec les adresses."""
        livraison = creer_livraison(scene["commande"])

        # Villeurbanne -> Lyon 2e : de l'ordre de 4 km a vol d'oiseau, majore
        # du detour urbain.
        assert livraison.distance_km is not None
        assert 3 < float(livraison.distance_km) < 8

    def test_la_remuneration_suit_le_bareme_publie(self, scene):
        livraison = creer_livraison(scene["commande"])
        attendu, _ = remuneration("STANDARD", livraison.distance_km)

        assert livraison.remuneration_livreur_centimes == attendu
        assert attendu >= BAREME["STANDARD"]["minimum_centimes"]

    def test_le_calcul_s_explique_en_une_phrase(self, scene):
        """Un livreur doit pouvoir verifier ce qu'on lui doit."""
        _, detail = remuneration("STANDARD", 4.0)

        assert "de base" in detail
        assert "EUR/km" in detail

    def test_creer_deux_fois_ne_fait_pas_deux_courses(self, scene):
        """Un vendeur qui refait passer sa part a PRETE ne doit pas engendrer
        une deuxieme course."""
        premiere = creer_livraison(scene["commande"])
        seconde = creer_livraison(scene["commande"])

        assert premiere.id == seconde.id
        assert Livraison.objects.filter(commande=scene["commande"]).count() == 1

    def test_sans_coordonnees_on_paie_le_minimum_sans_inventer(self, scene):
        """Une distance fausse sur une fiche de paie est pire qu'une distance
        absente."""
        adresse = scene["commande"].adresse_livraison
        adresse.latitude = adresse.longitude = None
        adresse.save(update_fields=["latitude", "longitude"])

        livraison = creer_livraison(scene["commande"])

        assert livraison.distance_km is None
        assert livraison.remuneration_livreur_centimes == \
            BAREME["STANDARD"]["minimum_centimes"]


class TestLEntrepotRecoitEtMonteSaTournee:
    def _jusqu_a_l_entrepot(self, client, scene):
        vendeur = connecter(client, "boutique@exemple.fr")
        for statut in ("EN_PREPARATION", "PRETE", "EXPEDIEE"):
            client.patch(
                reverse("avancer-preparation", args=[scene["sous"].id]),
                {"statut": statut}, content_type="application/json", headers=vendeur,
            )
        scene["sous"].refresh_from_db()
        return connecter(client, "entrepot@exemple.fr")

    def test_expedier_rattache_le_colis_a_un_entrepot(self, client, scene):
        """« Expedier vers l'entrepot » n'expediait vers aucun entrepot : le
        champ n'etait rempli que par le jeu de demonstration."""
        self._jusqu_a_l_entrepot(client, scene)

        assert scene["sous"].entrepot_id == scene["entrepot"].id
        assert scene["sous"].date_expedition_entrepot is not None

    def test_le_colis_apparait_sur_l_ecran_de_l_entrepot(self, client, scene):
        entetes = self._jusqu_a_l_entrepot(client, scene)

        donnees = client.get(reverse("colis-recus"), headers=entetes).json()["data"]

        assert donnees["total"] == 1
        assert donnees["groupes"][0]["vendeur"] == "Maison Perrin"

    def test_on_ne_charge_pas_un_colis_qui_n_est_pas_arrive(self, client, scene):
        """Charger un colis que le vendeur n'a pas expedie enverrait le livreur
        chercher du vide."""
        creer_livraison(scene["commande"])
        entetes = connecter(client, "entrepot@exemple.fr")

        reponse = client.post(reverse("calculer-tournee"), {},
                              content_type="application/json", headers=entetes)

        assert reponse.status_code == 409
        assert reponse.json()["erreur"]["code"] == "rien_a_charger"

    def test_la_tournee_se_calcule_a_la_demande(self, client, scene):
        entetes = self._jusqu_a_l_entrepot(client, scene)
        client.post(reverse("confirmer-reception", args=[scene["sous"].id]), {},
                    content_type="application/json", headers=entetes)

        reponse = client.post(reverse("calculer-tournee"), {},
                              content_type="application/json", headers=entetes)

        assert reponse.status_code == 200
        donnees = reponse.json()["data"]
        assert donnees["nombre_arrets"] == 1
        assert donnees["statut"] == StatutTournee.BROUILLON
        assert float(donnees["distance_totale_km"]) > 0

    def test_le_calcul_se_rejoue_autant_qu_on_veut(self, client, scene):
        """*« Il peut le refaire quand il veut, et le resultat peut differer. »*"""
        entetes = self._jusqu_a_l_entrepot(client, scene)
        client.post(reverse("confirmer-reception", args=[scene["sous"].id]), {},
                    content_type="application/json", headers=entetes)
        premiere = client.post(reverse("calculer-tournee"), {},
                               content_type="application/json",
                               headers=entetes).json()["data"]

        seconde = client.post(reverse("calculer-tournee"),
                              {"id_tournee": premiere["id"]},
                              content_type="application/json",
                              headers=entetes).json()["data"]

        assert seconde["id"] == premiere["id"]
        assert seconde["nombre_arrets"] == 1
        # Et surtout : pas de doublon d'arret apres un recalcul.
        assert Tournee.objects.get(pk=premiere["id"]).arrets.count() == 1

    def test_la_reception_recalcule_la_distance_sur_le_vrai_depart(self, client, scene):
        """L'entrepot n'est une hypothese qu'au moment de la commande : quand le
        colis arrive, il ne l'est plus."""
        entetes = self._jusqu_a_l_entrepot(client, scene)

        reponse = client.post(reverse("confirmer-reception", args=[scene["sous"].id]), {},
                              content_type="application/json", headers=entetes)

        donnees = reponse.json()["data"]
        assert donnees["statut_commande"] == StatutCommande.RECUE_ENTREPOT
        assert donnees["distance_km"] is not None
        assert donnees["remuneration_centimes"] > 0


class TestConfierLaTournee:
    @pytest.fixture
    def tournee_prete(self, client, scene):
        vendeur = connecter(client, "boutique@exemple.fr")
        for statut in ("EN_PREPARATION", "PRETE", "EXPEDIEE"):
            client.patch(
                reverse("avancer-preparation", args=[scene["sous"].id]),
                {"statut": statut}, content_type="application/json", headers=vendeur,
            )
        entetes = connecter(client, "entrepot@exemple.fr")
        client.post(reverse("confirmer-reception", args=[scene["sous"].id]), {},
                    content_type="application/json", headers=entetes)
        tournee = client.post(reverse("calculer-tournee"), {},
                              content_type="application/json",
                              headers=entetes).json()["data"]
        return tournee, entetes

    def test_un_livreur_express_ne_prend_pas_de_tournee(self, client, scene, tournee_prete):
        """Une journee perdue pour lui et pour les clients."""
        tournee, entetes = tournee_prete

        reponse = client.post(
            reverse("attribuer-tournee", args=[tournee["id"]]),
            {"id_livreur": scene["express"].id},
            content_type="application/json", headers=entetes,
        )

        assert reponse.status_code == 409
        assert reponse.json()["erreur"]["code"] == "mauvais_mode"

    def test_la_liste_ne_propose_que_des_livreurs_standard(self, client, scene,
                                                           tournee_prete):
        """Proposer un choix qu'on refusera ensuite est une erreur qu'on
        laisse faire."""
        _, entetes = tournee_prete

        proposes = client.get(reverse("livreurs-pour-tournee"),
                              headers=entetes).json()["data"]

        assert [livreur["id"] for livreur in proposes] == [scene["livreur"].id]

    def test_attribuer_previent_le_livreur_et_marque_ses_courses(self, client, scene,
                                                                 tournee_prete):
        from engagement.models import Notification

        tournee, entetes = tournee_prete

        client.post(
            reverse("attribuer-tournee", args=[tournee["id"]]),
            {"id_livreur": scene["livreur"].id},
            content_type="application/json", headers=entetes,
        )

        assert Tournee.objects.get(pk=tournee["id"]).statut == StatutTournee.AFFECTEE
        assert Livraison.objects.get(commande=scene["commande"]).livreur_id == \
            scene["livreur"].id
        assert Notification.objects.filter(
            utilisateur=scene["livreur"].utilisateur
        ).exists()

    def test_une_tournee_partie_ne_se_recalcule_plus(self, client, scene, tournee_prete):
        """On ne reordonne pas les arrets de quelqu'un qui roule."""
        tournee, entetes = tournee_prete
        client.post(reverse("attribuer-tournee", args=[tournee["id"]]),
                    {"id_livreur": scene["livreur"].id},
                    content_type="application/json", headers=entetes)
        client.post(reverse("faire-partir-tournee", args=[tournee["id"]]), {},
                    content_type="application/json", headers=entetes)

        reponse = client.post(reverse("calculer-tournee"), {"id_tournee": tournee["id"]},
                              content_type="application/json", headers=entetes)

        assert reponse.status_code == 409
        assert reponse.json()["erreur"]["code"] == "tournee_partie"

    def test_une_tournee_ne_part_pas_sans_livreur(self, client, scene, tournee_prete):
        tournee, entetes = tournee_prete

        reponse = client.post(reverse("faire-partir-tournee", args=[tournee["id"]]), {},
                              content_type="application/json", headers=entetes)

        assert reponse.json()["erreur"]["code"] == "sans_livreur"

    def test_le_depart_fait_avancer_la_commande_du_client(self, client, scene,
                                                          tournee_prete):
        """La synchronisation dans l'autre sens : le client voit sa commande
        partir sans avoir rien fait (O-5)."""
        tournee, entetes = tournee_prete
        client.post(reverse("attribuer-tournee", args=[tournee["id"]]),
                    {"id_livreur": scene["livreur"].id},
                    content_type="application/json", headers=entetes)
        client.post(reverse("faire-partir-tournee", args=[tournee["id"]]), {},
                    content_type="application/json", headers=entetes)

        scene["commande"].refresh_from_db()
        assert scene["commande"].statut_actuel == StatutCommande.EN_TOURNEE

    def test_le_personnel_d_une_boutique_ne_monte_pas_de_tournee(self, client, scene, db):
        """Vendeur et entrepot sont tous deux « gestionnaires » (D-05), et ils
        ne font pas le meme metier."""
        Gestionnaire.objects.create(
            utilisateur=_utilisateur("boutique.staff@exemple.fr", "GESTIONNAIRE"),
            type_gestionnaire="STAFF_VENDEUR", vendeur=scene["boutique"],
        )

        reponse = client.post(reverse("calculer-tournee"), {},
                              content_type="application/json",
                              headers=connecter(client, "boutique.staff@exemple.fr"))

        assert reponse.status_code == 403
