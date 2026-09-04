"""Les medias d'un produit — les gardes du bloc N-1.

Ton reproche etait precis : *« les 4 vues et l'apercu anime, c'est bete. Tu as
pris la photo d'origine, tu as zoome, et tu as fait une video du zoom. »* Et
plus loin : *« pas systematiquement le meme nombre de photos et la presence
d'une video — parfois une photo suffit. »*

Ce fichier verrouille les trois regles qui en decoulent. Aucune ne se voit dans
une relecture de code : ce sont des proprietes de l'ensemble du catalogue, pas
d'une fonction.
"""
import pytest
from django.utils.text import slugify
from PIL import Image

from catalogue.models import Categorie, PhotoProduit, Produit
from coeur.management.commands.seed_catalogue import Command
from comptes.models import Utilisateur, Vendeur


@pytest.fixture
def commande():
    fabrique = Command()
    fabrique.fournies = fabrique.telecharges = fabrique.fabriquees = 0
    fabrique.galeries = fabrique.animes = fabrique.reparees = 0
    fabrique.hors_ligne = True
    return fabrique


@pytest.fixture
def boutique(db):
    utilisateur = Utilisateur.objects.create_user(
        email="vues@exemple.fr", password="Demonstration!2026", statut_compte="ACTIF",
        nom="Vues", prenom="Test", role="VENDEUR",
    )
    return Vendeur.objects.create(
        utilisateur=utilisateur, nom_boutique="Boutique d'essai",
        type_activite="EXPRESS", statut_validation="VALIDE",
    )


def produit_avec(boutique, nom, categorie="Plats"):
    cat, _ = Categorie.objects.get_or_create(slug=slugify(categorie), defaults={"nom": categorie})
    return Produit.objects.create(
        vendeur=boutique, categorie=cat, nom=nom, description=nom,
        prix_unitaire_centimes=1000, stock_disponible=5, seuil_alerte=1,
        poids_grammes=400,
    )


class TestLeProfilVarie:
    """Le defaut d'origine : cinquante-huit produits, quatre photos chacun."""

    def test_le_profil_ne_donne_pas_toujours_le_meme_nombre(self, commande, boutique):
        noms = [
            "Curry de legumes", "Bol de ramen", "Tarte aux pommes", "Cafe filtre",
            "Casque audio", "Clavier mecanique", "Sac isotherme", "Miel de foret",
            "Terrine de campagne", "Jus de pomme", "Pain complet", "Chargeur rapide",
        ]
        profils = {commande.profil_media(produit_avec(boutique, nom)) for nom in noms}
        assert len(profils) > 1, (
            "Tous les produits recevraient le meme nombre de medias — "
            "c'est exactement le defaut du bloc N-1."
        )

    def test_une_seule_photo_est_un_cas_frequent(self, commande, boutique):
        """« Parfois une photo suffit » — et ce doit etre le cas le plus courant."""
        seuls = sum(1 for combien, _ in commande.PROFILS if combien == 1)
        assert seuls >= len(commande.PROFILS) / 3

    def test_l_apercu_est_minoritaire(self, commande):
        """Une video sur chaque fiche est le signe d'un catalogue genere."""
        avec = sum(1 for _, apercu in commande.PROFILS if apercu)
        assert 0 < avec <= len(commande.PROFILS) / 2


class TestOnNeMelangePasPhotoEtSchema:
    """Une photographie ne se complete pas par des dessins."""

    def test_une_vraie_photo_reste_seule(self, commande, boutique, tmp_path, settings):
        settings.MEDIA_ROOT = str(tmp_path)
        produit = produit_avec(boutique, "Terrine de campagne")

        # Une « photographie » : du bruit, que le peuplement ne saurait dessiner.
        import random

        image = Image.new("RGB", (900, 675))
        alea = random.Random(7)
        image.putdata([
            (alea.randrange(256), alea.randrange(256), alea.randrange(256))
            for _ in range(900 * 675)
        ])
        chemin = tmp_path / "produits"
        chemin.mkdir(parents=True, exist_ok=True)
        image.save(chemin / "photo.webp", "WEBP", quality=82)
        url = f"{settings.MEDIA_URL}produits/photo.webp"
        produit.image_principale_url = url
        produit.save(update_fields=["image_principale_url"])
        PhotoProduit.objects.create(produit=produit, url=url, ordre=1, texte_alternatif="x")

        assert commande.est_dessinee(produit, url) is False
        commande.completer_les_medias(produit, ("aucune", "", 0))

        produit.refresh_from_db()
        assert produit.photos.count() == 1, "Des schemas ont ete accoles a une photographie."
        assert produit.video_url == ""

    def test_une_vignette_dessinee_est_reconnue(self, commande, boutique, tmp_path, settings):
        settings.MEDIA_ROOT = str(tmp_path)
        produit = produit_avec(boutique, "Curry de legumes")

        url = commande.obtenir_image(produit.nom, ("aucune", "", 0), "Plats")
        assert commande.est_dessinee(produit, url) is True, (
            "Le peuplement ne reconnait plus sa propre vignette : il accolerait "
            "des schemas a de vraies photos, ou l'inverse."
        )


class TestLesVuesNeSontPasDesRecadrages:
    """Trois recadrages de la meme image ne sont pas trois angles."""

    def test_chaque_vue_est_une_composition_differente(self, commande, boutique):
        produit = produit_avec(boutique, "Curry de legumes")
        vues = [
            commande.dessiner_vue(produit, cle, libelle).resize((64, 48), Image.LANCZOS)
            for _, cle, libelle in commande.VUES
        ]

        for indice, une in enumerate(vues):
            for autre in vues[indice + 1:]:
                ecart = sum(
                    abs(x - y)
                    for pixel_a, pixel_b in zip(une.getdata(), autre.getdata(), strict=True)
                    for x, y in zip(pixel_a, pixel_b, strict=True)
                ) / (64 * 48 * 3)
                assert ecart > 12, (
                    "Deux vues se ressemblent comme deux recadrages d'une meme "
                    "image — le defaut que le bloc N-1 reprochait."
                )

    def test_aucune_dimension_n_est_inventee(self, commande, boutique):
        """La vue « en bref » ne dit que ce qu'on sait vraiment.

        Une premiere version dessinait « 26 cm x 17 cm », calcule sur le poids.
        Une cote fausse sur une fiche produit fait acheter un objet qui n'entre
        pas : c'est pire qu'un zoom, qui ne fait perdre que du temps.
        """
        import inspect

        source = inspect.getsource(Command.dessiner_vue)
        bloc = source[source.index('elif cle == "fiche"'):source.index("else:\n            # En")]
        # Les commentaires sont retires : celui qui raconte le defaut d'origine
        # contient justement « 26 cm », et ferait echouer sa propre garde.
        code = "\n".join(
            ligne for ligne in bloc.splitlines() if not ligne.lstrip().startswith("#")
        )
        assert " cm" not in code
        assert "poids_grammes" in code
