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
import json
import logging
import os
import random
from dataclasses import dataclass
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


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

    **Le refus est inscrit dans la reference**, par un prefixe, et non deduit
    de ses derniers caracteres. La premiere version rendait `ECHOUE` pour
    toute reference finissant par « 99 » — or la reference est un condensat du
    numero de commande, qui n'a rien a voir avec le montant. Une commande sur
    deux cent cinquante-six echouait donc **au hasard**, sans que rien
    l'explique, ni a l'ecran ni dans les journaux.

    C'est un test intermittent qui l'a revele, et c'etait bien pire qu'un test
    intermittent : la meme loterie tournait dans la demonstration.
    """

    nom = "simulateur"

    #: Ce qui marque une intention vouee a l'echec. Le simulateur est le seul
    #: a fabriquer ses references, donc le seul a poser ce prefixe.
    PREFIXE_REFUS = "pi_sim_refuse_"

    def ouvrir(self, montant_centimes: int, reference_commande: str) -> IntentionPaiement:
        graine = hashlib.sha256(reference_commande.encode()).hexdigest()[:16]
        refuse = montant_centimes % 100 == 99
        reference = f"{self.PREFIXE_REFUS if refuse else 'pi_sim_'}{graine}"
        return IntentionPaiement(
            reference=reference,
            secret_client=f"{reference}_secret",
            montant_centimes=montant_centimes,
            statut="REFUSE" if refuse else "AUTORISE",
            simule=True,
        )

    def capturer(self, reference: str) -> str:
        return "ECHOUE" if reference.startswith(self.PREFIXE_REFUS) else "CAPTURE"

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
    """Le vrai assistant, quand une cle de modele existe (D-43, D-141).

    **Un modele de langage branche sur un catalogue est un generateur de faux
    delais de livraison** si on le laisse repondre librement. C'est le risque
    principal, et il est traite ici par la construction, pas par une consigne
    polie :

      · le modele ne recoit QUE la base de connaissances du simulateur et le
        contexte de la personne. Rien d'autre. Il n'a pas acces a la base ;
      · la consigne systeme lui interdit d'inventer un delai, un prix, un
        statut ou une politique qui ne sont pas dans ce qu'on lui donne, et
        lui demande de dire qu'il ne sait pas plutot que de meubler ;
      · la reponse est bornee en longueur : un assistant de support qui ecrit
        six paragraphes n'est pas lu.

    Ce que le modele apporte reellement par rapport au simulateur : la
    **reformulation** — comprendre « ma commande est ou ? » comme « livraison »
    — et les questions ouvertes qu'aucune liste de mots-cles n'attrape.

    **Il ne recommande pas.** Une recommandation, c'est « ce que les gens qui
    ont achete ceci ont aussi achete » : une requete. Payer un modele pour
    melanger une liste serait plus lent, plus cher et moins juste que le
    simulateur, qui garde donc ce role.
    """

    nom = "mistral"

    # Compatible avec l'API de Mistral, et avec toute API qui parle le meme
    # dialecte que `chat/completions` — c'est devenu le format commun.
    ADRESSE = "https://api.mistral.ai/v1/chat/completions"
    MODELE_PAR_DEFAUT = "mistral-small-latest"

    # Six secondes : au-dela, la personne a deja referme le volet. Mieux vaut
    # la reponse seche du simulateur tout de suite qu'une belle reponse trop
    # tard.
    DELAI_SECONDES = 6

    CONSIGNE = (
        "Tu es l'assistant de RivDinde, une place de marche de livraison. "
        "Tu reponds en francais, en trois phrases au maximum, sur un ton simple.\n\n"
        "REGLE ABSOLUE : tu ne reponds QU'A PARTIR des informations ci-dessous. "
        "Tu n'inventes jamais un delai, un prix, un statut de commande, un numero "
        "de commande ni une politique commerciale. Si la reponse ne s'y trouve pas, "
        "tu dis que tu ne sais pas et tu invites la personne a ouvrir un "
        "signalement depuis la commande concernee.\n\n"
        "Ce que tu sais :\n{connaissances}"
    )

    def __init__(self, cle: str, modele: str = ""):
        self.cle = cle
        self.modele = modele or os.environ.get("MODELE_IA", "").strip() or self.MODELE_PAR_DEFAUT
        # Le simulateur reste la, et sert de filet : voir `repondre`.
        self.repli = AssistantSimule()

    def _connaissances(self) -> str:
        return "\n".join(f"- {reponse}" for _, reponse in AssistantSimule.CONNAISSANCES)

    def repondre(self, question: str, contexte: dict | None = None) -> ReponseAssistant:
        """Interroger le modele — et retomber sur le simulateur si quoi que ce soit rate.

        Cle expiree, quota depasse, reseau coupe, service en panne : aucun de
        ces cas ne doit rendre l'assistant muet. La demonstration doit tenir
        debout sans reseau (D-18), et une reponse seche vaut mieux qu'une
        erreur affichee a un visiteur.
        """
        situation = ""
        if contexte:
            role = contexte.get("role")
            ecran = contexte.get("ecran")
            if role:
                situation += f"\nLa personne est connectee en tant que {role}."
            if ecran:
                situation += f"\nElle est sur l'ecran : {ecran}."

        corps = json.dumps({
            "model": self.modele,
            "messages": [
                {"role": "system",
                 "content": self.CONSIGNE.format(connaissances=self._connaissances()) + situation},
                {"role": "user", "content": question[:1000]},
            ],
            # Peu de creativite : on veut une reformulation fidele, pas une
            # invention. Et une reponse courte, qui sera lue.
            "temperature": 0.2,
            "max_tokens": 320,
        }).encode()

        requete = Request(
            self.ADRESSE, data=corps, method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.cle}",
            },
        )
        try:
            with urlopen(requete, timeout=self.DELAI_SECONDES) as reponse:
                charge = json.loads(reponse.read())
            texte = charge["choices"][0]["message"]["content"].strip()
        except Exception as souci:  # noqa: BLE001 — tout echec mene au repli
            logger.warning("Assistant %s indisponible (%s) : repli sur le simulateur.",
                           self.modele, type(souci).__name__)
            return self.repli.repondre(question, contexte)

        if not texte:
            return self.repli.repondre(question, contexte)

        return ReponseAssistant(
            texte=texte,
            # La source nomme le modele : une reponse rediger par une machine
            # doit se presenter comme telle.
            sources=[f"modele {self.modele}"],
            simule=False,
        )

    def recommander(self, produits_vus: list, catalogue: list, combien: int = 4) -> list:
        """Deleguee au simulateur, volontairement : ce n'est pas un travail de modele."""
        return self.repli.recommander(produits_vus, catalogue, combien)


def assistant():
    """L'assistant en service : le vrai s'il y a une cle, le simulateur sinon.

    Aucune variable a basculer, aucun drapeau : **poser la cle suffit**, et la
    retirer suffit a revenir au simulateur. C'est ce qui rend la demonstration
    faisable sans reseau et sans compte chez qui que ce soit (D-18).
    """
    cle = os.environ.get("CLE_MODELE_IA", "").strip()
    return AssistantParApi(cle) if cle else AssistantSimule()
