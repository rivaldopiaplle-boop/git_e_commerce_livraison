# De NestJS/React à Django/Vue — le guide de traduction

> Réponse au bloc F-3 : *« c'est quoi l'équivalent de `src` dans Nest et React,
> MUI, hot, hook, bootstrap, component… c'est quoi la logique ici, en faisant
> une analogie avec le projet banque ? »*
>
> Tu connais déjà tout ce qu'il y a dans ce projet. **Ce ne sont pas de nouveaux
> concepts, ce sont les mêmes avec d'autres noms.** Ce document met les deux
> colonnes côte à côte, avec les vrais chemins des deux dépôts.

---

## 1. Ce qui ne change jamais, quel que soit l'écosystème

Avant les tableaux, la seule chose à retenir : **tout backend web fait les mêmes
six choses**, et tout front en fait quatre. Les frameworks ne changent que le
vocabulaire et la répartition des fichiers.

Un backend : *recevoir une requête → vérifier qui appelle → valider ce qui
entre → appliquer la règle métier → parler à la base → renvoyer du JSON.*

Un front : *afficher un état → réagir à un clic → appeler l'API → réafficher.*

NestJS répartit ça en `controller` / `service` / `dto` / `guard`. Django le
répartit en `urls` / `views` / `serializers` / `permissions`. **Ce sont les
mêmes six cases.**

---

## 2. Backend — NestJS ↔ Django

### 2.1 La racine du code

| banque-app (NestJS) | RivDinde (Django) | Ce que c'est |
|---|---|---|
| `backend/src/` | `backend/` | La racine du code. **Django n'a pas de `src/`** : les paquets Python sont directement sous `backend/` |
| `backend/src/main.ts` | `backend/manage.py` et `backend/config/wsgi.py` | Le point d'entrée. `manage.py` en développement, `wsgi.py` pour Gunicorn en ligne |
| `backend/src/app.module.ts` | `backend/config/settings.py` | L'assemblage : quels modules existent, quelle base, quels réglages |
| `backend/package.json` | `backend/requirements.txt` | Les dépendances déclarées |
| `backend/node_modules/` | `backend/.venv/` | Les dépendances installées. Ni l'un ni l'autre n'est versionné |
| `backend/.env` | `backend/.env` | Identique, au mot près |

**Le mot qui manque : `src`.** En Python, un dossier contenant un
`__init__.py` est un *paquet*, et c'est lui l'unité d'organisation. Mettre le
tout dans un `src/` n'apporterait rien qu'un niveau de plus à écrire dans chaque
import.

### 2.2 Un module métier

Dans banque-app, `backend/src/comptes/` contient quatre choses :

```
comptes/
├── comptes.controller.ts     les routes HTTP
├── comptes.service.ts        la logique métier
├── comptes.module.ts         la déclaration du module
└── dto/                      la validation des entrées
```

L'équivalent Django s'appelle une **app**, et c'est exactement le même
découpage — sans le fichier de déclaration :

```
comptes/
├── urls.py            les routes           ← comptes.controller.ts (le routage)
├── views.py           les points d'entrée  ← comptes.controller.ts (les méthodes)
├── serializers.py     entrée et sortie     ← dto/
├── services.py        la logique métier    ← comptes.service.ts
├── models.py          les tables           ← prisma/schema.prisma (la partie « comptes »)
├── permissions.py     qui a le droit       ← guards/
├── admin.py           le back-office (§ 5) ← aucun équivalent Nest
├── migrations/        l'historique du schéma
└── tests/
```

**La différence qui compte** : NestJS a un conteneur d'injection de dépendances
— `constructor(private comptesService: ComptesService)`. Django n'en a pas :
on écrit `from .services import creer_compte` et on appelle la fonction. Moins
de cérémonie, moins de magie ; en contrepartie, remplacer une implémentation
pour un test se fait par `monkeypatch` plutôt que par un module de test.

### 2.3 Le concept, ligne à ligne

| NestJS | Django / DRF | Remarque |
|---|---|---|
| `@Controller('comptes')` | `urls.py` + `views.py` | Django sépare l'URL du code qui répond |
| `@Get(':id')` | `path("<int:id>", vues.detail)` | |
| `@Body() dto: CreerCompteDto` | `serializer = CompteSerializer(data=request.data)` | |
| `class-validator` (`@IsEmail()`) | champs du serializer (`EmailField`) | Même idée : on décrit, on ne vérifie pas à la main |
| `@UseGuards(JwtAuthGuard)` | `permission_classes = [IsAuthenticated]` | |
| `guards/roles.guard.ts` | `permissions.py` → `class EstVendeur(BasePermission)` | |
| `passport` + `strategies/` | `djangorestframework-simplejwt` | |
| `PrismaService` | l'ORM intégré : `Produit.objects.filter(...)` | Django **est** son propre ORM, pas besoin de service |
| `prisma/schema.prisma` | `models.py` de chaque app | Le schéma est du code Python, pas un langage à part |
| `npx prisma migrate dev` | `python manage.py makemigrations` puis `migrate` | Même mécanique : un fichier de migration versionné |
| `npx prisma studio` | `/admin/` (§ 5) | Django va beaucoup plus loin |
| `common/filters/` | `EXCEPTION_HANDLER` de DRF | |
| `main.ts` → `app.enableCors()` | `django-cors-headers` + `CORS_ALLOWED_ORIGINS` | |
| `*.spec.ts` avec Jest | `tests/test_*.py` avec pytest | |
| `eslint` + `prettier` | `ruff` — il fait les deux | |
| `npm run start:dev` | `python manage.py runserver` | Rechargement automatique dans les deux cas |
| `npm run build` | *rien* | Python ne compile pas. Il n'y a pas de `dist/` côté backend |

### 2.4 Le vocabulaire Django qui n'existe pas chez Nest

- **App** : un paquet métier. `python manage.py startapp catalogue` crée le
  squelette. Une app doit être déclarée dans `INSTALLED_APPS`.
- **Migration** : un fichier Python généré qui décrit un changement de schéma.
  L'équivalent exact des migrations Prisma, à ceci près qu'il est lisible et
  modifiable à la main.
- **QuerySet** : le résultat *paresseux* d'une requête. `Produit.objects.filter(...)`
  ne touche pas la base tant qu'on ne lit pas le résultat. C'est ce qui permet
  d'enchaîner `.filter().exclude().order_by()` sans faire trois requêtes.
- **Management command** : un script exécutable via `manage.py`. Chez Nest, tu
  écrivais des scripts autonomes ; ici, `python manage.py seed_admin` a accès à
  toute l'application. Exemple réel :
  [`backend/coeur/management/commands/seed_admin.py`](../../backend/coeur/management/commands/seed_admin.py).

---

## 3. Front — React ↔ Vue

### 3.1 Les fichiers

| banque-app (React) | RivDinde (Vue) |
|---|---|
| `frontend-web/src/main.tsx` | `frontend-web/src/main.ts` |
| `src/app/App.tsx` | `src/App.vue` |
| `src/app/AppShell.tsx` | `src/composants/CoquilleApp.vue` (à venir) |
| `src/app/router.tsx` | `src/routeur.ts` (vue-router) |
| `src/features/comptes-client/` | `src/vues/client/` |
| `src/shared/api/` | `src/api/` |
| `src/app/theme.ts`, `tokens.ts` | variables CSS dans `src/style.css` + Tailwind |
| `src/assets/` | `public/` et `src/assets/` |
| **Vite** | **Vite** — le même outil, à l'identique |

Le découpage `features/` de banque-app était bon : on le garde, sous le nom
`vues/`. Un dossier par rôle, pas un dossier par type de fichier.

### 3.2 Un composant

React, dans banque-app :

```tsx
export function CarteCompte({ compte }: { compte: Compte }) {
  const [ouvert, setOuvert] = useState(false)
  useEffect(() => { charger() }, [])
  const solde = useMemo(() => formater(compte.solde), [compte.solde])
  return <div className="carte" onClick={() => setOuvert(!ouvert)}>{solde}</div>
}
```

Vue, ici — **un seul fichier, trois blocs** :

```vue
<script setup lang="ts">
const props = defineProps<{ compte: Compte }>()
const ouvert = ref(false)
onMounted(() => charger())
const solde = computed(() => formater(props.compte.solde))
</script>

<template>
  <div class="carte" @click="ouvert = !ouvert">{{ solde }}</div>
</template>

<style scoped>
.carte { border-radius: 12px; }
</style>
```

Exemple réel dans le dépôt :
[`frontend-web/src/composants/LogoRivDinde.vue`](../../frontend-web/src/composants/LogoRivDinde.vue).

### 3.3 Le concept, ligne à ligne

| React | Vue 3 | Remarque |
|---|---|---|
| JSX dans le `return` | bloc `<template>` | Vue sépare le balisage du code |
| `useState(0)` | `ref(0)` | En Vue, on lit et on écrit `.value` **dans le script**, jamais dans le template |
| `useState({...})` | `reactive({...})` | Pour un objet, sans `.value` |
| `useEffect(fn, [])` | `onMounted(fn)` | |
| `useEffect(fn, [x])` | `watch(x, fn)` | |
| `useEffect(fn)` (sans tableau) | `watchEffect(fn)` | |
| `useMemo(fn, [x])` | `computed(fn)` | **Vue trouve les dépendances tout seul** : pas de tableau à tenir à jour, donc pas ce bogue-là |
| `useCallback` | inutile | Vue ne recrée pas la fonction à chaque rendu |
| `props` | `defineProps<{...}>()` | |
| `onChange={fn}` en props | `defineEmits<{ (e: 'change'): void }>()` | Vue distingue ce qui entre de ce qui sort |
| `children` | `<slot />` | |
| `useContext` | `provide` / `inject` | |
| Zustand, Redux, TanStack Query | **Pinia** | Un seul outil couvre les trois usages |
| `react-router` | `vue-router` | API très proche |
| `className` | `class` | Vue accepte l'attribut HTML normal |
| CSS Modules, emotion | `<style scoped>` | Intégré, rien à installer |
| `key` dans un `.map()` | `:key` dans un `v-for` | Même règle, même raison |
| **MUI** | **PrimeVue** | Voir [design-system.md](../04-maquettes/design-system.md) § 9 |
| Bootstrap (le CSS) | **Tailwind CSS** | |
| `ReactDOM.createRoot().render()` | `createApp(App).mount('#app')` | C'est ça, « bootstrapper » une application |
| **HMR / hot reload** | **identique** | C'est Vite dans les deux projets, pas React ni Vue |

### 3.4 Les trois pièges quand on arrive de React

1. **`.value`**. Une `ref` se lit `compteur.value` dans le `<script>`, mais
   `{{ compteur }}` dans le `<template>` — Vue déballe automatiquement dans le
   balisage. C'est l'erreur numéro un des trois premiers jours.
2. **La mutation est autorisée.** En React, on écrit
   `setListe([...liste, x])`. En Vue, `liste.push(x)` suffit et déclenche le
   rendu. Copier par réflexe fonctionne mais n'apporte rien.
3. **Le template n'est pas du JavaScript.** Pas de `.map()`, pas de ternaire
   pour afficher ou non : `v-for`, `v-if`, `v-else`. C'est plus contraint, et
   c'est ce qui rend un template Vue lisible par quelqu'un qui ne connaît pas
   le projet.

---

## 4. Mobile — Expo/React Native ↔ Ionic Vue + Capacitor

| banque-app (Expo) | RivDinde (Ionic + Capacitor) |
|---|---|
| `frontend-mobile/App.tsx` | `frontend-mobile/src/App.vue` |
| `app.json` | `capacitor.config.ts` |
| `<View>`, `<Text>`, `<FlatList>` | `<div>`, `<p>`, `<ion-list>` — **du HTML** |
| `expo start` | `ionic serve` — ça s'ouvre dans un navigateur |
| `eas build` | `npx cap sync` puis `npx cap open android` |
| `expo-location` | `@capacitor/geolocation` |
| `expo-camera` | `@capacitor/camera` |
| `expo-notifications` | `@capacitor/push-notifications` |
| Rendu **natif** | Rendu **web dans une webview native** |

**La différence de fond** : React Native traduit tes composants en vrais
composants natifs. Capacitor embarque une page web dans une application native
et lui donne accès au matériel. En pratique, sur une application de livraison,
l'utilisateur ne voit pas la différence — et tu réutilises directement ce que tu
sais faire en Vue. La contrepartie est écrite dans
[D-20](../00-pilotage/journal-decisions.md).

---

## 5. `/admin/` — ce que c'est, et ce que ce n'est pas

> Réponse au bloc F-2 : *« c'est toi qui l'as écrit ou tu l'as importé ? à quoi
> ça sert ? si c'est le front, tu es fou, il y a les règles d'or et les CMS
> pour ça. »*

**Je n'ai écrit aucune ligne.** C'est le **Django Admin**, livré avec Django.
Il tient en deux lignes déjà présentes : `django.contrib.admin` dans
`INSTALLED_APPS`, et `path("admin/", admin.site.urls)` dans `config/urls.py`.

### Ce que c'est

Un back-office **engendré automatiquement à partir des modèles**. Dès qu'une
table existe, il sait la lister, la filtrer, la trier, la créer, la modifier, la
supprimer — avec les droits, la validation et le journal des modifications. Il
n'a pas d'équivalent dans NestJS ; le plus proche que tu connaisses est
`prisma studio`, mais Prisma Studio n'est qu'un éditeur de tables, alors que
Django Admin connaît les règles métier.

### À quoi il sert ici

1. **Pendant le développement** : voir ce qu'un test a créé, corriger un statut
   à la main, valider un vendeur avant même que l'écran existe. Sans lui, il
   faudrait écrire du SQL ou coder un écran pour chaque vérification.
2. **En exploitation** : dépanner un cas tordu que le produit ne prévoit pas.
3. **En entretien** : montrer le modèle de données en trente secondes.

C'est d'ailleurs **une des raisons pour lesquelles Django a été choisi** pour ce
projet précis — c'est écrit dans
[stack-technique.md](stack-technique.md) § 2.

### Ce que ce n'est pas

**Ce n'est pas le front du produit, et ça ne le sera jamais.** Tu as raison sur
ce point, et le doute est légitime. L'interface du produit, ce sont :

- l'application **Vue** pour le client, le vendeur, le gestionnaire et l'admin,
  décrite dans [contrat-web.md](../03-contrats/contrat-web.md) — sidebar
  rétractable, navbar, panneau droit, onglets, boutons-icônes : les règles d'or
  6 et 8 ;
- l'application **Ionic** pour le client et le livreur, décrite dans
  [contrat-mobile.md](../03-contrats/contrat-mobile.md) — cinq onglets, le
  troisième étant le « + ».

Django Admin n'a rien de tout ça et n'essaiera pas de l'avoir. Ce sont **deux
publics différents** : le produit s'adresse à Léa, Karim et Amine ; `/admin/`
s'adresse à toi, développeur.

### Et la règle d'or n°5 ?

Elle joue *pour* lui : « ne réinvente jamais la roue ». Un back-office technique
gratuit, complet et sécurisé, qui apparaît en deux lignes — s'en priver pour
coder à la main des écrans que personne ne verra serait exactement l'inverse de
ce que tu demandes.

---

## 6. Récapitulatif — où est quoi, dans ce dépôt

```
rivdinde/
├── backend/                    ← src/ de NestJS
│   ├── config/                 ← app.module.ts + main.ts
│   │   ├── settings.py             assemblage, base, CORS, réglages
│   │   ├── urls.py                 la table de routage racine
│   │   └── wsgi.py                 le point d'entrée de production
│   ├── coeur/                  ← un module NestJS
│   │   ├── views.py                controller
│   │   ├── urls.py                 les @Get / @Post
│   │   ├── models.py               schema.prisma
│   │   ├── tests/                  *.spec.ts
│   │   └── management/commands/    tes scripts, mais avec l'app chargée
│   ├── requirements.txt        ← package.json
│   └── .venv/                  ← node_modules/
│
├── frontend-web/               ← identique à banque-app, à React près
│   ├── src/main.ts             ← main.tsx
│   ├── src/App.vue             ← App.tsx
│   ├── src/composants/         ← shared/
│   ├── src/vues/               ← features/
│   └── public/                 ← assets servis tels quels
│
└── frontend-mobile/            ← frontend-mobile/ (Expo → Capacitor)
```

---

## 7. Les cinq commandes à connaître par cœur

| Ce que tu veux | banque-app | RivDinde |
|---|---|---|
| Tout lancer | `node demarrer.mjs` | `python demarrer.py` |
| Ajouter une dépendance backend | `npm i paquet` | ajouter à `requirements.txt` puis `pip install -r` |
| Changer le schéma | modifier `schema.prisma` puis `prisma migrate dev` | modifier `models.py` puis `manage.py makemigrations` et `migrate` |
| Lancer les tests | `npm test` | `pytest` (depuis `backend/`) |
| Vérifier le style | `npm run lint` | `ruff check .` |

**Une précision qui évite une heure perdue** : toutes les commandes Python
passent par l'environnement virtuel. Soit tu l'actives
(`backend\.venv\Scripts\Activate.ps1`), soit tu appelles son interpréteur
directement (`backend\.venv\Scripts\python.exe manage.py ...`). Un `pip install`
lancé hors environnement installe dans le Python du système, et le projet ne le
voit pas.
