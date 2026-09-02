"""Les noms de variables d'environnement s'accordent — M-4.

Trois fichiers nommaient les memes reglages differemment :

  · `render.yaml` posait `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` et
    `CLOUDINARY_URL` ; les reglages lisent `ALLOWED_HOSTS`, `CORS_ORIGINS` et
    trois variables Cloudinary distinctes ;
  · `.env.example` proposait `STRIPE_CLE_SECRETE` et `AI_API_KEY` ; le code lit
    `STRIPE_SECRET_KEY` et `CLE_MODELE_IA`.

**Chaque desaccord desactive une fonctionnalite EN SILENCE.** La variable
existe, personne ne la lit, la valeur par defaut s'applique, et rien ne le
signale — ni erreur, ni journal. Le front deploye se serait fait refuser par le
navigateur au premier appel, et on aurait cherche du cote du reseau.

Ce test compare donc ce que le CODE lit a ce que la CONFIGURATION propose, dans
les deux sens.
"""
import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
RACINE = BACKEND.parent

# Les modules du projet, sans la bibliotheque standard ni les dependances.
APPLICATIONS = [
    "catalogue", "coeur", "commandes", "comptes", "config",
    "engagement", "livraisons", "paiements",
]

LECTURE = re.compile(r"(?:os\.environ\.get|env|env_liste|env_bool)\(\s*\"([A-Z_]{3,})\"")

# Ce qui est declare pour plus tard, sciemment. Les laisser sans explication
# ferait croire qu'ils sont branches ; les retirer ferait perdre le nom exact
# a poser le jour ou on branche le service.
PAS_ENCORE_LUES = {
    # Le paiement reel : la cle publique et la signature du webhook ne servent
    # qu'une fois `PaiementStripe` ecrit (D-18).
    "STRIPE_CLE_PUBLIQUE",
    "STRIPE_WEBHOOK_SECRET",
    # L'envoi d'e-mails par une API plutot que par SMTP.
    "EMAIL_API_KEY",
    # Le geocodage d'une adresse saisie (D-25) : decide, pas encore appele.
    "NOMINATIM_URL",
    "NOMINATIM_CONTACT",
}

# Posees par l'hebergeur, jamais par nous.
FOURNIES_PAR_L_HEBERGEUR = {"RENDER_EXTERNAL_HOSTNAME", "PORT"}


def variables_lues():
    """Tout ce que le code du projet va chercher dans l'environnement."""
    trouvees = set()
    for application in APPLICATIONS:
        for fichier in (BACKEND / application).rglob("*.py"):
            if "migrations" in fichier.parts or "tests" in fichier.parts:
                continue
            trouvees |= set(LECTURE.findall(fichier.read_text(encoding="utf-8")))
    return trouvees - FOURNIES_PAR_L_HEBERGEUR


def variables_du_modele():
    """Les variables proposees dans `.env.example`."""
    contenu = (BACKEND / ".env.example").read_text(encoding="utf-8")
    return set(re.findall(r"^([A-Z_]{3,})=", contenu, re.MULTILINE))


def variables_de_render():
    """Les variables que le fichier de deploiement pose sur le serveur."""
    contenu = (RACINE / "deploiement" / "render.yaml").read_text(encoding="utf-8")
    return set(re.findall(r"^\s*- key:\s*([A-Z_]{3,})\s*$", contenu, re.MULTILINE))


def test_le_modele_ne_propose_aucune_variable_inventee():
    """Une variable du modele que personne ne lit ne sert a rien, ou pire.

    Elle fait croire qu'un reglage existe. `STRIPE_CLE_SECRETE` en etait une :
    le code cherchait `STRIPE_SECRET_KEY`, et le paiement serait reste en
    simulation avec une vraie cle posee dans le fichier.
    """
    orphelines = sorted(variables_du_modele() - variables_lues() - PAS_ENCORE_LUES)

    assert not orphelines, (
        f"`.env.example` propose des variables que le code ne lit pas : "
        f"{', '.join(orphelines)}. Corrige le nom, ou ajoute-les a "
        f"`PAS_ENCORE_LUES` en disant pourquoi."
    )


def test_le_modele_propose_tout_ce_que_le_code_attend():
    """L'inverse compte autant.

    Une variable lue mais documentee nulle part est une variable que personne
    ne pensera a poser le jour de la mise en ligne.
    """
    # `DEMO_AUTORISEE` est un garde-fou de developpement, jamais un reglage.
    manquantes = sorted(variables_lues() - variables_du_modele() - {"DEMO_AUTORISEE"})

    assert not manquantes, (
        f"Le code lit des variables absentes de `.env.example` : "
        f"{', '.join(manquantes)}."
    )


def test_render_pose_les_bons_noms():
    """Le defaut d'origine : `render.yaml` posait trois noms sur sept a cote.

    Aucune erreur au deploiement — la valeur par defaut s'applique — et le
    front se serait fait refuser par le navigateur au premier appel.
    """
    inconnues = sorted(variables_de_render() - variables_lues())

    assert not inconnues, (
        f"`render.yaml` pose des variables que le code ne lit pas : "
        f"{', '.join(inconnues)}. Une variable mal nommee ne provoque aucune "
        f"erreur : elle desactive un reglage en silence."
    )


def test_render_pose_ce_qui_est_indispensable_en_ligne():
    """Ce sans quoi la mise en ligne repond 400, 500, ou sert un ecran vide."""
    posees = variables_de_render()

    for indispensable in (
        "DJANGO_SECRET_KEY",   # sans elle, Django refuse de demarrer hors DEBUG
        "DEBUG",               # laisser DEBUG a vrai en ligne expose les traces
        "DATABASE_URL",        # sinon la base locale, qui n'existe pas la-bas
        "ALLOWED_HOSTS",       # sinon 400 sur chaque requete
        "CORS_ORIGINS",        # sinon le front est bloque par le navigateur
    ):
        assert indispensable in posees, (
            f"`render.yaml` ne pose pas {indispensable} : la mise en ligne "
            f"echouera, et pas toujours de facon bruyante."
        )
