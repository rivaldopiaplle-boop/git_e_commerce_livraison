"""Remplit le catalogue de demonstration, images comprises (decision D-24).

    python manage.py seed_catalogue

Trois niveaux, du meilleur au dernier recours :

1. **Tes propres fichiers**, s'ils existent : `donnees-demo/images/<slug>.jpg`.
   Ils ont toujours la priorite.
2. **Le telechargement** depuis une liste figee de photos sous licence libre
   (Unsplash, ou Flickr par mots-cles quand aucune photo Unsplash ne convenait).
   Chaque image a ete regardee avant d'entrer dans la liste.
3. **Une image fabriquee** par Pillow — un degrade aux couleurs de la marque
   portant le nom du produit. Hors ligne, ou si une adresse est morte, la
   demonstration ne casse jamais parce qu'un site tiers a bouge.

Les images passent par le **meme traitement** qu'un televersement de vendeur :
recadrage, conversion en WebP, retrait des metadonnees. Le peuplement teste
donc la chaine d'images au lieu de la contourner.
"""
import hashlib
import io
import os
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

from catalogue.models import Categorie, PhotoProduit, Produit
from comptes.models import Vendeur

# Le regroupement des categories en univers.
UNIVERS = {
    "Plats": "Restauration",
    "Entrees": "Restauration",
    "Desserts": "Restauration",
    "Boulangerie": "Restauration",
    "Audio": "High-tech",
    "Informatique": "High-tech",
    "Telephonie": "High-tech",
    "Accessoires": "High-tech",
    "Epicerie": "Maison",
    "Boissons": "Maison",
}

LARGEUR = 900
HAUTEUR = 675
DOSSIER = "produits"

# Photos sous licence libre. La liste est figee et versionnee : le script ne
# parcourt jamais le web au hasard pour ramasser des images dont personne ne
# connait la licence.
#
# Chaque image a ete REGARDEE avant d'entrer dans cette liste. C'est la seule
# verification possible : rien, dans une URL, ne dit qu'une photo correspond
# au produit. Une premiere version montrait une chaise pour un clavier
# mecanique et un appareil photo pour un sac a dos.
#
# Deux sources, selon ce qui donnait le meilleur resultat :
#   ("unsplash", "<identifiant>")        photo choisie, qualite studio
#   ("flickr", "<mots-cles>", <verrou>)  recherche par mots-cles, verrou fige
#                                        la photo pour qu'elle ne change plus
CATALOGUE = [
    # ── Chez Karim — Express, restauration ──────────────────────────────
    ("Chez Karim", "Plats", "Bol de ramen maison",
     "Nouilles fraiches, bouillon mijote douze heures, oeuf mollet.",
     1290, 40, ("flickr", "ramen,noodles", 3)),
    ("Chez Karim", "Plats", "Burger du marche",
     "Boeuf charolais, cheddar affine, pain brioche du jour.",
     1450, 35, ("unsplash", "1550547660-d9450f859349")),
    ("Chez Karim", "Plats", "Pizza napolitaine",
     "Pate levee 48 heures, tomates San Marzano, mozzarella di bufala.",
     1350, 28, ("unsplash", "1565299624946-b28f40a0ae38")),
    ("Chez Karim", "Plats", "Assiette du chef",
     "Le plat du jour, compose le matin selon le marche.",
     1690, 12, ("unsplash", "1504674900247-0877df9cc836")),
    ("Chez Karim", "Entrees", "Salade de saison",
     "Legumes croquants, graines torrefiees, vinaigrette maison.",
     890, 50, ("unsplash", "1540189549336-e6e99c3679fe")),
    ("Chez Karim", "Desserts", "Tarte du jour",
     "Patisserie preparee le matin, en quantite limitee.",
     620, 0, ("flickr", "tart,pastry", 3)),

    # ── TechSophie — Standard, electronique reconditionnee ──────────────
    ("TechSophie", "Audio", "Casque a reduction de bruit",
     "Reconditionne grade A, batterie changee, garantie deux ans.",
     18900, 14, ("unsplash", "1505740420928-5e560c06d30e")),
    ("TechSophie", "Audio", "Enceinte portable",
     "Autonomie douze heures, resistante aux projections.",
     7900, 22, ("flickr", "bluetooth,speaker", 1)),
    ("TechSophie", "Informatique", "Ordinateur portable 14 pouces",
     "Reconditionne, 16 Go de memoire, disque 512 Go.",
     64900, 6, ("unsplash", "1496181133206-80ce9b88a853")),
    ("TechSophie", "Telephonie", "Telephone reconditionne",
     "Grade A, batterie neuve, debloque tout operateur.",
     32900, 9, ("unsplash", "1511707171634-5f897ff02aa9")),
    ("TechSophie", "Accessoires", "Montre connectee",
     "Suivi d'activite, autonomie sept jours.",
     12900, 18, ("unsplash", "1523275335684-37898b6baf30")),
    ("TechSophie", "Accessoires", "Lunettes de soleil polarisees",
     "Verres categorie 3, monture recyclee.",
     4900, 31, ("unsplash", "1572635196237-14b3f281503f")),
    ("TechSophie", "Accessoires", "Sac a dos urbain",
     "Compartiment ordinateur 15 pouces, tissu recycle.",
     6900, 25, ("flickr", "backpack,leather", 3)),
    ("TechSophie", "Informatique", "Clavier mecanique",
     "Switches silencieux, retroeclairage, sans fil.",
     8900, 0, ("flickr", "keyboard,gaming", 2)),

    # -- Le Fournil d a cote -- Express, boulangerie ---------------------
    ("Le Fournil d a cote", "Boulangerie", "Pain au levain",
     "Farine de meule bio, fermentation lente de dix-huit heures.",
     450, 24, ("flickr", "sourdough,bread,loaf", 5)),
    ("Le Fournil d a cote", "Boulangerie", "Croissant au beurre",
     "Beurre de Charentes, feuilletage a la main, cuit toutes les deux heures.",
     130, 60, ("flickr", "croissant", 22)),
    ("Le Fournil d a cote", "Boulangerie", "Baguette tradition",
     "Cuite quatre fois par jour, sans additif.",
     120, 3, ("flickr", "baguette", 11)),
    ("Le Fournil d a cote", "Desserts", "Flan patissier",
     "Vanille de Madagascar, cuit dans sa pate.",
     380, 8, ("flickr", "portuguesetart", 83)),

    # -- Maison Perrin -- Standard, epicerie fine ------------------------
    ("Maison Perrin", "Epicerie", "Huile d olive premiere pression",
     "Recolte a froid, bouteille de 50 cl, exploitation familiale.",
     1490, 40, ("flickr", "extravirgin", 103)),
    ("Maison Perrin", "Epicerie", "Miel de montagne",
     "Recolte d altitude, pot de 500 g, non chauffe.",
     990, 18, ("flickr", "honey,jar", 3)),
    ("Maison Perrin", "Boissons", "Cafe en grains, torrefaction artisanale",
     "Arabica d Ethiopie, torrefie a Lyon, sachet de 1 kg.",
     2290, 26, ("flickr", "coffeebeans", 42)),
    ("Maison Perrin", "Epicerie", "Coffret d epices",
     "Douze epices entieres en fioles, avec leur carnet de recettes.",
     3490, 2, ("flickr", "spicejar", 114)),

    # -- Marseille Grill -- Express, hors rayon depuis Lyon --------------
    ("Marseille Grill", "Plats", "Brochettes marinees",
     "Agneau marine vingt-quatre heures, servi avec sa semoule.",
     1590, 20, ("flickr", "kebab,skewer,grill", 4)),
    ("Marseille Grill", "Entrees", "Assiette de mezze",
     "Six entrees a partager, preparees le matin.",
     1190, 15, ("flickr", "mezze,hummus,appetizer", 3)),
    # ── Rallonge du catalogue (M-0) ─────────────────────────────────────
    #
    # Vingt-quatre produits, c'est trop peu pour eprouver ce que le catalogue
    # sait faire : la recherche rendait toujours tout, les facettes n'ecartaient
    # rien, la pagination ne se declenchait jamais, et le graphe des ventes
    # tenait sur trois barres.
    #
    # Les prix et les stocks sont VARIES a dessein : un catalogue ou tout coute
    # entre 10 et 20 euros ne permet pas d'essayer un tri par prix, et un
    # catalogue ou tout est en stock ne montre jamais une rupture.

    # -- Chez Karim, Express : une carte de restaurant credible --------
    ("Chez Karim", "Plats", "Poke bowl saumon",
     "Riz vinaigre, saumon label rouge, edamame, sesame.",
     1390, 24, ("flickr", "poke,bowl", 5)),
    ("Chez Karim", "Plats", "Curry de legumes",
     "Lait de coco, patate douce, pois chiches. Vegetalien.",
     1190, 30, ("flickr", "curry,vegetables", 7)),
    ("Chez Karim", "Plats", "Wrap poulet grille",
     "Galette de ble, poulet marine, crudites, sauce yaourt.",
     990, 45, ("flickr", "wrap,chicken", 11)),
    ("Chez Karim", "Entrees", "Soupe du jour",
     "Legumes de saison, changee chaque matin.",
     590, 18, ("flickr", "soup,bowl", 13)),
    ("Chez Karim", "Entrees", "Salade cesar",
     "Sucrine, parmesan, croutons maison, anchois.",
     890, 26, ("flickr", "caesar,salad", 17)),
    ("Chez Karim", "Desserts", "Fondant au chocolat",
     "Coeur coulant, chocolat 70 %, servi tiede.",
     650, 20, ("flickr", "chocolate,cake", 19)),
    ("Chez Karim", "Desserts", "Panna cotta fruits rouges",
     "Creme infusee a la vanille, coulis de fruits rouges.",
     590, 15, ("flickr", "pannacotta,dessert", 23)),
    ("Chez Karim", "Boissons", "Limonade artisanale",
     "Citrons de Menton, sucre de canne, bulles fines.",
     390, 60, ("flickr", "lemonade,drink", 29)),

    # -- Le Fournil : la boulangerie du matin --------------------------
    ("Le Fournil d a cote", "Boulangerie", "Croissant au beurre",
     "Beurre AOP Charentes-Poitou, feuilletage a la main.",
     140, 80, ("flickr", "croissant,bakery", 31)),
    ("Le Fournil d a cote", "Boulangerie", "Pain aux cereales",
     "Sept graines, farine T80, longue fermentation.",
     380, 22, ("flickr", "bread,seeds", 37)),
    ("Le Fournil d a cote", "Boulangerie", "Chausson aux pommes",
     "Pommes du Limousin, feuilletage pur beurre.",
     220, 34, ("flickr", "applepastry,bakery", 41)),
    ("Le Fournil d a cote", "Desserts", "Tarte au citron meringuee",
     "Citrons de Sicile, meringue doree au chalumeau.",
     420, 12, ("flickr", "lemontart,meringue", 43)),
    ("Le Fournil d a cote", "Desserts", "Cookie chocolat noisette",
     "Cuit du jour, coeur fondant, noisettes du Piemont.",
     250, 48, ("flickr", "cookie,chocolate", 47)),

    # -- Marseille Grill : hors rayon depuis Lyon, et c'est le but -----
    ("Marseille Grill", "Plats", "Brochettes d agneau",
     "Agneau marine aux herbes, semoule fine.",
     1590, 20, ("flickr", "lamb,skewer", 53)),
    ("Marseille Grill", "Entrees", "Houmous et pain plat",
     "Pois chiches ecrases, tahini, huile d olive.",
     690, 25, ("flickr", "hummus,bread", 59)),
    ("Marseille Grill", "Boissons", "The a la menthe",
     "The vert gunpowder, menthe fraiche, servi sucre.",
     350, 40, ("flickr", "mint,tea", 61)),

    # -- TechSophie : de quoi trier par prix sur deux ordres de grandeur
    ("TechSophie", "Audio", "Ecouteurs sans fil",
     "Reconditionnes, boitier de charge neuf, reduction de bruit.",
     8900, 27, ("flickr", "earbuds,wireless", 67)),
    ("TechSophie", "Audio", "Platine vinyle",
     "Entrainement par courroie, cellule remplacee, revisee.",
     22900, 5, ("flickr", "turntable,vinyl", 71)),
    ("TechSophie", "Informatique", "Ecran 27 pouces",
     "Dalle IPS, 2560x1440, pied reglable en hauteur.",
     19900, 8, ("flickr", "monitor,desk", 73)),
    ("TechSophie", "Informatique", "Souris ergonomique",
     "Verticale, sans fil, reconditionnee grade A.",
     4900, 33, ("flickr", "mouse,computer", 79)),
    ("TechSophie", "Informatique", "Disque externe 2 To",
     "USB-C, teste sur banc, garanti un an.",
     7900, 16, ("flickr", "harddrive,storage", 83)),
    ("TechSophie", "Telephonie", "Tablette 10 pouces",
     "Reconditionnee, 128 Go, etui inclus.",
     24900, 7, ("flickr", "tablet,device", 89)),
    ("TechSophie", "Telephonie", "Chargeur rapide 65 W",
     "Trois ports, compatible ordinateur portable.",
     3500, 52, ("flickr", "charger,usb", 97)),
    ("TechSophie", "Accessoires", "Batterie externe 20 000 mAh",
     "Charge deux appareils a la fois, indicateur de niveau.",
     4500, 38, ("flickr", "powerbank,battery", 101)),
    ("TechSophie", "Accessoires", "Support ordinateur portable",
     "Aluminium recycle, hauteur reglable, pliable.",
     3900, 29, ("flickr", "laptopstand,desk", 103)),

    # -- Maison Perrin : l'epicerie fine -------------------------------
    ("Maison Perrin", "Epicerie", "Miel de montagne",
     "Recolte des Cevennes, pot de 500 grammes.",
     1290, 26, ("flickr", "honey,jar", 107)),
    ("Maison Perrin", "Epicerie", "Confiture d abricots",
     "Abricots du Roussillon, 65 % de fruits.",
     690, 34, ("flickr", "jam,apricot", 109)),
    ("Maison Perrin", "Epicerie", "Terrine de campagne",
     "Porc fermier, poivre concasse, bocal de 180 grammes.",
     890, 19, ("flickr", "terrine,pate", 113)),
    ("Maison Perrin", "Epicerie", "Sel de Guerande",
     "Recolte a la main, fleur de sel, boite de 250 grammes.",
     580, 44, ("flickr", "salt,guerande", 127)),
    ("Maison Perrin", "Epicerie", "Riz de Camargue",
     "Riz rouge complet, sachet d un kilo.",
     720, 30, ("flickr", "rice,grain", 131)),
    ("Maison Perrin", "Boissons", "Jus de pomme trouble",
     "Pommes de Normandie, sans sucre ajoute, bouteille d un litre.",
     490, 40, ("flickr", "applejuice,bottle", 137)),
    ("Maison Perrin", "Boissons", "Infusion verveine menthe",
     "Plantes de Provence, boite de 40 grammes.",
     650, 28, ("flickr", "herbaltea,leaves", 139)),
    ("Maison Perrin", "Boissons", "Sirop de sureau",
     "Fleurs cueillies a la main, bouteille de 50 centilitres.",
     840, 14, ("flickr", "syrup,bottle", 149)),

    # -- Morvan Primeurs : SUSPENDUE. Son catalogue existe et doit
    #    disparaitre de la vitrine sans que rien ne soit efface (D-61).
    #    Sans produits, la suspension ne se demontrait pas.
    ("Morvan Primeurs", "Epicerie", "Panier de legumes de saison",
     "Composition variable selon la recolte, environ quatre kilos.",
     1890, 15, ("flickr", "vegetables,basket", 151)),
    ("Morvan Primeurs", "Epicerie", "Pommes de terre de Noirmoutier",
     "Primeurs, sachet de deux kilos.",
     790, 22, ("flickr", "potatoes,harvest", 157)),
    ("Morvan Primeurs", "Epicerie", "Fromage de chevre fermier",
     "Affine trois semaines, lait cru.",
     650, 18, ("flickr", "goatcheese,dairy", 163)),
]
# Des cas que le catalogue doit savoir montrer, et qu'un jeu de donnees
# uniforme cache : un produit retire de la vente, un stock sous le seuil,
# un article lourd, un article sans photo. Chacun existe ici pour qu'un
# ecran soit confronte a lui au moins une fois.
#   nom du produit -> champs a forcer apres creation
PARTICULARITES = {
    # Retire de la vente par son vendeur : visible dans son back-office,
    # absent du catalogue public (D-13, suppression logique).
    "Lunettes de soleil polarisees": {"est_visible": False},
    # Sous le seuil d alerte, sans etre en rupture : le cas que le tableau
    # de bord doit remonter en jaune et non en rouge.
    "Baguette tradition": {"seuil_alerte": 10},
    "Coffret d epices": {"seuil_alerte": 5},
    "Ordinateur portable 14 pouces": {"seuil_alerte": 8, "poids_grammes": 2400},
    # En rupture franche : bouton gele et alerte de retour (D-06).
    "Clavier mecanique": {"stock_disponible": 0},
    "Tarte du jour": {"stock_disponible": 0},
}


class Command(BaseCommand):
    help = "Cree les categories, les produits et leurs images de demonstration."

    def reposer_particularites(self, produit):
        """Reappliquer les cas limites d'un produit, meme s'il existe deja.

        Ce sont eux qui rendent visibles les scenarios 4.1, 4.5 et D-06 :
        un produit retire de la vente, deux ruptures franches, trois seuils
        d'alerte. Sans cette methode, un seul essai a l'ecran les perdait
        definitivement.
        """
        particularites = PARTICULARITES.get(produit.nom)
        if not particularites:
            return
        change = [
            champ for champ, valeur in particularites.items()
            if getattr(produit, champ) != valeur
        ]
        if not change:
            return
        for champ, valeur in particularites.items():
            setattr(produit, champ, valeur)
        produit.save(update_fields=list(particularites))
        self.stdout.write(f"  {produit.nom} : {', '.join(change)} remis en place.")

    def add_arguments(self, analyseur):
        analyseur.add_argument(
            "--hors-ligne",
            action="store_true",
            dest="hors_ligne",
            help="N'essaie meme pas de telecharger : fabrique toutes les images.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.hors_ligne = options["hors_ligne"]
        self.telecharges = 0
        self.fabriquees = 0
        self.fournies = 0
        self.galeries = 0
        self.animes = 0
        self.reparees = 0

        boutiques = {v.nom_boutique: v for v in Vendeur.objects.all()}
        if not boutiques:
            self.stdout.write(self.style.WARNING(
                "Aucune boutique : lance d'abord `python manage.py seed_demo`."
            ))
            return

        categories = {}
        crees = 0

        for nom_boutique, nom_categorie, nom, description, prix, stock, photo in CATALOGUE:
            vendeur = boutiques.get(nom_boutique)
            if vendeur is None:
                continue

            if nom_categorie not in categories:
                categorie, _ = Categorie.objects.get_or_create(
                    slug=slugify(nom_categorie), defaults={"nom": nom_categorie}
                )
                # Sept categories a plat ne disent rien. Regroupees en deux
                # univers, elles se lisent d'un coup d'oeil — et le modele
                # prevoyait deja la reflexivite pour cela (A13 du MCD).
                parente = self.univers(UNIVERS.get(nom_categorie, "Autres"))
                if categorie.parente_id != parente.id:
                    categorie.parente = parente
                    categorie.save(update_fields=["parente"])
                categories[nom_categorie] = categorie

            existant = Produit.objects.filter(vendeur=vendeur, nom=nom).first()
            if existant is not None:
                # Le produit est la : on ne le recree pas, mais on REPOSE ses
                # particularites. Elles n'etaient appliquees qu'a la creation,
                # si bien qu'un essai en cours de route — remettre en vente un
                # produit retire, reapprovisionner une rupture — les effacait
                # sans retour possible. Le jeu de demonstration doit se
                # remettre d'aplomb en une commande (D-96).
                self.reposer_particularites(existant)
                self.completer_les_medias(existant, photo)
                continue

            produit = Produit.objects.create(
                vendeur=vendeur,
                categorie=categories[nom_categorie],
                nom=nom,
                description=description,
                prix_unitaire_centimes=prix,
                stock_disponible=stock,
                seuil_alerte=5,
                poids_grammes=400 if vendeur.type_activite == "EXPRESS" else 1200,
            )

            self.reposer_particularites(produit)

            chemin = self.obtenir_image(nom, photo, nom_categorie)
            produit.image_principale_url = chemin
            produit.save(update_fields=["image_principale_url"])
            PhotoProduit.objects.create(
                produit=produit, url=chemin, ordre=1,
                texte_alternatif=f"{nom} — {vendeur.nom_boutique}",
            )
            self.completer_les_medias(produit, photo)
            crees += 1

        self.stdout.write("")
        if crees:
            self.stdout.write(self.style.SUCCESS(f"Catalogue : {crees} produit(s) cree(s)."))
            self.stdout.write(
                f"  images : {self.fournies} fournie(s), {self.telecharges} telechargee(s), "
                f"{self.fabriquees} fabriquee(s)"
            )
        else:
            self.stdout.write(self.style.SUCCESS("Catalogue deja en place."))

        if self.galeries or self.animes or self.reparees:
            self.stdout.write(
                f"  medias : {self.reparees} photo(s) principale(s) refaite(s), "
                f"{self.galeries} vue(s) de galerie, "
                f"{self.animes} apercu(s) anime(s)"
            )
        self.stdout.write("")

    # ── Ce qu'un produit a comme medias ──────────────────────────────────
    #
    # La version precedente donnait a CHAQUE produit quatre photos et un
    # apercu anime. Les trois photos supplementaires etaient des recadrages
    # de la photo principale, et l'apercu un lent zoom sur cette meme photo.
    # Autrement dit : la meme image, cinq fois, dans cinq tailles.
    #
    # Deux defauts, et le second est le plus grave :
    #
    #   · **un zoom n'est pas un autre angle.** Une galerie qui repete la
    #     meme image ne montre rien de plus, elle fait perdre du temps ;
    #   · **l'uniformite.** Cinquante-huit fiches avec exactement le meme
    #     nombre de medias, ca ne s'invente pas : ca se genere. Un catalogue
    #     reel est irregulier — le traiteur du coin a pris une photo au
    #     telephone, le revendeur de high-tech en a huit fournies par le
    #     fabricant.
    #
    # Le nombre de medias suit donc un profil tire du nom du produit :
    # stable d'un peuplement a l'autre, different d'un produit a l'autre.
    # **Un produit sur trois n'a qu'une seule photo, et c'est tres bien.**
    PROFILS = [
        (1, False),  # le petit vendeur qui a pris une photo, et c'est tout
        (1, False),
        (1, False),
        (2, False),
        (2, False),
        (3, False),
        (3, True),   # celui qui a fait l'effort d'un apercu
        (4, True),
    ]

    # Les vues complementaires. Elles ne sont PAS des recadrages : chacune est
    # une composition differente, dessinee. Elles disent ce qu'elles sont —
    # des illustrations — parce qu'une fausse photo est pire qu'une absence de
    # photo, et que c'est ce qu'on m'a deja reproche au bloc J.
    #
    # Le jour ou un vendeur televerse ses vraies photos, elles prennent la
    # place de celles-ci sans qu'une ligne de code change : voir
    # `medias_fournis()`, qui lit `donnees-demo/images/<slug>-2.jpg` et
    # suivants.
    VUES = [
        (2, "emballage", "Ce que vous recevez"),
        (3, "fiche", "En bref"),
        (4, "situation", "En situation"),
    ]

    def profil_media(self, produit):
        """Combien de photos, et un apercu ou non."""
        graine = int(hashlib.md5(produit.nom.encode()).hexdigest()[:8], 16)
        return self.PROFILS[graine % len(self.PROFILS)]

    def completer_les_medias(self, produit, source):
        """Poser la photo principale, puis les medias que le profil prevoit.

        Elle ne posait que la galerie, et abandonnait si la photo principale
        manquait. Un produit qui perdait son image — fichier efface, media non
        versionne restaure depuis zero — restait donc sans image pour toujours,
        et relancer la commande n'y changeait rien.

        Meme famille de defaut que les particularites (D-109) : **une commande
        de peuplement doit remettre la demonstration d'aplomb, pas seulement la
        monter la premiere fois.** Elle retire donc aussi ce qui est en trop,
        sans quoi les quatre vues de l'ancienne version survivraient a jamais.
        """
        principale = produit.photos.filter(ordre=1).first()
        if principale is None or self.charger_media(principale.url) is None:
            chemin = self.obtenir_image(
                produit.nom, source,
                produit.categorie.nom if produit.categorie_id else "Autres",
            )
            produit.image_principale_url = chemin
            produit.save(update_fields=["image_principale_url"])
            produit.photos.filter(ordre=1).delete()
            principale = PhotoProduit.objects.create(
                produit=produit, url=chemin, ordre=1,
                texte_alternatif=f"{produit.nom} — {produit.vendeur.nom_boutique}",
            )
            self.reparees += 1

        combien, avec_apercu = self.profil_media(produit)
        fournis = self.medias_fournis(produit)
        if fournis:
            # Tes fichiers priment sur le profil : si tu as depose cinq photos,
            # le produit en a cinq. Le profil ne sert qu'a ne pas inventer.
            combien = 1 + len(fournis)
        elif not self.est_dessinee(produit, principale.url):
            # **Une photographie ne se complete pas par des schemas.** Vingt
            # produits ont une vraie photo sous licence libre ; leur adjoindre
            # trois dessins ferait une galerie qui change de registre au
            # deuxieme cliquet, et c'est encore plus voyant qu'un zoom.
            #
            # Ceux-la gardent donc leur photo, seule. C'est exactement ce que
            # tu as dit : « parfois une photo suffit. »
            combien, avec_apercu = 1, False

        # Ce qui depasse le profil s'en va. C'est cette ligne qui efface les
        # « detail », « matiere » et « situation » de l'ancienne version.
        produit.photos.filter(ordre__gt=combien).delete()

        for rang, (ordre, cle, libelle) in enumerate(self.VUES):
            if ordre > combien:
                break
            if produit.photos.filter(ordre=ordre).exists():
                continue
            if rang < len(fournis):
                chemin = fournis[rang]
                alternatif = f"{produit.nom} — {libelle.lower()}"
            else:
                chemin = self.ecrire_vue(produit, cle, libelle)
                alternatif = f"{produit.nom} — {libelle.lower()} (illustration)"
            PhotoProduit.objects.create(
                produit=produit, url=chemin, ordre=ordre, texte_alternatif=alternatif,
            )
            self.galeries += 1

        if not avec_apercu:
            if produit.video_url:
                produit.video_url = ""
                produit.save(update_fields=["video_url"])
            return

        if not produit.video_url:
            produit.video_url = self.ecrire_apercu_anime(produit)
            produit.save(update_fields=["video_url"])
            self.animes += 1

    def est_dessinee(self, produit, chemin_public):
        """Cette image a-t-elle ete DESSINEE par le peuplement ?

        La question decide de tout ce qui suit : **on n'accole pas des schemas
        a une photographie.** Une galerie qui commence par une vraie photo et
        continue par trois dessins change de registre au deuxieme cliquet, et
        cela se voit encore plus qu'un zoom.

        Premiere tentative, abandonnee : compter les couleurs distinctes. Une
        vignette dessinee en a quelques milliers, une photo plusieurs dizaines
        de milliers… sauf une photo d'ordinateur sur fond blanc, qui en avait
        15 000 et passait pour un dessin. **Un seuil est toujours faux quelque
        part.**

        La bonne methode ne devine pas : elle **redessine** la vignette que ce
        produit aurait eue, et la compare a l'image stockee. Si elles se
        ressemblent, l'image EST cette vignette. C'est exact, cela ne demande
        aucun drapeau en base — qui mentirait le jour ou un vendeur
        remplacerait sa photo sans le mettre a jour — et cela reste vrai si
        les couleurs de la maquette changent.
        """
        image = self.charger_media(chemin_public)
        if image is None:
            return True

        categorie = produit.categorie.nom if produit.categorie_id else "Autres"
        attendue = self.traiter(self.image_fabriquee(produit.nom, categorie))

        # Comparaison sur une reduction : la compression WebP deplace quelques
        # niveaux par pixel, elle ne deplace pas une forme.
        petit = (64, 48)
        a = image.resize(petit, Image.LANCZOS).getdata()
        b = attendue.resize(petit, Image.LANCZOS).getdata()
        ecart = sum(
            abs(x - y) for pixel_a, pixel_b in zip(a, b, strict=True)
            for x, y in zip(pixel_a, pixel_b, strict=True)
        ) / (len(a) * 3)
        return ecart < 12

    def medias_fournis(self, produit):
        """Tes propres vues complementaires : `<slug>-2.jpg`, `-3`, `-4`.

        Le peuplement lisait deja `donnees-demo/images/<slug>.jpg` pour la
        photo principale. Il lit maintenant la suite, dans le meme dossier et
        avec la meme regle : **ce que tu fournis prime sur ce que je dessine.**
        C'est la seule facon d'avoir un jour de vraies photos sous plusieurs
        angles — aucun script ne peut les inventer.
        """
        slug = slugify(produit.nom)
        dossier = os.path.join(settings.RACINE.parent, "donnees-demo", "images")
        cible = os.path.join(settings.MEDIA_ROOT, DOSSIER)
        os.makedirs(cible, exist_ok=True)

        trouves = []
        for rang in (2, 3, 4, 5, 6):
            for extension in ("jpg", "jpeg", "png", "webp"):
                origine = os.path.join(dossier, f"{slug}-{rang}.{extension}")
                if not os.path.exists(origine):
                    continue
                destination = os.path.join(cible, f"{slug}-{rang}.webp")
                chemin_public = f"{settings.MEDIA_URL}{DOSSIER}/{slug}-{rang}.webp"
                if not os.path.exists(destination):
                    self.traiter(Image.open(origine)).save(
                        destination, "WEBP", quality=82, method=5
                    )
                    self.fournies += 1
                trouves.append(chemin_public)
                break
            else:
                break
        return trouves

    def charger_media(self, chemin_public):
        """Relire une image deja ecrite, depuis son chemin public."""
        relatif = chemin_public.replace(settings.MEDIA_URL, "", 1).lstrip("/")
        chemin = os.path.join(settings.MEDIA_ROOT, relatif)
        if not os.path.exists(chemin):
            return None
        image = Image.open(chemin)
        image.load()
        return image.convert("RGB")

    def ecrire_vue(self, produit, cle, libelle):
        """Une vue complementaire DESSINEE, pas un recadrage.

        Chaque cle donne une composition differente : un colis pour
        « ce que vous recevez », une reglette cotee pour « les dimensions »,
        une scene pour « en situation ». Elles se ressemblent aussi peu que
        trois photos prises sous trois angles se ressemblent — ce qui etait
        precisement le reproche fait aux recadrages.

        Elles ne pretendent pas etre des photographies : le texte alternatif
        dit « illustration », et le cartouche en bas de l'image le repete.
        """
        slug = f"{slugify(produit.nom)}-{cle}"
        dossier = os.path.join(settings.MEDIA_ROOT, DOSSIER)
        os.makedirs(dossier, exist_ok=True)
        destination = os.path.join(dossier, f"{slug}.webp")
        chemin_public = f"{settings.MEDIA_URL}{DOSSIER}/{slug}.webp"
        if os.path.exists(destination):
            return chemin_public

        self.dessiner_vue(produit, cle, libelle).save(
            destination, "WEBP", quality=82, method=5
        )
        return chemin_public

    def dessiner_vue(self, produit, cle, libelle):
        """La composition elle-meme, en memoire."""
        categorie = produit.categorie.nom if produit.categorie_id else "Autres"
        fond, accent, encre = self.TEINTES.get(
            UNIVERS.get(categorie, "Autres"), self.TEINTES["Autres"]
        )
        # Un fond legerement different par vue : deux vignettes cote a cote
        # dans la bande de miniatures doivent se distinguer au premier regard.
        decalage = {"emballage": 0.06, "fiche": -0.04, "situation": 0.10}[cle]
        fond = tuple(
            max(0, min(255, int(c + (accent[k] - c) * decalage)))
            for k, c in enumerate(fond)
        )

        image = Image.new("RGB", (LARGEUR, HAUTEUR), fond)
        dessin = ImageDraw.Draw(image)
        police = self.police
        centre_x, centre_y = LARGEUR // 2, HAUTEUR // 2 - 30

        if cle == "emballage":
            # Un colis vu de trois-quarts, avec l'etiquette de la boutique.
            largeur, hauteur, profondeur = 300, 210, 90
            gauche, haut = centre_x - largeur // 2, centre_y - hauteur // 2
            dessin.polygon(
                [(gauche, haut), (gauche + profondeur, haut - profondeur // 2),
                 (gauche + largeur + profondeur, haut - profondeur // 2),
                 (gauche + largeur, haut)],
                fill=tuple(int(c * 0.93) for c in fond), outline=accent,
            )
            dessin.polygon(
                [(gauche + largeur, haut), (gauche + largeur + profondeur,
                                            haut - profondeur // 2),
                 (gauche + largeur + profondeur, haut + hauteur - profondeur // 2),
                 (gauche + largeur, haut + hauteur)],
                fill=tuple(int(c * 0.86) for c in fond), outline=accent,
            )
            dessin.rectangle([gauche, haut, gauche + largeur, haut + hauteur],
                             fill="#ffffff", outline=accent, width=3)
            # L'etiquette : c'est elle qui rend un colis credible.
            dessin.rectangle([gauche + 26, haut + 34, gauche + largeur - 26, haut + 118],
                             fill=fond, outline=accent)
            dessin.text((gauche + 40, haut + 48), produit.vendeur.nom_boutique[:22],
                        font=police(22), fill=encre)
            dessin.text((gauche + 40, haut + 80), "RivDinde", font=police(18), fill=accent)
            for rang in range(6):
                x = gauche + 40 + rang * 38
                dessin.rectangle([x, haut + 140, x + 12 + (rang % 3) * 5, haut + 176],
                                 fill=encre)

        elif cle == "fiche":
            # Ce qu'on SAIT du produit, et rien d'autre.
            #
            # La premiere version dessinait une reglette cotee « 26 cm × 17 cm »
            # calculee sur le poids. Autrement dit : des dimensions inventees,
            # affichees sur une fiche produit. C'est pire qu'un zoom — un zoom
            # ne fait perdre que du temps, une cote fausse fait acheter un
            # objet qui n'entre pas.
            lignes = [
                ("Poids", f"{produit.poids_grammes} g" if produit.poids_grammes else None),
                ("Univers", UNIVERS.get(categorie, "Autres")),
                ("Categorie", categorie),
                ("Boutique", produit.vendeur.nom_boutique),
                ("Livraison",
                 "Express, en moins d'une heure"
                 if produit.vendeur.type_activite == "EXPRESS"
                 else "Standard, groupee en tournee"),
            ]
            lignes = [(cle_ligne, valeur) for cle_ligne, valeur in lignes if valeur]

            haut = centre_y - (len(lignes) * 58) // 2 - 20
            dessin.rounded_rectangle([90, haut - 34, LARGEUR - 90, haut + len(lignes) * 58 + 20],
                                     radius=20, fill="#ffffff", outline=accent, width=3)
            for rang, (cle_ligne, valeur) in enumerate(lignes):
                y = haut + rang * 58
                if rang:
                    dessin.line([124, y - 12, LARGEUR - 124, y - 12],
                                fill=tuple(int(c * 0.92) for c in fond), width=2)
                dessin.text((128, y + 4), cle_ligne.upper(), font=police(19), fill=accent)
                dessin.text((328, y), str(valeur)[:34], font=police(25), fill=encre)

        else:
            # En situation : une table, une lumiere, l'objet pose dessus.
            dessin.ellipse([centre_x - 340, centre_y - 280, centre_x + 340, centre_y + 150],
                           fill=tuple(int(c * 0.97) for c in fond))
            table = centre_y + 150
            dessin.rectangle([0, table, LARGEUR, HAUTEUR],
                             fill=tuple(int(c * 0.88) for c in fond))
            dessin.line([0, table, LARGEUR, table], fill=accent, width=4)

            largeur, hauteur = 380, 240
            gauche = centre_x - largeur // 2
            # L'ombre portee AVANT l'objet : sans elle, il flotte au lieu
            # d'etre pose. Dessinee apres, elle passerait par-dessus.
            dessin.ellipse([gauche - 40, table - 18, gauche + largeur + 40, table + 30],
                           fill=tuple(int(c * 0.78) for c in fond))
            dessin.rounded_rectangle([gauche, table - hauteur, gauche + largeur, table],
                                     radius=20, fill="#ffffff", outline=accent, width=4)

            # Le nom, sur deux lignes au besoin : le tronquer dans sa propre
            # mise en situation serait absurde.
            mots, lignes, courante = produit.nom.split(), [], ""
            for mot in mots:
                essai = f"{courante} {mot}".strip()
                if len(essai) > 16 and courante:
                    lignes.append(courante)
                    courante = mot
                else:
                    courante = essai
            lignes.append(courante)
            y = table - hauteur + 42
            for ligne in lignes[:3]:
                dessin.text((gauche + 30, y), ligne, font=police(30), fill=encre)
                y += 42

        # Le cartouche : il nomme la vue ET dit que c'est une illustration.
        # Sans lui, on croirait a une photographie ratee.
        #
        # La mention est ecrite dans un gris clair et non dans l'accent : sur
        # le fond sombre du cartouche, l'accent bleu etait illisible — la
        # meme maladie que le bouton blanc sur blanc du bloc M.
        dessin.rectangle([0, HAUTEUR - 82, LARGEUR, HAUTEUR], fill=encre)
        dessin.text((40, HAUTEUR - 66), libelle.upper(), font=police(25), fill="#ffffff")
        dessin.text((40, HAUTEUR - 34), "illustration — non contractuelle",
                    font=police(18), fill="#c9cfdd")
        return image

    def police(self, taille):
        for nom in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
            try:
                return ImageFont.truetype(nom, taille)
            except OSError:
                continue
        return ImageFont.load_default()

    def ecrire_apercu_anime(self, produit):
        """Un enchainement des VUES, en WebP anime.

        L'ancienne version etait un lent zoom sur la photo principale. Tu l'as
        dit sans detour : « c'est bete ». Une video qui zoome sur une image
        fixe n'apporte rien qu'un doigt sur un ecran ne fasse deja mieux.

        Celle-ci enchaine les compositions — le produit, son colis, ses
        dimensions, sa mise en situation — avec une pause sur chacune. C'est
        ce que fait une vraie video de produit : elle FAIT LE TOUR.

        Ce n'est toujours pas une video, et l'appeler ainsi serait mentir :
        c'est une image animee de quelques dizaines de kilo-octets, fabriquee
        sans encodeur ni reseau. Le champ `video_url` accepte les deux, et le
        front joue une vraie video le jour ou un vendeur en televerse une.
        """
        slug = slugify(produit.nom)
        dossier = os.path.join(settings.MEDIA_ROOT, DOSSIER)
        destination = os.path.join(dossier, f"{slug}-apercu.webp")
        chemin_public = f"{settings.MEDIA_URL}{DOSSIER}/{slug}-apercu.webp"
        if os.path.exists(destination):
            return chemin_public

        # Le tiers de la taille et une qualite moderee : l'apercu doit peser
        # quelques dizaines de kilo-octets, pas trois cents. Une fiche produit
        # qui met deux secondes a s'afficher sur un telephone en 4G n'aide
        # personne a acheter — et le projet tourne sur une offre gratuite.
        petit = (LARGEUR // 3, HAUTEUR // 3)
        images = []
        rangs = set()
        for photo in produit.photos.order_by("ordre"):
            vue = self.charger_media(photo.url)
            if vue is not None:
                images.append(vue.resize(petit, Image.LANCZOS))
                rangs.add(photo.ordre)

        # Completer avec les vues que le profil n'a pas retenues — celles-la
        # seulement : un apercu qui repasse deux fois sur la meme image serait
        # exactement le defaut qu'on vient de corriger.
        for ordre, cle, libelle in self.VUES:
            if ordre in rangs:
                continue
            images.append(self.dessiner_vue(produit, cle, libelle).resize(petit, Image.LANCZOS))

        if len(images) < 2:
            return ""

        images[0].save(
            destination, "WEBP", save_all=True, append_images=images[1:],
            duration=900, loop=0, quality=52, method=6,
        )
        return chemin_public

    def univers(self, nom):
        """La categorie parente, creee au besoin."""
        if not hasattr(self, "_univers"):
            self._univers = {}
        if nom not in self._univers:
            self._univers[nom], _ = Categorie.objects.get_or_create(
                slug=slugify(nom), defaults={"nom": nom}
            )
        return self._univers[nom]

    # ── Les images ───────────────────────────────────────────────────────

    def obtenir_image(self, nom_produit, source, categorie="Autres"):
        """Renvoie le chemin public de l'image, quelle que soit sa provenance."""
        slug = slugify(nom_produit)
        dossier = os.path.join(settings.MEDIA_ROOT, DOSSIER)
        os.makedirs(dossier, exist_ok=True)
        destination = os.path.join(dossier, f"{slug}.webp")
        chemin_public = f"{settings.MEDIA_URL}{DOSSIER}/{slug}.webp"

        if os.path.exists(destination):
            return chemin_public

        image = self.image_fournie(slug) or self.image_telechargee(source)
        if image is None:
            image = self.image_fabriquee(nom_produit, categorie)
            self.fabriquees += 1

        self.traiter(image).save(destination, "WEBP", quality=82, method=5)
        return chemin_public

    def image_fournie(self, slug):
        """Tes propres fichiers, s'ils existent. Ils priment sur tout le reste."""
        dossier = os.path.join(settings.RACINE.parent, "donnees-demo", "images")
        for extension in ("jpg", "jpeg", "png", "webp"):
            chemin = os.path.join(dossier, f"{slug}.{extension}")
            if os.path.exists(chemin):
                self.fournies += 1
                return Image.open(chemin)
        return None

    def image_telechargee(self, source):
        if self.hors_ligne:
            return None

        if source[0] == "unsplash":
            url = f"https://images.unsplash.com/photo-{source[1]}?w={LARGEUR}&q=80"
        else:
            # Le verrou fige la photo : sans lui, la meme adresse renvoie une
            # image differente a chaque appel, et le catalogue change de tete
            # a chaque peuplement.
            url = f"https://loremflickr.com/{LARGEUR}/{HAUTEUR}/{source[1]}?lock={source[2]}"
        try:
            donnees = urlopen(
                Request(url, headers={"User-Agent": "RivDinde/0.1 (projet etudiant)"}),
                timeout=12,
            ).read()
            image = Image.open(io.BytesIO(donnees))
            image.load()
            self.telecharges += 1
            return image
        except Exception:
            # Site injoignable, adresse morte, pas de reseau : on fabrique.
            return None

    # Les couleurs de remplacement, par univers. Elles viennent des jetons de
    # la maquette : une vignette fabriquee doit avoir l'air d'appartenir au
    # site, pas d'etre un trou.
    TEINTES = {
        "Restauration": ((251, 243, 232), (234, 140, 42), (184, 101, 15)),
        "High-tech": ((234, 240, 255), (37, 99, 235), (30, 64, 175)),
        "Maison": ((232, 248, 238), (22, 163, 74), (21, 128, 61)),
        "Autres": ((244, 245, 248), (91, 100, 120), (15, 20, 32)),
    }

    def image_fabriquee(self, nom_produit, categorie="Autres"):
        """Une vignette de remplacement ASSUMEE, pas un degrade au hasard.

        Le premier essai de peuplement etendu l'a montre sans appel : la
        recherche d'images par mots-cles rend n'importe quoi. Sur trente-quatre
        produits, vingt-cinq n'ont rien recu du tout, et parmi les neuf photos
        obtenues, un « poke bowl » etait une tasse posee sur un clavier et un
        « ecran 27 pouces » l'interieur d'un magasin.

        **Une photo fausse est pire qu'une absence de photo.** Elle fait douter
        de tout le reste du catalogue, et c'est exactement ce qu'on m'a
        reproche au bloc J.

        Cette vignette dit donc ce qu'elle est : le nom du produit, son
        univers, aux couleurs de la maquette. Elle est deterministe — le meme
        produit donne toujours la meme image — et elle a l'air d'appartenir au
        site plutot que d'etre un trou.
        """
        fond, accent, encre = self.TEINTES.get(
            UNIVERS.get(categorie, "Autres"), self.TEINTES["Autres"]
        )
        image = Image.new("RGB", (LARGEUR, HAUTEUR), fond)
        dessin = ImageDraw.Draw(image)

        # Un motif de cercles concentriques, decale selon le produit : deux
        # vignettes voisines ne doivent pas se ressembler au point qu'on croie
        # a un bogue d'affichage.
        graine = int(hashlib.md5(nom_produit.encode()).hexdigest()[:8], 16)
        centre_x = LARGEUR // 2 + (graine % 160) - 80
        centre_y = HAUTEUR // 2 + (graine // 160 % 90) - 45
        for rayon in range(430, 60, -46):
            teinte = tuple(
                int(f + (a - f) * (1 - rayon / 470) * 0.16)
                for f, a in zip(fond, accent, strict=True)
            )
            dessin.ellipse(
                [centre_x - rayon, centre_y - rayon, centre_x + rayon, centre_y + rayon],
                outline=teinte, width=2,
            )

        police = self.police

        # Le nom du produit, sur deux lignes au besoin : tronquer un nom de
        # produit dans sa propre vignette serait absurde.
        mots, lignes, courante = nom_produit.split(), [], ""
        for mot in mots:
            essai = f"{courante} {mot}".strip()
            if len(essai) > 20 and courante:
                lignes.append(courante)
                courante = mot
            else:
                courante = essai
        lignes.append(courante)

        grande = police(52)
        y = HAUTEUR // 2 - len(lignes) * 34
        for ligne in lignes[:3]:
            dessin.text((56, y), ligne, font=grande, fill=encre)
            y += 66

        petite = police(24)
        dessin.text((56, y + 12), categorie.upper(), font=petite, fill=accent)

        # Un trait d'accent en bas : ce qui distingue une vignette dessinee
        # d'une image ratee.
        dessin.rectangle([0, HAUTEUR - 10, LARGEUR, HAUTEUR], fill=accent)
        return image

    def traiter(self, image):
        """Le meme traitement qu'un televersement de vendeur (contrat-medias).

        Conversion, recadrage au format de la grille, retrait des metadonnees :
        une photo prise au telephone porte les coordonnees GPS de qui l'a prise.
        """
        image = image.convert("RGB")

        # Recadrage centre au format 4:3, pour que la grille du catalogue ne
        # soit pas un patchwork de hauteurs differentes.
        ratio_cible = LARGEUR / HAUTEUR
        largeur, hauteur = image.size
        if largeur / hauteur > ratio_cible:
            nouvelle_largeur = int(hauteur * ratio_cible)
            gauche = (largeur - nouvelle_largeur) // 2
            image = image.crop((gauche, 0, gauche + nouvelle_largeur, hauteur))
        else:
            nouvelle_hauteur = int(largeur / ratio_cible)
            haut = (hauteur - nouvelle_hauteur) // 2
            image = image.crop((0, haut, largeur, haut + nouvelle_hauteur))

        image = image.resize((LARGEUR, HAUTEUR), Image.LANCZOS)

        # Une image reconstruite depuis ses seuls pixels ne porte plus aucune
        # metadonnee — ni EXIF, ni GPS.
        propre = Image.new("RGB", image.size)
        propre.putdata(list(image.getdata()))
        return propre
