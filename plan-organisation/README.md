# Plan d'organisation — Plateforme Commande & Livraison

> Porte d'entrée du dossier. Aucun code n'est encore écrit : tout ce qui suit
> sert à ce que le code, quand il commencera, n'ait pas à revenir en arrière.

---

## Par où commencer

**Si tu reprends le projet après une pause**, lis dans cet ordre :

1. [00-pilotage/ta-part-du-travail.md](00-pilotage/ta-part-du-travail.md) — **ce que j'attends de toi**, et rien d'autre à chercher
2. [01-produit/perimetre-et-mvp.md](01-produit/perimetre-et-mvp.md) — ce qu'on fait et ce qu'on ne fait pas
3. [00-pilotage/journal-decisions.md](00-pilotage/journal-decisions.md) — les 27 décisions prises, et pourquoi
4. [05-execution/demarrage-projet.md](05-execution/demarrage-projet.md) — la prochaine chose à faire

**Si tu veux coder une fonctionnalité**, ouvre trois fichiers :
le scénario correspondant, la règle métier qu'il applique, et le contrat d'API.

---

## Structure du dossier

```
plan-organisation/
├── README.md                    ← tu es ici
├── questions.txt                ← ta boîte d'entrée : tu écris, je dispatche
│
├── 00-pilotage/                 Comment le projet se conduit
│   ├── regles-d-or.md              Tes 8 règles, rendues opposables
│   ├── critique-etat-des-lieux.md  Ce qui va, ce qui ne va pas, ce qui manque
│   ├── journal-decisions.md        Ce qui est tranché, et pourquoi (D-01 à D-27)
│   ├── questions-ouvertes.md       Ce qui reste à trancher, par urgence
│   ├── ta-part-du-travail.md       Ce que tu dois installer, créer, vérifier
│   └── glossaire.md                Un mot = un sens
│
├── 01-produit/                  Ce que le produit fait
│   ├── perimetre-et-mvp.md         Deux paliers, et le hors périmètre assumé
│   ├── roles-et-parcours.md        Qui existe, qui crée qui, matrice des droits
│   ├── scenarios.md                Tout ce qui peut arriver, en SI/ALORS
│   └── regles-metier.md            Les invariants R-01 à R-33 et les patterns
│
├── 02-modele/                   Les données
│   ├── mcd.html                    Diagramme Merise interactif — 33 entités, 51 associations
│   ├── dictionnaire-donnees.md     Le modèle, entité par entité — fait foi
│   └── mcd-maintenance.md          Comment modifier le diagramme sans le casser
│
├── 03-contrats/                 Ce qui ne doit plus bouger une fois codé
│   ├── contrat-api.md              Conventions, erreurs, endpoints, charges utiles
│   ├── contrat-web.md              Écrans par rôle, navigation, règles front
│   ├── contrat-mobile.md           Client et livreur, structure à 5 onglets
│   ├── contrat-medias.md           Photos produit : envoi, stockage, images de démonstration
│   ├── contrat-notifications-ia.md Matrice événement → canal, périmètre IA
│   ├── contrat-deploiement.md      Environnements, conteneurs, migrations, vitrine
│   └── contrat-cicd.md             De git push à la mise en ligne
│
├── 04-maquettes/                À quoi ça ressemble
│   ├── maquettes.html              Maquettes interactives, 5 rôles, web + mobile
│   ├── identite-visuelle.html      Le nom, le logo, ses déclinaisons, ses règles
│   ├── design-system.md            Couleurs, icônes, composants communs
│   └── correspondance-ecrans.md    Maquette → route → composant → endpoints
│
└── 05-execution/                Comment on le fabrique
    ├── stack-technique.md          Choix techniques, et ce qu'on refuse
    ├── demarrage-projet.md         Les tranches, dans l'ordre, avec tests de sortie
    ├── qualite-et-verification.md  Linters, tests, banc de preuves
    └── vitrine-et-demonstration.md La démonstration de dix minutes
```

---

## Où va quelle information

| Tu veux savoir… | Va voir |
|---|---|
| Qui a le droit de faire quoi | `01-produit/roles-et-parcours.md` |
| Ce qui doit toujours être vrai | `01-produit/regles-metier.md` |
| Ce qui se passe dans tel cas limite | `01-produit/scenarios.md` |
| Quel champ existe sur quelle table | `02-modele/dictionnaire-donnees.md` |
| Quelle URL appeler, avec quoi | `03-contrats/contrat-api.md` |
| Quelle couleur, quelle icône | `04-maquettes/design-system.md` |
| Comment une photo de produit arrive | `03-contrats/contrat-medias.md` |
| Ce que je dois faire, moi | `00-pilotage/ta-part-du-travail.md` |
| Quoi coder maintenant | `05-execution/demarrage-projet.md` |
| Le nom, le logo, les couleurs de marque | `04-maquettes/identite-visuelle.html` |
| Pourquoi on a choisi ça | `00-pilotage/journal-decisions.md` |

---

## Le projet en trois phrases

Une plateforme où plusieurs boutiques vendent, où des clients commandent, et où
des livreurs livrent. Deux régimes coexistent : **Express** (restauration,
trajet direct, une boutique par commande, catalogue filtré par rayon) et
**Standard** (colis, passage par un entrepôt, plusieurs boutiques possibles,
tournées groupées). C'est ce double régime qui fait l'intérêt du projet — et
les deux sont dans le MVP, parce qu'un circuit Standard sans entrepôt ne tient
pas debout.

---

## Règles de tenue de ce dossier

1. **Une information vit à un seul endroit.** Ailleurs, on met un lien. Le
   dossier précédent répétait la même règle dans quatre fichiers, avec quatre
   formulations légèrement différentes — c'est ainsi qu'on se contredit.
2. **Une décision prise entre dans le journal**, avec sa date et son pourquoi.
3. **Une question ouverte reste visible** tant qu'elle n'est pas tranchée. On ne
   la résout pas en silence dans un paragraphe.
4. **Le modèle de données précède le code**, et le diagramme suit le
   dictionnaire, jamais l'inverse.
5. **Rien ne se code sans son contrat.**

---

## État d'avancement

| | État |
|---|---|
| Périmètre et paliers | Écrit — MVP = Express **et** Standard (révision du bloc C) |
| Rôles et droits | Écrit |
| Scénarios | Écrits et révisés |
| Règles métier | Écrites |
| Modèle de données | Écrit — 33 entités |
| Diagramme MCD | **Régénéré et vérifié** — aligné avec le dictionnaire |
| Contrats | Écrits — API, web, mobile, médias, notifications, déploiement, CI/CD |
| Maquettes | Faites (5 rôles, web + mobile, états vides) |
| Identité visuelle | **Colibri** — nom, logo 3D, déclinaisons ([identite-visuelle.html](04-maquettes/identite-visuelle.html)), en attente de ton feu vert |
| Décisions | **30 prises, 0 en attente** |
| Ta part | [ta-part-du-travail.md](00-pilotage/ta-part-du-travail.md) — installer les outils, lancer, commiter |
| Code | **Tranche 0 vérifiée** — API, base, front, tests et linter au vert. Restent le rendu navigateur et le premier envoi |
