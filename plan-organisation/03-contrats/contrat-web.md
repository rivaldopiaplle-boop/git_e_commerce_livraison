# Contrat Web — Vue 3 + Vite

> Ce que l'application web doit faire, écran par écran et rôle par rôle.
> L'apparence commune (couleurs, symboles, composants) est dans
> [design-system.md](../04-maquettes/design-system.md) ; ici on parle de
> structure, de navigation et de contenu.
>
> Rôles concernés : **Client**, **Vendeur**, **Gestionnaire** (les deux types),
> **Admin**. Le livreur n'a pas de web (règle d'or n°6).

---

## 1. Structure imposée (règle d'or n°9)

```
┌───────────────────────────────────────────────────────────┐
│ NAVBAR — recherche · statut du compte · notifications · moi│
├──────────┬─────────────────────────────────┬──────────────┤
│ SIDEBAR  │  CONTENU                        │  PANNEAU     │
│ gauche   │  ┌─── onglets ───┐              │  droit       │
│ rétrac-  │  │ tableaux, cartes, listes     │  rétractable │
│ table    │  │ avec boutons-icônes          │  (détail,    │
│          │  └──────────────────────────────│   panier,    │
│          │                                 │   aide)      │
└──────────┴─────────────────────────────────┴──────────────┘
```

- **Sidebar** : navigation principale, rétractable en barre d'icônes. L'état
  replié est mémorisé par utilisateur.
- **Navbar** : ce qui doit rester visible en permanence — recherche, cloche de
  notifications, avertissement de compte en attente, menu du compte.
- **Panneau droit** : détail sans quitter la page. Le panier client vit ici.
  Rétractable, jamais obligatoire pour continuer.
- **Popups** : uniquement pour une action courte et bloquante (confirmation,
  saisie d'un motif). Jamais pour afficher un contenu long.
- **Onglets** : à l'intérieur du contenu, pour découper un tableau de bord.
- **Listes** : boutons-icônes pour consulter et gérer, avec infobulle.

---

## 2. Trois états obligatoires par écran

Aucun écran n'est considéré fini sans : **état vide** rédigé et actionnable,
**état de chargement** (squelette, pas un spinner plein écran), **état d'erreur**
avec une action de reprise. C'est la règle d'or n°2 appliquée au front.

---

## 3. Client — accent vert `#16a34a`

| Écran | Contenu | Palier |
|---|---|---|
| Accueil / catalogue | Bandeau « Livrer à … », boutiques Express proches, catalogue Standard, filtres | 1 |
| Fiche produit | **Galerie avec zoom**, prix, stock, vendeur, avis, ajout au panier ou bouton gelé + alerte | 1 |
| Panier (panneau droit) | Lignes, avertissement de prix modifié, **aperçu du découpage en commandes** | 1 |
| Tunnel de commande | Adresse, récapitulatif par commande, frais, paiement | 1 |
| Confirmation | Les N commandes créées, chacune avec son suivi | 1 |
| Mes commandes | Liste filtrable, frise de suivi par commande | 1 |
| Détail commande | Frise, détail par boutique, actions autorisées, facture | 1 |
| Mes adresses | Ajout, adresse principale, instructions de livraison | 1 |
| Avis | Noter produit, boutique, livreur après livraison | 2 |
| Notifications, profil | | 1 |

Point d'attention : le client web et le client mobile montrent **les mêmes
informations** ; ce sont la disposition et la densité qui changent, pas le
contenu (règle d'or n°7).

## 4. Vendeur — accent bleu `#2563eb`

| Écran | Contenu | Palier |
|---|---|---|
| Tableau de bord | Onglets : ventes du jour, commandes à préparer, alertes de stock | 1 |
| Catalogue | Liste des produits, création, modification, masquage, **photos par glisser-déposer** ([contrat-medias.md](contrat-medias.md)) | 1 |
| Commandes entrantes | File par statut, action limitée au statut suivant | 1 |
| Détail commande | Contenu, client (informations minimales), livraison | 1 |
| Stock | Niveaux, seuils, ajustement avec motif, historique des mouvements | 1 |
| Personnel | Créer et désactiver ses gestionnaires staff vendeur | 1 |
| Paramètres boutique | Nom, adresse, rayon de livraison, horaires, compte Stripe | 1 |
| Sous-commandes | Sa part des commandes Standard multi-vendeur | 1 |
| Promotions, statistiques | | 2 |

Un vendeur ne voit **jamais** les données d'un autre vendeur, y compris dans une
commande multi-vendeur où il ne voit que sa sous-commande.

## 5. Gestionnaire — accent orange `#ea580c`

L'interface est la même, le contenu dépend de `type_gestionnaire`.

**Staff vendeur (Nadia)** — palier 1 : commandes à préparer, détail de
préparation, stock, ajustement avec motif.
Ni prix de vente, ni chiffre d'affaires, ni statistiques — **absents de
l'interface et refusés par le serveur**, les deux (règle R-29).

**Staff entrepôt (Samir)** — palier 1 : colis reçus, réception d'un colis,
constitution d'une tournée (sélection, ordre des arrêts), affectation à un
livreur, suivi des tournées en cours.

## 6. Admin — accent rouge `#b91c1c`

| Écran | Contenu | Palier |
|---|---|---|
| Tableau de bord | Onglets : activité, comptes à valider, litiges, alertes | 1 |
| Validations | Vendeurs et livreurs en attente, pièces fournies, valider ou rejeter avec motif | 1 |
| Utilisateurs | Recherche tous rôles, suspension, réactivation | 1 |
| Vue commande complète | Statuts, paiement, livraison, échanges, preuves — **sur un seul écran** (scénario 14.1) | 1 |
| Entrepôts | Créer un entrepôt, y affecter du personnel | 1 |
| Litiges | File, arbitrage, remboursement partiel ou total | 2 |
| Journal d'audit | Qui a fait quoi, quand, sur quoi | 1 |

Le Django Admin sert de back-office de secours dès le premier jour (règle d'or
n°5), mais **les écrans d'arbitrage sont refaits en Vue** : ce sont eux qu'on
montre en entretien.

---

## 7. Navigation et routes

```
/                        catalogue
/produit/:id             fiche produit
/panier                  panier plein écran (le panneau droit reste la voie normale)
/commande                tunnel
/mes-commandes           /mes-commandes/:id
/compte/*                profil, adresses, notifications

/vendeur/*               tableau de bord, catalogue, commandes, stock, personnel, parametres
/gestion/*               commandes à préparer, stock  |  colis, tournées
/admin/*                 tableau de bord, validations, utilisateurs, commandes, entrepots, litiges, audit
```

Une route interdite pour le rôle courant redirige vers son accueil avec un
message explicite — jamais une page blanche, jamais une erreur technique.

---

## 8. Règles techniques front

- **Vue 3, Composition API, `<script setup>`**, TypeScript.
- **Pinia** pour l'état partagé : session, panier, notifications. Rien d'autre en
  global — le reste est local au composant ou rechargé par la vue.
- **Un seul client HTTP** centralisé : ajoute le jeton, rafraîchit à l'expiration,
  traduit l'enveloppe d'erreur en objet utilisable, journalise.
- **Aucune donnée simulée dans les écrans.** Un écran sans données affiche son
  état vide. C'est une leçon directe du projet banque : les fausses données
  masquent les endpoints manquants jusqu'au jour de la démonstration.
- **Aucune règle métier dupliquée côté front.** Les transitions de statut
  viennent du serveur (`details.transitions_possibles`), les montants sont
  calculés par le serveur. Le front affiche, il ne décide pas.
- **Accessibilité minimale** : navigation au clavier, contraste suffisant,
  libellés sur les boutons-icônes. Un bouton qui n'est qu'une icône sans
  infobulle est un bug.
