# Contrat d'API

> Ce document est **opposable** : le front peut être écrit contre lui avant que
> le back existe, et inversement. Ce qui n'y est pas écrit n'existe pas.
> Toute modification se répercute ici **avant** d'être codée.
>
> Backend : Django + Django REST Framework. Base : `/api/v1`.

---

## 1. Conventions générales

### Format
- Toutes les requêtes et réponses sont en JSON, encodage UTF-8.
- Les noms de champs sont en `snake_case`, en français, cohérents avec le
  [dictionnaire de données](../02-modele/dictionnaire-donnees.md).
- Les dates sont en ISO 8601 UTC : `2026-08-27T14:32:00Z`.
- **Les montants sont des entiers en centimes.** `1250` = 12,50 €. Jamais de
  flottant. La devise est l'euro, implicite.
- Les identifiants sont des entiers (ou des UUID si on choisit d'exposer autre
  chose que la clé primaire — à trancher avant le premier endpoint).

### Enveloppe de réponse

Succès :
```json
{ "data": { }, "meta": { } }
```

Erreur :
```json
{
  "error": {
    "code": "STOCK_INSUFFISANT",
    "message": "Le produit « Casque X » n'est plus disponible en quantité 2.",
    "details": { "id_produit": 42, "stock_restant": 1 }
  }
}
```

Le `message` est destiné à être **affiché tel quel** à l'utilisateur : c'est le
back qui possède le texte métier, pas le front. Le `code` est destiné au front
pour décider d'un comportement (rediriger, ouvrir une popup, surligner un champ).

### Pagination
`GET` de collection : `?page=1&limite=20` (20 par défaut, 100 maximum).
```json
{ "data": [ ], "meta": { "page": 1, "limite": 20, "total": 137, "pages": 7 } }
```

### Tri et filtres
`?tri=-date_commande` (le `-` inverse). Les filtres disponibles sont listés
endpoint par endpoint ; un filtre inconnu renvoie `400`, jamais un silence.

### Authentification
JWT via `djangorestframework-simplejwt`. En-tête `Authorization: Bearer <token>`.
Jeton d'accès court (15 min), jeton de rafraîchissement long (7 jours).
Le rôle est porté par le jeton, mais **jamais fait confiance côté serveur sans
revérification en base** pour les actions sensibles (un compte peut avoir été
suspendu depuis l'émission du jeton).

### Codes HTTP

| Code | Emploi |
|---|---|
| 200 / 201 / 204 | Succès, création, suppression |
| 400 | Requête invalide (validation) |
| 401 | Non authentifié ou jeton expiré |
| 403 | Authentifié mais pas le droit — **jamais 404 pour masquer** |
| 404 | La ressource n'existe pas |
| 409 | Conflit métier (stock, double attribution, statut incompatible) |
| 422 | Règle métier violée avec explication détaillée |
| 429 | Trop de requêtes |
| 500 | Erreur serveur — jamais de trace technique renvoyée au client |

### Codes d'erreur métier

| Code | Sens | HTTP |
|---|---|---|
| `STOCK_INSUFFISANT` | Stock parti entre l'ajout au panier et le paiement | 409 |
| `PRODUIT_INDISPONIBLE` | Produit masqué ou vendeur suspendu | 409 |
| `PANIER_MULTI_VENDEUR_EXPRESS` | Deuxième boutique Express dans le panier | 409 |
| `HORS_RAYON_LIVRAISON` | Boutique Express trop loin de l'adresse | 422 |
| `TRANSITION_STATUT_INTERDITE` | Passage de statut non autorisé | 409 |
| `LIVRAISON_DEJA_ATTRIBUEE` | Un autre livreur l'a prise | 409 |
| `LIVREUR_DEJA_EN_COURSE` | Un livreur Express en a déjà une | 409 |
| `COMPTE_EN_ATTENTE_VALIDATION` | Vendeur ou livreur pas encore validé | 403 |
| `COMPTE_SUSPENDU` | Compte suspendu par un admin | 403 |
| `PAIEMENT_NON_CONFIRME` | Webhook Stripe pas encore reçu | 409 |
| `CODE_PROMO_INVALIDE` | Expiré, épuisé ou non applicable | 422 |

---

## 2. Matrice des rôles

`P` public · `C` client · `V` vendeur · `GV` gestionnaire staff vendeur ·
`GE` gestionnaire staff entrepôt · `L` livreur · `A` admin

| Domaine | P | C | V | GV | GE | L | A |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Catalogue (lecture) | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Catalogue (écriture) | | | ✔ | stock | | | |
| Panier | ✔ | ✔ | | | | | |
| Commandes (siennes) | | ✔ | ✔ | ✔ | | ✔ | ✔ |
| Paiement | | ✔ | | | | | |
| Livraisons | | lecture | lecture | | ✔ | ✔ | ✔ |
| Tournées | | | | | ✔ | lecture | ✔ |
| Utilisateurs / validation | | | | | | | ✔ |
| Statistiques | | | ✔ (siennes) | | | ✔ (gains) | ✔ |

---

## 3. Authentification et comptes

| Méthode | Chemin | Rôle | Effet |
|---|---|---|---|
| POST | `/auth/inscription/client` | P | Crée un compte actif immédiatement |
| POST | `/auth/inscription/vendeur` | P | Crée un compte `EN_ATTENTE_VALIDATION` |
| POST | `/auth/inscription/livreur` | P | Crée un compte `EN_ATTENTE_VALIDATION` |
| POST | `/auth/connexion` | P | Renvoie les jetons |
| POST | `/auth/rafraichir` | P | Nouveau jeton d'accès |
| POST | `/auth/deconnexion` | tous | Invalide le jeton de rafraîchissement |
| POST | `/auth/mot-de-passe/oubli` | P | Envoie un lien |
| POST | `/auth/mot-de-passe/reinitialiser` | P | **Conserve le panier** (scénario 10.2) |
| GET | `/moi` | tous | Profil complet avec rôle et statut |
| PATCH | `/moi` | tous | Modifie ses informations |

`POST /auth/connexion`
```json
{ "email": "lea@exemple.fr", "mot_de_passe": "..." }
```
```json
{ "data": {
  "acces": "eyJ...", "rafraichissement": "eyJ...",
  "utilisateur": { "id": 1, "prenom": "Léa", "role": "CLIENT", "statut_compte": "ACTIF" }
} }
```
**SI** le compte est `EN_ATTENTE_VALIDATION` **ALORS** la connexion réussit mais
l'application n'affiche que l'écran d'attente ; les endpoints métier renvoient
`403 COMPTE_EN_ATTENTE_VALIDATION`. On ne ment jamais à l'utilisateur sur l'état
de son compte.

---

## 4. Catalogue

| Méthode | Chemin | Rôle | Note |
|---|---|---|---|
| GET | `/produits` | P | Filtres : `categorie`, `vendeur`, `type_service`, `disponible`, `recherche`, `lat`, `lon` |
| GET | `/produits/{id}` | P | |
| POST | `/produits` | V | |
| PATCH | `/produits/{id}` | V (propriétaire) | |
| DELETE | `/produits/{id}` | V | Masquage logique |
| PATCH | `/produits/{id}/stock` | V, GV | Motif obligatoire si ajustement |
| POST | `/produits/{id}/alerte-dispo` | C | « Être alerté quand disponible » |
| POST | `/produits/{id}/photos` | V (propriétaire) | Envoi multipart, six photos maximum |
| PATCH | `/produits/{id}/photos/ordre` | V (propriétaire) | Réordonner ; la première devient la principale |
| DELETE | `/produits/{id}/photos/{idPhoto}` | V (propriétaire) | Suppression réelle du fichier |

Les trois routes de photos sont détaillées — formats, limites, traitement serveur,
stockage — dans [contrat-medias.md](contrat-medias.md). Une fiche produit renvoie
`image_principale_url` **et** le tableau `photos` ordonné.

### Stock — implémenté

| Verbe | Chemin | Qui | Effet |
|---|---|---|---|
| `PATCH` | `/produits/{id}/stock` | V, GV | Ajuste. **Motif obligatoire** si `type=AJUSTEMENT` |
| `GET` | `/produits/{id}/mouvements` | V, GV | L'historique, avec l'auteur de chaque mouvement |
| `GET` | `/vendeurs/stock-bas` | V, GV | Les produits sous leur seuil d'alerte |

Le stock ne peut jamais devenir négatif, ni descendre sous `stock_reserve` —
ce qui est retenu par un paiement en cours ([D-15](../00-pilotage/journal-decisions.md)).

### Panier et commande — implémentés

| Verbe | Chemin | Qui | Effet |
|---|---|---|---|
| `GET` | `/panier` | P | Le panier courant. En-tête `X-Panier-Session` pour un visiteur |
| `POST` | `/panier/lignes` | P | Ajoute. `409` si le stock ne suit pas |
| `PATCH` `DELETE` | `/panier/lignes/{id}` | P | Change la quantité, retire |
| `GET` | `/panier/apercu-commandes` | P | **Ce que le panier donnera**, avant tout engagement |
| `POST` | `/commandes` | C | Applique le découpage (D-10) et réserve le stock |
| `GET` | `/mes-commandes` | C | Le suivi client |
| `GET` | `/commandes/{id}` | C, V, A | Le détail, avec son historique de statuts |
| `GET` | `/vendeurs/commandes` | V, GV | La file de préparation — **sa part seulement** |
| `PATCH` | `/vendeurs/sous-commandes/{id}` | V, GV | Fait avancer d'un cran |

`PATCH /vendeurs/sous-commandes/{id}` renvoie `suites_possibles` : **le front
n'a pas à connaître la machine à états**, il affiche les boutons que le serveur
lui donne. C'est ce qui garantit qu'un vendeur ne saute jamais une étape.

**L'en-tête `X-Panier-Session`** doit être déclaré dans `CORS_ALLOW_HEADERS`,
sinon le navigateur bloque *toutes* les requêtes avant de les envoyer. Cinq
tests le vérifient — ce bug a rendu l'application entièrement muette une fois.
| GET | `/categories` | P | Arborescence complète |
| GET | `/boutiques` | P | Filtrées par rayon si `lat`/`lon` fournis |
| GET | `/boutiques/{id}` | P | |

**Filtrage géographique (règle R-12)** : quand `lat` et `lon` sont fournis, les
produits des vendeurs `EXPRESS` dont la distance dépasse leur
`rayon_livraison_km` **ne sont pas renvoyés du tout**. Les produits `STANDARD` ne
sont jamais filtrés par la distance. Sans `lat`/`lon`, seul le catalogue Standard
est renvoyé, avec `meta.position_requise: true` pour que le front demande la
position (voir [Q-05](../00-pilotage/questions-ouvertes.md)).

---

## 5. Panier

| Méthode | Chemin | Rôle |
|---|---|---|
| GET | `/panier` | P (invité par en-tête de session), C |
| POST | `/panier/lignes` | P, C |
| PATCH | `/panier/lignes/{id}` | P, C |
| DELETE | `/panier/lignes/{id}` | P, C |
| POST | `/panier/fusionner` | C | À la connexion, fusionne le panier invité |
| GET | `/panier/apercu-commandes` | C | **Prévisualise le découpage** avant paiement |

`GET /panier/apercu-commandes` est l'endpoint qui rend la règle R-10 visible pour
le client : il renvoie les commandes qui **seront** créées, avec leurs frais.
```json
{ "data": {
  "commandes_prevues": [
    { "type_service": "EXPRESS", "vendeur": "Chez Karim", "produits": 3,
      "montant_produits_centimes": 2400, "montant_livraison_centimes": 250 },
    { "type_service": "STANDARD", "vendeurs": ["TechSophie", "ModeAmel"], "produits": 2,
      "montant_produits_centimes": 8900, "montant_livraison_centimes": 0,
      "note": "Livraison offerte au-delà de 50 €" }
  ],
  "montant_total_centimes": 11550
} }
```

---

## 6. Commandes

| Méthode | Chemin | Rôle | Note |
|---|---|---|---|
| POST | `/commandes` | C | Applique le découpage et crée N commandes |
| GET | `/commandes` | C, V, GV, GE, L, A | Filtré automatiquement selon le rôle |
| GET | `/commandes/{id}` | selon droits | 403 si ce n'est pas la sienne |
| POST | `/commandes/{id}/annuler` | C, V, A | Motif obligatoire pour V |
| GET | `/commandes/{id}/historique` | selon droits | Alimente la frise de suivi |
| PATCH | `/sous-commandes/{id}/statut` | V, GV, GE | Transitions autorisées uniquement |

`POST /commandes` renvoie **toujours une liste**, même s'il n'y a qu'une commande :
```json
{ "data": { "commandes": [
    { "id": 101, "numero": "CMD-2026-000101", "type_service": "EXPRESS", "statut": "EN_ATTENTE_PAIEMENT" },
    { "id": 102, "numero": "CMD-2026-000102", "type_service": "STANDARD", "statut": "EN_ATTENTE_PAIEMENT" }
  ],
  "intention_paiement_id": "pi_..." } }
```
Le front n'a donc **jamais** de cas particulier « une seule commande » à écrire.

`PATCH /sous-commandes/{id}/statut` : seul le statut immédiatement suivant est
accepté ; toute autre valeur renvoie `409 TRANSITION_STATUT_INTERDITE` avec, dans
`details.transitions_possibles`, la liste des statuts atteignables — le front en
déduit les boutons à afficher sans les coder en dur.

---

## 7. Paiement

| Méthode | Chemin | Rôle |
|---|---|---|
| POST | `/paiements/intention` | C |
| GET | `/paiements/{id}` | C, A |
| POST | `/paiements/{id}/rembourser` | A |
| POST | `/webhooks/stripe` | — (signature Stripe) |

La création de l'intention **réserve le stock** pour environ 10 minutes (R-03).
Le webhook est la seule source de vérité (R-19) : il n'est pas authentifié par
JWT mais par la signature Stripe, et il est **idempotent** — un même événement
reçu deux fois ne produit qu'un effet.

---

## 8. Livraison

| Méthode | Chemin | Rôle | Note |
|---|---|---|---|
| GET | `/livraisons/disponibles` | L | Filtré selon `mode_livraison`, vide si le livreur Express est déjà en course |
| POST | `/livraisons/{id}/accepter` | L | `409 LIVRAISON_DEJA_ATTRIBUEE` en cas de course |
| POST | `/livraisons/{id}/abandonner` | L | Retour au vivier |
| PATCH | `/livraisons/{id}/statut` | L | |
| POST | `/livraisons/{id}/tentative` | L | Résultat + preuve (photo) |
| POST | `/livraisons/{id}/position` | L | Position courante, appelé périodiquement |
| GET | `/livraisons/{id}/suivi` | C | Statut + position approximative du livreur |
| POST | `/livraisons/{id}/appeler-client` | L | Passe par le service d'appel masqué |

### Tournées

| Méthode | Chemin | Rôle |
|---|---|---|
| GET | `/entrepots/{id}/colis` | GE |
| POST | `/entrepots/{id}/tournees` | GE |
| PATCH | `/tournees/{id}/arrets` | GE |
| POST | `/tournees/{id}/affecter` | GE |
| GET | `/tournees/ma-tournee` | L |
| PATCH | `/tournees/{id}/arrets/{id}/statut` | L |

---

## 9. Administration

| Méthode | Chemin | Rôle |
|---|---|---|
| GET | `/admin/tableau-de-bord` | A |
| GET | `/admin/validations` | A |
| POST | `/admin/vendeurs/{id}/valider` · `/rejeter` | A |
| POST | `/admin/livreurs/{id}/valider` · `/rejeter` | A |
| POST | `/admin/utilisateurs/{id}/suspendre` | A |
| GET | `/admin/litiges` · `POST /admin/litiges/{id}/resoudre` | A |
| POST | `/admin/entrepots` · `/admin/entrepots/{id}/gestionnaires` | A |
| GET | `/admin/audit` | A |
| POST | `/vendeurs/gestionnaires` | V — un vendeur crée son propre staff |

---

## 10. Notifications

| Méthode | Chemin | Rôle |
|---|---|---|
| GET | `/notifications` | tous |
| PATCH | `/notifications/{id}/lue` | tous |
| POST | `/notifications/tout-lire` | tous |
| PATCH | `/moi/preferences-notifications` | tous |

---

## 11. Suivi en direct — ce qu'on fait au MVP

Pas de WebSocket au palier 1 ([D-16](../00-pilotage/journal-decisions.md)) : le
front interroge `/commandes/{id}` et `/livraisons/{id}/suivi` toutes les 10 à 30
secondes selon l'écran, et la réponse porte un en-tête `ETag` pour que les appels
inchangés soient gratuits.

Les canaux WebSocket restent prévus pour le palier 2, **avec les mêmes charges
utiles que les réponses REST** : passer à Django Channels ne changera alors que
le transport, pas le front.

---

## 12. Santé et exploitation

| Méthode | Chemin | Note |
|---|---|---|
| GET | `/sante` | État de l'API et de la base, sans authentification |
| GET | `/version` | Numéro de version et empreinte du commit déployé |

---

## Ajouté au bloc J — les espaces de chaque rôle

Chaque entrée de barre latérale de la maquette a désormais sa route. Le rôle
indiqué est **vérifié par le serveur** : un appel avec un autre rôle reçoit 403,
pas une page masquée (scénario 14.1).

| Méthode | Chemin | Rôle | Ce qu'il renvoie |
|---|---|---|---|
| `GET` | `/moi/adresses` | client | son carnet, l'adresse principale en tête |
| `POST` | `/moi/adresses` | client | ajoute une adresse ; la première devient principale |
| `PATCH` | `/moi/adresses/{id}` | client | modifie, ou désigne comme principale |
| `DELETE` | `/moi/adresses/{id}` | client | retire du carnet — l'adresse survit pour les commandes passées (D-13) |
| `GET` | `/moi/notifications` | tous | les 30 dernières, et le nombre de non lues |
| `POST` | `/moi/notifications/lues` | tous | marque tout comme lu |
| `GET` | `/vendeurs/personnel` | vendeur | ses gestionnaires, et ce à quoi ils n'ont pas accès |
| `GET` | `/vendeurs/statistiques` | **vendeur seul** | CA, commission, panier moyen, 30 jours, meilleures ventes, avis |
| `GET` | `/vendeurs/avis` | vendeur | les avis qui visent sa boutique ou ses produits |
| `GET` | `/entrepots/colis` | gestionnaire entrepôt | les colis reçus, groupés par boutique déposante |
| `GET` | `/entrepots/tournees` | gestionnaire entrepôt | les tournées et leurs arrêts ordonnés |
| `GET` | `/entrepots/tableau-de-bord` | gestionnaire entrepôt | colis, tournées, livreurs rattachés |
| `GET` | `/livreurs/mes-courses` | livreur | **ses** courses, sa tournée en cours, ses gains |
| `GET` | `/livreurs/tableau-de-bord` | livreur | en cours, livrées, échouées, gains |
| `GET` | `/admin/utilisateurs` | admin | tous les comptes, filtrables par rôle et statut |
| `POST` | `/admin/utilisateurs/{id}/suspendre` | admin | bascule actif ↔ suspendu ; jamais de suppression |
| `GET` | `/admin/boutiques` | admin | toutes les boutiques, y compris refusées |
| `GET` | `/admin/livreurs` | admin | tous les livreurs et leur disponibilité |
| `GET` | `/admin/litiges` | admin | ouverts d'abord, avec la commande et son montant |
| `GET` | `/admin/journal` | admin | les 150 derniers changements de statut |
| `GET` | `/admin/validations/resume` | admin | le compte de dossiers par état |

### Deux corrections sur des routes existantes

- **`GET /vendeurs/produits`** est désormais ouverte au **personnel** du vendeur.
  Elle lui était refusée (403), ce qui empêchait son écran de stock de s'ouvrir.
  `POST` reste réservé au vendeur : publier est une décision commerciale (D-04).
  La charge utile expose maintenant `est_visible`, `stock_disponible`,
  `stock_reserve`, `stock_commandable`, `est_en_rupture` et `seuil_alerte` —
  sans quoi un produit masqué ne peut pas être remis en vente.
- **`PATCH /produits/{id}/stock`** accepte `nouvelle_quantite` en plus de
  `quantite`, et déduit l'écart (D-49). `GET /vendeurs/tableau-de-bord`
  n'inclut plus `revenu_centimes` quand l'appelant est un gestionnaire (D-50).
