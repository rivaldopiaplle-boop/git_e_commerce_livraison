# Scénarios — ce qui peut arriver, et ce que l'interface doit prévoir

> Chaque ligne « SI … ALORS … » correspond à un état d'écran ou à un message à
> prévoir explicitement. Avant de coder un écran, vérifier qu'il couvre le cas
> nominal **et** les cas limites de sa section.
>
> Les personae, les droits et les écrans par rôle sont dans
> [roles-et-parcours.md](roles-et-parcours.md). Les invariants et les patterns
> sont dans [regles-metier.md](regles-metier.md) — ici on raconte, là-bas on
> garantit.
>
> Révision de cette version : section 16 du document précédent redistribuée dans
> les sections concernées, scénario du dernier article corrigé (voir 4.2), le
> gestionnaire d'entrepôt nommé Samir, ajout des scénarios entrepôt et tournée
> qui manquaient.

---

## 1. État initial — juste après le déploiement

L'application est vide : aucun produit, aucune commande, aucun compte.

- **Fatou (admin)** est créée par la commande `seed_admin`, hors de toute
  interface web. Aucun formulaire public « devenir admin » n'existe.
- Les autres rôles entrent chacun par une porte différente : voir le tableau
  d'entrée dans [roles-et-parcours.md](roles-et-parcours.md).

**SI** un rôle se connecte alors qu'il n'y a encore rien **ALORS** il voit un
état vide rédigé et actionnable, jamais un tableau vide ni une page blanche.

---

## 2. Ce que voit chaque rôle à la connexion

| Rôle | En premier |
|---|---|
| **Léa** (client) | Catalogue livrable à son adresse, statut de sa dernière commande, accès panier |
| **Karim / Sophie** (vendeur) | Commandes à préparer, alertes de stock bas, ventes du jour |
| **Nadia** (gestionnaire vendeur) | Commandes à préparer, niveaux de stock — jamais de chiffre d'affaires |
| **Samir** (gestionnaire entrepôt) | Colis reçus à trier, tournées à constituer |
| **Amine** (livreur Express) | Une seule course proposée à proximité, ou sa course en cours |
| **Julien** (livreur Standard) | Sa tournée du jour, sous forme de liste ordonnée d'arrêts |
| **Fatou** (admin) | Indicateurs globaux, comptes en attente de validation, litiges ouverts |

**SI** Amine a déjà une course en cours **ALORS** il ne voit jamais la liste des
courses disponibles — un livreur Express ne porte qu'une commande à la fois.

---

## 3. Cycle de vie nominal — deux flux distincts

### 3.1 Flux Express (Karim, restauration)

1. Karim ajoute un plat au menu → visible immédiatement au catalogue, pour les
   seuls clients dans son rayon.
2. Léa commande et paie → notification instantanée à Karim.
3. Nadia prépare → `en préparation` → `prête`.
4. Le système propose la course au livreur Express disponible le plus proche →
   Amine accepte.
5. Amine récupère chez Karim, livre chez Léa.
6. Léa suit une frise de statuts ; Amine met à jour depuis son mobile.
7. Après livraison, Léa peut noter le plat, la boutique et le livreur.

### 3.2 Flux Standard (Sophie, électronique)

1. Sophie ajoute un produit avec son stock → visible au catalogue national.
2. Léa commande et paie.
3. Sophie prépare le colis et l'expédie vers l'entrepôt régional de la zone de Léa.
4. **Samir** réceptionne, contrôle et range le colis en attente de tournée.
5. Samir constitue une tournée pour la zone → l'affecte à **Julien**.
6. Julien livre ses arrêts dans l'ordre de la tournée.
7. Léa suit une frise plus large, au vocabulaire différent (« expédié vers
   l'entrepôt », « en tournée »).

**Conséquence d'interface** : même composant de frise, mais deux jeux d'étapes et
deux vocabulaires. Les boutons d'action sont toujours limités aux transitions
autorisées depuis le statut courant.

---

## 4. Produit et stock

### 4.1 — Produit disponible
**SI** stock > 0 **ALORS** ajout au panier normal.
**SI** stock = 0 **ALORS** bouton « Ajouter au panier » gelé, plus l'option
« Être alerté quand disponible ». Le produit reste visible sauf masquage vendeur.

### 4.2 — Le stock tombe à 0 alors que Léa a l'article dans son panier
*(Scénario corrigé — l'ancienne rédaction affichait 0 à Léa tout en affichant 1
aux autres, ce qui donne une interface incompréhensible.)*

- Le stock affiché est **le stock réel, le même pour tout le monde**, y compris
  pour qui a déjà l'article dans son panier. Le panier n'est pas une réservation.
- **Au moment du paiement**, le stock est reverrouillé en base : le premier
  paiement validé obtient l'article, le second est refusé avec un message métier
  clair et un panier qui reste intact.
- **SI** Léa arrive au paiement et que l'article est parti **ALORS** elle voit
  précisément quelle ligne pose problème et peut la retirer sans tout refaire.
- Une réservation courte (≈10 min) est posée à la création de l'intention de
  paiement, pour qu'elle ne perde pas l'article pendant la saisie de sa carte.

### 4.3 — Sophie change un prix pendant que des paniers sont actifs
- Le panier affiche le prix courant à chaque affichage, avec un avertissement
  « prix mis à jour » si le prix a changé depuis l'ajout.
- Le prix se fige au paiement, et est recopié dans la ligne de commande.

### 4.4 — Nadia constate un écart entre stock réel et stock système
- Ajustement manuel avec **motif obligatoire** (casse, inventaire, erreur),
  enregistré dans l'historique des mouvements — jamais de correction silencieuse.

### 4.5 — Un vendeur veut retirer un produit encore présent dans des paniers
- Le produit devient invisible au catalogue mais reste affiché dans les paniers
  existants, marqué « n'est plus disponible », et bloque le paiement de cette
  ligne uniquement.

---

## 5. Panier

### 5.1 — Léa navigue sans compte
Panier invité possible ; à la connexion, fusion avec son panier de compte.

### 5.2 — Léa abandonne son panier
Conservé 30 jours si elle est connectée. Relance automatique par e-mail
(fonctionnalité retenue). Compléments possibles : « souvent achetés ensemble »,
alerte de retour en stock, liste de souhaits.

### 5.3 — Panier contenant plusieurs vendeurs
- **Express** : interdit. L'ajout d'une seconde boutique Express déclenche un
  avertissement explicite avec choix (vider le panier ou annuler l'ajout).
- **Standard** : autorisé, la commande se décompose en sous-commandes par vendeur.

### 5.4 — Panier mixte Express + Standard
Autorisé. Au passage en caisse, le panier produit plusieurs commandes selon la
règle de découpage : chaque boutique Express donne une commande, l'ensemble des
boutiques Standard en donne une seule. Un seul paiement, plusieurs suivis.
Le récapitulatif avant paiement **montre ce découpage** et les frais de chaque
commande — le client ne doit jamais découvrir après coup qu'il a passé trois
commandes.

### 5.5 — Léa change d'adresse alors que son panier contient une boutique Express hors rayon
**ALORS** la ligne concernée est signalée comme non livrable à la nouvelle
adresse, avec proposition de la retirer — jamais une erreur au moment de payer.

---

## 6. Commande

### 6.1 — Annulation par Léa
**SI** statut = `payée` **ALORS** annulation en autonomie, remboursement automatique.
**SI** statut ≥ `en préparation` **ALORS** passage par le vendeur ou le support.

### 6.2 — Annulation par Karim (rupture, fermeture exceptionnelle)
Motif obligatoire → notification forte immédiate à Léa (in-app + e-mail, push
quand il existera) et remboursement automatique.

### 6.3 — Léa modifie son adresse après commande
**SI** aucun livreur n'a encore pris la commande **ALORS** modification possible.
**SINON** impossible dans l'application : contact direct.

### 6.4 — Commande jamais prise en charge
Après un délai défini : alerte automatique à Fatou, et proposition à Léa d'un
geste commercial ou d'une annulation remboursée. Jamais une commande payée
laissée sans action visible.

### 6.5 — Sous-commandes d'une commande Standard multi-vendeur
Chaque vendeur ne voit que sa part et ne peut faire évoluer que celle-ci. Le
client, lui, voit une commande unique dont la frise progresse au rythme de la
sous-commande la plus lente, avec le détail par boutique s'il déplie.

---

## 7. Paiement

### 7.1 — Paiement refusé
Statut `en attente de paiement`, nouvelle tentative possible sans reconstituer
le panier.

### 7.2 — Paiement accepté par la banque mais confirmation non reçue
La confirmation définitive vient du **webhook serveur-à-serveur**. Tant qu'il
n'est pas reçu : `en attente de confirmation`, avec vérification de rattrapage.

### 7.3 — Remboursement
Automatique (annulation avant préparation) ou manuel (litige tranché par Fatou).
Statut `remboursée` visible, avec délai estimé.

### 7.4 — Répartition entre plusieurs vendeurs
Assurée par Stripe Connect : un seul règlement client, réparti automatiquement
selon la part de chaque vendeur, commission plateforme déduite.

### 7.5 — Fraude suspectée
Compte temporairement limité, message neutre au client, alerte à Fatou pour revue.

---

## 8. Livraison

### 8.1 — Le client est absent
**SI** une consigne existe (« laisser devant la porte ») **ALORS** le livreur la
suit, prend une photo de preuve, statut `livrée`.
**SINON** il déclare « client absent » → statut `tentative échouée`, Léa est
notifiée immédiatement avec ses options (reprogrammer, personne de contact).
**SI** aucune réaction dans le délai **ALORS** retour au vendeur (Express) ou à
l'entrepôt (Standard) : **deux tentatives gratuites**, puis remboursement du
produit et retenue des frais de livraison
([D-23](../00-pilotage/journal-decisions.md)).

### 8.2 — Contacter le client
Appel par numéro masqué, jamais le numéro réel. Au MVP, ce service est simulé.

### 8.3 — Aucun livreur n'accepte
Élargissement progressif de la zone de recherche, puis alerte à Fatou ou au
gestionnaire d'entrepôt.

### 8.4 — Le livreur accepte puis abandonne
La course repart au vivier ; le temps perdu reste visible côté admin.

### 8.5 — Deux livreurs acceptent en même temps
Un seul obtient l'attribution (verrou transactionnel), l'autre reçoit un message
clair — jamais deux livreurs en route pour le même colis.

### 8.6 — Colis endommagé ou incomplet
Bouton « Signaler un problème » distinct d'un avis : ouvre un litige, avec
remboursement partiel ou total possible.

### 8.7 — Adresse introuvable
Contact via 8.2 ; si impossible, même traitement que 8.1.

### 8.8 — Retard sur l'estimation
L'estimation se met à jour ; au-delà d'un seuil, notification proactive au
client, sans attendre qu'il s'inquiète.

### 8.9 — Attribution des courses et des tournées

| | Express | Standard |
|---|---|---|
| Quand | Dès que la commande est prête | Par lot, sur les colis en attente d'un même entrepôt |
| Logique MVP | Livreur disponible le plus proche | Par zone, puis ordre d'arrivée |
| Logique cible | Idem, avec prise en compte de la charge | Optimisation de tournée par un solveur existant |

Le mécanisme est interchangeable par construction (pattern Strategy) : brancher
un vrai solveur plus tard ne touche pas au reste du système.

---

## 9. Entrepôt et tournées *(section nouvelle)*

### 9.1 — Un colis arrive à l'entrepôt
Samir le scanne ou le saisit → statut `reçu en entrepôt`, visible par le client
dans sa frise et par le vendeur dans sa sous-commande.
**SI** un colis attendu n'arrive pas dans le délai **ALORS** alerte au vendeur
concerné, pas au client.

### 9.2 — Samir constitue une tournée
Il sélectionne des colis d'une même zone, les regroupe en tournée, ordonne les
arrêts, puis affecte la tournée à un livreur Standard disponible.
**SI** aucun livreur n'est disponible **ALORS** la tournée reste `prête`, et
l'attente est visible dans le tableau de bord admin.

### 9.3 — Julien démarre sa tournée
Il ne peut pas sauter un arrêt sans le déclarer (livré, absent, refusé). Sa
progression est visible côté entrepôt et côté clients concernés.

### 9.4 — Un colis reste en entrepôt trop longtemps
Alerte à Samir puis à Fatou, avec proposition de remboursement au client.

---

## 10. Compte et rôles

### 10.1 — Livreur désactivé pendant une course
Désactivé pour les nouvelles attributions seulement ; la course en cours se
termine, sauf suspension d'urgence où Fatou réattribue manuellement.

### 10.2 — Mot de passe oublié en plein paiement
Réinitialisation qui conserve le panier.

### 10.3 — Vendeur suspendu par Fatou
Catalogue immédiatement invisible ; les commandes en cours sont traitées
explicitement (annulées et remboursées, ou menées à terme), jamais orphelines.

### 10.4 — Session expirée pendant une action sensible
Re-authentification sans perte de l'état en cours.

### 10.5 — Création, modification et suppression de rôles
Rôles plateforme (vendeur, livreur, gestionnaire d'entrepôt, admin) : par un
admin. Gestionnaire staff vendeur : par son vendeur uniquement. Suppression
toujours logique, avec journal d'audit.

---

## 11. Promotions

### 11.1 — Code expiré ou déjà utilisé
Message explicite dès la saisie, avant le paiement.

### 11.2 — Deux promotions non cumulables
Le système applique la plus favorable et le dit clairement — jamais de cumul
silencieux, jamais de choix caché.

### 11.3 — Promotion sur une commande annulée
Le code redevient utilisable si la commande est annulée avant préparation.

---

## 12. Avis

### 12.1 — Avis avant livraison
Impossible : le bouton n'apparaît qu'après le statut `livrée`.

### 12.2 — Avis signalé comme abusif
Passe en modération admin ; jamais de suppression unilatérale par la partie visée.

### 12.3 — Trois cibles distinctes
Un avis porte sur un produit, sur une boutique ou sur un livreur. La note de
boutique est celle qui compte le plus pour un client Express.

---

## 13. Notifications

### 13.1 — Notifications push désactivées
Toute information critique reste consultable dans l'application. Le push est un
canal complémentaire, jamais l'unique moyen d'être informé.

### 13.2 — Tous les rôles sont notifiables
Pas seulement le client : validation de compte, commande à préparer, tournée
affectée, litige ouvert.

---

## 14. Admin et litiges

### 14.1 — Litige entre Léa et un vendeur
Fatou voit sur un seul écran l'historique complet : statuts, paiement, livraison,
échanges, preuves. Aucun recoupement manuel entre plusieurs pages.

### 14.2 — Validation d'un nouveau vendeur
Statut `en attente de validation` tant que Fatou n'a pas approuvé ; aucune
publication de catalogue avant.

---

## 15. Sécurité et permissions

### 15.1 — Accès à une commande qui n'est pas la sienne
Bloqué **côté serveur** (403), pas seulement masqué dans l'interface.

### 15.2 — Un livreur valide une livraison qui ne lui est pas attribuée
Bloqué côté serveur : l'attribution fait foi.

### 15.3 — Un gestionnaire tente d'accéder au chiffre d'affaires
Bloqué côté serveur, et absent de son interface — les deux, pas l'un ou l'autre.
