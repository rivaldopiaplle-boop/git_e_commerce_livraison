# Contrat de déploiement

> Règle d'or n°2 : le déploiement se prépare en semaine 1, pas en semaine 10.
> Un projet qui ne se déploie pas ne se démontre pas, et un projet qu'on ne
> démontre pas n'existe pas pour un recruteur.

---

## 1. Ce qu'on déploie

| Élément | Où | Certitude |
|---|---|---|
| Base PostgreSQL | **Neon** (offre gratuite, une base par environnement) | Élevée |
| API Django | **Render**, conteneur Docker | Acté (D-19) |
| Front web Vue | **Vercel**, fichiers statiques | Acté (D-19) |
| Application mobile | Fichier `.apk` téléchargeable, pas de publication sur les magasins | Élevée |
| Images et fichiers envoyés | **Cloudinary** | Acté (D-24) |

Ce qu'on **ne** déploie pas : Redis, Celery, moteur de recherche, solveur de
tournées. Tous relèvent du palier 2 et chacun ajoute un service à maintenir.

---

## 2. Environnements

| Environnement | Base | Objectif |
|---|---|---|
| **local** | PostgreSQL en conteneur | Développement, une seule commande pour tout lancer |
| **vitrine** | Neon | Démonstration publique permanente, remise à zéro régulière |
| **production** | Neon | Existe surtout pour prouver qu'on sait séparer les environnements |

Aucun secret n'est jamais écrit dans le dépôt : variables d'environnement, avec
un fichier `.env.exemple` versionné qui liste les variables **sans leurs valeurs**.

---

## 3. L'hébergement — décidé, et sa contrainte principale

**Décision [D-19](../00-pilotage/journal-decisions.md)** : front Vue sur
**Vercel**, API Django en conteneur sur **Render**, base sur **Neon**, images sur
**Cloudinary**.

### Pourquoi pas Django sur Vercel, comme tu le proposais
Vercel exécute des fonctions sans état : le processus est recréé à chaque appel,
le disque est vide, il n'y a ni tâche de fond ni commande de démarrage, et la
durée d'une requête est plafonnée à une dizaine de secondes en offre gratuite.
On peut y faire tourner Django — des gens le font — mais alors `migrate` ne peut
plus s'exécuter à l'hébergeur, aucun fichier téléversé ne survit, et le moindre
traitement un peu long est coupé. Ce n'est pas « héberger mal », c'est un modèle
d'exécution qui ne correspond pas à un backend Django. Vercel reste en revanche
le meilleur choix pour le front Vue, qui est exactement ce qu'il sait faire.

### Les trois contraintes de Render, et leurs parades

| Contrainte | Parade |
|---|---|
| **Le service s'endort après 15 minutes sans trafic** et met environ une minute à repartir | Une tâche GitHub Actions appelle `/api/v1/sante` toutes les dix minutes, **activée le jour de la démonstration seulement** — la maintenir en permanence consommerait tout le quota mensuel d'heures gratuites |
| Le disque est effacé à chaque redéploiement | Rien de durable ne s'y écrit : les images vont chez Cloudinary ([contrat-medias.md](contrat-medias.md)), les données chez Neon |
| Le premier appel après réveil est lent | Le front affiche « réveil du serveur, quelques secondes… » au lieu d'une page blanche, avec une nouvelle tentative automatique. Un écran blanc pendant l'entretien coûte plus cher que le délai lui-même |

### Rester capable de changer d'hébergeur
L'API est un conteneur Docker standard : aucune dépendance à Render au-delà de
deux variables d'environnement. Si l'offre gratuite change — elles changent tous
les six mois — la bascule coûte une journée. Les critères à réappliquer ce
jour-là, dans l'ordre : accepte un `Dockerfile` tel quel ; ne s'endort pas ou se
réveille vite ; variables et journaux accessibles ; se déploie depuis GitHub
Actions sans clic manuel ; ne demande pas de carte bancaire. Plan de repli
toujours valable : un petit serveur virtuel avec Docker Compose — et c'est un bon
sujet d'entretien en soi.

---

## 4. Conteneurisation

- Un `Dockerfile` pour l'API : image Python fine, dépendances installées en
  couche séparée pour le cache, construction en plusieurs étapes, exécution par
  un utilisateur non privilégié, serveur WSGI (Gunicorn) et non le serveur de
  développement.
- Un `docker-compose.yml` de développement : API, PostgreSQL, capteur d'e-mails
  local (type Mailpit), et plus tard le simulateur de services externes.
- Le front Vue est construit puis servi en statique : il n'a pas besoin de
  conteneur en production.
- La même image est utilisée en vitrine et en production. Ce qui change, ce sont
  les variables d'environnement, jamais l'image.

---

## 5. Migrations

Les migrations Django s'exécutent **automatiquement au démarrage du conteneur**,
jamais à la main en production. Règles :

- Une migration ne supprime jamais une colonne dans la même version que le code
  qui cesse de l'utiliser : on déploie le code d'abord, on supprime ensuite.
- Aucune migration destructrice n'est appliquée sans sauvegarde préalable.
- Le `seed_admin` est **idempotent** : le relancer ne crée pas un deuxième admin.

---

## 6. Données de démonstration

L'environnement vitrine est amorcé par une commande `seed_demo` qui crée un jeu
crédible : trois boutiques (une Express, deux Standard), une vingtaine de
produits avec photos, des clients, des livreurs, et des commandes **à tous les
statuts** — y compris une livrée, une en cours de livraison, une annulée, un
litige ouvert. Sans cela, la démonstration ne montre qu'un catalogue vide.

Voir [vitrine-et-demonstration.md](../05-execution/vitrine-et-demonstration.md).

---

## 7. Services externes en vitrine

| Service | En vitrine |
|---|---|
| Stripe | **Mode test**, avec les numéros de carte de test affichés à l'écran |
| E-mail | Tous les envois vers **une seule adresse**, le destinataire réel étant rappelé dans l'objet (pratique standard des environnements de test, déjà éprouvée sur le projet banque) |
| Push | Simulateur, sauf si un projet Firebase gratuit est configuré |
| Appel masqué | Simulateur uniquement |

Un bandeau permanent indique « environnement de démonstration — aucun paiement
réel ». C'est une exigence d'honnêteté, et ça évite toute ambiguïté en entretien.

---

## 8. Surveillance minimale

- `GET /sante` : état de l'API et de la base, sans authentification.
- `GET /version` : version et empreinte du commit déployé — pour savoir en un
  coup d'œil ce qui tourne réellement.
- Journaux structurés en JSON, avec un identifiant de requête.
- Aucune trace technique renvoyée au client : le détail va dans les journaux, le
  client reçoit un message et un identifiant d'incident.

---

## 9. Ce qu'une vraie production aurait et que ce projet n'aura pas

À dire spontanément en entretien, c'est une force :
sauvegardes automatiques testées, haute disponibilité, plan de reprise, secrets
dans un coffre dédié, alerte à l'astreinte, tests de charge, audit de sécurité.
Ce projet vise la démonstration ; il en connaît les limites et sait les nommer.
