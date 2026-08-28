# Plan de démarrage — quoi faire, dans quel ordre

> Découpé en **tranches verticales** : chaque tranche traverse toute la pile
> (modèle → API → écran web → écran mobile), conformément à la règle d'or n°4
> « on avance partout à la fois ». Aucune tranche n'est terminée sans son test
> de sortie.
>
> Les durées sont indicatives : ce qui compte est l'ordre et les tests de sortie.
> Les onze tranches couvrent **tout le MVP**, Express et Standard compris
> (révision du bloc C) ; le palier 2 commence après la tranche 11.

---

## Avant tout : plus rien ne bloque

Les questions qui empêchaient de coder proprement sont tranchées au bloc C :
mobile en **Ionic Vue + Capacitor** ([D-20](../00-pilotage/journal-decisions.md)),
entrepôt et circuit Standard **dans le MVP** ([D-17 révisée](../00-pilotage/journal-decisions.md)),
adresse en **entité partagée** ([D-21](../00-pilotage/journal-decisions.md)),
hébergement **Render + Vercel + Neon** ([D-19](../00-pilotage/journal-decisions.md)).
Ce que tu dois faire de ton côté avant la tranche 0 est listé dans
[ta-part-du-travail.md](../00-pilotage/ta-part-du-travail.md).

---

## Tranche 0 — Le squelette qui tourne — **code écrit, test de sortie à passer**

1. ✅ Structure du dépôt, `.gitignore` (les secrets d'abord), `README.md`.
2. ✅ `docker-compose.yml` : PostgreSQL avec sonde de santé, Mailpit pour
   capturer les courriels.
3. ✅ Django 5 + DRF : configuration pilotée par variables d'environnement,
   `backend/.env.example` entièrement commenté, endpoint `/api/v1/sante` qui
   vérifie réellement la base — et deux tests, dont un qui prouve qu'il ne fuit
   ni la clé secrète ni la chaîne de connexion.
4. ✅ Vue 3 + Vite + TypeScript + Pinia : une page qui appelle `/sante`, avec
   ses trois états (chargement, en ligne, injoignable) et un message d'erreur
   qui dit quoi faire.
5. ✅ `demarrer.py` : vérifie les outils, monte les conteneurs, **attend** que
   Postgres accepte les connexions, crée l'environnement virtuel, installe,
   migre, lance. Options `--etat`, `--sans-web`, `--preparer`, `--arreter`.
6. ✅ GitHub Actions : `ruff` + `pytest` sur une vraie base Postgres, et
   compilation du front.

**Test de sortie — passé sur la machine de développement** : `python demarrer.py`
monte les conteneurs, prépare l'environnement, migre ; `ruff` ne signale rien,
les deux tests passent, l'API renvoie
`{"statut":"en ligne","base_de_donnees":"connectee"}` et le front sert sa page.

Restent deux vérifications qui ne peuvent pas être faites à sa place : **le
rendu dans un vrai navigateur**, et **la chaîne d'intégration**, qui ne
s'exécutera qu'au premier envoi sur GitHub.
Marche à suivre : [ta-part-du-travail.md](../00-pilotage/ta-part-du-travail.md) § D.

*Le script est volontairement écrit pour tourner sur une vieille version de
Python : s'il tombe sur 3.8, il l'explique au lieu de planter avec une erreur
de syntaxe.*

*Pourquoi en premier* : le jour où l'on ajoute ça après coup, on ne l'ajoute
jamais. Et c'est ce qui rend le projet reprenable après une interruption.

---

## Tranche 1 — Modèle et comptes (1 semaine)

1. Traduire le [dictionnaire de données](../02-modele/dictionnaire-donnees.md) en
   modèles Django — **tout le MVP d'un coup**, Standard et entrepôt compris. Une
   migration ajoutée plus tard sur un modèle déjà peuplé coûte dix fois plus cher
   qu'une colonne écrite tout de suite.
2. Première migration, `UTILISATEUR` en `AbstractUser` avec profils par rôle.
3. `seed_admin` (idempotent) et `seed_demo` (jeu de démonstration).
4. Authentification JWT : inscription client, inscription vendeur et livreur en
   attente, connexion, rafraîchissement, mot de passe oublié.
5. Classes de permission par rôle, une par ligne de la matrice des droits.
6. Écrans web : connexion, inscription, écran d'attente de validation, coquille
   d'application avec sidebar, navbar et accent de couleur par rôle.

**Test de sortie** : un client s'inscrit et se connecte ; un vendeur créé reste
bloqué tant que l'admin ne valide pas, et un test automatisé le prouve ; les cinq
accents de couleur s'affichent correctement selon le rôle connecté.

---

## Tranche 2 — Catalogue (1 semaine)

1. API produits et catégories, avec les droits vendeur.
2. Filtrage géographique du catalogue Express (à vol d'oiseau, sans PostGIS).
3. Géocodage d'une adresse par Nominatim à l'enregistrement, jamais à
   l'affichage ([D-25](../00-pilotage/journal-decisions.md)).
4. **Photos produit** : téléversement vendeur, conversion, envoi chez Cloudinary,
   galerie côté client — voir [contrat-medias.md](../03-contrats/contrat-medias.md).
5. Écran vendeur : catalogue, création et modification d'un produit.
6. Écran client : catalogue, fiche produit, galerie, bandeau « Livrer à … ».
7. États vides des deux côtés.

**Test de sortie** : un vendeur ajoute un produit **avec trois photos** depuis le
navigateur, il apparaît chez un client situé dans le rayon avec sa galerie, et
**n'apparaît pas** chez un client situé au-delà.

---

## Tranche 3 — Stock (3 jours)

1. Stock, réservation, seuil d'alerte, mouvements tracés avec motif.
2. Bouton gelé et alerte de disponibilité côté client.
3. Écran de stock côté vendeur et gestionnaire.
4. Création des gestionnaires staff vendeur par le vendeur.

**Test de sortie** : un ajustement de stock sans motif est refusé ; un
gestionnaire peut ajuster le stock mais reçoit un 403 sur le chiffre d'affaires.

---

## Tranche 4 — Panier (4 jours)

1. Panier connecté et panier invité, fusion à la connexion.
2. Règle « un seul vendeur Express » avec avertissement explicite.
3. Prix courant à chaque affichage, avertissement de changement de prix.
4. Panneau droit du panier côté web.

**Test de sortie** : un visiteur remplit un panier, se connecte, retrouve son
panier fusionné ; l'ajout d'une seconde boutique Express déclenche
l'avertissement et non un blocage muet.

---

## Tranche 5 — Commande et paiement (1,5 semaine)

1. Service `CommandeSplitter` et `GET /panier/apercu-commandes`.
2. Transitions de statut sous forme de machine à états, avec les transitions
   possibles renvoyées par l'API.
3. Vérification du stock sous verrou transactionnel et réservation courte.
4. Stripe en mode test, webhook idempotent, remboursement, **et Stripe Connect
   dès maintenant** : la commande Standard multi-vendeur étant dans le MVP,
   ajouter la répartition après coup obligerait à reprendre tout le paiement.
5. Tunnel de commande et écran de confirmation côté web.
6. Écran vendeur des commandes entrantes, avec les seules actions autorisées.

**Test de sortie** : une commande complète est passée et payée de bout en bout en
environnement de test ; un test simule deux paiements concurrents sur le dernier
article et prouve qu'un seul aboutit.

---

## Tranche 6 — Livraison Express (1 semaine)

1. Attribution au livreur disponible le plus proche (pattern Strategy).
2. Acceptation avec verrou, abandon, statuts, tentatives avec preuve.
3. Position du livreur et suivi côté client.
4. Écran client de suivi avec frise.

**Test de sortie** : deux livreurs acceptent la même course en même temps, un
seul l'obtient, l'autre reçoit un message clair.

---

## Tranche 7 — Mobile livreur (1 à 1,5 semaine)

1. Initialiser le projet mobile en **Ionic Vue + Capacitor** ([D-20](../00-pilotage/journal-decisions.md)).
2. Connexion, disponibilité, course en cours, courses disponibles.
3. Géolocalisation pendant la course, file d'attente hors ligne.
4. Bouton d'action unique qui suit le statut.

**Test de sortie** : depuis un téléphone réel, un livreur accepte une course
créée depuis le web et la mène jusqu'à `livrée`.

---

## Tranche 8 — Admin et notifications (1 semaine)

1. Écrans admin : tableau de bord, validations, vue complète d'une commande,
   journal d'audit.
2. Notifications in-app et e-mail, avec le simulateur.
3. Création des entrepôts et de leur personnel par l'admin.

**Test de sortie** : un vendeur candidat est validé par l'admin et son catalogue
devient visible dans la seconde ; toute l'opération est tracée dans le journal
d'audit.

*À ce stade, le circuit Express est complet de bout en bout. Les trois tranches
suivantes ajoutent le circuit Standard, qui réutilise tout ce qui précède.*

---

## Tranche 9 — Entrepôt et sous-commandes (1 semaine)

1. Réception d'un colis à l'entrepôt, sous-commandes par vendeur, statuts de
   préparation.
2. Écran gestionnaire staff entrepôt : colis reçus, tri par zone.
3. Répartition Stripe Connect effective sur une commande multi-vendeur.
4. Frais Standard par zone et seuil de gratuité (pattern Strategy, déjà en place
   depuis la tranche 5).

**Test de sortie** : un panier contenant deux boutiques Standard produit **une**
commande, **deux** sous-commandes, **un** paiement et **deux** répartitions dont
la somme, commission comprise, est exactement le montant payé.

---

## Tranche 10 — Tournées et livreur Standard (1 semaine)

1. Constitution d'une tournée par zone et ordre d'arrivée, arrêts ordonnés.
2. Affectation d'une tournée à un livreur Standard.
3. Écran gestionnaire entrepôt : préparation et affectation des tournées.
4. Mobile livreur Standard : tournée du jour, arrêt suivant, statut par arrêt.

**Test de sortie** : depuis un téléphone, un livreur Standard déroule une tournée
de trois arrêts ; chaque arrêt fait évoluer sa commande, et une tentative
échouée déclenche la politique des deux tentatives
([D-23](../00-pilotage/journal-decisions.md)).

---

## Tranche 11 — Mise en ligne et démonstration (1 semaine)

1. Déploiement réel : Neon, image de l'API sur Render, front sur Vercel,
   publication automatique depuis `main`.
2. Cloudinary branché en production, et **rien de durable sur le disque**
   ([D-19](../00-pilotage/journal-decisions.md)).
3. Jeu de démonstration en ligne, comptes de démonstration, bandeau
   « environnement de démonstration ».
4. Tâche de réveil de l'API, à n'activer que le jour de la démonstration.

**Test de sortie — et fin du MVP** : sur l'URL publique, un panier mixte donne
trois commandes livrées par deux circuits, déroulées devant quelqu'un en moins de
dix minutes, en changeant de rôle à l'écran.

---

## Ensuite — palier 2

Promotions, avis et modération, litiges arbitrés, factures PDF, notifications
push, statistiques vendeur, assistant d'aide, optimisation réelle des tournées,
suivi temps réel. Même méthode, mêmes tests de sortie. Détail dans
[perimetre-et-mvp.md](../01-produit/perimetre-et-mvp.md).

---

## Règle de méthode, valable tout du long

À chaque fonctionnalité, dans cet ordre : **modèle → endpoint + test → écran web
→ écran mobile si le rôle est mobile.** Jamais un écran avant que son endpoint
existe et soit testé. Jamais de données simulées dans un écran pour compenser un
endpoint manquant : c'est ainsi qu'on découvre le jour de la démonstration que
rien n'est branché.
