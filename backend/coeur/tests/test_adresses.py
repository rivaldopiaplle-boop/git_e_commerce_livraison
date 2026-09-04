"""Ce que chaque role voit d'une adresse de livraison — D-74.

**Ta question, L-2** : *« mes adresses : ces informations ne sont pas utilisees
par le vendeur, l'entrepot, le gestionnaire ni le livreur, pourquoi ? »*

Elle etait juste : le client saisissait une adresse et des instructions
(« code portail 4512, 3e etage »), et personne ne les voyait ensuite. Le
vendeur ne savait meme pas dans quelle ville partait son colis.

Ces tests verrouillent le **cloisonnement**, dans les deux sens : chacun recoit
ce dont son metier a besoin, et personne ne recoit plus. Une adresse complete
diffusee a toute la chaine est une donnee personnelle exposee sans necessite.
"""
import pytest

from coeur.adresses import ADMIN, ENTREPOT, LIVREUR, VENDEUR, adresse_pour, resume
from comptes.models import Adresse
from livraisons.models import ZoneLivraison


@pytest.fixture
def adresse(db):
    zone = ZoneLivraison.objects.create(nom="Lyon centre", codes_postaux="69001,69002")
    return Adresse.objects.create(
        libelle="Domicile",
        rue="8 rue Victor Hugo",
        complement="Batiment B",
        code_postal="69002",
        ville="Lyon",
        instructions_livraison="Code portail 4512, 3e etage.",
        latitude=45.7550,
        longitude=4.8320,
        zone=zone,
    )


@pytest.mark.django_db
def test_le_vendeur_sait_ou_part_son_colis(adresse):
    """Sans la ville, il ne sait pas s'il expedie a cote ou a l'autre bout du pays."""
    vue = adresse_pour(VENDEUR, adresse)

    assert vue == {"ville": "Lyon", "code_postal": "69002"}


@pytest.mark.django_db
def test_le_vendeur_ne_connait_ni_la_rue_ni_l_etage(adresse):
    """Il prepare un colis : il n'a pas a connaitre l'etage de quelqu'un."""
    vue = adresse_pour(VENDEUR, adresse)

    assert "rue" not in vue
    assert "instructions" not in vue
    assert "complement" not in vue


@pytest.mark.django_db
def test_l_entrepot_recoit_les_rues_car_il_ordonne_des_arrets(adresse):
    """Monter une tournee sans les rues reviendrait a ordonner au hasard."""
    vue = adresse_pour(ENTREPOT, adresse)

    assert vue["rue"] == "8 rue Victor Hugo"
    assert vue["zone"] == "Lyon centre"


@pytest.mark.django_db
def test_l_entrepot_ne_recoit_pas_les_instructions_de_porte(adresse):
    """Elles ne servent qu'a celui qui se presente devant la porte."""
    assert "instructions" not in adresse_pour(ENTREPOT, adresse)


@pytest.mark.django_db
def test_le_livreur_recoit_tout_car_c_est_lui_qui_sonne(adresse):
    vue = adresse_pour(LIVREUR, adresse)

    assert vue["rue"] == "8 rue Victor Hugo"
    assert vue["complement"] == "Batiment B"
    assert vue["instructions"] == "Code portail 4512, 3e etage."
    # Les coordonnees : c'est ce qui permet d'ouvrir un itineraire d'un clic.
    assert vue["latitude"] == pytest.approx(45.7550)
    assert vue["longitude"] == pytest.approx(4.8320)


@pytest.mark.django_db
def test_l_admin_voit_autant_que_le_livreur(adresse):
    """Il arbitre les litiges : il lui faut les deux versions au complet."""
    assert adresse_pour(ADMIN, adresse) == adresse_pour(LIVREUR, adresse)


@pytest.mark.django_db
def test_une_adresse_absente_ne_fait_pas_tomber_l_ecran(db):
    """Une commande sans adresse ne devrait pas exister ; un ecran ne doit pas
    tomber pour autant."""
    assert adresse_pour(LIVREUR, None) is None
    assert resume(None) == ""


@pytest.mark.django_db
def test_le_resume_suit_le_meme_cloisonnement(adresse):
    """Une ligne de liste ne doit pas en dire plus que l'ecran de detail."""
    assert resume(adresse, VENDEUR) == "69002 Lyon"
    assert resume(adresse, LIVREUR) == "8 rue Victor Hugo, 69002 Lyon"


@pytest.mark.django_db
def test_l_entrepot_recoit_les_coordonnees_pour_sa_carte(adresse):
    """Ajoute au bloc N-5, avec la carte des tournees.

    Sans coordonnees, l'ecran des tournees ne peut placer aucun arret. Elles
    n'ouvrent rien de nouveau : l'entrepot voit deja la rue, qui en dit
    strictement plus qu'un couple de nombres.
    """
    vue = adresse_pour(ENTREPOT, adresse)

    assert vue["latitude"] == pytest.approx(45.7550)
    assert vue["longitude"] == pytest.approx(4.8320)
    # Et toujours pas les instructions de porte : la carte n'y change rien.
    assert "instructions" not in vue


@pytest.mark.django_db
def test_le_vendeur_ne_recoit_toujours_pas_de_coordonnees(adresse):
    """La carte de l'entrepot ne devait pas elargir la vue du vendeur."""
    vue = adresse_pour(VENDEUR, adresse)

    assert "latitude" not in vue
    assert "rue" not in vue
