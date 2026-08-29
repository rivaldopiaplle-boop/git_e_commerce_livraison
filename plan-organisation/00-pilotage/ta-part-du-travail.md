# Ta part du travail

> **Tu as signalé que mes demandes étaient de plus en plus dures à trouver
> (bloc E-4). C'était vrai** — elles étaient noyées au milieu de la référence.
> Désormais : _tout ce que j'attends de toi tient dans le premier écran_, daté
> et numéroté. Le reste du fichier est de la documentation qu'on consulte, pas
> qu'on relit.

---

# ⬛ À FAIRE MAINTENANT — mis à jour le 29 août

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **1** | **`python demarrer.py`, puis Ctrl+Maj+R** sur <http://localhost:5173>. Tape dans la recherche : ça filtre **pendant la frappe**. Efface : tout revient | 3 min | § D |
| **2** | **Ajoute un produit au panier** — la carte au survol, ou depuis la fiche. Le panneau de droite s'ouvre. **Aucun compte n'est nécessaire.** Puis connecte-toi avec Léa : le panier te suit | 3 min | — |
| **3** | **Bascule Lyon → Paris** dans le bandeau : « Restauration » disparaît des filtres, les compteurs suivent. C'était le bug que tu as trouvé | 2 min | — |
| **4** | **Dis-moi ce qui ne va pas**, précisément | 5 min | — |

Je committe et je pousse désormais moi-même — **sauf `questions.txt`**, qui ne
partira jamais sur le dépôt. Tu n'as plus à t'en occuper.

---

## Ce que tu avais signalé, et ce que j'en ai fait

| | Ton constat | Ce qui a été fait |
|---|---|---|
| **G-8** | Une animation à côté du titre | La mascotte se balance doucement — deux mouvements combinés pour que ce ne soit pas mécanique, et suspendue si le système demande moins de mouvement. Une vraie animation 3D reste hors de ma portée : envoie-moi une vidéo et je l'intègre |
| **G-9** | La recherche ne filtre qu'à Entrée, et effacer ne remet rien | Recherche **instantanée**, 250 ms après la dernière frappe, avec un bouton « Effacer » explicite |
| **G-10** | « Plats 4 » depuis Paris alors qu'on ne voit rien | Les compteurs sont **calculés sur le résultat réellement visible** ([D-35](journal-decisions.md)). Depuis Paris, « Restauration » disparaît entièrement |
| **G-11** | Sept catégories à plat | Regroupées en **univers** — Restauration, High-tech — via la réflexivité déjà prévue au modèle |
| **G-12** | Ni panier, ni sidebar, ni panneau droit | **Panier complet** sans compte, qui suit à la connexion ([D-34](journal-decisions.md)) · **sidebar de filtres** repliable à gauche · **panneau panier** à droite · ajout rapide au survol d'une carte |
| **G-14** | Un clavier avec la photo d'une chaise | J'ai **regardé les 14 images**, pas seulement celle-là : 4 étaient fausses. Toutes corrigées et revérifiées |
| **G-15** | Pas de filtrage par boutique | Facette « Boutiques » avec son compteur |
| **G-16** | Trois boutons qui ne font rien | Les liens sont corrects — **deux tests le prouvent maintenant**. J'ai trouvé et corrigé deux plantages de rendu qui pouvaient rendre la page muette, et ajouté un gestionnaire d'erreurs qui les rend visibles dans la console. Si ça persiste, ouvre F12 et envoie-moi le message |

---

## Ce qui a changé, côté code

- **Panier** : API complète (voir, ajouter, modifier, retirer), session anonyme,
  fusion à la connexion, garde de stock, prix courant, alerte multi-boutique.
- **Facettes** : univers, catégories et boutiques, avec des compteurs honnêtes.
- **62 tests** — 42 backend, 20 front — dont 10 sur le seul panier.
- **Deux bugs de fragilité corrigés** dans la fiche produit : une chaîne
  optionnelle interrompue plantait tout l'écran si la charge utile changeait de
  forme. Le test les a trouvés, pas moi.


---

# Référence

_Ce qui suit ne se relit pas : on vient y chercher une réponse précise._

## Comment on communique, en trois fichiers

| Fichier                                        | Qui écrit | Ce qu'on y met                                                                                   |
| ---------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------ |
| `questions.txt`                                | **Toi**   | Tes demandes, tes doutes, tes corrections. Ta boîte d'entrée, dans ton style, sans mise en forme |
| **Ce fichier, tout en haut**                   | Moi       | Ce que tu dois faire de tes mains, daté, dans le premier écran                                   |
| [questions-ouvertes.md](questions-ouvertes.md) | Moi       | Mes questions à toi, classées par urgence, avec ma recommandation                                |
| [journal-decisions.md](journal-decisions.md)   | Moi       | Ce qui est tranché, et pourquoi                                                                  |

---

## A. Les outils — **tu as déjà tout**

Vérifié sur ta machine : Python **3.14.7**, Node **25.8.2**, npm **11.11.1**,
Docker **29.7.2**, VS Code **1.135**.

Un point à connaître : **Git Bash voit encore un vieux Python 3.8** installé il
y a des années, alors que PowerShell voit le 3.14. `demarrer.py` détecte le cas
et repart tout seul avec le bon interpréteur — tu peux lancer depuis l'un ou
l'autre.

> **Piège PowerShell** rencontré au passage : `where` y est un alias de
> `Where-Object`, d'où tes sorties vides. Pour localiser un exécutable :
> `where.exe python` ou `Get-Command python`.

**Android Studio n'est pas à installer maintenant** — plusieurs gigaoctets, et
il ne sert qu'à la tranche 7 pour fabriquer le `.apk`. Je te préviendrai ici.

---

## B. Le dépôt Git

Déjà fait : dépôt initialisé, branche `main`, distant déclaré vers
`rivaldopiaplle-boop/git_e_commerce_livraison`, `plan-organisation/` mis en
index.

**Le premier envoi est fait** : commit `55d6899`, poussé, 66 fichiers suivis —
dont `.github/workflows/ci.yml`, donc l'intégration continue s'est exécutée au
moins une fois. La commande, pour les prochaines fois :

```powershell
git add .
git commit -m "ce que ce lot change"
git push
```

Avant d'envoyer, **regarde `git status`** : aucun fichier `.env` ne doit
apparaître. J'ai vérifié qu'ils sont ignorés, mais une seconde de contrôle vaut
mieux qu'une clé à révoquer.

**Dépôt public dès le début, jamais un secret dedans.** Une clé publiée sur
GitHub est détectée et exploitée en quelques heures : c'est automatisé.

---

## C. Les comptes de services

| Service                 | À quoi ça sert              | Quand      | Carte bancaire ? |
| ----------------------- | --------------------------- | ---------- | ---------------- |
| **GitHub**              | Dépôt, intégration continue | fait       | Non              |
| **Neon**                | Base PostgreSQL en ligne    | Tranche 1  | Non              |
| **Cloudinary**          | Photos produit              | Tranche 2  | Non              |
| **Stripe**              | Paiement, en **mode test**  | Tranche 5  | Non en mode test |
| **Resend** ou **Brevo** | E-mails réels               | Tranche 8  | Non              |
| **Render**              | Hébergement de l'API        | Tranche 11 | Non              |
| **Vercel**              | Hébergement du front        | Tranche 11 | Non              |

Aucun ne demande de carte bancaire pour ce dont on a besoin. **Si l'un t'en
demande une, arrête-toi et dis-le-moi** : l'offre aura changé, on choisira
autre chose.

### Où vont les clés

```
Clé obtenue chez le service
        │
        ├──►  backend/.env                  (ignoré par Git, jamais envoyé)
        └──►  GitHub → Settings → Secrets   (intégration et déploiement)
```

`backend/.env` est créé automatiquement par `demarrer.py`, copié depuis
**`backend/.env.example`** — le fichier que tu m'as désigné au bloc D-3, dans la
forme exacte de celui de ton projet banque : versionné, chaque variable
expliquée, **aucune valeur**.

**Ne colle jamais une clé dans notre conversation ni dans `questions.txt`.** Je
n'en ai pas besoin : je travaille avec les noms, pas les valeurs. Si une clé est
publiée par accident, va la révoquer chez le service — la retirer d'un commit ne
suffit pas, l'historique reste.

---

## D. Ce que tu vérifies, à chaque tranche

Mon travail n'est pas fini parce que le code existe : il est fini quand **tu** as
vu le test de sortie passer. Les onze tests sont dans
[demarrage-projet.md](../05-execution/demarrage-projet.md).

```powershell
python demarrer.py
```

**Une seule commande** qui monte la base, prépare l'environnement, migre, crée le
compte administrateur et lance l'API et le front. C'est l'enseignement direct du
projet banque : le jour où démarrer demande six commandes dans le bon ordre, on
ne relance plus le projet après trois semaines — et on ne le montre pas à un
recruteur.

|                    |                                      |
| ------------------ | ------------------------------------ |
| Front web          | <http://localhost:5173>              |
| API                | <http://localhost:8000/api/v1/sante> |
| Administration     | <http://localhost:8000/admin/>       |
| Courriels capturés | <http://localhost:8026>              |

```powershell
python demarrer.py --etat        # ce qui tourne, ce qui répond
python demarrer.py --sans-web    # l'API seule
python demarrer.py --arreter     # arrêter les conteneurs
```

Les ports (5433, 1026, 8026) sont **décalés exprès** : le projet banque occupe
5432, 1025 et 8025 sur ta machine, et les deux doivent pouvoir tourner ensemble.

**Ce que je te demande à chaque fois** : lancer, cliquer, et me dire ce qui te
paraît faux, laid ou incompréhensible. Tu es le premier utilisateur ; ce que tu
ne comprends pas, un recruteur ne le comprendra pas non plus.

---

## E. Au déploiement (tranche 11)

1. Créer les comptes Render et Vercel, connectés à ton GitHub.
2. Recopier les variables d'environnement dans les deux interfaces — je te
   donnerai la liste, nom par nom.
3. Vérifier que l'URL publique répond, avec les comptes de démonstration.
4. **Le jour de l'entretien** : activer la tâche de réveil de l'API une heure
   avant, la désactiver après. La raison est dans
   [contrat-deploiement.md](../03-contrats/contrat-deploiement.md) — le service
   gratuit s'endort au bout de quinze minutes et met une minute à repartir.
5. Dérouler la démonstration de dix minutes **au moins une fois en entier, à
   voix haute, seul**, avant de la faire devant quelqu'un.

---

## F. Ce que tu n'as pas à faire

- Chercher, renommer ou fournir des images de produits
  ([D-24](journal-decisions.md) — le script de peuplement s'en charge ; tu peux
  déposer les tiennes, c'est une option, pas une corvée).
- Écrire du `docker-compose.yml`, des `Dockerfile`, des fichiers d'intégration.
- Créer la structure, les modèles, les migrations.
- Rédiger la documentation.
- Traduire les décisions en code : c'est à ça que sert tout ce dossier.

---

## G. Historique de ce que tu as déjà fait

| Quand  | Quoi                                                                                                             |
| ------ | ---------------------------------------------------------------------------------------------------------------- |
| Bloc C | Tranché l'hébergement, le mobile, l'entrepôt dans le MVP, l'adresse partagée                                     |
| Bloc D | Validé mes recommandations sur les retours produit et l'affichage de l'argent                                    |
| Bloc D | Initialisé le dépôt, la branche `main`, le distant GitHub                                                        |
| Bloc E | Signalé le `.env`, l'absence d'extension Vue, l'admin sans identifiants — les trois sont réglés                  |
| Bloc F | Commité **et poussé** la tranche 0, créé les comptes Neon, Cloudinary et Stripe, choisi le nom et fourni le logo |
