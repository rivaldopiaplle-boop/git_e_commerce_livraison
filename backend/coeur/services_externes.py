"""Les services payants, derriere une interface, avec un simulateur — D-18.

La regle vient du bloc C et elle vaut pour tout ce qui coute de l'argent ou
demande une cle : **on programme contre une interface, jamais contre le
fournisseur**. Deux implementations existent alors :

  · le **simulateur**, qui repond des donnees plausibles sans reseau ni cle.
    C'est lui qui tourne en developpement, dans les tests et sur la vitrine ;
  · le **vrai fournisseur**, choisi par une variable d'environnement le jour
    ou une cle existe.

Ce que ca evite, concretement :

  1. **Le projet se demontre sans cle.** Un recruteur clone le depot et tout
     marche, y compris le paiement et l'assistant.
  2. **Les tests ne touchent jamais le reseau** (D-37) : ils sont
     reproductibles, et ils passent dans une chaine d'integration sans
     secrets.
  3. **Le jour ou la cle arrive, un seul fichier change** — pas trente appels
     eparpilles dans les vues.
"""
import hashlib
import os
import random
from dataclasses import dataclass

# ═══════════════════════════════════════════════════════════════════════════
#  Le paiement (D-12, D-18)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class IntentionPaiement:
    """Ce qu'un fournisseur de paiement rend quand on ouvre un paiement.

    `secret_client` est ce que le navigateur utilise pour finir le paiement ;
    `reference` est ce qu'on garde en base pour rapprocher plus tard.
    """

    reference: str
    secret_client: str
    montant_centimes: int
    statut: str
    simule: bool


class PaiementSimule:
    """Un fournisseur de paiement qui ne debite rien et ne demande aucune cle.

    Il est **deterministe** : le meme montant donne toujours la meme reference.
    Une demonstration dont les identifiants changent a chaque relance est
    impossible a scenariser.

    Il sait aussi **echouer** : un montant se terminant par 99 centimes est
    refuse. Sans un moyen simple de provoquer un echec, le chemin d'erreur
    n'est jamais teste — et c'est celui qui se voit en production.
    """

    nom = "simulateur"

    def ouvrir(self, montant_centimes: int, reference_commande: str) -> IntentionPaiement:
        graine = hashlib.sha256(reference_commande.encode()).hexdigest()[:16]
        refuse = montant_centimes % 100 == 99
        return IntentionPaiement(
            reference=f"pi_sim_{graine}",
            secret_client=f"pi_sim_{graine}_secret",
            montant_centimes=montant_centimes,
            statut="REFUSE" if refuse else "AUTORISE",
            simule=True,
        )

    def capturer(self, reference: str) -> str:
        return "ECHOUE" if reference.endswith("99") else "CAPTURE"

    def rembourser(self, reference: str, montant_centimes: int) -> str:
        return "REMBOURSE"


class PaiementStripe:
    """Le vrai fournisseur. Il n'entre en jeu que si une cle existe.

    Volontairement non implemente tant que la cle n'est pas la : ecrire du
    code qu'on ne peut ni lancer ni tester donne une fausse impression
    d'avancement, et il faudrait le reecrire de toute facon en le confrontant
    a l'API reelle.
    """

    nom = "stripe"

    def __init__(self, cle: str):
        self.cle = cle

    def ouvrir(self, montant_centimes: int, reference_commande: str) -> IntentionPaiement:
        raise NotImplementedError(
            "Le branchement Stripe s'ecrira avec la cle sous la main. "
            "En attendant, le simulateur couvre le parcours complet."
        )

    def capturer(self, reference: str) -> str:
        raise NotImplementedError

    def rembourser(self, reference: str, montant_centimes: int) -> str:
        raise NotImplementedError


def fournisseur_de_paiement():
    """Le simulateur, sauf si une cle Stripe est presente."""
    cle = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    return PaiementStripe(cle) if cle else PaiementSimule()


# ═══════════════════════════════════════════════════════════════════════════
#  L'assistant (D-43)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class ReponseAssistant:
    texte: str
    sources: list
    simule: bool


class AssistantSimule:
    """Un assistant qui repond sans modele, a partir de ce que la base sait.

    D-43 range l'agent en deux temps : **les recommandations d'abord**, puis
    l'assistant de support. Les deux se font sans modele de langage tant qu'on
    n'en a pas :

      · une recommandation, c'est « ce que les gens qui ont achete ceci ont
        aussi achete » — une requete, pas une intelligence ;
      · une question de support porte neuf fois sur dix sur une commande
        precise, et la reponse est **dans la base**. Un modele qui invente une
        date de livraison serait bien pire qu'une reponse exacte et seche.

    Ce qu'un modele apporterait vraiment : la reformulation, et les questions
    ouvertes. C'est pour cela que l'interface existe — pour le brancher sans
    rien changer d'autre.
    """

    nom = "simulateur"

    # Ce que l'assistant sait repondre sans rien inventer. L'ordre compte :
    # la premiere entree dont un mot-cle apparait gagne.
    CONNAISSANCES = [
        (
            ("livraison", "livree", "quand", "arrive", "recu"),
            "Le suivi de votre commande est dans « Mes commandes » : chaque etape y "
            "figure, de la preparation a la remise. Une commande Express arrive en "
            "general en moins de quarante minutes ; une commande Standard passe par "
            "un entrepot et met de vingt-quatre a soixante-douze heures.",
        ),
        (
            ("rupture", "stock", "indisponible", "epuise"),
            "Un produit en rupture reste visible au catalogue, avec son bouton d'achat "
            "gele et un bouton « Etre alerte quand il revient ». Vous serez prevenu des "
            "que le vendeur le reapprovisionne.",
        ),
        (
            ("avis", "noter", "note", "commentaire"),
            "Vous pouvez noter la boutique, chaque produit recu et le livreur, une fois "
            "la commande livree. On ne note que ce qu'on a recu : c'est ce qui rend les "
            "avis credibles.",
        ),
        (
            ("annuler", "annulation", "rembours"),
            "Une commande s'annule tant que le vendeur ne l'a pas preparee. Ensuite, "
            "ouvrez un litige depuis la commande : le vendeur a quarante-huit heures "
            "pour repondre, et un administrateur tranche avec les deux versions sous "
            "les yeux.",
        ),
        (
            ("plusieurs", "separe", "deux commandes", "scinde"),
            "Un panier qui melange plusieurs boutiques donne plusieurs commandes, "
            "livrees separement — mais un seul paiement. Les boutiques Express sont "
            "livrees en direct, les Standard regroupees par un entrepot.",
        ),
        (
            ("adresse", "demenage", "code postal"),
            "Votre adresse principale decide des boutiques Express visibles au "
            "catalogue : celles qui ne livrent pas chez vous n'apparaissent jamais. "
            "Changez-la dans « Mes adresses ».",
        ),
        (
            ("paiement", "carte", "payer"),
            "Le paiement est en mode simulation sur cette demonstration : aucune carte "
            "n'est debitee et aucune donnee bancaire n'est demandee.",
        ),
    ]

    def repondre(self, question: str, contexte: dict | None = None) -> ReponseAssistant:
        minuscule = question.lower()
        for mots, reponse in self.CONNAISSANCES:
            if any(mot in minuscule for mot in mots):
                return ReponseAssistant(texte=reponse, sources=["base de connaissances"],
                                        simule=True)

        # Ne rien savoir se dit. Un assistant qui repond n'importe quoi plutot
        # que « je ne sais pas » detruit la confiance en trois echanges.
        return ReponseAssistant(
            texte=(
                "Je ne sais pas repondre a cette question. Vous pouvez ouvrir un "
                "signalement depuis la commande concernee : un humain la reprendra avec "
                "tout le contexte, sans que vous ayez a tout ressaisir."
            ),
            sources=[],
            simule=True,
        )

    def recommander(self, produits_vus: list, catalogue: list, combien: int = 4) -> list:
        """« Ceux qui ont regarde ceci ont aussi regarde. »

        Sans historique — un visiteur qui arrive — on rend les meilleures
        ventes plutot que rien : c'est ce que font les vraies places de
        marche, et c'est honnete de l'appeler autrement.
        """
        if not catalogue:
            return []
        if not produits_vus:
            return catalogue[:combien]

        categories = {p.get("categorie") for p in produits_vus if p.get("categorie")}
        proches = [
            produit for produit in catalogue
            if produit.get("categorie") in categories
            and produit["id"] not in {p["id"] for p in produits_vus}
        ]
        # Une graine fixe : la meme visite donne les memes suggestions, sans
        # quoi la page changerait a chaque rafraichissement.
        melangeur = random.Random(sum(p["id"] for p in produits_vus))
        melangeur.shuffle(proches)
        return (proches or catalogue)[:combien]


class AssistantParApi:
    """Le vrai assistant, quand une cle de modele existe (D-43).

    Non implemente pour la meme raison que Stripe : du code non testable
    donne une fausse impression d'avancement.
    """

    nom = "api"

    def __init__(self, cle: str):
        self.cle = cle

    def repondre(self, question: str, contexte: dict | None = None) -> ReponseAssistant:
        raise NotImplementedError(
            "Le branchement du modele s'ecrira avec la cle sous la main."
        )

    def recommander(self, produits_vus: list, catalogue: list, combien: int = 4) -> list:
        raise NotImplementedError


def assistant():
    cle = os.environ.get("CLE_MODELE_IA", "").strip()
    return AssistantParApi(cle) if cle else AssistantSimule()
