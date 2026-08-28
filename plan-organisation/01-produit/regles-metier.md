# Règles métier et invariants

> Les scénarios racontent ce qui arrive. Cette page dit ce qui doit **toujours**
> être vrai, et quel mécanisme le garantit. C'est le document à côté du clavier
> quand on écrit un service ou un test.
>
> Chaque règle est numérotée `R-xx` ; les tests du banc de preuves portent le
> même numéro, pour qu'on puisse remonter d'un test cassé à la règle violée.

---

## 1. Catalogue et stock

**R-01 — Le stock affiché est le stock réel, identique pour tous.**
Aucune décrémentation à l'ajout au panier, pour personne. Le panier n'est pas
une réservation. *(Corrige le scénario 4.2 — voir [D-15](../00-pilotage/journal-decisions.md).)*

**R-02 — Le stock ne peut jamais devenir négatif.**
Garanti par un verrou transactionnel au moment de la validation du paiement
(`select_for_update` en Django), pas par une vérification préalable en lecture.
Deux paiements simultanés sur le dernier article : le premier obtient l'article,
le second reçoit une erreur métier explicite `409 STOCK_INSUFFISANT` — jamais une
erreur technique brute.

**R-03 — Une réservation courte existe, mais seulement au paiement.**
À la création de l'intention de paiement, le stock est réservé pour une durée
courte (≈10 minutes) puis libéré automatiquement si le paiement n'aboutit pas.
C'est ce qui évite qu'un client perde son article pendant qu'il saisit sa carte.

**R-04 — Un produit à stock nul reste visible, mais non commandable.**
Bouton gelé, plus l'option « Être alerté quand disponible ». Le vendeur seul peut
masquer un produit.

**R-05 — Le prix affiché au panier est toujours le prix courant.**
Jamais un prix figé en cache. Si le prix a changé depuis l'ajout, un
avertissement visuel l'indique. Le prix ne se fige qu'à la validation du
paiement, et il est alors recopié dans la ligne de commande — une commande passée
ne change jamais de montant.

**R-06 — Tout mouvement de stock a une cause tracée.**
Vente, réapprovisionnement, ajustement manuel avec motif obligatoire (casse,
inventaire, erreur), annulation. Aucune modification silencieuse d'un chiffre.

---

## 2. Panier et découpage en commandes

**R-07 — Un panier peut être anonyme.**
Un visiteur remplit un panier ; à la connexion, le panier invité fusionne avec
le panier du compte (les quantités s'additionnent, le prix courant s'applique).

**R-08 — Un panier Express ne contient qu'un seul vendeur.**
L'ajout d'un produit d'une autre boutique Express déclenche un avertissement
explicite (« votre panier contient déjà des articles d'un autre commerçant,
voulez-vous le vider ? »), jamais un blocage muet.

**R-09 — Un panier Standard peut contenir plusieurs vendeurs.**
Il devient une commande unique multi-vendeur, décomposée en sous-commandes.

**R-10 — Un panier mixte produit plusieurs commandes.**
Règle de découpage appliquée à la validation, dans cet ordre :
1. grouper les lignes par vendeur ;
2. chaque vendeur **Express** donne **une commande indépendante** ;
3. tous les vendeurs **Standard** donnent **une seule commande** multi-vendeur ;
4. chaque commande obtenue a ses propres frais, sa propre livraison et son propre
   suivi ; le client ne règle qu'une fois.

Exemple, celui de ta question A-17 : deux boutiques Express et deux boutiques
Standard dans le panier → **3 commandes** (2 Express + 1 Standard à deux
sous-commandes), un seul paiement, trois suivis distincts.

**R-11 — Une boutique trop éloignée n'est jamais dans le panier.**
Le cas « une boutique Express de la zone B alors que le client habite la zone A »
ne peut pas se produire : le catalogue Express est filtré par rayon avant même
l'affichage (R-12). C'est le filtrage qui protège, pas les frais de livraison.

---

## 3. Géographie et frais

**R-12 — Le catalogue Express est filtré par rayon autour de l'adresse du client.**
Au-delà du rayon maximal d'une boutique, elle n'apparaît pas. Le rayon est un
attribut de la boutique, pas une constante globale.

**R-13 — Le catalogue Standard n'a pas de restriction de distance.**

**R-14 — Les frais de livraison sont calculés par bandes, jamais au mètre.**
Express : bandes de distance à l'intérieur du rayon couvert.
Standard : barème par zone, avec un seuil de gratuité au-delà d'un montant.

**R-15 — Les frais sont affichés avant le paiement, jamais découverts après.**

---

## 4. Commande, paiement, remboursement

**R-16 — Une commande ne change de statut que vers le statut suivant autorisé.**
Jamais de menu libre de statuts : les boutons proposés sont exactement les
transitions permises depuis le statut courant, pour le rôle courant.

**R-17 — Le client peut annuler seul tant que la préparation n'a pas commencé.**
Au-delà, l'annulation passe par le vendeur ou le support.

**R-18 — Une annulation vendeur exige un motif** et déclenche une notification
forte (in-app + e-mail, et push quand il existera) plus le remboursement.

**R-19 — La confirmation d'un paiement vient du webhook, jamais du navigateur.**
Tant que le webhook n'est pas reçu, la commande reste « en attente de
confirmation », avec une vérification de rattrapage périodique.

**R-20 — Un paiement multi-vendeur est réparti par Stripe Connect.**
Aucune logique de répartition écrite à la main. La part de chaque vendeur et la
commission plateforme sont enregistrées côté commande pour l'audit.

**R-21 — Un montant est stocké en entier, en centimes.**
Jamais de flottant sur de l'argent. Devise unique : euro.

---

## 5. Livraison

**R-22 — Une livraison appartient à un seul livreur à la fois.**
Deux livreurs qui acceptent simultanément : un seul obtient l'attribution
(verrou transactionnel), l'autre reçoit un message clair.

**R-23 — Un livreur Express n'a qu'une course active.**
Tant qu'elle n'est pas terminée, il ne voit pas la liste des courses disponibles.

**R-24 — Un livreur Standard travaille par tournée.**
Il voit une liste ordonnée d'arrêts, jamais des livraisons à choisir une par une.

**R-25 — Une livraison abandonnée retourne au vivier.**
Le temps déjà écoulé reste visible côté admin, pour détecter les abus répétés.

**R-26 — Une livraison sans preuve n'est pas « livrée ».**
Selon le cas : signature, photo de dépôt si consigne, ou confirmation du client.

**R-27 — Une tentative échouée est un événement enregistré, pas un échec silencieux.**
Le client est notifié immédiatement avec ses options. Politique de deuxième
tentative : voir [Q-06](../00-pilotage/questions-ouvertes.md).

**R-28 — Le livreur ne connaît jamais le numéro réel du client.**
Appel par numéro masqué, ou message in-app. Au MVP, le simulateur tient ce rôle.

---

## 6. Comptes, sécurité, traçabilité

**R-29 — Toute autorisation est vérifiée côté serveur.**

**R-30 — Aucune suppression physique.**
Statut `SUSPENDU` / `DESACTIVE`, avec journal d'audit.

**R-31 — Toute action sensible est journalisée** : validation ou suspension d'un
compte, changement de rôle, remboursement, arbitrage de litige, ajustement de
stock. Qui, quoi, quand, sur quoi.

**R-32 — Une session qui expire ne détruit rien.**
Re-authentification sans perte de panier ni de formulaire en cours.

**R-33 — Un avis n'est possible qu'après une livraison effectuée.**

---

## 7. Les patterns retenus, et pourquoi

Un pattern n'est justifié que par une variation déjà identifiée (règle d'or n°11).

| Pattern | Où | Variation qu'il absorbe |
|---|---|---|
| **Strategy** | Attribution des livraisons | Express = plus proche disponible ; Standard = par zone et ordre d'arrivée aujourd'hui, solveur de tournées demain — sans réécrire l'appelant |
| **Strategy** | Calcul des frais de livraison | Bandes Express vs barème par zone Standard, plus les promotions de frais |
| **State machine** | Statuts de commande et de livraison | Empêche structurellement une transition illégale (R-16), et se teste seule |
| **Service dédié** (`CommandeSplitter`) | Panier → commandes | Toute la règle R-10 en un seul endroit testable, hors des vues |
| **Ports et adaptateurs** | Stripe, e-mail, push, appel masqué | Une implémentation réelle et un simulateur ([D-18](../00-pilotage/journal-decisions.md)) : c'est ce qui rend la démonstration possible sans compte payant |
| **Observer / événements** | Notifications | Un changement de statut publie un événement ; les canaux s'y abonnent, sans que le code de commande connaisse l'e-mail ou le push |
| **Repository fin** | Requêtes catalogue géographiques | Isole le filtrage par rayon, qui changera si on passe à PostGIS |

Patterns explicitement **écartés** : pas de CQRS, pas d'event sourcing, pas de
microservices. Un monolithe Django bien découpé est le bon choix ici, et savoir
dire pourquoi en entretien vaut mieux qu'une architecture surdimensionnée.
