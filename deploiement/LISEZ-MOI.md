# Mettre RivDinde en ligne — le guide détaillé

> Trois hébergeurs, trois raisons, zéro carte bancaire. Le découpage vient de
> [D-19](../plan-organisation/00-pilotage/journal-decisions.md) et il n'a pas
> bougé depuis.
>
> Compter **une heure** la première fois. Les pièges sont à la fin, et ils
> valent la lecture : chacun a réellement coûté du temps sur ce projet.

| Morceau | Où | Pourquoi là et pas ailleurs |
|---|---|---|
| Base PostgreSQL | **Neon** | Render n'offre Postgres gratuitement que 90 jours : la démonstration mourrait à date fixe |
| API Django | **Render**, image Docker | Un backend Django est un processus long ; Vercel exécute des fonctions sans état |
| Front web | **Vercel** | C'est exactement son métier : des fichiers statiques sur un réseau de diffusion |
| Images produit | **Cloudinary** | Le disque de Render est éphémère — une photo téléversée disparaît au redéploiement suivant |
| Application mobile | **APK signé**, distribué à la main | Publier sur le Play Store coûte 25 $ et n'apporte rien à une démonstration |

---

## Avant de commencer

```
cd backend && python manage.py check --deploy
```

Il liste ce que Django juge dangereux en production. Tout ne s'applique pas
(certains avertissements supposent un HTTPS géré par nous, que Render fournit),
mais lis-les : c'est plus rapide que de les découvrir en ligne.

---

## 1. La base, chez Neon

Crée un projet, puis **deux bases** dedans : `rivdinde_vitrine` et
`rivdinde_production`. Neon donne une chaîne de connexion par base.

Deux bases et non une seule : c'est ce qui permet de **remettre la vitrine à
zéro** avant un entretien sans toucher au reste. Une démonstration se prépare,
elle ne s'improvise pas sur des données abîmées par les essais de la veille.

> **Prends la chaîne *pooled*** — celle qui contient `-pooler`. Sans elle,
> Render ouvre une connexion par processus et Neon ferme la porte au bout de
> quelques dizaines. Le symptôme est déroutant : ça marche, puis ça ne marche
> plus, puis ça remarche.

La chaîne ressemble à :

```
postgresql://utilisateur:motdepasse@ep-xxx-pooler.eu-central-1.aws.neon.tech/rivdinde_vitrine?sslmode=require
```

Garde `?sslmode=require` : Neon refuse les connexions en clair.

---

## 2. L'API, chez Render

Render lit [`render.yaml`](render.yaml) : rien n'est à cliquer sauf les
secrets, qui n'ont rien à faire dans un dépôt.

### Les variables à poser à la main

| Variable | Valeur | Où la trouver |
|---|---|---|
| `DATABASE_URL` | la chaîne **pooled** de Neon | tableau de bord Neon → Connection string |
| `CLOUDINARY_CLOUD_NAME` | le nom du compte | Cloudinary → Product Environment Credentials |
| `CLOUDINARY_API_KEY` | la clé | idem |
| `CLOUDINARY_API_SECRET` | le secret | idem |

Les autres — `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ORIGINS`,
`DEMO_AUTORISEE` — sont dans `render.yaml`. La clé secrète est **engendrée par
Render** à la première mise en ligne : elle n'est jamais écrite nulle part.

> ⚠ **Les noms de variables comptent, et une erreur ne se voit pas.**
> Ce fichier a posé pendant un temps `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`
> et `CLOUDINARY_URL`, alors que les réglages lisent `ALLOWED_HOSTS`,
> `CORS_ORIGINS` et trois variables Cloudinary distinctes. Aucune erreur au
> déploiement : la valeur par défaut s'applique, et le front se serait fait
> refuser par le navigateur au premier appel.
>
> `coeur/tests/test_variables_environnement.py` compare désormais ce que le
> code lit à ce que la configuration propose, dans les deux sens.

### Ce qui se passe au démarrage du conteneur

```
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn config.wsgi
```

Migrations et fichiers statiques tournent **au démarrage**, pas à la
construction de l'image. Une mise en ligne n'exige donc jamais une commande
manuelle, qu'on finirait par oublier un jour de stress. Le prix : la première
requête après un déploiement met une trentaine de secondes.

---

## 3. Le front web, chez Vercel

Racine du projet : `frontend-web`. Vercel lit [`vercel.json`](vercel.json).

Une seule variable :

```
VITE_API_URL=https://rivdinde-api.onrender.com/api/v1
```

> **`VITE_` n'est pas décoratif.** Vite n'expose au navigateur que les
> variables préfixées ainsi. Une variable nommée `API_URL` serait lue comme
> `undefined`, et le front appellerait `undefined/produits`.
>
> Et elle est **figée à la construction**, pas lue à l'exécution : changer
> l'adresse de l'API impose de reconstruire. Ce n'est pas un bogue, c'est ce
> qu'est un fichier statique.

La règle de réécriture renvoie toutes les URL vers `index.html`. Sans elle,
recharger `/espace/catalogue` donnerait un 404 : le serveur cherche un fichier
qui n'existe pas, puisque c'est le routeur du navigateur qui fabrique cette
page.

---

## 4. Relier les deux : l'étape qu'on oublie

Une fois Vercel déployé, tu connais son domaine. **Retourne sur Render** et
mets-le dans `CORS_ORIGINS` :

```
CORS_ORIGINS=https://rivdinde.vercel.app
```

Sans quoi le navigateur bloque chaque appel **avant de l'envoyer** : l'API
répond parfaitement, ses journaux sont vides, et le front affiche « l'API ne
répond pas ».

> Ce piège a coûté une demi-journée au bloc H. Il ne se voit ni dans les tests,
> ni avec `curl` : **seul un navigateur applique le contrôle CORS**.

Attention aussi :

- **pas de barre oblique finale** — `https://rivdinde.vercel.app/` ne
  correspond pas à `https://rivdinde.vercel.app` ;
- **`https` et non `http`** ;
- Vercel crée une URL **par déploiement** (`rivdinde-abc123.vercel.app`). Seul
  le domaine stable est dans `CORS_ORIGINS` : les aperçus de branche seront
  bloqués, et c'est voulu.

---

## 5. Peupler la vitrine

Une fois, depuis le terminal de Render (onglet *Shell*) :

```
DEMO_AUTORISEE=1 python manage.py seed_admin
DEMO_AUTORISEE=1 python manage.py seed_demo
```

`seed_demo` enchaîne lui-même le catalogue et l'activité : environ 30 comptes,
59 produits, 85 commandes.

Il **refuse de s'exécuter** hors développement sans `DEMO_AUTORISEE` : il crée
des comptes à mot de passe connu, et une variable posée sciemment vaut mieux
qu'un garde-fou qu'on croit avoir mis.

Puis, pour vérifier :

```
python manage.py verifier_couverture --strict
```

Il interroge la vraie base et échoue si un scénario du dossier produit n'a plus
rien à montrer.

> Le peuplement **fabrique les images** si le réseau manque, ce qui est le cas
> sur le shell de Render. Les 24 vraies photos sont dans le dépôt sous
> `plan-organisation/donnees-demo/images/` et sont reprises en priorité.

---

## 6. L'application mobile

```
cd frontend-mobile
echo "VITE_API_URL=https://rivdinde-api.onrender.com/api/v1" > .env
npm run build
npx cap add android      # la première fois seulement
npx cap sync android
npx cap open android     # Android Studio prend le relais pour signer l'APK
```

Deux choses à vérifier **avant** de fabriquer l'APK que tu distribues :

1. **`server.url` doit être commenté** dans `capacitor.config.ts`. S'il pointe
   encore vers ton IP de développement, l'application cherchera ta machine chez
   la personne qui l'installe, et n'affichera rien du tout ;
2. **l'API doit être en HTTPS.** Android bloque le HTTP en clair depuis la
   version 9. `cleartext: true` le rétablit, mais c'est une porte ouverte à ne
   garder qu'en développement.

Le lancement en local est décrit dans
[`frontend-mobile/LISEZ-MOI.md`](../frontend-mobile/LISEZ-MOI.md).

---

## Les pièges de l'offre gratuite, et leurs parades

### Le service Render s'endort après 15 minutes

Il met **une minute** à repartir. Un recruteur qui ouvre le lien pendant ce
temps voit une page blanche et n'insiste pas.

La parade est dans [`.github/workflows/reveil.yml`](../.github/workflows/reveil.yml) :
une tâche appelle `/api/v1/sante` toutes les dix minutes. Elle est
**désactivée par défaut** et s'active à la main le jour de la démonstration —
la laisser tourner en continu consommerait le quota mensuel d'heures gratuites
en trois semaines.

Le réflexe qui vaut mieux que tout : **ouvre le lien dix minutes avant
l'entretien**, pas devant la personne.

### Neon met la base en veille elle aussi

Réveil plus rapide — quelques secondes — et le ping de l'API la réveille au
passage : la parade ci-dessus couvre les deux.

### La première requête après une mise en ligne est lente

Migrations puis `collectstatic` : compte trente secondes. C'est le prix du
choix « rien à lancer à la main », et il se paie une fois par déploiement.

---

## Les pièges qui ne viennent pas de l'offre gratuite

### « 400 Bad Request » sur toutes les pages

`ALLOWED_HOSTS` ne contient pas le domaine. Django refuse une requête dont
l'en-tête `Host` n'est pas déclaré, avec un 400 sans explication.

Render publie son domaine dans `RENDER_EXTERNAL_HOSTNAME`, que les réglages
ajoutent automatiquement — mais si tu poses un domaine personnalisé, il faut
l'ajouter à la main.

### « Le front est vide, l'API répond »

CORS. Voir l'étape 4. C'est **toujours** ça.

Pour en avoir le cœur net, sans navigateur :

```
curl -s -D - -o /dev/null https://rivdinde-api.onrender.com/api/v1/produits \
  -H "Origin: https://rivdinde.vercel.app" | grep -i access-control-allow-origin
```

Pas de ligne en retour = le navigateur bloquera.

### « Les images ne s'affichent pas »

Le disque de Render est éphémère : tout ce que `seed_catalogue` a écrit dans
`media/` disparaît au redéploiement suivant. C'est la raison d'être de
Cloudinary. Si les trois variables `CLOUDINARY_*` ne sont pas posées, le projet
retombe sur le disque local — et les images tiennent jusqu'au prochain
déploiement, pas au-delà.

### « L'administration Django refuse ma connexion »

`CSRF_TRUSTED_ORIGINS` doit contenir le domaine de l'API en `https://`. Django
4 et suivants exigent le schéma complet, et le message d'erreur ne le dit pas
clairement.

### « Le paiement reste en simulation malgré ma clé »

Vérifie le **nom** de la variable : le code lit `STRIPE_SECRET_KEY`. Tant
qu'elle est vide, `fournisseur_de_paiement()` rend le simulateur — c'est voulu
([D-18](../plan-organisation/00-pilotage/journal-decisions.md)), et c'est
silencieux par construction.

`GET /api/v1/services` dit lequel tourne, sans avoir à lire le code.

### « Le webhook Stripe n'arrive jamais »

L'URL de webhook ne peut pas être `localhost` : Stripe appelle depuis
l'extérieur. En développement, `stripe listen --forward-to` fait le pont ; en
ligne, il faut l'URL publique de Render.

Et **garde le mode test** tant que le projet est une démonstration.

---

## Vérifier que la mise en ligne a réussi

Dans cet ordre, sans en sauter :

```
curl https://rivdinde-api.onrender.com/api/v1/sante      # {"data":{"etat":"ok"}}
curl https://rivdinde-api.onrender.com/api/v1/produits   # le catalogue public
curl https://rivdinde-api.onrender.com/api/v1/services   # simulateur ou vrai fournisseur
```

Puis, dans le navigateur : ouvre le front, connecte-toi avec un compte de
démonstration, **ajoute un article au panier**. C'est le premier appel qui
porte un en-tête personnalisé (`X-Panier-Session`), donc le premier que le
navigateur soumet au contrôle CORS complet.

Si le panier échoue alors que l'API répond, c'est presque toujours
`CORS_ORIGINS`.
