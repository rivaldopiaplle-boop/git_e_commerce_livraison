"""L'accueil en un seul appel, et ce qu'il montre — O-1, O-2, O-5.

Ton reproche : *« les onglets menus sont tres peu remplis, surtout le premier
onglet accueil »*, et surtout *« rien n'est synchronise et dynamique »*.

Deux choses sont verrouillees ici :

  · **ce que l'accueil montre**, parce qu'un accueil a trois tuiles est le
    defaut qu'on vient de corriger ;
  · **la coherence entre l'accueil et les ecrans**. Le compteur « courses
    disponibles » de l'accueil et la liste de l'ecran « A proximite »
    annoncaient des choses differentes — sept ici, aucune la-bas — parce que
    deux calculs separes existaient. Un chiffre qui contredit la page suivante
    est pire qu'un chiffre absent.
"""
import pytest
from django.urls import reverse

from catalogue.models import Categorie, Produit
from commandes.models import Commande, LigneCommande, SousCommande, StatutCommande
from comptes.models import (
    Adresse,
    AdresseClient,
    Client,
    Livreur,
    StatutCompte,
    StatutDisponibilite,
    Utilisateur,
    Vendeur,
)
from livraisons.models import Livraison, StatutLivraison

MOT_DE_PASSE = "Demonstration!2026"


def _utilisateur(email, role):
    return Utilisateur.objects.create_user(
        email=email, password=MOT_DE_PASSE, nom="Essai", prenom=email.split("@")[0],
        role=role, statut_compte=StatutCompte.ACTIF,
    )


def connecte(client_http, utilisateur):
    reponse = client_http.post(
        reverse("connexion"), {"email": utilisateur.email, "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {reponse.json()['data']['acces']}"}


@pytest.fixture
def boutique(db):
    adresse = Adresse.objects.create(
        rue="1 rue du Marche", code_postal="69002", ville="Lyon",
        latitude=45.755, longitude=4.832,
    )
    return Vendeur.objects.create(
        utilisateur=_utilisateur("boutique@exemple.fr", "VENDEUR"),
        nom_boutique="Chez Karim", type_activite="EXPRESS",
        statut_validation="VALIDE", adresse=adresse, rayon_livraison_km=10,
    )


@pytest.fixture
def cliente(db, boutique):
    profil = Client.objects.create(utilisateur=_utilisateur("cliente@exemple.fr", "CLIENT"))
    adresse = Adresse.objects.create(
        libelle="Domicile", rue="8 rue Victor Hugo", code_postal="69002",
        ville="Lyon", latitude=45.757, longitude=4.834,
    )
    AdresseClient.objects.create(client=profil, adresse=adresse, est_principale=True)
    return profil


@pytest.fixture
def produits(boutique):
    categorie, _ = Categorie.objects.get_or_create(slug="plats", defaults={"nom": "Plats"})
    return [
        Produit.objects.create(
            vendeur=boutique, categorie=categorie, nom=f"Plat {rang}", description="x",
            prix_unitaire_centimes=1200, stock_disponible=10, seuil_alerte=1,
        )
        for rang in range(1, 4)
    ]


class TestLAccueilDuClient:
    def test_il_dit_ou_l_on_est_livre(self, client, cliente, produits):
        """C'est cette adresse qui decide des boutiques Express visibles (D-09)."""
        donnees = client.get(reverse("mon-accueil"),
                             **connecte(client, cliente.utilisateur)).json()["data"]

        assert donnees["role"] == "CLIENT"
        assert donnees["adresse"]["libelle"] == "Domicile"
        assert donnees["adresse"]["ville"] == "Lyon"

    def test_il_remplit_reellement_l_ecran(self, client, cliente, produits):
        """Le defaut d'origine : deux compteurs et un bouton."""
        donnees = client.get(reverse("mon-accueil"),
                             **connecte(client, cliente.utilisateur)).json()["data"]

        assert donnees["populaires"], "aucun produit a montrer"
        assert donnees["categories"], "aucune categorie a proposer"
        assert donnees["boutiques_express"], "aucune boutique proche"
        assert "panier" in donnees
        assert "compteurs" in donnees

    def test_les_boutiques_express_sont_triees_par_distance(self, client, cliente,
                                                            boutique, produits):
        loin = Vendeur.objects.create(
            utilisateur=_utilisateur("loin@exemple.fr", "VENDEUR"),
            nom_boutique="Loin d'ici", type_activite="EXPRESS", statut_validation="VALIDE",
            adresse=Adresse.objects.create(
                rue="1 rue lointaine", code_postal="69009", ville="Lyon",
                latitude=45.79, longitude=4.79,
            ),
            rayon_livraison_km=30,
        )
        categorie = Categorie.objects.get(slug="plats")
        Produit.objects.create(
            vendeur=loin, categorie=categorie, nom="Plat lointain", description="x",
            prix_unitaire_centimes=1000, stock_disponible=5, seuil_alerte=1,
        )

        donnees = client.get(reverse("mon-accueil"),
                             **connecte(client, cliente.utilisateur)).json()["data"]
        distances = [b["distance_km"] for b in donnees["boutiques_express"]]

        assert distances == sorted(distances)

    def test_le_code_de_remise_apparait_enfin_cote_client(self, client, cliente,
                                                          boutique, produits):
        """O-5 : *« le livreur a besoin que le client lui fournisse le code de
        remise, mais dans l'espace client je n'ai rien vu qui corresponde »*.

        Il etait genere et n'apparaissait nulle part. Un code qu'on ne peut pas
        lire n'est pas un code, c'est une porte fermee.
        """
        adresse = Adresse.objects.filter(adresseclient__client=cliente).first()
        commande = Commande.objects.create(
            numero_commande="RD-TEST-ACCUEIL", client=cliente, adresse_livraison=adresse,
            type_service="EXPRESS", statut_actuel=StatutCommande.EN_LIVRAISON,
            montant_produits_centimes=1200, montant_livraison_centimes=0,
            montant_total_centimes=1200,
        )
        sous = SousCommande.objects.create(commande=commande, vendeur=boutique)
        LigneCommande.objects.create(
            sous_commande=sous, produit=produits[0], nom_produit_capture=produits[0].nom,
            prix_unitaire_centimes=1200, quantite=1, sous_total_centimes=1200,
        )
        Livraison.objects.create(
            commande=commande, adresse_livraison=adresse,
            statut_livraison=StatutLivraison.EN_ROUTE, code_confirmation="4821",
        )

        donnees = client.get(reverse("mon-accueil"),
                             **connecte(client, cliente.utilisateur)).json()["data"]

        assert donnees["commande_en_cours"]["numero_commande"] == "RD-TEST-ACCUEIL"
        assert donnees["commande_en_cours"]["code_confirmation"] == "4821"

    def test_une_commande_terminee_n_est_plus_en_cours(self, client, cliente,
                                                       boutique, produits):
        adresse = Adresse.objects.filter(adresseclient__client=cliente).first()
        Commande.objects.create(
            numero_commande="RD-TEST-FINIE", client=cliente, adresse_livraison=adresse,
            type_service="EXPRESS", statut_actuel=StatutCommande.LIVREE,
            montant_produits_centimes=1200, montant_livraison_centimes=0,
            montant_total_centimes=1200,
        )

        donnees = client.get(reverse("mon-accueil"),
                             **connecte(client, cliente.utilisateur)).json()["data"]

        assert donnees["commande_en_cours"] is None
        assert donnees["compteurs"]["livrees"] == 1


class TestLAccueilDuLivreur:
    @pytest.fixture
    def coursier(self, db):
        return Livreur.objects.create(
            utilisateur=_utilisateur("coursier@exemple.fr", "LIVREUR"),
            mode_livraison="EXPRESS", statut_validation="VALIDE",
            statut_disponibilite=StatutDisponibilite.DISPONIBLE,
        )

    def test_il_montre_la_journee_et_non_le_cumul_de_toujours(self, client, coursier):
        """C'est ce qu'un livreur regarde le matin et le soir."""
        donnees = client.get(reverse("mon-accueil"),
                             **connecte(client, coursier.utilisateur)).json()["data"]

        assert donnees["role"] == "LIVREUR"
        assert set(donnees["aujourdhui"]) == {"courses", "gains_centimes", "distance_km"}

    def test_il_dit_si_le_compte_attend_encore_une_validation(self, client, db):
        """Sinon on voit un tableau de bord vide sans comprendre pourquoi."""
        attente = Livreur.objects.create(
            utilisateur=_utilisateur("attente@exemple.fr", "LIVREUR"),
            mode_livraison="EXPRESS", statut_validation="EN_ATTENTE",
        )

        donnees = client.get(reverse("mon-accueil"),
                             **connecte(client, attente.utilisateur)).json()["data"]

        assert donnees["statut_validation"] == "EN_ATTENTE"


@pytest.mark.django_db
class TestLeCompteurEtLaListeDisentLaMemeChose:
    """O-5 : sept courses sur l'accueil, aucune sur l'ecran suivant."""

    @pytest.fixture
    def coursier(self, db):
        return Livreur.objects.create(
            utilisateur=_utilisateur("coursier2@exemple.fr", "LIVREUR"),
            mode_livraison="EXPRESS", statut_validation="VALIDE",
            statut_disponibilite=StatutDisponibilite.DISPONIBLE,
        )

    @pytest.fixture
    def course_libre(self, cliente, boutique, produits):
        adresse = Adresse.objects.filter(adresseclient__client=cliente).first()
        commande = Commande.objects.create(
            numero_commande="RD-TEST-LIBRE", client=cliente, adresse_livraison=adresse,
            type_service="EXPRESS", statut_actuel=StatutCommande.PRETE,
            montant_produits_centimes=1200, montant_livraison_centimes=0,
            montant_total_centimes=1200,
        )
        SousCommande.objects.create(commande=commande, vendeur=boutique)
        return Livraison.objects.create(
            commande=commande, adresse_livraison=adresse,
            statut_livraison=StatutLivraison.A_ATTRIBUER,
        )

    def test_les_deux_comptent_pareil_quand_il_y_a_une_course(self, client, coursier,
                                                              course_libre):
        entetes = connecte(client, coursier.utilisateur)

        accueil = client.get(reverse("mon-accueil"), **entetes).json()["data"]
        liste = client.get(reverse("livraisons-disponibles"), **entetes).json()["data"]

        assert accueil["disponibles"] == len(liste["livraisons"]) == 1
        assert accueil["raison_indisponibilite"] == liste["raison"] == ""

    def test_les_deux_disent_la_meme_raison_quand_il_n_y_a_rien(self, client, coursier,
                                                                course_libre):
        """Le cas exact de ton essai : une course en route masque les autres."""
        course_libre.livreur = coursier
        course_libre.statut_livraison = StatutLivraison.EN_ROUTE
        course_libre.save(update_fields=["livreur", "statut_livraison"])
        entetes = connecte(client, coursier.utilisateur)

        accueil = client.get(reverse("mon-accueil"), **entetes).json()["data"]
        liste = client.get(reverse("livraisons-disponibles"), **entetes).json()["data"]

        assert accueil["disponibles"] == len(liste["livraisons"]) == 0
        assert accueil["raison_indisponibilite"] == liste["raison"] == "course_en_cours"

    def test_hors_ligne_est_une_raison_a_part_entiere(self, client, coursier, course_libre):
        """« Aucune course » et « vous avez raccroche » n'appellent pas le meme geste."""
        coursier.statut_disponibilite = StatutDisponibilite.HORS_LIGNE
        coursier.save(update_fields=["statut_disponibilite"])

        liste = client.get(reverse("livraisons-disponibles"),
                           **connecte(client, coursier.utilisateur)).json()["data"]

        assert liste["raison"] == "hors_ligne"

    def test_un_livreur_standard_ne_prend_pas_de_course_a_la_volee(self, client, db,
                                                                   course_libre):
        tournee = Livreur.objects.create(
            utilisateur=_utilisateur("standard@exemple.fr", "LIVREUR"),
            mode_livraison="STANDARD", statut_validation="VALIDE",
            statut_disponibilite=StatutDisponibilite.DISPONIBLE,
        )

        liste = client.get(reverse("livraisons-disponibles"),
                           **connecte(client, tournee.utilisateur)).json()["data"]

        assert liste["raison"] == "mauvais_mode"
