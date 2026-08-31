"""Le fil d'evenements du projet — D-62, D-95.

C'est le trou de conception que le bloc L a mis au jour, et il etait le meme
partout : **une action changeait une ligne en base et s'arretait la**. Valider
un vendeur ne prevenait pas le vendeur. Suspendre un compte ne laissait aucune
trace. Ajuster un stock n'apparaissait nulle part chez le proprietaire de la
boutique.

Le principe, en une phrase : **toute action sensible emet un evenement**, et
des abonnes en tirent les consequences. Chaque abonne fait UNE chose :

    journaliser   ecrit l'entree du journal d'audit (qui, quoi, sur quoi,
                  avant, apres, quand, pourquoi)
    notifier      previent les personnes concernees, avec le lien vers
                  l'ecran ou agir

Ce n'est pas un patron inutile ici : sans lui, chaque vue devrait se souvenir
d'ecrire dans le journal ET de notifier trois personnes differentes, et elle
finirait par en oublier une — ce qui est exactement ce qui s'est passe.

Le declenchement reste **synchrone** : pas de file d'attente, pas de courtier
de messages. Ecrire deux lignes de plus dans la meme transaction coute moins
cher que d'heberger un Redis, et [D-16](journal-decisions) a deja tranche
contre l'infrastructure temps reel au MVP.
"""
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Evenement:
    """Ce qui vient de se passer, decrit une seule fois.

    `destinataires` porte des utilisateurs, pas des adresses : c'est le service
    de notification qui sait par quel canal les joindre, selon leurs
    preferences.
    """

    nom: str
    acteur: Any = None
    objet: Any = None
    type_objet: str = ""
    id_objet: int | None = None
    titre: str = ""
    message: str = ""
    lien: str = ""
    motif: str = ""
    avant: dict | None = None
    apres: dict | None = None
    destinataires: list = field(default_factory=list)


_ABONNES: list[Callable[[Evenement], None]] = []


def abonner(fonction):
    """Enregistre un abonne. Utilisable comme decorateur."""
    _ABONNES.append(fonction)
    return fonction


def emettre(evenement: Evenement):
    """Previent tous les abonnes.

    Un abonne qui echoue ne doit pas faire echouer l'action metier : on ne
    refuse pas une validation de vendeur parce que l'envoi d'une notification
    a rate. L'erreur est signalee, l'action tient.
    """
    for abonne in list(_ABONNES):
        try:
            abonne(evenement)
        except Exception as souci:  # noqa: BLE001 - on ne casse jamais l'action metier
            import logging

            logging.getLogger("rivdinde.evenements").warning(
                "abonne %s en echec sur %s : %s", abonne.__name__, evenement.nom, souci
            )


# ═══════════════════════════════════════════════════════════════════════════
#  Les abonnes
# ═══════════════════════════════════════════════════════════════════════════


@abonner
def journaliser(evenement: Evenement):
    """Ecrit l'entree du journal d'audit (D-95).

    Six questions, une reponse chacune : qui, quoi, sur quoi, avant, apres,
    quand. Le pourquoi rejoint `donnees_apres` quand un motif est donne — un
    refus sans motif ne se relit pas.
    """
    from engagement.models import JournalAudit

    apres = dict(evenement.apres or {})
    if evenement.motif:
        apres["motif"] = evenement.motif

    JournalAudit.objects.create(
        utilisateur=evenement.acteur if getattr(evenement.acteur, "pk", None) else None,
        action=evenement.nom,
        type_objet=evenement.type_objet or "",
        id_objet=evenement.id_objet,
        donnees_avant=evenement.avant or None,
        donnees_apres=apres or None,
    )


@abonner
def notifier(evenement: Evenement):
    """Previent chaque personne concernee, avec le lien vers l'ecran ou agir.

    Le canal dans l'application est toujours ecrit : une information critique
    n'a jamais un canal unique (scenario 12.1). Le courriel et la notification
    poussee suivent les preferences du destinataire — et le jour ou le service
    d'envoi existera, il lira ces memes lignes.
    """
    from engagement.models import CanalNotification, Notification

    if not evenement.destinataires or not evenement.titre:
        return

    vus = set()
    for destinataire in evenement.destinataires:
        identifiant = getattr(destinataire, "pk", None)
        if identifiant is None or identifiant in vus:
            continue
        vus.add(identifiant)
        Notification.objects.create(
            utilisateur=destinataire,
            type=evenement.nom,
            titre=evenement.titre[:150],
            contenu=evenement.message,
            lien_action=evenement.lien[:200],
            canal=CanalNotification.IN_APP,
        )
