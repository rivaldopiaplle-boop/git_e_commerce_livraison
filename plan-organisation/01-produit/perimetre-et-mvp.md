# Périmètre — deux paliers, et ce qu'on ne fait pas

> Réponse directe à ta phrase du bloc A : *« je trouve qu'on s'éparpille et
> qu'on doit pas tout faire mais bien recadrer et définir ce qu'on veut faire »*.
>
> **Révision du bloc C** : ce document proposait trois paliers, avec le circuit
> Standard et l'entrepôt renvoyés au second. Tu as tranché l'inverse — *« le
> Standard fait partie du MVP »*, *« l'entrepôt c'est le premier, sinon comment
> les produits Standard et les livreurs Standard fonctionnent »*. Tu as raison :
> un circuit Standard sans entrepôt ne tient pas debout. Le périmètre du MVP est
> donc plus large, et il ne reste que deux paliers.

---

## Le projet en une phrase

Une plateforme où plusieurs boutiques vendent, où des clients commandent, et où
des livreurs livrent — avec **deux régimes de livraison** : *Express*
(restauration, trajet direct, une boutique par commande) et *Standard*
(colis, passage par un entrepôt, plusieurs boutiques possibles).

C'est le double régime qui fait l'intérêt du projet en entretien.

---

## Palier 1 — le MVP : les deux circuits, de bout en bout

Objectif : Léa commande chez Karim (Express) **et** chez Sophie et une autre
boutique (Standard) ; elle paie une fois ; Nadia prépare ; le colis Standard
transite par l'entrepôt de Rachid ; Amine livre le repas, Julien fait sa tournée ;
Léa suit les deux et note. Fatou valide les comptes. Le tout déployé et
démontrable en ligne.

| Domaine | Dans le MVP |
|---|---|
| Comptes | Client (auto-inscription), Vendeur Express et Standard (validation admin), Gestionnaire staff vendeur (créé par le vendeur), Gestionnaire staff entrepôt (créé par l'admin), Livreur Express et Standard (validation admin), Admin (seed) |
| Catalogue | Produits, catégories, photos multiples, disponibilité, filtrage Express par rayon, catalogue Standard sans restriction |
| Panier | Panier connecté et panier invité, fusion à la connexion, panier mixte Express + Standard |
| Commande | Découpage du panier (`CommandeSplitter`), commande Standard multi-vendeur, sous-commandes par vendeur, statuts, annulations |
| Paiement | Stripe en mode test, Stripe Connect et répartition entre vendeurs, webhook, remboursement |
| Livraison Express | Attribution au livreur disponible le plus proche, statuts, tentatives, preuve |
| Livraison Standard | Entrepôt, réception des colis, constitution des tournées, arrêts ordonnés, frais par zone et seuil de gratuité |
| Notifications | In-app persistant + e-mail. Push en palier 2 |
| Admin | Validation des vendeurs et livreurs, gestion des entrepôts et de leur personnel, vue complète d'une commande |
| Web | Écrans client, vendeur, gestionnaire vendeur, gestionnaire entrepôt, admin |
| Mobile | Écrans client, livreur Express et livreur Standard |
| Hors fonctionnel | Docker, CI, déploiement public, seed de démonstration, banc de preuves |

**Preuve de fin de palier** : sur l'URL publique, avec les comptes de
démonstration, un panier contenant une boutique Express et deux boutiques
Standard produit trois commandes cohérentes, payées en un seul règlement,
livrées par deux circuits différents — le tout déroulé devant quelqu'un en moins
de dix minutes, en changeant de rôle à l'écran.

---

## L'ordre de construction, lui, reste séquentiel

Le périmètre du MVP est un seul bloc. La **manière de le construire** ne l'est
pas : on termine une tranche avant d'ouvrir la suivante, sinon on se retrouve
avec cinq chantiers ouverts et rien qui marche.

1. **Socle** — comptes, rôles, permissions, Docker, CI. Rien de visible, tout en dépend.
2. **Catalogue et panier** — communs aux deux circuits.
3. **Commande et paiement** — le découpage du panier gère déjà les deux régimes,
   parce que le refaire après coup coûterait dix fois plus cher.
4. **Circuit Express complet** — la boucle la plus courte : elle valide de bout
   en bout la mécanique commande → livraison → suivi → notation.
5. **Circuit Standard complet** — entrepôt, tournées, arrêts. Il réutilise tout
   ce que l'étape 4 a mis en place ; c'est pour ça qu'il vient après, et non
   parce qu'il serait moins important.
6. **Déploiement public et démonstration**.

C'est la différence entre *le périmètre* (ce que le MVP contient) et *l'ordre*
(dans quel sens on le fabrique). Le détail avec les tests de sortie est dans
[demarrage-projet.md](../05-execution/demarrage-projet.md).

---

## Palier 2 — ce qui rend le produit crédible

Promotions, avis et modération, litiges arbitrés, factures PDF, notifications
push, assistant d'aide, statistiques vendeur, optimisation réelle des tournées
par un solveur existant, suivi temps réel par WebSocket, points relais.

Ces éléments sont bons à avoir et déjà spécifiés dans les scénarios ; aucun
n'est nécessaire pour raconter le projet.

---

## Hors périmètre, assumé et déclaré

Le dire explicitement en entretien est une force, pas une faiblesse — cela montre
qu'on distingue un projet de démonstration d'un produit.

- Retour produit / droit de rétractation (voir [Q-07](../00-pilotage/questions-ouvertes.md)).
- Multi-langue, multi-devise, TVA par pays.
- Facturation comptable réelle et conformité fiscale.
- Vraie mise en production : haute disponibilité, sauvegardes, plan de reprise.
- Application iOS publiée sur l'App Store (le build Android suffit à démontrer).
- Conformité RGPD complète (une page de politique et l'effacement d'un compte
  suffisent au niveau démonstration).

---

## Comment on décide qu'une idée nouvelle entre dans le projet

Trois questions, dans cet ordre :

1. **Est-ce que ça se voit dans la démonstration de dix minutes ?**
   Si non, ça va au palier 2 par défaut.
2. **Est-ce que ça oblige à changer le modèle de données ?**
   Si oui, ça doit être décidé maintenant même si c'est développé plus tard —
   changer une migration après coup coûte dix fois plus cher.
3. **Est-ce que ça existe déjà tout fait quelque part ?**
   Si oui, on l'intègre. Si non, on se demande sérieusement pourquoi personne ne
   l'a fait (règle d'or n°5).
