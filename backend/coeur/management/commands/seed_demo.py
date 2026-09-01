"""Peuple une base vide avec les personae du dossier de conception.

    python manage.py seed_demo

Les noms ne sont pas choisis au hasard : ce sont ceux de
plan-organisation/01-produit/scenarios.md. Quand un scenario parle de « Lea
commande chez Karim », on peut le derouler tel quel a l'ecran.

La commande est **idempotente** : la rejouer ne cree pas de doublon. Elle ne
touche jamais a un compte existant, ce qui permet de la lancer a chaque
demarrage sans reflechir.

Le mot de passe de demonstration est volontairement le meme pour tous et ecrit
en clair ici : c'est un jeu de donnees de vitrine, pas des comptes reels. Il
n'est cree que si DEBUG est actif ou si DEMO_AUTORISEE est mise.
"""
import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from comptes.models import (
    Adresse,
    Client,
    Gestionnaire,
    Livreur,
    Role,
    StatutCompte,
    StatutValidation,
    TypeGestionnaire,
    TypeService,
    Utilisateur,
    Vendeur,
)
from livraisons.models import Entrepot, ZoneLivraison

MOT_DE_PASSE_DEMO = "Demonstration!2026"


def adresse_unique(rue, code_postal, ville, **defauts):
    """Retrouver une adresse par sa rue, ou la creer.

    `Adresse.objects.get_or_create` explosait ici (`MultipleObjectsReturned`)
    des qu'une deuxieme adresse partageait la meme rue — ce qui arrive des
    qu'un client en saisit une au tunnel de commande. Le peuplement doit
    pouvoir se relancer sur une base vecue, pas seulement sur une base neuve.
    """
    existante = (
        Adresse.objects.filter(rue=rue, code_postal=code_postal, ville=ville)
        .order_by("id")
        .first()
    )
    if existante is not None:
        return existante, False
    return Adresse.objects.create(
        rue=rue, code_postal=code_postal, ville=ville, **defauts
    ), True


class Command(BaseCommand):
    help = "Cree les comptes et les lieux de demonstration."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not os.environ.get("DEMO_AUTORISEE"):
            raise CommandError(
                "seed_demo cree des comptes a mot de passe connu. "
                "Hors developpement, il faut poser DEMO_AUTORISEE=1 sciemment."
            )

        cree = []

        def utilisateur(email, prenom, nom, role, statut=StatutCompte.ACTIF):
            existant = Utilisateur.objects.filter(email=email).first()
            if existant:
                return existant, False
            compte = Utilisateur.objects.create_user(
                email=email, password=MOT_DE_PASSE_DEMO, prenom=prenom, nom=nom,
                role=role, statut_compte=statut,
            )
            cree.append(email)
            return compte, True

        # ── Les lieux ────────────────────────────────────────────────────
        adresse_entrepot, _ = adresse_unique(
            rue="12 rue de la Logistique", code_postal="69100", ville="Villeurbanne",
            libelle="Entrepot Est", latitude=45.7719, longitude=4.8902,
        )
        entrepot, _ = Entrepot.objects.get_or_create(
            nom="Entrepot Lyon-Est",
            defaults={"adresse": adresse_entrepot, "capacite": 5000},
        )
        zone, _ = ZoneLivraison.objects.get_or_create(
            nom="Lyon et couronne",
            defaults={
                "codes_postaux": "69001,69002,69003,69006,69007,69100",
                "entrepot": entrepot,
                "frais_base_centimes": 490,
                "seuil_gratuite_centimes": 5000,
            },
        )
        zone_nord, _ = ZoneLivraison.objects.get_or_create(
            nom="Lyon Nord",
            defaults={
                "codes_postaux": "69004,69005,69009,69300,69660",
                "entrepot": entrepot,
                "frais_base_centimes": 590,
                "seuil_gratuite_centimes": 6000,
            },
        )

        # Un second entrepot, dans une autre region : c'est la seule facon de
        # montrer qu'une tournee appartient a un entrepot et pas a la
        # plateforme entiere.
        adresse_entrepot_sud, _ = adresse_unique(
            rue="45 chemin des Docks", code_postal="13015", ville="Marseille",
            libelle="Entrepot Sud", latitude=43.3520, longitude=5.3480,
        )
        entrepot_sud, _ = Entrepot.objects.get_or_create(
            nom="Entrepot Marseille-Nord",
            defaults={"adresse": adresse_entrepot_sud, "capacite": 3000},
        )
        ZoneLivraison.objects.get_or_create(
            nom="Marseille et littoral",
            defaults={
                "codes_postaux": "13001,13002,13008,13015",
                "entrepot": entrepot_sud,
                "frais_base_centimes": 690,
                "seuil_gratuite_centimes": 7000,
            },
        )

        # ── Lea, cliente ─────────────────────────────────────────────────
        compte_lea, neuf = utilisateur("lea@exemple.fr", "Lea", "Martin", Role.CLIENT)
        client_lea, _ = Client.objects.get_or_create(utilisateur=compte_lea)
        adresse_lea, _ = adresse_unique(
            rue="8 rue Victor Hugo", code_postal="69002", ville="Lyon",
            libelle="Domicile", latitude=45.7550, longitude=4.8320, zone=zone,
            instructions_livraison="Code portail 4512, 3e etage.",
        )
        client_lea.adresses.through.objects.get_or_create(
            client=client_lea, adresse=adresse_lea, defaults={"est_principale": True}
        )

        # ── Karim, vendeur Express — et Nadia, son personnel ─────────────
        compte_karim, _ = utilisateur("karim@exemple.fr", "Karim", "Benali", Role.VENDEUR)
        adresse_karim, _ = adresse_unique(
            rue="24 cours Gambetta", code_postal="69003", ville="Lyon",
            libelle="Chez Karim", latitude=45.7545, longitude=4.8480, zone=zone,
        )
        vendeur_karim, _ = Vendeur.objects.get_or_create(
            utilisateur=compte_karim,
            defaults={
                "nom_boutique": "Chez Karim", "type_activite": TypeService.EXPRESS,
                "adresse": adresse_karim, "rayon_livraison_km": 6,
                "statut_validation": StatutValidation.VALIDE,
                "description": "Cuisine du marche, prete en quinze minutes.",
            },
        )
        compte_nadia, _ = utilisateur("nadia@exemple.fr", "Nadia", "Sow", Role.GESTIONNAIRE)
        Gestionnaire.objects.get_or_create(
            utilisateur=compte_nadia,
            defaults={"type_gestionnaire": TypeGestionnaire.STAFF_VENDEUR,
                      "vendeur": vendeur_karim},
        )

        # ── Sophie, vendeuse Standard ────────────────────────────────────
        compte_sophie, _ = utilisateur("sophie@exemple.fr", "Sophie", "Leroy", Role.VENDEUR)
        adresse_sophie, _ = adresse_unique(
            rue="5 avenue Jean Jaures", code_postal="69007", ville="Lyon",
            libelle="TechSophie", latitude=45.7420, longitude=4.8410, zone=zone,
        )
        Vendeur.objects.get_or_create(
            utilisateur=compte_sophie,
            defaults={
                "nom_boutique": "TechSophie", "type_activite": TypeService.STANDARD,
                "adresse": adresse_sophie,
                "statut_validation": StatutValidation.VALIDE,
                "description": "Electronique reconditionnee, garantie deux ans.",
            },
        )

        # ── Un vendeur qui attend, pour que l'ecran de validation ait
        #    quelque chose a montrer des le premier lancement ─────────────
        compte_ines, _ = utilisateur(
            "ines@exemple.fr", "Ines", "Haddad", Role.VENDEUR, StatutCompte.EN_ATTENTE
        )
        Vendeur.objects.get_or_create(
            utilisateur=compte_ines,
            defaults={"nom_boutique": "Fleurs d'Ines", "type_activite": TypeService.EXPRESS},
        )

        # ── Amine (Express) et Julien (Standard) ─────────────────────────
        compte_amine, _ = utilisateur("amine@exemple.fr", "Amine", "Cherif", Role.LIVREUR)
        Livreur.objects.get_or_create(
            utilisateur=compte_amine,
            defaults={"mode_livraison": TypeService.EXPRESS, "vehicule": "VELO",
                      "statut_validation": StatutValidation.VALIDE},
        )
        compte_julien, _ = utilisateur("julien@exemple.fr", "Julien", "Moreau", Role.LIVREUR)
        Livreur.objects.get_or_create(
            utilisateur=compte_julien,
            defaults={"mode_livraison": TypeService.STANDARD, "vehicule": "CAMIONNETTE",
                      "entrepot": entrepot, "statut_validation": StatutValidation.VALIDE},
        )

        # ── Rachid, gestionnaire d'entrepot ──────────────────────────────
        compte_rachid, _ = utilisateur("rachid@exemple.fr", "Rachid", "Amrani", Role.GESTIONNAIRE)
        Gestionnaire.objects.get_or_create(
            utilisateur=compte_rachid,
            defaults={"type_gestionnaire": TypeGestionnaire.STAFF_ENTREPOT, "entrepot": entrepot},
        )

        # -- D'autres clients, ailleurs -----------------------------------
        # Un seul client a Lyon ne prouve rien. Marc habite Paris : aucune
        # boutique Express ne le livre, et c'est justement ce que le filtrage
        # par rayon (D-09) doit rendre visible. Ines est a Marseille.
        def client(email, prenom, nom, rue, cp, ville, lat, lon, zone_client=None,
                   instructions=""):
            compte, _ = utilisateur(email, prenom, nom, Role.CLIENT)
            profil, _ = Client.objects.get_or_create(utilisateur=compte)
            adresse, _ = adresse_unique(
                rue=rue, code_postal=cp, ville=ville,
                libelle="Domicile", latitude=lat, longitude=lon,
                zone=zone_client, instructions_livraison=instructions,
            )
            profil.adresses.through.objects.get_or_create(
                client=profil, adresse=adresse, defaults={"est_principale": True}
            )
            return profil, adresse

        client("marc@exemple.fr", "Marc", "Dubois", "17 rue de Charonne", "75011", "Paris",
               48.8540, 2.3790, None, "Interphone au nom de Dubois.")
        client("ines.client@exemple.fr", "Ines", "Nadir", "3 rue de la Republique", "13001",
               "Marseille", 43.2965, 5.3760, None)
        client("theo@exemple.fr", "Theo", "Girard", "22 rue Sebastien Gryphe", "69007", "Lyon",
               45.7480, 4.8400, zone, "Laisser chez le gardien si absent.")
        client("awa@exemple.fr", "Awa", "Diop", "6 rue Duquesne", "69006", "Lyon",
               45.7690, 4.8480, zone)

        # Une deuxieme adresse pour Lea : un carnet d'adresses qui n'en
        # contient qu'une ne se demontre pas.
        adresse_bureau, _ = adresse_unique(
            rue="52 rue de la Republique", code_postal="69002", ville="Lyon",
            libelle="Bureau", latitude=45.7620, longitude=4.8360, zone=zone,
            instructions_livraison="Accueil du 2e etage.",
        )
        client_lea.adresses.through.objects.get_or_create(
            client=client_lea, adresse=adresse_bureau, defaults={"est_principale": False}
        )

        # -- Deux boutiques de plus, et deux cas limites -------------------
        def boutique(email, prenom, nom, nom_boutique, service, rue, cp, ville, lat, lon,
                     statut=StatutValidation.VALIDE, description="", rayon=6,
                     statut_compte=StatutCompte.ACTIF):
            compte, _ = utilisateur(email, prenom, nom, Role.VENDEUR, statut_compte)
            adresse, _ = adresse_unique(
                rue=rue, code_postal=cp, ville=ville,
                libelle=nom_boutique, latitude=lat, longitude=lon,
            )
            profil, _ = Vendeur.objects.get_or_create(
                utilisateur=compte,
                defaults={"nom_boutique": nom_boutique, "type_activite": service,
                          "adresse": adresse, "rayon_livraison_km": rayon,
                          "statut_validation": statut, "description": description},
            )
            return profil

        boutique("yasmine@exemple.fr", "Yasmine", "Bouali", "Le Fournil d a cote",
                 TypeService.EXPRESS, "9 rue Paul Bert", "69003", "Lyon", 45.7605, 4.8530,
                 description="Pains au levain et viennoiseries, cuits toute la journee.",
                 rayon=4)
        boutique("olivier@exemple.fr", "Olivier", "Perrin", "Maison Perrin",
                 TypeService.STANDARD, "14 quai Saint-Antoine", "69002", "Lyon", 45.7635, 4.8290,
                 description="Epicerie fine, expediee sous quarante-huit heures.")

        # Une boutique Express trop loin de Lyon : elle prouve que le rayon
        # ecarte reellement au lieu de trier.
        boutique("nour@exemple.fr", "Nour", "Bensaid", "Marseille Grill",
                 TypeService.EXPRESS, "18 rue Sainte", "13001", "Marseille", 43.2930, 5.3730,
                 description="Grillades a emporter, livrees dans le centre.", rayon=5)

        # Un dossier refuse : l'ecran de validation doit montrer aussi ce
        # qu'on a refuse, sinon on ne sait jamais ce qu'un dossier est devenu.
        boutique("hugo@exemple.fr", "Hugo", "Lemaitre", "Hugo Deals",
                 TypeService.STANDARD, "3 rue du Doyenne", "69005", "Lyon", 45.7620, 4.8270,
                 statut=StatutValidation.REJETE,
                 description="Dossier incomplet : SIRET non verifiable.",
                 statut_compte=StatutCompte.EN_ATTENTE)

        # Un dossier QUI ATTEND. Il manquait, et son absence rendait l'ecran
        # de validation vide : un administrateur arrivait sur « rien a
        # valider » et ne pouvait rien demontrer (scenario 14.2).
        boutique("camille@exemple.fr", "Camille", "Roux", "L Atelier Camille",
                 TypeService.STANDARD, "22 rue Sergent Blandan", "69001", "Lyon",
                 45.7720, 4.8320,
                 statut=StatutValidation.EN_ATTENTE,
                 description="Ceramique artisanale, pieces uniques. Dossier depose il y a "
                             "deux jours, en attente de verification du SIRET.",
                 statut_compte=StatutCompte.EN_ATTENTE)

        # Une boutique SUSPENDUE, et son compte avec : c'est le scenario 10.3,
        # et c'est aussi la preuve visible qu'on suspend sans supprimer (D-61).
        # Son catalogue disparait de la vitrine sans que rien ne soit efface.
        boutique("gaelle@exemple.fr", "Gaelle", "Morvan", "Morvan Primeurs",
                 TypeService.EXPRESS, "7 rue de la Charite", "69002", "Lyon", 45.7550, 4.8320,
                 statut=StatutValidation.SUSPENDU,
                 description="Suspendue le temps d une verification : trois litiges "
                             "ouverts en deux semaines sur des colis incomplets.",
                 statut_compte=StatutCompte.SUSPENDU, rayon=5)

        # -- Du personnel, des deux cotes ---------------------------------
        vendeur_sophie = Vendeur.objects.filter(nom_boutique="TechSophie").first()
        if vendeur_sophie:
            compte_lucas, _ = utilisateur("lucas@exemple.fr", "Lucas", "Fabre", Role.GESTIONNAIRE)
            Gestionnaire.objects.get_or_create(
                utilisateur=compte_lucas,
                defaults={"type_gestionnaire": TypeGestionnaire.STAFF_VENDEUR,
                          "vendeur": vendeur_sophie},
            )

        compte_samir, _ = utilisateur("samir@exemple.fr", "Samir", "Kaci", Role.GESTIONNAIRE)
        Gestionnaire.objects.get_or_create(
            utilisateur=compte_samir,
            defaults={"type_gestionnaire": TypeGestionnaire.STAFF_ENTREPOT,
                      "entrepot": entrepot_sud},
        )

        # -- Des livreurs, dont un qui attend sa validation ---------------
        compte_sonia, _ = utilisateur("sonia@exemple.fr", "Sonia", "Marchand", Role.LIVREUR)
        Livreur.objects.get_or_create(
            utilisateur=compte_sonia,
            defaults={"mode_livraison": TypeService.EXPRESS, "vehicule": "SCOOTER",
                      "statut_validation": StatutValidation.VALIDE},
        )
        compte_bruno, _ = utilisateur(
            "bruno@exemple.fr", "Bruno", "Vidal", Role.LIVREUR, StatutCompte.EN_ATTENTE
        )
        Livreur.objects.get_or_create(
            utilisateur=compte_bruno,
            defaults={"mode_livraison": TypeService.STANDARD, "vehicule": "CAMIONNETTE",
                      "entrepot": entrepot_sud},
        )

        # Le catalogue vient juste apres les boutiques : une vitrine sans
        # produit ne prouve rien et ne se montre pas.
        call_command("seed_catalogue")
        # Puis la vie de la plateforme : des commandes dans tous leurs etats,
        # des livraisons, des tournees, des avis, des litiges.
        call_command("seed_activite")

        self.stdout.write("")
        if cree:
            self.stdout.write(
                self.style.SUCCESS(f"Jeu de demonstration : {len(cree)} compte(s) cree(s).")
            )
        else:
            self.stdout.write(self.style.SUCCESS("Jeu de demonstration deja en place."))
        self.stdout.write(f"  Mot de passe commun : {self.style.WARNING(MOT_DE_PASSE_DEMO)}")
        self.stdout.write("")
        for email, qui in [
            ("lea@exemple.fr", "cliente, Lyon, deux adresses, commandes en cours"),
            ("marc@exemple.fr", "client, PARIS - aucune boutique Express ne le livre"),
            ("theo@exemple.fr", "client, Lyon, une commande annulee et un litige"),
            ("awa@exemple.fr", "cliente, Lyon, commandes livrees et avis deposes"),
            ("ines.client@exemple.fr", "cliente, Marseille"),
            ("karim@exemple.fr", "vendeur Express valide - Chez Karim"),
            ("sophie@exemple.fr", "vendeuse Standard validee - TechSophie"),
            ("yasmine@exemple.fr", "vendeuse Express validee - Le Fournil d a cote"),
            ("olivier@exemple.fr", "vendeur Standard valide - Maison Perrin"),
            ("nour@exemple.fr", "vendeur Express a Marseille - hors rayon depuis Lyon"),
            ("ines@exemple.fr", "vendeuse EN ATTENTE de validation"),
            ("hugo@exemple.fr", "vendeur REFUSE"),
            ("nadia@exemple.fr", "gestionnaire, personnel de Karim"),
            ("lucas@exemple.fr", "gestionnaire, personnel de Sophie"),
            ("rachid@exemple.fr", "gestionnaire, entrepot Lyon-Est"),
            ("samir@exemple.fr", "gestionnaire, entrepot Marseille-Nord"),
            ("amine@exemple.fr", "livreur Express (velo)"),
            ("sonia@exemple.fr", "livreuse Express (scooter)"),
            ("julien@exemple.fr", "livreur Standard, tournees"),
            ("bruno@exemple.fr", "livreur EN ATTENTE de validation"),
        ]:
            self.stdout.write(f"  {email:<24} {qui}")
        self.stdout.write("")
