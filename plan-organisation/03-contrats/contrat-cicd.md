# Contrat CI/CD — ce qui se passe entre `git push` et la mise en ligne

> Pourquoi une chaîne d'intégration dans un projet d'une seule personne ? Parce
> qu'elle remplace la discipline. Elle refuse ce qui ne compile pas, ce qui ne
> passe pas les tests, ce qui n'est pas formaté — sans qu'on ait à y penser un
> lundi soir. Et parce qu'un recruteur regarde l'onglet Actions d'un dépôt.

Outil : **GitHub Actions**. Mise en place dès la semaine 1, même quand il n'y a
presque rien à vérifier : une chaîne ajoutée tard n'est jamais ajoutée.

---

## 1. Les deux moments

| Moment | Déclencheur | Ce qui se passe |
|---|---|---|
| **Intégration** | Chaque `push` et chaque *pull request* | Contrôles de qualité et tests |
| **Publication** | `push` sur `main`, après une intégration verte | Construction de l'image et déploiement |

Un déploiement n'est jamais déclenché par une intégration rouge. C'est la seule
règle absolue de ce document.

---

## 2. L'intégration, tâche par tâche

Les tâches indépendantes tournent **en parallèle** ; on veut un retour en moins
de cinq minutes, sinon on prend l'habitude de ne plus regarder.

| Tâche | Outil | Ce qu'elle attrape |
|---|---|---|
| Format et style backend | `ruff format --check`, `ruff check` | Le désordre et les fautes de raisonnement simples |
| Types backend | `mypy` (progressif) | Les incohérences de types |
| Tests backend | `pytest` avec un PostgreSQL de service | Les régressions de comportement |
| Couverture | `pytest --cov` | Le code métier jamais exécuté par un test |
| Format et style front | `eslint`, `prettier --check` | Idem côté Vue |
| Compilation front | `vue-tsc --noEmit`, `vite build` | Ce qui ne compile pas |
| Tests front | `vitest` | Les composants et les magasins Pinia |
| Migrations | `makemigrations --check --dry-run` | **Un modèle modifié sans migration** — l'oubli le plus fréquent en Django |
| Image Docker | `docker build` | Un `Dockerfile` cassé, avant le déploiement |
| Dépendances | `pip-audit`, `npm audit` | Les vulnérabilités connues |

La tâche « migrations » mérite son existence à elle seule : c'est l'erreur qu'on
ne voit qu'au déploiement, quand il est trop tard.

---

## 3. Les tests, par étage

| Étage | Ce qu'on teste | Combien |
|---|---|---|
| **Unitaire** | Les règles métier pures : découpage du panier, calcul des frais, transitions de statut | Beaucoup, rapides |
| **Intégration API** | Chaque endpoint : permissions par rôle, codes d'erreur, effets en base | Un test par règle de permission |
| **Bout en bout métier** | Les scénarios du dossier `01-produit/`, rejoués sur une base neuve | Quelques-uns, lents |

Les tests de permission sont non négociables : **un rôle ne doit jamais accéder
aux routes d'un autre**, et c'est un test automatisé qui le prouve, pas une
relecture. Un test par ligne de la matrice des droits.

---

## 4. La publication

1. L'intégration passe au vert sur `main`.
2. L'image Docker est construite et étiquetée avec l'empreinte du commit.
3. L'image est publiée sur un registre.
4. L'hébergeur déploie la nouvelle image ; les migrations s'exécutent au démarrage.
5. Le front est construit et publié sur l'hébergeur statique.
6. Un appel à `/sante` et `/version` vérifie que la version attendue répond.
7. **Si la vérification échoue, on revient à l'image précédente.**

---

## 5. Ce que la chaîne ne fait pas, et pourquoi

- **Pas de déploiement automatique du mobile.** Construire un `.apk` à chaque
  poussée coûte du temps de calcul pour rien : construction sur demande.
- **Pas de tests d'interface exhaustifs.** Fragiles, lents, et ils masquent
  l'absence de tests métier. Un seul parcours critique automatisé suffit.
- **Pas de déploiement automatique en production depuis une branche.** Seule
  `main` déploie, et seulement en vitrine tant qu'il n'y a rien à protéger.

---

## 6. Comment la lire quand elle est rouge

Dans cet ordre : quelle tâche a échoué (format ≠ test ≠ construction), la
première ligne d'erreur (jamais la dernière), et enfin la question « est-ce que
ça passe en local ? ». Si oui, la différence est presque toujours une variable
d'environnement ou une version de dépendance non figée — d'où le verrouillage des
versions dans `requirements.txt` et `package-lock.json`.
