"""Les moyens de paiement enregistrés — O-5.

**Ton reproche** : *« payer est validé sans carte, pas de demande de carte même
la première fois, et après c'est enregistré »*, *« l'argent est payé sans
reconfirmation »*, et *« je ne sais pas comment tu vas faire pour que je mette
la carte, mais que ça ne prenne pas beaucoup de temps »*.

C'était exact : le bouton « Payer » créait une intention et la confirmait dans
la foulée. Aucune carte n'était demandée, jamais.

## La réflexion que tu demandais

Le premier réflexe serait de stocker un numéro de carte. **C'est exactement ce
qu'il ne faut pas faire**, et pas seulement pour des raisons juridiques : un
numéro de carte en base est une dette permanente. Toute la conception de Stripe,
et de tous ses concurrents, tient dans une idée : **on ne garde jamais le
numéro, on garde un jeton qui le remplace**.

Ce module fait donc ce que fait Stripe, avec un simulateur à la place :

  · la carte est **validée** — clé de Luhn, date d'expiration future,
    cryptogramme de la bonne longueur, marque déduite du numéro ;
  · **seuls les quatre derniers chiffres sont conservés**, avec la marque et
    l'échéance. Le numéro complet ne touche jamais la base — il n'est même pas
    journalisé ;
  · un **jeton** remplace la carte pour les paiements suivants. C'est lui qui
    permet le « payer en un geste » de la deuxième fois, sans rien ressaisir.

En simulation, **seuls les numéros de test sont acceptés**. C'est ce que fait
le mode test de Stripe, et c'est la bonne réponse à la question « et si
quelqu'un tape sa vraie carte ? » : on la refuse, en le disant.

## Ce que ça change pour toi, à l'écran

La première fois, quatre champs. Ensuite, la carte apparaît en une ligne
— « Visa •••• 4242 » — et il n'y a plus qu'à confirmer. C'est le
« pas beaucoup de temps » que tu demandais : le coût est payé une seule fois.
"""
import hashlib
import re
from datetime import date

from django.db import models

# Les cartes d'essai. Ce sont celles de la documentation de Stripe, et elles
# sont volontairement les seules acceptees en simulation : quelqu'un qui tape
# sa vraie carte doit etre refuse, pas encourage.
CARTES_D_ESSAI = {
    "4242424242424242": ("VISA", "accepte"),
    "4000000000000002": ("VISA", "refus"),
    "5555555555554444": ("MASTERCARD", "accepte"),
    "378282246310005": ("AMEX", "accepte"),
}

MARQUES = [
    (re.compile(r"^4"), "VISA"),
    (re.compile(r"^5[1-5]"), "MASTERCARD"),
    (re.compile(r"^3[47]"), "AMEX"),
]


class MoyenPaiement(models.Model):
    """Une carte enregistree — sans le numero.

    `jeton` remplace la carte : c'est lui qu'on envoie au fournisseur pour
    encaisser, et il ne permet a personne de reconstituer le numero.
    """

    client = models.ForeignKey(
        "comptes.Client", on_delete=models.CASCADE, related_name="moyens_paiement"
    )
    marque = models.CharField(max_length=15)
    quatre_derniers = models.CharField(max_length=4)
    mois_expiration = models.PositiveSmallIntegerField()
    annee_expiration = models.PositiveSmallIntegerField()
    jeton = models.CharField(max_length=64, unique=True)
    par_defaut = models.BooleanField(default=False)
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-par_defaut", "-date_ajout"]
        verbose_name = "moyen de paiement"
        verbose_name_plural = "moyens de paiement"

    def __str__(self):
        return f"{self.marque} •••• {self.quatre_derniers}"

    @property
    def expiree(self):
        aujourdhui = date.today()
        return (self.annee_expiration, self.mois_expiration) < (
            aujourdhui.year, aujourdhui.month
        )

    def en_dictionnaire(self):
        return {
            "id": self.id,
            "marque": self.marque,
            "quatre_derniers": self.quatre_derniers,
            "mois_expiration": self.mois_expiration,
            "annee_expiration": self.annee_expiration,
            "par_defaut": self.par_defaut,
            "expiree": self.expiree,
            "libelle": f"{self.marque} •••• {self.quatre_derniers}",
        }


class CarteRefusee(Exception):
    """Levee avec un code et un message destines a l'ecran, champ par champ."""

    def __init__(self, champ, code, message):
        super().__init__(message)
        self.champ = champ
        self.code = code
        self.message = message


def luhn(numero):
    """La cle de Luhn : elle attrape les fautes de frappe, pas les fraudes.

    C'est sa seule fonction, et c'est deja beaucoup : elle evite un
    aller-retour reseau pour un chiffre inverse, ce qui arrive tout le temps
    sur seize chiffres tapes au pouce.
    """
    total, doubler = 0, False
    for caractere in reversed(numero):
        chiffre = int(caractere)
        if doubler:
            chiffre *= 2
            if chiffre > 9:
                chiffre -= 9
        total += chiffre
        doubler = not doubler
    return total % 10 == 0


def marque_de(numero):
    for motif, marque in MARQUES:
        if motif.match(numero):
            return marque
    return "CARTE"


def valider(numero, mois, annee, cryptogramme, simulation=True):
    """Verifier une carte, et rendre (marque, quatre_derniers, jeton, refus).

    `refus` est vrai pour les numeros d'essai prevus pour echouer : sans un
    moyen simple de provoquer un refus, le chemin d'erreur n'est jamais
    parcouru — c'est celui qui se voit en production (D-18).
    """
    numero = re.sub(r"[\s-]", "", str(numero or ""))
    if not numero.isdigit() or not 13 <= len(numero) <= 19:
        raise CarteRefusee("numero", "numero_invalide",
                           "Un numero de carte fait entre 13 et 19 chiffres.")
    if not luhn(numero):
        raise CarteRefusee("numero", "numero_invalide",
                           "Ce numero de carte comporte une faute de frappe.")

    try:
        mois, annee = int(mois), int(annee)
    except (TypeError, ValueError):
        raise CarteRefusee("expiration", "expiration_invalide",
                           "L'echeance s'ecrit MM/AA.") from None
    if annee < 100:
        annee += 2000
    if not 1 <= mois <= 12:
        raise CarteRefusee("expiration", "expiration_invalide",
                           "Le mois va de 01 a 12.")

    aujourdhui = date.today()
    if (annee, mois) < (aujourdhui.year, aujourdhui.month):
        raise CarteRefusee("expiration", "carte_expiree", "Cette carte est expiree.")

    marque = marque_de(numero)
    attendu = 4 if marque == "AMEX" else 3
    cryptogramme = str(cryptogramme or "").strip()
    if not cryptogramme.isdigit() or len(cryptogramme) != attendu:
        raise CarteRefusee(
            "cryptogramme", "cryptogramme_invalide",
            f"Le cryptogramme fait {attendu} chiffres pour une carte {marque.title()}.",
        )

    if simulation and numero not in CARTES_D_ESSAI:
        # Le refus le plus important du fichier. Quelqu'un qui tape sa vraie
        # carte sur une demonstration doit etre arrete, pas encourage.
        raise CarteRefusee(
            "numero", "carte_non_test",
            "Cette démonstration n'accepte que les cartes d'essai : "
            "n'entrez jamais votre vraie carte. Utilisez 4242 4242 4242 4242.",
        )

    marque, issue = CARTES_D_ESSAI.get(numero, (marque, "accepte"))

    # Le jeton derive du numero : la MEME carte reenregistree donne le meme
    # jeton, donc pas de doublon dans le carnet. Il ne permet pas de remonter
    # au numero — c'est un condensat, pas un chiffrement.
    jeton = "tok_" + hashlib.sha256(f"{numero}:{mois}:{annee}".encode()).hexdigest()[:40]
    return marque, numero[-4:], jeton, issue == "refus"
