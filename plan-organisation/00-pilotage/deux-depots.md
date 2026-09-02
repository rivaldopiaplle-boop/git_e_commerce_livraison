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

# 3. Le public reçoit le tout — voir la note sur le --force juste après
git push --force-with-lease origin public-sans-mobile:main

# 4. On revient travailler
git checkout main
```

`git rebase main` rejoue le commit de retrait sur le dernier état. S'il y a un
conflit, c'est **toujours** parce qu'un fichier du public s'est remis à parler
du mobile : `demarrer.py`, `ci.yml`, `README.md` ou le guide de déploiement.
Corrige, `git rebase --continue`, et c'est fini.

### Pourquoi un `--force-with-lease`, et pourquoi ce n'est pas grave ici

Le rebase **réécrit** le commit de retrait : il en fabrique un nouveau, au-dessus
du nouveau travail. L'ancien n'est donc plus un ancêtre du nouveau, et un push
ordinaire est refusé. C'est normal, et c'est la contrepartie du choix
« une branche à un seul commit ».

Ce qui est réécrit se limite à **ce seul commit mécanique**. Tout l'historique
réel — celui qui vient de `main` — est identique de part et d'autre et n'est
jamais touché.

`--force-with-lease` plutôt que `--force` : il **refuse** si le dépôt distant a
bougé depuis ton dernier `fetch`. Un `--force` sec écraserait ce changement sans
rien dire ; c'est exactement la commande qui fait perdre du travail.

> **La conséquence, à connaître** : si tu clones un jour le dépôt **public**
> ailleurs et que tu y travailles, le prochain rebase effacera ce travail. Le
> public est une **cible de publication**, pas un espace de travail. C'est le
> même piège que celui de la fin de ce document, sous un autre angle.

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
