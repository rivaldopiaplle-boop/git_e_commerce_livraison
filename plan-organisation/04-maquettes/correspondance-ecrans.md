# Correspondance maquettes → écrans Vue

> Sur le projet banque, ce document (`00-correspondance-react.md`) a évité des
> semaines de flottement : il dit quelle maquette devient quel composant, sur
> quelle route, avec quels endpoints. On reprend le procédé.
>
> Il se remplit au fur et à mesure : une ligne complétée = un écran réellement
> branché sur l'API. Tant qu'un écran n'a pas ses endpoints, il n'est pas prêt.

---

## Comment se servir de [maquettes.html](maquettes.html)

Ouvrir le fichier dans un navigateur. La barre du haut permet de basculer :

- **le rôle** — client, vendeur, gestionnaire, livreur, admin (l'accent de
  couleur change avec lui) ;
- **le support** — web ou mobile ;
- **le mode** — Express ou Standard pour le vendeur et le livreur, staff vendeur
  ou staff entrepôt pour le gestionnaire ;
- **l'état vide** — pour voir ce que chaque écran affiche quand il n'y a rien.

Cette bascule d'état vide est la fonctionnalité la plus utile du fichier :
c'est l'écran qu'on oublie de coder et qu'un recruteur voit en premier sur une
base neuve.

---

## Conventions de nommage

- Une **vue** correspond à une route : `VueCatalogue.vue`, `VueMesCommandes.vue`.
- Un **composant** est réutilisable et ne connaît pas de route : `BadgeStatut.vue`.
- Un **magasin** Pinia par domaine partagé : `session`, `panier`, `notifications`.
- Les composants communs vivent dans `composants/communs/`, les écrans par rôle
  dans `vues/<role>/`.

---

## Client — accent vert

| Maquette | Route | Vue | Endpoints | Palier | État |
|---|---|---|---|---|---|
| Catalogue | `/` | `VueCatalogue` | `GET /produits`, `GET /boutiques` | 1 | à faire |
| Fiche produit | `/produit/:id` | `VueProduit` | `GET /produits/{id}`, `POST /panier/lignes`, `POST /produits/{id}/alerte-dispo` | 1 | à faire |
| Panier (panneau droit) | — | `PanneauPanier` | `GET /panier`, `PATCH`, `DELETE`, `GET /panier/apercu-commandes` | 1 | à faire |
| Tunnel de commande | `/commande` | `VueTunnel` | `POST /commandes`, `POST /paiements/intention` | 1 | à faire |
| Confirmation | `/commande/confirmation` | `VueConfirmation` | `GET /commandes` | 1 | à faire |
| Mes commandes | `/mes-commandes` | `VueMesCommandes` | `GET /commandes` | 1 | à faire |
| Détail commande | `/mes-commandes/:id` | `VueCommande` | `GET /commandes/{id}`, `GET .../historique`, `GET /livraisons/{id}/suivi` | 1 | à faire |
| Adresses | `/compte/adresses` | `VueAdresses` | `GET/POST/PATCH /moi/adresses` | 1 | à faire |
| Notifications | `/compte/notifications` | `VueNotifications` | `GET /notifications` | 1 | à faire |

## Vendeur — accent bleu

| Maquette | Route | Vue | Endpoints | Palier | État |
|---|---|---|---|---|---|
| Tableau de bord (onglets) | `/vendeur` | `VueVendeurAccueil` | `GET /commandes?statut=`, `GET /produits?stock_bas=1` | 1 | à faire |
| Commandes entrantes | `/vendeur/commandes` | `VueVendeurCommandes` | `GET /commandes`, `PATCH /sous-commandes/{id}/statut` | 1 | à faire |
| Catalogue | `/vendeur/catalogue` | `VueVendeurCatalogue` | `GET/POST/PATCH /produits` | 1 | à faire |
| Stock | `/vendeur/stock` | `VueVendeurStock` | `PATCH /produits/{id}/stock` | 1 | à faire |
| Personnel | `/vendeur/personnel` | `VueVendeurPersonnel` | `POST /vendeurs/gestionnaires` | 1 | à faire |
| Paramètres boutique | `/vendeur/parametres` | `VueVendeurParametres` | `PATCH /boutiques/{id}` | 1 | à faire |
| Avis reçus | `/vendeur/avis` | `VueVendeurAvis` | `GET /avis?vendeur=` | 2 | à faire |

## Gestionnaire — accent orange

| Maquette | Route | Vue | Endpoints | Palier | État |
|---|---|---|---|---|---|
| Commandes à préparer (staff vendeur) | `/gestion/commandes` | `VueGestionCommandes` | `GET /commandes`, `PATCH /sous-commandes/{id}/statut` | 1 | à faire |
| Stock (staff vendeur) | `/gestion/stock` | `VueGestionStock` | `PATCH /produits/{id}/stock` | 1 | à faire |
| Colis reçus (staff entrepôt) | `/gestion/colis` | `VueEntrepotColis` | `GET /entrepots/{id}/colis` | 1 | à faire |
| Tournées à préparer | `/gestion/tournees` | `VueEntrepotTournees` | `POST /entrepots/{id}/tournees`, `PATCH /tournees/{id}/arrets`, `POST /tournees/{id}/affecter` | 1 | à faire |

## Admin — accent rouge

| Maquette | Route | Vue | Endpoints | Palier | État |
|---|---|---|---|---|---|
| Tableau de bord | `/admin` | `VueAdminAccueil` | `GET /admin/tableau-de-bord` | 1 | à faire |
| Validations | `/admin/validations` | `VueAdminValidations` | `GET /admin/validations`, `POST .../valider`, `.../rejeter` | 1 | à faire |
| Utilisateurs | `/admin/utilisateurs` | `VueAdminUtilisateurs` | `GET /admin/utilisateurs`, `POST .../suspendre` | 1 | à faire |
| Vue commande complète | `/admin/commandes/:id` | `VueAdminCommande` | `GET /commandes/{id}` et tout son historique | 1 | à faire |
| Entrepôts | `/admin/entrepots` | `VueAdminEntrepots` | `POST /admin/entrepots`, `.../gestionnaires` | 1 | à faire |
| Litiges | `/admin/litiges` | `VueAdminLitiges` | `GET /admin/litiges`, `POST .../resoudre` | 2 | à faire |
| Journal d'audit | `/admin/audit` | `VueAdminAudit` | `GET /admin/audit` | 1 | à faire |

## Mobile client — accent vert

| Maquette | Onglet | Écran | Endpoints | Palier |
|---|---|---|---|---|
| Accueil | 1 | `EcranAccueil` | `GET /produits?lat=&lon=` | 1 |
| Recherche | 2 | `EcranRecherche` | `GET /produits?recherche=` | 1 |
| « + » | 3 | `FeuillePlus` | panier, favoris, promos, aide | 1 |
| Commandes | 4 | `EcranCommandes` | `GET /commandes` | 1 |
| Profil | 5 | `EcranProfil` | `GET /moi` | 1 |

## Mobile livreur — accent violet

| Maquette | Onglet | Écran | Endpoints | Palier |
|---|---|---|---|---|
| Ma course (Express) | 1 | `EcranCourse` | `PATCH /livraisons/{id}/statut`, `POST .../tentative`, `POST .../position` | 1 |
| Disponibles (Express) | 2 | `EcranDisponibles` | `GET /livraisons/disponibles`, `POST .../accepter` | 1 |
| Ma tournée (Standard) | 1 | `EcranTournee` | `GET /tournees/ma-tournee` | 2 |
| Arrêt suivant (Standard) | 2 | `EcranArret` | `PATCH /tournees/{id}/arrets/{id}/statut` | 2 |
| « + » | 3 | `FeuillePlus` | historique, gains, aide | 1 |
| Notifications | 4 | `EcranNotifications` | `GET /notifications` | 1 |
| Profil / disponibilité | 5 | `EcranProfilLivreur` | `PATCH /moi` | 1 |

---

## Ce que les maquettes ne montrent pas, et qu'il faudra concevoir

- Les **écrans de connexion et d'inscription** par rôle, y compris l'écran
  d'attente de validation d'un vendeur ou d'un livreur.
- Les **états de chargement** : les maquettes montrent le plein et le vide, pas
  l'entre-deux.
- Les **erreurs** : plus de stock au paiement, boutique hors rayon après un
  changement d'adresse, session expirée.
- Le **parcours de paiement Stripe** lui-même, qui est en partie une interface
  fournie par Stripe.
- Les **cartes et itinéraires** du livreur, qui dépendent du fournisseur de
  cartographie retenu.
