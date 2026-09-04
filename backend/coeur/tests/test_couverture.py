"""Le tableau de couverture ne se désynchronise pas du dossier produit — D-96.

**Ta demande, L-15** : *« crée autant de données que possible pour rendre
visible chaque scénario et chaque décision »*.

Une promesse pareille se défait en silence : on ajoute un scénario au dossier
produit, personne ne pense au jeu de données, et six semaines plus tard la
démonstration a des trous que personne ne sait nommer.

Ces tests sont le garde-fou. Ils ne regardent PAS la base — un test tourne sur
une base vide, et vérifier des données de démonstration y serait absurde. Ils
vérifient ce qui peut l'être hors ligne :

  1. **chaque scénario du dossier produit a une ligne** dans
     `donnees-demo/couverture.md` ;
  2. **chaque ligne « donnée » a un contrôle** dans `verifier_couverture` ;
  3. **aucun contrôle ne cite un scénario qui n'existe pas.**

La vérification des données elles-mêmes est le travail de
`python manage.py verifier_couverture`, qui interroge la base réelle.
"""
import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[3]
SCENARIOS = RACINE / "plan-organisation" / "01-produit" / "scenarios.md"
COUVERTURE = RACINE / "plan-organisation" / "donnees-demo" / "couverture.md"


def scenarios_du_dossier():
    """Les numéros de scénario tels que le dossier produit les écrit."""
    texte = SCENARIOS.read_text(encoding="utf-8")
    return {
        correspondance.group(1)
        for correspondance in re.finditer(r"^### (\d+\.\d+)\b", texte, re.MULTILINE)
    }


def lignes_de_couverture():
    """Les lignes du tableau : {numéro: genre}.

    Le document est un tableau Markdown ; on lit la première colonne (le
    numéro) et la troisième (le genre).
    """
    texte = COUVERTURE.read_text(encoding="utf-8")
    lignes = {}
    for correspondance in re.finditer(
        r"^\|\s*(\d+\.\d+)\s*\|([^|]*)\|\s*(donnée|règle|absent)\s*\|",
        texte,
        re.MULTILINE,
    ):
        lignes[correspondance.group(1)] = correspondance.group(3)
    return lignes


def controles_de_la_commande():
    """Les clés de `verifier_couverture`, sans importer Django."""
    from coeur.management.commands.verifier_couverture import _controles

    return set(_controles())


def test_le_document_de_couverture_existe():
    assert COUVERTURE.exists(), (
        "donnees-demo/couverture.md est la table de correspondance exigée par D-96."
    )


def test_chaque_scenario_du_dossier_a_une_ligne():
    """Le trou que ce test empêche : ajouter un scénario et oublier les données."""
    manquants = sorted(
        scenarios_du_dossier() - set(lignes_de_couverture()),
        key=lambda cle: [int(n) for n in cle.split(".")],
    )

    assert not manquants, (
        f"{len(manquants)} scenario(s) absent(s) de donnees-demo/couverture.md : "
        f"{', '.join(manquants)}. Ajoute une ligne pour chacun, en disant "
        f"franchement s'il est couvert par une donnee, par une regle testee, "
        f"ou pas encore ecrit."
    )


def test_le_document_ne_cite_pas_de_scenario_inexistant():
    """L'inverse compte autant : un scenario renumerote laisserait une ligne fantome."""
    inconnus = sorted(set(lignes_de_couverture()) - scenarios_du_dossier())

    assert not inconnus, (
        f"donnees-demo/couverture.md cite des scenarios absents du dossier "
        f"produit : {', '.join(inconnus)}."
    )


@pytest.mark.django_db
def test_chaque_scenario_illustre_par_une_donnee_a_son_controle():
    """Dire « couvert par une donnee » sans requete qui le prouve ne vaut rien."""
    attendus = {
        numero for numero, genre in lignes_de_couverture().items() if genre == "donnée"
    }
    sans_controle = sorted(
        attendus - controles_de_la_commande(),
        key=lambda cle: [int(n) for n in cle.split(".")],
    )

    assert not sans_controle, (
        f"Ces scenarios sont annonces comme couverts par une donnee mais aucune "
        f"requete ne le verifie dans `verifier_couverture` : "
        f"{', '.join(sans_controle)}."
    )


@pytest.mark.django_db
def test_aucun_controle_ne_cite_un_scenario_inexistant():
    """Les ajouts hors dossier portent un « + » : ils ne peuvent pas se confondre."""
    numerotes = {cle for cle in controles_de_la_commande() if not cle.startswith("+")}
    # « 2 » designe la section entiere « ce que voit chaque role », qui n'a pas
    # de sous-numero dans le dossier.
    inconnus = sorted(numerotes - scenarios_du_dossier() - {"2"})

    assert not inconnus, (
        f"`verifier_couverture` contrôle des scenarios absents du dossier "
        f"produit : {', '.join(inconnus)}."
    )

def test_le_journal_des_decisions_ne_perd_jamais_de_decisions():
    """Le journal ne peut que grandir, et ses numeros se suivent.

    Au bloc O, un script d'ajout a efface 149 decisions d'un coup : il ouvrait
    le fichier en ECRITURE avant de le lire, ce que Python fait dans cet ordre.
    Le fichier est reparti a cinq decisions, le script a rendu 0, le commit est
    parti, et **rien ne l'a signale**. C'est git qui l'a rattrape.

    Ce test verifie deux choses qu'aucun oeil ne verifie :

      · le journal contient au moins autant de decisions que la derniere fois
        qu'on a regarde. Le plancher se releve a la main, sciemment ;
      · **les numeros se suivent sans trou**. Un trou signifie soit une
        decision perdue, soit une decision jamais ecrite — et les deux sont
        des defauts.
    """
    import re
    from pathlib import Path

    journal = (Path(__file__).resolve().parents[3]
               / "plan-organisation" / "00-pilotage" / "journal-decisions.md")
    numeros = sorted(
        int(n) for n in re.findall(r"^### D-(\d+) ", journal.read_text(encoding="utf-8"), re.M)
    )

    # Le plancher : releve a la main quand on ajoute des decisions.
    assert len(numeros) >= 159, (
        f"Le journal ne contient plus que {len(numeros)} decisions. "
        "Il ne peut que grandir : quelque chose en a efface."
    )
    assert numeros == list(range(1, numeros[-1] + 1)), (
        "Les numeros de decision doivent se suivre sans trou : "
        f"il manque {sorted(set(range(1, numeros[-1] + 1)) - set(numeros))}."
    )
