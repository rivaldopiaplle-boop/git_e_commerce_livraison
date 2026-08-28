<div align="center">

<img src="frontend-web/public/favicon.svg" width="88" alt="Colibri">

# Colibri

**commander, livrer, suivre**

Une plateforme de commerce et de livraison à deux régimes :
**Express** (restauration, trajet direct) et **Standard** (colis, entrepôt, tournées groupées).

</div>

---

## Démarrer

Une seule commande, depuis la racine :

```powershell
python demarrer.py
```

Elle monte la base, prépare l'environnement, applique les migrations et lance
l'API et le front. À la fin, quatre adresses :

| | |
|---|---|
| Front web | http://localhost:5173 |
| API | http://localhost:8000/api/v1/sante |
| Administration Django | http://localhost:8000/admin/ |
| Courriels capturés | http://localhost:8026 |

Les ports de la base et des courriels (5433, 1026, 8026) sont volontairement
décalés des ports habituels : un autre projet peut occuper 5432 et 8025 sur la
même machine, et les deux doivent pouvoir tourner ensemble.

Autres usages :

```powershell
python demarrer.py --etat        # ce qui tourne, ce qui répond
python demarrer.py --sans-web    # API seule
python demarrer.py --preparer    # installe et migre, sans rien lancer
python demarrer.py --arreter     # arrête les conteneurs
```

**Prérequis** : Python 3.10 ou plus, Node 20 ou plus, Docker Desktop. Le script
vérifie tout et le dit clairement s'il manque quelque chose — et si le terminal
utilise un vieux Python alors qu'un récent est installé, il repart tout seul avec
le bon. Détail dans
[ta-part-du-travail.md](plan-organisation/00-pilotage/ta-part-du-travail.md).

**Aucune clé n'est nécessaire pour démarrer.** Sans Stripe, sans Cloudinary,
sans compte nulle part, le projet tourne : les services externes ont chacun un
simulateur local.

---

## Ce que c'est

Cinq rôles, deux circuits de livraison, un seul paiement même quand la commande
concerne plusieurs boutiques.

| Rôle | Support | Ce qu'il fait |
|---|---|---|
| **Client** | Web + mobile | Parcourt, commande, paie, suit, note |
| **Vendeur** | Web | Catalogue, stock, commandes entrantes, son personnel |
| **Gestionnaire** | Web | Prépare — pour un vendeur, ou dans un entrepôt |
| **Livreur** | Mobile | Une course à la fois (Express) ou une tournée (Standard) |
| **Admin** | Web | Valide les comptes, arbitre, surveille |

Un panier mixte se découpe tout seul : une commande par boutique Express, une
commande Standard multi-vendeur qui transite par l'entrepôt — et un seul
règlement pour le client, réparti par Stripe Connect.

---

## Structure

```
colibri/
├── plan-organisation/     Toute la conception : décisions, modèle, contrats, maquettes
├── backend/               Django 5 + Django REST Framework
├── frontend-web/          Vue 3 + Vite + TypeScript
├── frontend-mobile/       Ionic Vue + Capacitor          (tranche 7)
├── donnees-demo/          Catalogue et images de démonstration
├── docker-compose.yml     Postgres + attrapeur de courriels
└── demarrer.py            Une commande pour tout lancer
```

---

## La conception avant le code

Tout ce que le code applique est écrit avant, dans
[`plan-organisation/`](plan-organisation/README.md) : **30 décisions motivées**,
un modèle de **33 entités**, sept contrats, et des maquettes des cinq rôles.

| Pour savoir… | Ouvrir |
|---|---|
| Où en est le projet, quoi faire ensuite | [plan-organisation/README.md](plan-organisation/README.md) |
| Ce que le MVP contient, et ce qu'il refuse | [perimetre-et-mvp.md](plan-organisation/01-produit/perimetre-et-mvp.md) |
| Pourquoi tel choix technique | [journal-decisions.md](plan-organisation/00-pilotage/journal-decisions.md) |
| Le modèle de données | [mcd.html](plan-organisation/02-modele/mcd.html) · [dictionnaire-donnees.md](plan-organisation/02-modele/dictionnaire-donnees.md) |
| L'identité visuelle | [identite-visuelle.html](plan-organisation/04-maquettes/identite-visuelle.html) |

---

## État

**Tranche 0 sur 11** — le squelette qui tourne, et c'est vérifié : `ruff` sans
reproche, deux tests au vert, l'API qui renvoie
`{"statut":"en ligne","base_de_donnees":"connectee"}`, le front qui compile et
sert sa page. L'intégration continue, elle, ne s'exécutera qu'au premier envoi.

Rien de fonctionnel encore, et c'est voulu : ce socle est ce qui rend le reste
reprenable après trois semaines d'interruption.

Le plan des onze tranches, chacune avec son test de sortie, est dans
[demarrage-projet.md](plan-organisation/05-execution/demarrage-projet.md).

---

## Pile technique

Django 5 · Django REST Framework · PostgreSQL · Vue 3 · Vite · TypeScript ·
Pinia · Ionic + Capacitor · Docker · GitHub Actions · Stripe Connect · Neon ·
Render · Vercel · Cloudinary

Et ce qu'on a **refusé** — Celery, Redis, Elasticsearch, PostGIS, GraphQL,
microservices — avec les raisons, dans
[stack-technique.md](plan-organisation/05-execution/stack-technique.md).
