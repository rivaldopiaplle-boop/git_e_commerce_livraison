# Deux dépôts, et comment les tenir à jour

> **Décision M-3.** Le dépôt **privé** porte le projet complet, mobile compris.
> Le dépôt **public** porte le même projet **sans** `frontend-mobile/`.

| Dépôt | Contenu | Adresse |
|---|---|---|
| Privé | tout, y compris le mobile | `git@github.com:rivaldopiaplle-boop/git_e_commerce_livraison_v2.git` |
| Public | tout sauf `frontend-mobile/` | `git@github.com:rivaldopiaplle-boop/git_e_commerce_livraison.git` |

---

## Pourquoi ce montage plutôt qu'un autre

Trois façons de retirer le mobile du public étaient possibles. Celle-ci a été
retenue parce que c'est la seule qui ne perd rien :

| Option | Ce qu'elle coûte |
|---|---|
| **Un commit de retrait** *(retenue)* | rien. L'historique est intact, le mobile revient d'un `git revert` |
| Réécrire l'historique public | ~135 commits changent d'identifiant, toute copie existante du dépôt casse, et le gain est nul : le code mobile reste visible sur le privé |
| Revenir à un commit d'avant le mobile | emporte aussi le paiement, les litiges, les graphes, tout le bloc M |

Le dépôt public garde donc **tout le travail** — API, front web, 176 tests
backend, 107 tests front, dossier de conception, guide de déploiement — sauf
le dossier `frontend-mobile/`.

**Les décisions [D-20](journal-decisions.md) et [D-40](journal-decisions.md)
restent écrites dans le dossier de conception.** Effacer la trace d'un choix
d'architecture parce que le code correspondant est ailleurs falsifierait le
dossier — et c'est le dossier qu'un recruteur lit en premier.

---

## Les branches, en local

```
main                  la version complète  → dépôt privé
public-sans-mobile    main + 1 commit de retrait → dépôt public
```

`public-sans-mobile` ne contient **qu'un seul commit** au-dessus de `main`.
C'est ce qui rend la manœuvre rejouable indéfiniment.

---

## Livrer, après avoir travaillé sur `main`

```bash
# 1. Le complet part sur le privé
git checkout main
git push prive main

# 2. Le commit de retrait se repose au-dessus du nouveau travail
git checkout public-sans-mobile
git rebase main

# 3. Le public reçoit le tout
git push origin public-sans-mobile:main

# 4. On revient travailler
git checkout main
```

`git rebase main` rejoue le commit de retrait sur le dernier état. S'il y a un
conflit, c'est **toujours** parce qu'un fichier du public s'est remis à parler
du mobile : `demarrer.py`, `ci.yml`, `README.md` ou le guide de déploiement.
Corrige, `git rebase --continue`, et c'est fini.

### Si les remotes manquent

```bash
git remote add prive git@github.com:rivaldopiaplle-boop/git_e_commerce_livraison_v2.git
```

`origin` pointe déjà sur le public.

---

## Ce que le commit de retrait touche

| Fichier | Ce qui change |
|---|---|
| `frontend-mobile/` | supprimé |
| `demarrer.py` | le lancement du mobile, `preparer_mobile()`, `adresse_reseau()` et l'option `--sans-mobile` |
| `.github/workflows/ci.yml` | le job `mobile` |
| `README.md` | l'arborescence, plus un encadré disant où vit le mobile |
| `deploiement/LISEZ-MOI.md` | la section 6 renvoie au dépôt séparé |
| `plan-organisation/…/ta-part-du-travail.md` | le lien vers le guide mobile |

**Rien d'autre.** Aucun test, aucun code d'API, aucune décision.

---

## Le piège à ne pas oublier

**Ne travaille jamais directement sur `public-sans-mobile`.** Tout ce qui y
serait écrit disparaîtrait au prochain `git rebase main`.

Cette branche n'a qu'un seul rôle : porter le commit de retrait. Le travail se
fait sur `main`, toujours.
