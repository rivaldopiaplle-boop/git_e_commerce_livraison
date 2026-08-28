# Ta part du travail

> Réponse aux blocs C-6 et C-14. **Un seul endroit** pour ce que tu dois
> installer, créer, décider et vérifier — dans l'ordre, avec la commande exacte.
> Tu n'as pas à chercher ailleurs : quand j'ai besoin de quelque chose de toi,
> ça arrive ici.

---

## Comment on communique, en trois fichiers

| Fichier | Qui écrit | Ce qu'on y met |
|---|---|---|
| `questions.txt` | **Toi** | Tes demandes, tes doutes, tes corrections. Ta boîte d'entrée, dans ton style, sans mise en forme |
| [questions-ouvertes.md](questions-ouvertes.md) | Moi | Mes questions à toi, classées par urgence, avec ma recommandation pour chacune |
| **Ce fichier** | Moi | Ce que tu dois faire de tes mains : installer, créer un compte, vérifier, décider |
| [journal-decisions.md](journal-decisions.md) | Moi | Ce qui est tranché, et pourquoi. On n'y revient qu'en révisant explicitement |

Un dossier de plus n'apporterait qu'un endroit supplémentaire où chercher. Trois
fichiers, trois usages, aucun recouvrement.

**Règle de lecture** : à chaque reprise du projet, tu ouvres ce fichier en
premier. Si la section « en attente de toi » est vide, tu n'as rien à faire et je
peux avancer seul.

---

## En attente de toi, maintenant

| | Quoi | Temps | Bloque quoi |
|---|---|---|---|
| 1 | ~~Installer les outils~~ — **tu as déjà tout** (§ A) | fait | — |
| 2 | **Lancer `python demarrer.py`** et me dire ce que tu vois (§ D) | 5 min | La suite de la tranche 1 |
| 3 | **Faire le premier commit** (§ B) | 2 min | Rien, mais plus on attend, plus c'est gros |
| 4 | Créer les comptes Neon, Cloudinary, Stripe (§ C) | ~20 min | Les tranches 1, 2 et 5 |

Déjà fait de ton côté, et bien vu : dépôt initialisé, branche `main`, dépôt
distant `git_e_commerce_livraison` déclaré, dossier `plan-organisation/` mis en
index. Les questions [Q-07 et Q-08](questions-ouvertes.md) sont tranchées
([D-28](journal-decisions.md), [D-29](journal-decisions.md)).

Le reste attend le moment où il servira — créer un compte Vercel aujourd'hui pour
s'en servir dans deux mois n'avance à rien.

> **Vérifié sur ta machine** : Python 3.14.7, Node 25.8.2, npm 11.11.1, Docker
> 29.7.2. Tout est là. Le vieux Python 3.8 que voit Git Bash n'est plus un
> problème : `demarrer.py` détecte le 3.14 installé et repart tout seul avec.
>
> Petit piège PowerShell rencontré au passage : `where` y est un alias de
> `Where-Object`, d'où ta sortie vide. Pour localiser un exécutable, c'est
> `where.exe python` ou `Get-Command python`.

---

## A. Les outils à installer

Sur ta machine Windows, dans cet ordre.

| Outil | Version | Pourquoi | Vérifier avec |
|---|---|---|---|
| **Git** | récente | Tout le projet | `git --version` |
| **Python** | **3.10 ou plus** (tu as 3.14.7) | Django 5 | `python --version` |
| **Node.js** | **20 ou plus** (tu as 25.8.2) | Vue, Vite, Ionic | `node --version` |
| **Docker Desktop** | récente (tu as 29.7.2) | Base locale, image de l'API | `docker --version` |
| **VS Code** | récente | Tu l'as déjà | — |

Sur Windows 10, **Docker Desktop a besoin de WSL 2** : son installateur le
propose, accepte. C'est le seul point d'installation qui peut demander un
redémarrage.

**Android Studio n'est pas à installer maintenant** — il pèse plusieurs gigas et
ne sert qu'à la tranche 7, pour fabriquer le `.apk`. Je te préviendrai ici.

### Le test qui dit que tout est bon

Dans PowerShell, à la racine du projet :

```powershell
git --version; python --version; node --version; docker --version
docker run --rm hello-world
```

Cinq lignes qui répondent, et la dernière qui affiche « Hello from Docker ». Si
une seule échoue, dis-le-moi avec le message exact plutôt que de contourner.

---

## B. Le dépôt Git

**C'est fait** : dépôt initialisé, branche `main`, distant déclaré vers
`rivaldopiaplle-boop/git_e_commerce_livraison`, et `plan-organisation/` mis en
index. Le `.gitignore`, le `README.md` et tout le code de la tranche 0 sont
écrits et t'attendent.

Il reste le premier commit, qui n'est pas à moi de faire :

```powershell
git add .
git commit -m "Tranche 0 : conception complete et squelette qui tourne"
git push -u origin main
```

Avant d'envoyer, **jette un œil à `git status`** : aucun fichier `.env` ne doit
apparaître. S'il y en a un, arrête-toi et dis-le-moi — le `.gitignore` les
exclut, mais une vérification coûte dix secondes et un secret publié coûte une
révocation.

**Public dès le début, mais jamais un secret dedans.** Une clé Stripe publiée
sur GitHub est détectée et exploitée en quelques heures — c'est automatisé.

---

## C. Les comptes de services

| Service | À quoi ça sert | Quand le créer | Carte bancaire ? |
|---|---|---|---|
| **GitHub** | Dépôt, intégration continue | Maintenant | Non |
| **Neon** | Base PostgreSQL en ligne | Tranche 1 | Non |
| **Cloudinary** | Photos produit | Tranche 2 | Non |
| **Stripe** | Paiement, en **mode test** | Tranche 5 | Non en mode test |
| **Resend** ou **Brevo** | E-mails réels | Tranche 8 | Non |
| **Render** | Hébergement de l'API | Tranche 11 | Non |
| **Vercel** | Hébergement du front | Tranche 11 | Non |

Aucun de ces services ne demande de carte bancaire pour ce dont on a besoin.
**Si l'un d'eux t'en demande une, arrête-toi et dis-le-moi** : ça veut dire que
l'offre a changé, et on choisira autre chose.

Sur Stripe, reste en **mode test** : les cartes de test paient sans qu'un centime
n'existe, et c'est parfaitement démontrable en entretien.

### Où mettent les clés — et où elles ne vont jamais

```
Clé obtenue chez le service
        │
        ├──► backend/.env                 (ignoré par Git, jamais envoyé)
        └──► GitHub → Settings → Secrets   (pour l'intégration et le déploiement)
```

`backend/.env` est créé automatiquement par `demarrer.py`, copié depuis
**`backend/.env.example`** — le fichier que tu m'as désigné au bloc D-3. Celui-là
est versionné : il liste chaque variable, explique à quoi elle sert et pourquoi,
et ne contient **aucune valeur**. C'est exactement la forme du
`backend/.env.example` de ton projet banque.

**Ne colle jamais une clé dans notre conversation, ni dans `questions.txt`.**
Je n'en ai pas besoin : je travaille avec `.env.example`, qui n'a que les noms.
Quand une clé manquera, le message d'erreur te dira laquelle — pas à moi de la
connaître.

Si une clé se retrouve publiée par accident : va la révoquer chez le service et
génère-en une nouvelle. La retirer d'un commit ne suffit pas, l'historique reste.

---

## D. Ce que tu vérifies, à chaque tranche

Mon travail n'est pas terminé parce que le code existe : il est terminé quand
**tu** as vu le test de sortie passer. Les onze tests de sortie sont dans
[demarrage-projet.md](../05-execution/demarrage-projet.md) ; à chaque fin de
tranche, je te donne ici la commande exacte et ce que tu dois voir à l'écran.

### Le test de sortie de la tranche 0, à faire maintenant

**À la racine** :

```powershell
python demarrer.py
```

**Je l'ai déjà fait tourner sur ta machine** : conteneurs démarrés,
environnement virtuel créé, dépendances installées, migrations appliquées,
`ruff` sans reproche, 2 tests au vert, et l'API qui répond
`{"statut":"en ligne","base_de_donnees":"connectee"}`. Le front sert bien la
page, titre « Colibri », favicon compris.

**Ce qui reste à toi, et que je ne peux pas faire** : ouvrir
<http://localhost:5173> dans ton navigateur et regarder. Tu dois voir le logo
Colibri, le nom, et **« API en ligne »** avec une pastille turquoise. Dis-moi
si c'est laid, si ça tarde, ou si la pastille est rouge.

Les conteneurs de Colibri tournent en ce moment sur ta machine, à côté de ceux
du projet banque — c'est voulu, les ports ont été décalés exprès. Pour les
arrêter : `python demarrer.py --arreter`.

```powershell
python demarrer.py --etat        # ce qui tourne, ce qui répond
python demarrer.py --sans-web    # l'API seule
python demarrer.py --arreter     # arrêter les conteneurs
```

Le principe, valable tout du long :

**Une seule commande** qui monte la base, applique les migrations, peuple les
données de démonstration et lance l'API, le web et, si besoin, le mobile. C'est
l'enseignement direct du projet banque : le jour où lancer le projet demande six
commandes dans le bon ordre, on ne le relance plus après trois semaines
d'interruption — et on ne le montre pas à un recruteur.

**Ce que je te demande de faire à chaque fois** : lancer, cliquer, et me dire ce
qui te paraît faux, laid ou incompréhensible. Tu es le premier utilisateur ; ce
que tu ne comprends pas, un recruteur ne le comprendra pas non plus.

**Et une chose de plus, pour la tranche 0** : ouvre
[identite-visuelle.html](../04-maquettes/identite-visuelle.html) et dis-moi si
le nom **Colibri** et le logo te plaisent. Tant que tu n'as pas répondu, le nom
ne vit que dans l'identité visuelle, le README et le code de la tranche 0 —
en changer coûte une commande.

---

## E. Au déploiement (tranche 11)

1. Créer les comptes Render et Vercel, connectés à ton GitHub.
2. Recopier les variables d'environnement dans les deux interfaces — je te
   donnerai la liste exacte, nom par nom.
3. Vérifier que l'URL publique répond, avec les comptes de démonstration.
4. **Le jour de l'entretien** : activer la tâche de réveil de l'API une heure
   avant, et la désactiver après. La raison est dans
   [contrat-deploiement.md](../03-contrats/contrat-deploiement.md) : le service
   gratuit s'endort au bout de quinze minutes et met une minute à repartir.
5. Faire tourner la démonstration de dix minutes **au moins une fois en entier,
   à voix haute, seul**, avant de la faire devant quelqu'un.

---

## F. Ce que tu n'as pas à faire

Pour lever tout doute — ces choses sont de mon côté :

- Chercher, renommer ou fournir des images de produits
  ([D-24](journal-decisions.md) : le script de peuplement s'en charge, et tu peux
  déposer les tiennes si tu préfères, mais c'est une option).
- Écrire du `docker-compose.yml`, des `Dockerfile` ou des fichiers GitHub Actions.
- Créer la structure des dossiers, les modèles, les migrations.
- Rédiger la documentation.
- Traduire les décisions en code : c'est exactement ce à quoi sert tout ce
  dossier.

---

## G. Les deux décisions qui t'attendent

Ni l'une ni l'autre ne bloque le démarrage. Détail et recommandations dans
[questions-ouvertes.md](questions-ouvertes.md).

- **[Q-07]** Les retours de produits en bon état (droit de rétractation) :
  je recommande de les mettre hors périmètre, et de le déclarer.
- **[Q-08]** Afficher l'argent à chaque rôle — « vous touchez 8,50 € sur cette
  commande » côté vendeur, « cette course vous rapporte 4,20 € » côté livreur :
  je recommande oui, les montants existent déjà dans le modèle.

Sans réponse de ta part, j'applique les recommandations et je le note au journal.
Tu pourras toujours revenir dessus — mais plus tard coûte plus cher.
