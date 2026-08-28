# Ce qui vérifie ce projet

> Absent du plan initial, alors que c'est ce qui permet de dire « ça marche »
> sans croiser les doigts. Repris de la méthode du projet banque, qui distinguait
> quatre familles d'erreurs et un outil pour chacune.

---

## Les quatre familles d'erreurs, et qui les attrape

| Famille | Exemple | Qui l'attrape |
|---|---|---|
| **La faute d'orthographe** | Un nom de variable faux, un import manquant | Le compilateur TypeScript, l'analyse Python |
| **La faute de raisonnement** | Une variable inutilisée, une comparaison toujours vraie, un `except` vide | Les linters : `ruff`, `eslint` |
| **La faute de comportement** | Le stock devient négatif, un gestionnaire voit le chiffre d'affaires | Le banc de preuves |
| **L'oubli** | Un modèle modifié sans migration, un test qu'on a « oublié » de lancer | La chaîne d'intégration |

Chacune coûte de plus en plus cher à corriger, dans cet ordre. D'où l'ordre dans
lequel on s'en sert.

---

## 1. Les linters et les types

Backend : `ruff format` et `ruff check` (rapides, un seul outil pour le format et
l'analyse), plus `mypy` en mode progressif — on n'annote pas tout d'un coup, on
annote les services métier.

Front : `eslint` avec la configuration Vue, `prettier`, et `vue-tsc --noEmit`
pour vérifier les types des composants.

Ces outils tournent en local (idéalement à l'enregistrement du fichier) **et**
dans la chaîne d'intégration. En local pour ne pas attendre, en intégration pour
que ce ne soit pas facultatif.

---

## 2. Les tests unitaires — les règles métier pures

Ce sont les tests qui rapportent le plus ici, parce que la valeur de ce projet
est dans ses règles. Un test par règle de
[regles-metier.md](../01-produit/regles-metier.md), **portant le même numéro** :

```
test_R10_panier_mixte_produit_trois_commandes
test_R02_stock_ne_devient_jamais_negatif
test_R08_seconde_boutique_express_refusee
test_R14_frais_standard_gratuits_au_dela_du_seuil
test_R16_transition_statut_illegale_refusee
```

Quand un test casse, on sait immédiatement quelle règle est violée — et si la
règle a changé, on met à jour les deux ensemble.

Cibles prioritaires : le `CommandeSplitter`, le calcul des frais, la machine à
états, le filtrage par rayon, la fusion des paniers.

---

## 3. Les tests d'API — les permissions avant tout

**Une ligne de la matrice des droits = un test.** C'est la partie la plus
ingrate et la plus rentable : c'est aussi le premier endroit qu'un recruteur
technique regarde quand un projet a six rôles.

Trois cas par endpoint sensible : le rôle autorisé réussit, un rôle non autorisé
reçoit 403, et un utilisateur du bon rôle mais sur la donnée d'un autre reçoit
403 lui aussi. C'est ce troisième cas qu'on oublie, et c'est la vraie faille.

Outils : `pytest` + `pytest-django` + `factory_boy` pour construire les jeux de
données sans copier-coller.

---

## 4. Le banc de preuves — les scénarios rejoués

Un script qui part d'une **base neuve amorcée**, puis déroule les scénarios de
[scenarios.md](../01-produit/scenarios.md) de bout en bout, en appelant la vraie
API, et qui affiche ce qu'il vérifie ligne par ligne.

Parcours minimum du MVP :

1. L'admin valide un vendeur et un livreur.
2. Le vendeur publie un produit.
3. Un client hors rayon **ne voit pas** ce produit ; un client dans le rayon le voit.
4. Le client commande, paie (Stripe en mode test), la commande passe `PAYEE`.
5. Le gestionnaire prépare, la commande passe `PRETE`.
6. Deux livreurs acceptent en même temps : un seul obtient la course.
7. Le livreur livre avec preuve, la commande passe `LIVREE`.
8. Le client note ; il ne peut pas noter une commande non livrée.
9. Un autre client tente d'accéder à cette commande : 403.

C'est aussi, tel quel, **le script de la démonstration en entretien**. Un seul
travail pour deux usages.

---

## 5. Les tests front

`vitest` pour les magasins Pinia et les composants qui contiennent une logique
(frise de statut, affichage des montants en centimes, calcul du panier affiché).
On ne teste pas l'apparence : ça casse à chaque changement de CSS pour rien.

Un seul parcours d'interface automatisé, le tunnel de commande, avec Playwright.
Au-delà, le coût de maintenance dépasse le bénéfice sur un projet d'une personne.

---

## 6. L'ordre dans lequel s'en servir

```
1. Pendant qu'on écrit       →  linters + types (immédiat)
2. Avant de committer        →  tests unitaires du domaine touché (quelques secondes)
3. Avant de pousser          →  tests d'API (une minute)
4. Après un changement de pile →  banc de preuves sur base neuve (quelques minutes)
5. À chaque poussée          →  la chaîne d'intégration refait tout
```

---

## 7. Ce qu'on ne teste pas, et pourquoi

L'apparence, les bibliothèques tierces (Stripe, Django : ils ont leurs propres
tests), et les écrans purement d'affichage sans logique. Chercher un pourcentage
de couverture élevé sur ces zones donne un chiffre flatteur et aucune sécurité.

L'objectif raisonnable : **couverture élevée sur les services métier, faible
ailleurs, et assumée.**
