# Stack technique

> Règle d'or n°5 : ne rien réinventer. Règle d'or n°2 : penser production
> d'abord. Contrainte personnelle : **Django et Vue sont obligatoires**, pour ne
> pas refaire le NestJS/React du projet banque et doubler ton champ de compétence.

---

## 1. Vue d'ensemble

| Couche | Retenu | Statut |
|---|---|---|
| Backend | **Python / Django + Django REST Framework** | Acté (D-14) |
| Base de données | **PostgreSQL** via l'ORM Django | Acté |
| Front web | **Vue 3 + Vite + TypeScript + Pinia** | Acté (D-14) |
| Interface web | **Tailwind CSS + PrimeVue**, icônes **Lucide** | Acté (D-26) |
| Mobile | **Ionic Vue + Capacitor** | Acté (D-20) |
| Paiement | **Stripe** + **Stripe Connect** | Acté |
| Base hébergée | **Neon** (PostgreSQL sans serveur, offre gratuite) | Acté |
| Hébergement API | **Render**, conteneur Docker | Acté (D-19) |
| Hébergement web | **Vercel** | Acté (D-19) |
| Images | **Cloudinary**, disque local en développement | Acté (D-24) |
| Géocodage | **Nominatim** (OpenStreetMap), distances en haversine | Acté (D-25) |
| Conteneurisation | **Docker + Docker Compose** | Acté |
| CI/CD | **GitHub Actions** | Acté |
| E-mail | Un service transactionnel (Resend, Brevo…) + simulateur local | Acté |
| Push | **Firebase Cloud Messaging**, palier 2 | Acté |
| Cartographie | **Leaflet + OpenStreetMap** (gratuit, sans clé) | Recommandé |
| Itinéraire affiché au livreur | Application de navigation du téléphone, par lien | Recommandé |
| Temps réel | Interrogation périodique au MVP, **Django Channels** au palier 2 | Acté (D-16) |
| Optimisation de tournées | **Google OR-Tools**, palier 2 | Acté |

---

## 2. Pourquoi ces choix

### Django + DRF
Le gain décisif sur **ce** projet précis : le Django Admin donne gratuitement un
back-office pour six rôles et une quinzaine de tables, dès le premier jour. Les
validations de vendeurs, les ajustements de stock, l'arbitrage de litiges y sont
utilisables avant même d'écrire un écran Vue. On refait ensuite en Vue seulement
ce qu'on veut montrer. Aucun autre écosystème ne donne ça sans travail.

L'ORM Django apporte aussi ce dont ce projet a besoin sur les points délicats :
`select_for_update` pour le verrou de stock (R-02), les transactions atomiques
pour le découpage du panier, et les migrations versionnées.

### Vue 3 + Vite
Composition API très proche des Hooks React que tu connais : la transition est
rapide, ce qui est exactement l'objectif (apprendre un second écosystème sans
repartir de zéro). Pinia pour l'état, VueUse pour la géolocalisation et les
utilitaires, Vite pour un démarrage instantané.

### Mobile : Ionic Vue + Capacitor (D-20)
« Vue Native » n'existe plus comme produit vivant. Le choix réel était entre un
rendu natif (NativeScript-Vue) et une webview native (Ionic + Capacitor). Sur le
papier le natif est plus impressionnant ; en pratique, l'application livreur a
besoin de géolocalisation continue, de cartes et de notifications — trois
domaines où l'écosystème Capacitor est riche et documenté, et où NativeScript-Vue
peut coûter une semaine sur un greffon manquant. Capacitor produit une vraie
application installable, réutilise directement les composants Vue, et laisse
expliquer un choix d'ingénierie en entretien plutôt que subir un blocage.

### Tailwind + PrimeVue pour l'interface (D-26)
La règle d'or n°6 demande des tableaux avec boutons-icônes, des tiroirs, des
fenêtres, des onglets et des panneaux rétractables. Les écrire à la main
correctement — accessibilité, clavier, focus, tri, pagination — représente
plusieurs semaines pour un résultat inférieur. PrimeVue les fournit, Tailwind
porte la mise en page et l'accent de couleur par rôle. Le détail, et surtout ce
qu'on emprunte aux CMS marchands sans emprunter leur architecture, est dans
[design-system.md](../04-maquettes/design-system.md).

### Stripe puis Stripe Connect
Stripe seul suffit tant qu'une commande ne concerne qu'un vendeur (Express).
Connect devient nécessaire dès la commande Standard multi-vendeur, qui est dans
le MVP : on l'intègre donc dès la tranche paiement, mais inutile de
subir sa complexité dès le début.

### Cartographie et géocodage sans clé d'API (D-25)
Leaflet avec les fonds OpenStreetMap ne demande ni compte ni carte bancaire.
Nominatim transforme une adresse en coordonnées, appelé **une fois** à
l'enregistrement d'une adresse et jamais à l'affichage — sa politique d'usage
plafonne à une requête par seconde, ce qui est très au-dessus de nos besoins mais
interdit de l'appeler dans une boucle. La distance entre deux points est calculée
en local par la formule de haversine : aucun appel réseau, aucune latence.
Google Maps serait plus beau, mais exige une carte bancaire dès l'inscription.
**Limite assumée** : le vol d'oiseau n'est pas la distance routière — suffisant
pour des bandes de frais (D-11), et honnête à expliquer en entretien.

### Pourquoi pas de WebSocket au MVP
Django Channels impose un serveur ASGI **et** un Redis. Sur un hébergement
gratuit, c'est le service en trop : plus de configuration, plus de pannes, pour
gagner quelques secondes de fraîcheur d'affichage. L'interrogation périodique
donne le même résultat visible. Les charges utiles étant identiques, passer aux
WebSockets plus tard ne changera que le transport.

---

## 3. Ce qu'on n'ajoute pas, et pourquoi

| Écarté | Raison |
|---|---|
| Celery + Redis | Les tâches différées de Django suffisent au MVP ; deux services de plus à héberger |
| Elasticsearch | La recherche plein texte de PostgreSQL suffit largement |
| PostGIS | Le calcul à vol d'oiseau suffit pour un rayon de livraison ; PostGIS complique l'hébergement |
| GraphQL | REST est plus simple à documenter et à démontrer |
| Microservices | Un monolithe Django bien découpé est le bon choix, et savoir le dire est un point fort |
| Kubernetes | Sans objet à cette échelle |

Cette liste vaut autant que la liste des choix : en entretien, expliquer ce
qu'on a **refusé** montre du jugement.

---

## 4. Organisation du dépôt

Monorepo, un seul dépôt Git :

```
colibri/
├── plan-organisation/     ← ce dossier
├── backend/               ← Django 5 + DRF
├── frontend-web/          ← Vue 3 + Vite + TypeScript
├── frontend-mobile/       ← Ionic Vue + Capacitor (tranche 7)
├── donnees-demo/          ← catalogue de démonstration + images (D-24)
├── .github/workflows/     ← intégration et publication
├── docker-compose.yml     ← Postgres + attrapeur de courriels
├── demarrer.py            ← une seule commande pour tout lancer
├── .gitignore
└── README.md
```

Les noms de dossiers reprennent **exactement** ceux du projet banque
(`backend/`, `frontend-web/`, `frontend-mobile/`) : passer d'un projet à
l'autre ne demande alors aucun effort de mémoire. Les simulateurs de services
externes ne sont pas un dossier à part ici — ils vivent dans
`backend/services/`, à côté de l'interface qu'ils implémentent (D-18), ce qui
évite qu'une implémentation dérive de l'autre sans qu'on le voie.

Le `simulateur/` et le `demarrer.py` sont deux enseignements directs du projet
banque : le premier rend le projet démontrable sans compte payant, le second
rend le projet reprenable après trois semaines d'interruption.

---

## 5. Architecture de déploiement visée

```
   [ Mobile Vue ]              [ Web Vue ]
        │                          │
        │  HTTPS / REST            │  HTTPS / REST
        ▼                          ▼
   [ API Django + Gunicorn — conteneur Docker ]
        │
        ├── [ Neon — PostgreSQL ]
        ├── [ Cloudinary — images ]
        ├── [ Nominatim — géocodage ]
        ├── [ Stripe ]                (ou simulateur)
        └── [ E-mail / Push ]         (ou simulateur)
```

Le web est publié sur **Vercel**, l'API tourne en conteneur sur **Render**
([D-19](../00-pilotage/journal-decisions.md)). Détails, réveil de l'API et
procédure de bascule d'hébergeur :
[contrat-deploiement.md](../03-contrats/contrat-deploiement.md).
