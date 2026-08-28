# Critique de l'existant — ce que le bloc A a réussi, raté, et oublié

> Lecture complète des cinq documents produits par la session précédente
> (scénarios, MCD, maquettes, contrats, stack, démarrage), confrontés à tes
> règles d'or et à ce que le projet banque a appris.
> Ce document est volontairement direct : c'est son utilité.
>
> **Suite donnée, au bloc C** : tu as répondu point par point et tout est
> tranché. Chaque critique ci-dessous porte désormais sa résolution en fin de
> section. Le document reste tel quel plutôt que d'être réécrit — le raisonnement
> qui a mené aux décisions vaut plus que le constat, et c'est exactement le genre
> de trace qu'un recruteur aime voir.

| Critique | Résolution |
|---|---|
| 2.1 Modèle en retard | Diagramme régénéré, 33 entités, aligné sur le dictionnaire |
| 2.2 Dernier article en stock | [D-15](journal-decisions.md) — pas de réservation au panier, verrou au paiement |
| 2.3 Contrat d'API incomplet | Réécrit, avec les charges utiles et les routes de photos |
| 2.4 Règle d'or n°3 non traitée | [vitrine-et-demonstration.md](../05-execution/vitrine-et-demonstration.md) |
| 2.5 Rien sur la vérification | [qualite-et-verification.md](../05-execution/qualite-et-verification.md) |
| 2.6 Périmètre non maîtrisé | Deux paliers, MVP élargi au Standard sur ta décision ([D-17 révisée](journal-decisions.md)) |
| 3.1 NativeScript risqué | [D-20](journal-decisions.md) — Ionic Vue + Capacitor |
| 3.2 Hébergeur incertain | [D-19](journal-decisions.md) — Render + Vercel + Neon, avec la parade du réveil |
| 3.3 Channels au MVP | [D-16](journal-decisions.md) — interrogation périodique, WebSocket en palier 2 |
| 3.4 Twilio | [D-18](journal-decisions.md) — derrière une interface, simulé au MVP |

---

## 1. Ce qui est solide, et qu'il ne faut pas défaire

- **Les scénarios en SI/ALORS.** C'est le meilleur document du lot. Le principe
  « chaque ligne SI/ALORS est un état d'écran à prévoir » est exactement la bonne
  méthode, et il tient la règle d'or n°2 (production d'abord).
- **Les personae nommés.** Léa, Karim, Sophie, Nadia, Amine, Julien, Fatou : tu
  avais raison de refuser les X/Y/Z. On lit trois fois plus vite.
- **La distinction Express / Standard.** C'est la vraie colonne vertébrale du
  projet, et elle est bien tenue partout : catalogue, découpage du panier,
  attribution des livraisons, frais.
- **Les états vides pensés dès le départ.** Rare, et directement présentable en
  entretien.
- **Les maquettes HTML interactives** avec bascule rôle / web-mobile / mode /
  état vide : très bon outil, déjà conforme aux règles 6 à 8.

---

## 2. Défauts sérieux — à corriger avant de coder

### 2.1 Le modèle de données est en retard sur les décisions

C'est le problème le plus grave : plusieurs décisions actées **n'ont aucune
traduction dans le MCD**, donc les migrations Django seraient fausses dès le
premier jour.

| Décision actée | Traduction dans le MCD actuel |
|---|---|
| Admin, rôle central | **L'entité ADMIN n'existe pas du tout** |
| Sous-commandes par vendeur (D-10) | Absente : COMMANDE — COMPOSER — PRODUIT ne permet pas de dire « la part de Sophie » |
| Tournée d'un livreur Standard | Absente : LIVRAISON est liée 1,1 à une commande, rien ne groupe les arrêts |
| Rayon Express (D-09) | **Le vendeur n'a ni adresse, ni latitude, ni longitude** — le filtrage est donc impossible |
| Répartition Stripe Connect (D-12) | PAIEMENT est 1,1 avec COMMANDE, aucune trace des parts vendeurs |
| « Être alerté quand disponible » (D-06) | Aucune entité d'abonnement au retour en stock |
| Ajustement de stock avec motif (scénario 4.4) | Aucun historique de mouvement de stock |
| Tentative échouée, preuve photo (scénario 8.1) | Aucune entité tentative ni preuve |
| Litige arbitré par l'admin (scénario 13) | Aucune entité litige |
| Journal d'audit (D-13) | Absent |

Trois erreurs de modélisation en plus, indépendantes des décisions :

- `NOTIFICATION` n'est reliée qu'au **client**, alors que tous les rôles reçoivent
  des notifications (validation de compte, commande à préparer, litige ouvert).
- `AVIS` couvre le produit et le livreur mais **pas le vendeur**, alors qu'une
  boutique Express se note comme un restaurant — c'est même la note qui compte
  le plus pour le client.
- Il n'existe **aucune entité d'authentification commune** : sept rôles, sept
  tables portant chacune son `email` et son `mot_de_passe_hash`. Comment
  garantit-on alors l'unicité d'un e-mail entre les tables, et que se passe-t-il
  si un livreur devient aussi client ?

→ **Corrigé au bloc C** : la cible est écrite dans
[dictionnaire-donnees.md](../02-modele/dictionnaire-donnees.md) et le diagramme
[mcd.html](../02-modele/mcd.html) a été régénéré d'après elle — 33 entités,
51 associations, les deux alignés
(voir [mcd-maintenance.md](../02-modele/mcd-maintenance.md)).

### 2.2 Le scénario du dernier article en stock est incohérent

Le scénario 4.2 dit : *« Ajouter au panier décrémente l'affichage pour Léa (elle
voit 0), mais un autre client peut encore voir 1 »*. C'est l'inverse de ce qu'il
faut : Léa, qui tient l'article dans son panier, croit qu'il est épuisé, tandis
que l'autre client le croit disponible. Aucun site ne fonctionne comme ça.

Le comportement réel du commerce en ligne : **stock affiché = stock réel pour
tout le monde**, aucune réservation au panier, verrou transactionnel au paiement,
et éventuellement une réservation courte à la création de l'intention de paiement.
→ Correction proposée en [D-15](journal-decisions.md).

### 2.3 Le contrat d'API n'est pas un contrat

C'est une liste d'URL. Il manque tout ce qui fait qu'un contrat évite les
allers-retours pendant le développement : qui a le droit d'appeler quoi, le corps
de la requête, le corps de la réponse, les codes d'erreur métier, la pagination,
le format des dates et des montants.
Point de comparaison utile : le contrat d'API du projet banque fait 56 Ko et t'a
permis d'écrire le front et le back sans te contredire. Ici on est à 3 Ko.
→ Réécrit dans [contrat-api.md](../03-contrats/contrat-api.md).

### 2.4 La règle d'or n°3 (l'entretien) n'est traitée nulle part

Aucun document ne parle de démonstration, de comptes de démonstration, de jeu de
données crédible, ni d'URL publique. C'est pourtant une de tes règles
fondatrices, et c'est le point sur lequel le projet banque a le plus souffert :
il a fallu lui consacrer un document entier intitulé « sortir du bourbier
vitrine », écrit après coup.
→ Traité dès maintenant dans
[vitrine-et-demonstration.md](../05-execution/vitrine-et-demonstration.md).

### 2.5 Rien sur la vérification

Pas un mot sur les tests, le lint, ou comment on sait que ça marche. Le plan de
démarrage mentionne « tests pytest » en passant. Le projet banque avait un banc
de preuves qui rejouait les scénarios métier de bout en bout — c'est ce qui rend
un projet démontrable, et ce qui impressionne réellement en entretien.
→ [qualite-et-verification.md](../05-execution/qualite-et-verification.md).

### 2.6 Le périmètre n'est pas maîtrisé

Tu l'as écrit toi-même : *« je trouve qu'on s'éparpille et qu'on doit pas tout
faire mais bien recadrer »*. Le bloc A a répondu à chaque question en ajoutant
une fonctionnalité, jamais en en retirant une. Résultat : deux modèles de
livraison, des entrepôts, des tournées, du multi-vendeur, des promotions, des
avis, des litiges, des notifications multicanal et un agent IA — pour une
personne seule.
→ [perimetre-et-mvp.md](../01-produit/perimetre-et-mvp.md) découpe tout ça en
des paliers avec une règle simple : **rien ne commence tant que le palier
précédent n'est pas démontrable de bout en bout.**

---

## 3. Choix techniques à rediscuter

### 3.1 NativeScript-Vue est un pari risqué

Le document de stack le présente comme « l'équivalent le plus direct » de Vue
Native, ce qui est vrai, mais passe sous silence le vrai coût : écosystème
mince, peu d'exemples, dépannage difficile — précisément sur ce dont l'appli
livreur a besoin (géolocalisation continue, cartes, notifications push).
→ Alternative recommandée et comparaison en [Q-01](questions-ouvertes.md).

### 3.2 « Railway ou Fly.io, gratuit » n'est plus une affirmation sûre

Les offres gratuites de ces hébergeurs ont changé plusieurs fois. Écrire un nom
d'hébergeur dans un plan sans date de vérification, c'est se préparer une
mauvaise surprise le jour du déploiement.
→ [Q-03](questions-ouvertes.md) et critères de choix dans le contrat de déploiement.

### 3.3 Django Channels au MVP coûte plus qu'il ne rapporte

WebSocket pour le stock et le suivi implique un serveur ASGI, un Redis et une
configuration d'hébergement particulière. Le gain visible pour l'utilisateur est
de quelques secondes de fraîcheur d'affichage.
→ Proposition [D-16](journal-decisions.md) : interrogation périodique au MVP.

### 3.4 Twilio pour l'appel masqué est payant et hors sujet au MVP

Bonne idée sur le fond, impossible à démontrer gratuitement.
→ Proposition [D-18](journal-decisions.md) : interface interne + simulateur,
comme le `simulateur-reseau` du projet banque.

---

## 4. Ce que le projet banque a appris, et qu'il faut réutiliser ici

| Leçon du projet banque | Application ici |
|---|---|
| Une **seule commande pour tout démarrer** (`demarrer.mjs`) | Un script équivalent dès la semaine 1 |
| Un **seed riche** rend le projet démontrable | Jeu de démonstration : 3 boutiques, une vingtaine de produits, des commandes à tous les statuts |
| Un **simulateur** pour les services externes | Stripe, e-mail, push, appel masqué |
| Un **banc de preuves** qui rejoue le métier | Rejouer les scénarios du dossier `01-produit/` |
| Un **guide de reprise** pour se remettre dans le projet | À écrire dès qu'il y aura du code à reprendre |
| Le plan est devenu **un dossier plat de 26 fichiers** difficile à naviguer | D'où la structure numérotée du présent dossier |
| La vitrine a été **traitée trop tard** et a coûté cher | Traitée dès le plan, ici |
