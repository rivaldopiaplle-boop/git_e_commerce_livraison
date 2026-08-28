# Glossaire — le vocabulaire du projet

> Un mot = un sens = un seul terme dans le code, l'API, les écrans et les
> documents. Le premier bug d'organisation d'un projet à plusieurs rôles, c'est
> quand « commande », « colis » et « livraison » désignent tantôt la même chose
> tantôt trois choses différentes.

## Acteurs

| Terme | Sens exact | Ne pas confondre avec |
|---|---|---|
| **Visiteur** | Personne non connectée qui consulte le catalogue et peut remplir un panier invité | Client |
| **Client** | Compte auto-inscrit qui commande et paie | Utilisateur (terme technique générique) |
| **Vendeur** | Propriétaire d'une boutique. Seul à voir le chiffre d'affaires et à fixer les prix | Gestionnaire |
| **Gestionnaire — staff vendeur** | Employé d'un vendeur : prépare, gère le stock physique. Jamais d'accès aux prix ni au CA | Vendeur |
| **Gestionnaire — staff entrepôt** | Employé de la plateforme dans un entrepôt régional : réceptionne, trie, constitue les tournées | Gestionnaire staff vendeur |
| **Livreur Express** | Une course à la fois, du vendeur au client, sans entrepôt | Livreur Standard |
| **Livreur Standard** | Une tournée de plusieurs arrêts au départ d'un entrepôt | Livreur Express |
| **Admin** | Personnel de la plateforme : valide les comptes, arbitre les litiges, crée les entrepôts | Vendeur |

## Objets métier

| Terme | Sens exact |
|---|---|
| **Produit** | Article vendu par un vendeur, avec un prix et un stock |
| **Panier** | Contenu en cours de sélection d'un client ou d'un visiteur. **N'est jamais une réservation de stock** |
| **Ligne de panier** | Un produit + une quantité dans un panier |
| **Commande** | Résultat du passage en caisse pour **un seul mode** (Express ou Standard). Un panier peut produire plusieurs commandes |
| **Sous-commande** | Part d'une commande Standard multi-vendeur revenant à un vendeur donné. C'est ce que le vendeur prépare et voit |
| **Paiement** | Une transaction Stripe. Un checkout client = un paiement, réparti ensuite entre vendeurs par Stripe Connect |
| **Livraison** | Le transport d'une commande jusqu'à l'adresse du client. Une commande = une livraison |
| **Tournée** | Suite ordonnée d'arrêts confiée à un livreur Standard. Une tournée = N livraisons |
| **Arrêt** | Un point d'une tournée : une livraison à effectuer, avec son rang dans l'ordre de passage |
| **Tentative de livraison** | Un passage du livreur chez le client. Une livraison peut avoir plusieurs tentatives (client absent) |
| **Entrepôt** | Point de regroupement régional des colis Standard, partagé entre plusieurs vendeurs, exploité par la plateforme |
| **Zone de livraison** | Découpage géographique servant à calculer les frais Standard et à router vers un entrepôt |
| **Rayon Express** | Distance maximale entre une boutique Express et le client. Au-delà, la boutique n'apparaît pas au catalogue |
| **Litige** | Réclamation ouverte après livraison (produit non conforme, colis endommagé), arbitrée par un admin |
| **Avis** | Note + commentaire laissés après livraison, sur un produit, un vendeur ou un livreur |

## Modes de service

| Terme | Sens exact |
|---|---|
| **Express** | Délai court, produits périssables ou immédiats. Un seul vendeur par commande. Trajet direct boutique → client. Catalogue filtré par rayon |
| **Standard** | Délai long, produits non périssables. Plusieurs vendeurs possibles dans une commande. Passage par un entrepôt. Catalogue sans restriction de distance |

Le mode est porté par le **vendeur** (attribut `type_activite`), pas par le
produit ni par la commande — décision actée, voir
[journal-decisions.md](journal-decisions.md#d-08).

## Termes techniques employés dans les documents

| Terme | Sens |
|---|---|
| **Verrou transactionnel** | `SELECT ... FOR UPDATE` : empêche deux paiements simultanés d'obtenir le même dernier article |
| **Webhook** | Appel serveur-à-serveur de Stripe vers notre API, seule source de vérité d'un paiement |
| **État vide (*empty state*)** | Écran prévu et rédigé pour le cas « il n'y a rien à afficher » |
| **Seed** | Jeu de données initial créé par commande, hors interface web |
| **Banc de preuves** | Suite de tests qui rejoue les scénarios métier de bout en bout sur une base neuve |
| **Vitrine** | Déploiement public de démonstration, destiné aux recruteurs, distinct d'une vraie production |
