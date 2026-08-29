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
| **1** | **Corriger ta configuration Cloudinary** dans `backend/.env` — voir l'encadré ci-dessous. C'est la seule chose bloquante | 3 min | § C |
| **2** | **`python demarrer.py`, puis Ctrl+Maj+R.** Le catalogue revient : le bug venait de moi, pas de toi | 2 min | § D |
| **3** | **Connecte-toi avec Karim** (`karim@exemple.fr`), va dans **Catalogue** : tu peux créer un produit, y déposer des photos et ajuster ton stock | 5 min | — |
| **4** | **Dis-moi ce qui ne va pas**, précisément | 5 min | — |

---

## ⚠ Ta configuration Cloudinary est fausse

Le service refuse tes clés : **`Invalid cloud_name Root`**. Tu as mis `Root`
comme `CLOUDINARY_CLOUD_NAME` — c'est le nom du dossier racine affiché dans leur
interface, pas le nom de ton espace.

Le vrai nom se lit sur le tableau de bord Cloudinary, en haut : **Product
Environment Credentials**, ligne `Cloud name`. C'est une suite de lettres, par
exemple `dxk3f9abc`. Corrige `CLOUDINARY_CLOUD_NAME` dans `backend/.env` et
relance.

**Tant que ce n'est pas corrigé, rien ne casse** : sans configuration valable,
les images vont sur le disque local et tout fonctionne. Mais le jour du
déploiement, ce sera bloquant — le disque du conteneur est effacé à chaque
redéploiement ([D-19](journal-decisions.md)). Le message d'erreur est maintenant
explicite au lieu d'un 500 muet.

---

## Ce qui bloquait tout, et pourquoi c'était ma faute

Catalogue vide, connexion impossible, « L'API ne répond pas » : **un seul bug,
et il était à moi.** J'avais ajouté un en-tête `X-Panier-Session` à toutes les
requêtes du front sans le déclarer côté serveur. Le navigateur bloque alors
chaque appel **avant même de l'envoyer**, et le front ne reçoit qu'une erreur
réseau — alors que l'API répondait parfaitement.

Ni `pytest` ni un client en ligne de commande ne déclenchent ce contrôle : **seul
un navigateur le fait**. C'est exactement le genre de bug que seuls tes essais
peuvent révéler. Corrigé, et **cinq tests** simulent désormais ce que le
navigateur envoie avant chaque requête, pour que ça ne se reproduise pas.

**H-3** est réglé au passage : un lien « Retour au catalogue » figure maintenant
en haut des écrans de connexion, d'inscription et d'attente, et le logo y est
cliquable — sur toute plateforme marchande, le logo ramène à la boutique.

---

## Ce qui a été ajouté

**Les écrans vendeur** :
- **Catalogue** : liste dense avec boutons-icônes — voir la fiche publique,
  modifier, retirer du catalogue — état vide qui explique quoi faire.
- **Fiche produit** en trois onglets : informations, photos, stock. Trois onglets
  plutôt qu'un formulaire fleuve, pour ne voir que l'étape en cours.
- **Photos** : dépôt par glisser-déposer, choix de la photo principale,
  suppression. Le serveur vérifie **le contenu réel du fichier** et non son
  extension, retire les métadonnées EXIF — une photo de téléphone porte les
  coordonnées GPS de qui l'a prise — recadre et convertit en WebP.
- **Stock** : ajustement avec **motif obligatoire**, refus si le stock devient
  négatif ou passe sous ce qui est réservé, et historique complet avec l'auteur
  de chaque mouvement.

**La règle du bloc H-4 est enregistrée** : en cas de conflit, l'usage des CMS
marchands l'emporte sur les règles d'or ([D-36](journal-decisions.md)). Elles
restent le comportement par défaut, pas un carcan.

**80 tests** — 60 backend, 20 front.


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
