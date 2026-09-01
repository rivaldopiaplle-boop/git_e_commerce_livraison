# Mettre RivDinde en ligne

> Trois hébergeurs, trois raisons, zéro carte bancaire. Le découpage vient de
> [D-19](../plan-organisation/00-pilotage/journal-decisions.md) et il n'a pas
> bougé depuis.

| Morceau | Où | Pourquoi là et pas ailleurs |
|---|---|---|
| Base PostgreSQL | **Neon** | Render n'offre Postgres gratuitement que 90 jours : la démonstration mourrait à date fixe |
| API Django | **Render**, image Docker | Un backend Django est un processus long ; Vercel exécute des fonctions sans état |
| Front web | **Vercel** | C'est exactement son métier : des fichiers statiques sur un réseau de diffusion |
| Images produit | **Cloudinary** | Le disque de Render est éphémère — une photo téléversée disparaît au redéploiement suivant |
| Application mobile | **APK signé**, distribué à la main | Publier sur le Play Store coûte 25 $ et n'apporte rien à une démonstration |

---

## L'ordre, et pourquoi il compte

### 1. La base, chez Neon

Créez un projet, puis **deux bases** dans ce projet : `rivdinde_vitrine` et
`rivdinde_production`. Neon donne une chaîne de connexion par base.

Deux bases et non une seule : c'est ce qui permet de **remettre la vitrine à
zéro** avant un entretien sans toucher à quoi que ce soit d'autre. Une
démonstration se prépare, elle ne s'improvise pas sur des données abîmées par
les essais de la veille.

> Prenez la chaîne **pooled** (elle contient `-pooler`). Sans elle, Render
> ouvre une connexion par processus et Neon ferme la porte au bout de quelques
> dizaines.

### 2. L'API, chez Render

Render lit [`render.yaml`](render.yaml) : rien n'est à cliquer sauf les deux
secrets, qui n'ont rien à faire dans un dépôt.

```
DATABASE_URL     la chaîne pooled de Neon
CLOUDINARY_URL   cloudinary://<clé>:<secret>@<nom>
```

Les migrations et `collectstatic` tournent **au démarrage du conteneur**, pas à
sa construction : une mise en ligne n'exige donc jamais une commande manuelle,
qu'on finirait par oublier un jour de stress.

### 3. Le front web, chez Vercel

Racine du projet : `frontend-web`. Vercel lit
[`vercel.json`](vercel.json). Une seule variable :

```
VITE_API_URL   https://rivdinde-api.onrender.com/api/v1
```

La règle de réécriture renvoie toutes les URL vers `index.html` — sans elle,
recharger `/espace/catalogue` donnerait un 404 : le serveur cherche un fichier
qui n'existe pas, puisque c'est le routeur du navigateur qui fabrique cette
page.

### 4. Le peuplement de la vitrine

Une fois, depuis le terminal de Render :

```
DEMO_AUTORISEE=1 python manage.py seed_admin
DEMO_AUTORISEE=1 python manage.py seed_demo
```

`seed_demo` refuse de s'exécuter hors développement sans `DEMO_AUTORISEE` :
il crée des comptes à mot de passe connu, et une variable posée sciemment vaut
mieux qu'un garde-fou qu'on croit avoir mis.

### 5. L'application mobile

```
cd frontend-mobile
echo "VITE_API_URL=https://rivdinde-api.onrender.com/api/v1" > .env
npm run build
npx cap add android      # la première fois seulement
npx cap sync android
npx cap open android     # Android Studio prend le relais pour signer l'APK
```

---

## Les trois pièges de l'offre gratuite, et leurs parades

### Le service Render s'endort après 15 minutes

Il met **une minute** à repartir. Un recruteur qui ouvre le lien pendant ce
temps voit une page blanche et n'insiste pas.

La parade est dans [`.github/workflows/reveil.yml`](../.github/workflows/reveil.yml) :
une tâche appelle `/api/v1/sante` toutes les dix minutes. Elle est
**désactivée par défaut** et s'active à la main le jour de la démonstration —
la laisser tourner en continu consommerait le quota mensuel d'heures gratuites
en trois semaines.

### La première requête après une mise en ligne est lente

Migrations puis `collectstatic` : comptez trente secondes. Ouvrez le lien une
fois avant l'entretien, pas devant la personne.

### Neon met la base en veille elle aussi

Le réveil est bien plus rapide (quelques secondes) et le ping de l'API la
réveille au passage : la parade ci-dessus couvre les deux.

---

## Vérifier que la mise en ligne a réussi

Dans cet ordre, et sans en sauter :

```
curl https://rivdinde-api.onrender.com/api/v1/sante        # {"data":{"etat":"ok"}}
curl https://rivdinde-api.onrender.com/api/v1/produits     # le catalogue public
```

puis, dans le navigateur : ouvrir le front, se connecter avec un compte de
démonstration, ajouter un article au panier. **Si le panier échoue alors que
l'API répond**, c'est presque toujours `CORS_ALLOWED_ORIGINS` : le navigateur
bloque la requête avant même de l'envoyer, et l'API n'en voit jamais la
trace — c'est exactement le piège qui a coûté une demi-journée au bloc H.
