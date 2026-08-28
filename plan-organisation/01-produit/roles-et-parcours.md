# Rôles, entrées dans le système, et droits

> Réponse consolidée aux questions A-1 à A-4 et A-19 : qui existe, qui crée qui,
> qui voit quoi. C'est la page à ouvrir quand on écrit une permission ou un menu.

## Les personae

| Rôle | Nom | Contexte | Support |
|---|---|---|---|
| Visiteur | — | Consulte sans compte | Web + mobile |
| Client | **Léa** | Achète pour elle-même | Web + mobile |
| Vendeur Express | **Karim** | « Chez Karim », restauration rapide | Web |
| Vendeur Standard | **Sophie** | « TechSophie », électronique | Web |
| Gestionnaire staff vendeur | **Nadia** | Employée de Karim, prépare les commandes | Web |
| Gestionnaire staff entrepôt | **Samir** | Employé de la plateforme, entrepôt Nord | Web |
| Livreur Express | **Amine** | Une course à la fois, à vélo | Mobile |
| Livreur Standard | **Julien** | Tournées groupées depuis l'entrepôt | Mobile |
| Admin | **Fatou** | Valide les comptes, arbitre les litiges | Web |

*(Le gestionnaire d'entrepôt n'avait pas de nom dans le bloc A, ce qui rendait la
lecture confuse dès qu'on parlait des deux types de gestionnaire. Il s'appelle
désormais **Samir**.)*

---

## Comment chacun entre dans le système

| Rôle | Entrée | Validation ? | Créé par |
|---|---|---|---|
| Visiteur | Aucune inscription | — | — |
| **Client** | Auto-inscription libre | Non | Lui-même |
| **Livreur** (Express ou Standard) | Candidature en auto-inscription | **Oui, admin** (identité, véhicule) | Lui-même, activé par l'admin |
| **Vendeur** | Candidature spontanée **ou** invitation de l'admin | **Oui, admin** | Lui-même ou l'admin |
| **Gestionnaire staff vendeur** | Jamais d'auto-inscription | Non | **Son vendeur** |
| **Gestionnaire staff entrepôt** | Jamais d'auto-inscription | Non | **Un admin** |
| **Admin** | Jamais d'auto-inscription | Non | Le premier par la commande `seed_admin`, les suivants par un admin |

### Le tout premier compte

Il n'existe aucun formulaire « devenir admin ». Fatou est créée par une commande
de gestion exécutée une fois au déploiement, hors de toute interface web. C'est
elle qui crée ensuite les autres admins et les gestionnaires d'entrepôt.

### Ce que chacun voit avant qu'il n'y ait le moindre contenu

Chaque rôle a un **état vide rédigé**, jamais un tableau vide silencieux :

- Karim / Sophie : « Ajoutez votre premier produit », avec le bouton.
- Léa : « Aucune boutique ne livre encore à votre adresse » — et non une page blanche.
- Amine / Julien : « Aucune course disponible pour l'instant », avec l'état de disponibilité.
- Nadia / Samir : « Rien à préparer ».
- Fatou : compteurs à zéro servant de liste de démarrage (« 0 vendeur à valider »).

---

## Vendeur, gestionnaire, admin : la distinction qui structure tout

C'est la question que tu posais le plus souvent (A-3, A-4, A-6, A-19). Résumé :

- **Le vendeur est un commerçant.** Il possède la boutique, fixe les prix, voit
  son chiffre d'affaires, est responsable devant la plateforme, recrute son
  propre personnel. Chacun peut ouvrir sa boutique — électronique, restauration,
  mode — c'est bien ce que tu décrivais en A-3 : **oui, chaque vendeur crée sa
  boutique**, et le catalogue de la plateforme est la somme des boutiques.
- **Le gestionnaire est du personnel.** Il exécute : préparer, empaqueter,
  ajuster un stock physique. Il ne voit ni les prix d'achat, ni le chiffre
  d'affaires, ni les statistiques. Il en existe deux sortes selon son employeur :
  le staff d'un vendeur (Nadia, employée de Karim) et le staff d'un entrepôt de
  la plateforme (Samir, employé de la plateforme).
- **L'admin est la plateforme.** Il n'a pas de boutique et ne vend rien. Il
  valide les commerçants et les livreurs, crée les entrepôts et leur personnel,
  arbitre les litiges, suspend les fraudeurs.

Dit autrement : **vendeur = qui vend, gestionnaire = qui manipule, admin = qui
arbitre.** Aucun des trois ne peut faire le travail d'un autre.

### Qui gère les entrepôts (question A-19)

Les entrepôts Standard appartiennent à la **plateforme**, pas aux vendeurs. Ils
sont créés par l'admin, qui y affecte des gestionnaires staff entrepôt. Un
entrepôt reçoit les colis de **plusieurs vendeurs Standard** pour une même
région : c'est précisément ce qui permet de grouper les tournées, et ça n'aurait
aucun sens si chaque vendeur avait le sien.

---

## Matrice des droits

Lecture : **C** créer · **L** lire · **M** modifier · **S** supprimer/suspendre ·
**—** aucun accès. « propre » = uniquement ses propres données.

| Objet | Client | Vendeur | Gest. vendeur | Gest. entrepôt | Livreur | Admin |
|---|---|---|---|---|---|---|
| Son compte | LM | LM | LM | LM | LM | LM |
| Comptes vendeurs | — | — | — | — | — | CLMS |
| Comptes livreurs | — | — | — | — | — | LMS |
| Gestionnaires staff vendeur | — | CLMS (propre) | L (soi) | — | — | LS |
| Gestionnaires staff entrepôt | — | — | — | L (soi) | — | CLMS |
| Entrepôts | — | — | — | L (le sien) | — | CLMS |
| Produits | L (catalogue) | CLMS (propre) | LM (stock uniquement) | — | — | LS |
| Prix d'un produit | L | CM | **—** | — | — | L |
| Stock | L (disponibilité) | LM | **LM** | L (entrepôt) | — | L |
| Panier | CLMS (propre) | — | — | — | — | — |
| Commande | CL (propre) | L (propre) + statut | L (propre boutique) + statut | L (entrepôt) | L (celle qui lui est attribuée) | L (toutes) |
| Chiffre d'affaires / stats | — | L (propre) | **—** | — | L (ses gains) | L (global) |
| Paiement / remboursement | L (propre) | L (propre part) | — | — | — | LM |
| Livraison | L (propre) | L (propre) | L | LM (tournées) | LM (la sienne) | LM |
| Tournée | — | — | — | **CLM** | L (la sienne) | L |
| Avis | C (après livraison) L | L (le concernant) | — | — | L (le concernant) | LMS (modération) |
| Litige | C L (propre) | L (le concernant) | — | — | L (le concernant) | **CLMS (arbitrage)** |
| Promotions | L | C L M S (propre) | — | — | — | CLMS |
| Journal d'audit | — | — | — | — | — | L |

Deux règles non négociables issues des scénarios 14.1 et 14.2 :

1. **Tout est vérifié côté serveur.** Cacher un bouton dans l'interface n'est pas
   une permission. Une commande qui n'est pas la sienne renvoie 403, pas une page
   masquée.
2. **L'attribution fait foi.** Un livreur ne peut valider que la livraison qui
   lui est attribuée, quoi qu'il déclare avoir fait physiquement.

---

## Écrans minimum par rôle

| Rôle | Support | Écrans |
|---|---|---|
| Client | Web + mobile | Catalogue, fiche produit, panier, tunnel de commande, paiement, suivi, historique, adresses, avis, notifications, profil |
| Vendeur | Web | Tableau de bord ventes, catalogue, commandes entrantes, stock, personnel, promotions, statistiques, paramètres boutique |
| Gestionnaire staff vendeur | Web | Commandes à préparer, stock, ajustement avec motif |
| Gestionnaire staff entrepôt | Web | Colis reçus, tri par zone, constitution des tournées, affectation aux livreurs |
| Livreur Express | Mobile | Course en cours, courses disponibles à proximité, navigation, contact client, livré / absent, gains, disponibilité |
| Livreur Standard | Mobile | Tournée du jour, arrêt suivant, navigation, livré / absent par arrêt, gains, disponibilité |
| Admin | Web | Tableau de bord global, validations, litiges, vue complète d'une commande, utilisateurs, entrepôts, journal d'audit |
