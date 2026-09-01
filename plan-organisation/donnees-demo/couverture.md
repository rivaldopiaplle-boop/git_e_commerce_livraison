# Couverture du jeu de démonstration

> **Ta demande, L-15** : *« crée autant de données que possible pour rendre
> visible chaque scénario et chaque décision »*. C'est la décision
> [D-96](../00-pilotage/journal-decisions.md).
>
> Ce document dit, pour **chacun** des scénarios de
> [`01-produit/scenarios.md`](../01-produit/scenarios.md), ce qui le rend
> visible. Il n'est pas décoratif : `backend/coeur/tests/test_couverture.py`
> échoue si un scénario disparaît de ce tableau, et
> `python manage.py verifier_couverture` interroge la base réelle pour dire
> lesquels n'ont plus rien à montrer.

---

## Les trois façons d'être couvert

Un scénario ne se démontre pas toujours par une donnée, et prétendre le
contraire serait malhonnête.

| Genre | Ce que ça veut dire | Ce qui le vérifie |
|---|---|---|
| **donnée** | une ligne existe en base, l'écran la montre | `manage.py verifier_couverture` |
| **règle** | un comportement que le serveur **refuse**. Il n'y a rien à peupler : un refus ne se met pas en vitrine | un test nommé dans la colonne |
| **absent** | pas encore écrit. Le dire vaut mieux que de le laisser croire couvert | — |

---

## Le tableau

### 3 — Cycle de vie nominal

| # | Scénario | Genre | Ce qui le rend visible |
|---|---|---|---|
| 3.1 | Flux Express | donnée | 18 commandes Express, du panier à la remise |
| 3.2 | Flux Standard | donnée | 15 commandes Standard, entrepôt et tournée compris |

### 4 — Produit et stock

| # | Scénario | Genre | Ce qui le rend visible |
|---|---|---|---|
| 4.1 | Produit disponible | donnée | 22 produits en vente, plus 2 ruptures franches (« Clavier mécanique », « Tarte du jour ») |
| 4.2 | Stock à 0 pendant que l'article est au panier | règle | `test_paiement.py::test_revenir_payer_quand_le_stock_est_parti_refuse_proprement` |
| 4.3 | Le prix change pendant qu'un panier est actif | règle | `test_panier.py` — le prix capturé sert à signaler, celui du produit fait foi |
| 4.4 | Écart entre stock réel et stock système | donnée | 10 mouvements d'ajustement, chacun avec son motif |
| 4.5 | Produit retiré alors qu'il est dans des paniers | donnée | « Lunettes de soleil polarisées », `est_visible = faux` |

### 5 — Panier

| # | Scénario | Genre | Ce qui le rend visible |
|---|---|---|---|
| 5.1 | Navigation sans compte | règle | `test_panier.py` — panier à clé de session, fusion à la connexion |
| 5.2 | Panier abandonné | règle | `test_paiement.py::test_une_reservation_abandonnee_expire_et_rend_le_stock` |
| 5.3 | Panier à plusieurs vendeurs | donnée | 4 commandes multi-vendeur |
| 5.4 | Panier mixte Express + Standard | règle | `test_decoupage.py` — 13 tests sur la règle D-10 |
| 5.5 | Changement d'adresse, boutique hors rayon | règle | `test_catalogue.py` — le rayon écarte au lieu de trier |

### 6 — Commande

| # | Scénario | Genre | Ce qui le rend visible |
|---|---|---|---|
| 6.1 | Annulation par la cliente | donnée | 1 commande annulée, avec son historique de statuts |
| 6.2 | Annulation par le vendeur | absent | le vendeur avance une commande, il ne l'annule pas encore |
| 6.3 | Adresse modifiée après commande | absent | à écrire avec la prise en charge par le livreur |
| 6.4 | Commande jamais prise en charge | absent | demande une tâche planifiée, écartée au MVP (D-19) |
| 6.5 | Sous-commandes d'une commande multi-vendeur | donnée | 37 sous-commandes, chacune suivie par son vendeur |

### 7 — Paiement

| # | Scénario | Genre | Ce qui le rend visible |
|---|---|---|---|
| 7.1 | Paiement refusé | donnée | 13 commandes en attente de paiement, repayables |
| 7.2 | Confirmation non reçue | donnée | 17 paiements confirmés **par le serveur** (D-12) |
| 7.3 | Remboursement | donnée | 1 commande remboursée, et un litige résolu qui l'explique |
| 7.4 | Répartition entre vendeurs | donnée | 21 répartitions, commission déduite |
| 7.5 | Fraude suspectée | absent | rien à détecter tant que le paiement est simulé (D-18) |

### 8 — Livraison

| # | Scénario | Genre | Ce qui le rend visible |
|---|---|---|---|
| 8.1 | Client absent | donnée | 1 livraison en échec, deux tentatives comptées |
| 8.2 | Contacter le client | absent | numéro masqué : service payant, hors MVP |
| 8.3 | Aucun livreur n'accepte | absent | demande l'élargissement progressif de zone |
| 8.4 | Le livreur abandonne | règle | `test_cycle_livraison` — la course repart au vivier |
| 8.5 | Deux livreurs acceptent en même temps | règle | `test_livreur.py` — `select_for_update`, 409 au second |
| 8.6 | Colis endommagé ou incomplet | donnée | 5 litiges, dont 2 pour colis incomplet |
| 8.7 | Adresse introuvable | absent | même traitement que 8.1, à écrire |
| 8.8 | Retard sur l'estimation | absent | demande une tâche planifiée |
| 8.9 | Attribution des courses | donnée | 8 courses attribuées, Express et Standard |

### 9 — Entrepôt et tournées

| # | Scénario | Genre | Ce qui le rend visible |
|---|---|---|---|
| 9.1 | Colis reçu à l'entrepôt | donnée | 1 colis reçu, visible côté client et côté vendeur |
| 9.2 | Constituer une tournée | donnée | 1 tournée prête, arrêts ordonnés |
| 9.3 | Démarrer une tournée | donnée | 1 tournée en cours |
| 9.4 | Colis trop longtemps en entrepôt | absent | demande une tâche planifiée |

### 10 — Compte et rôles

| # | Scénario | Genre | Ce qui le rend visible |
|---|---|---|---|
| 10.1 | Livreur désactivé pendant une course | règle | `test_livreur.py` — 409 : on ne se met pas hors ligne en pleine course |
| 10.2 | Mot de passe oublié en plein paiement | absent | la réinitialisation par e-mail demande un service d'envoi |
| 10.3 | Vendeur suspendu | donnée | « Morvan Primeurs », suspendue, catalogue invisible |
| 10.4 | Session expirée pendant une action | règle | `preuve-partage.test.ts` — le client d'API rejoue après renouvellement |
| 10.5 | Création et suppression de rôles | donnée | 4 comptes de personnel ; `test_personnel.py` pour la suspension |

### 11 — Promotions

| # | Scénario | Genre | Ce qui le rend visible |
|---|---|---|---|
| 11.1 | Code expiré ou déjà utilisé | donnée | 3 promotions, dont une expirée et une épuisée |
| 11.2 | Deux promotions non cumulables | absent | l'application d'un code au panier reste à écrire |
| 11.3 | Promotion sur commande annulée | absent | même raison |

### 12 — Avis

| # | Scénario | Genre | Ce qui le rend visible |
|---|---|---|---|
| 12.1 | Avis avant livraison | règle | `test_panier_et_avis.py` — le bouton n'apparaît qu'après `LIVREE` |
| 12.2 | Avis signalé comme abusif | donnée | 1 avis en modération |
| 12.3 | Trois cibles distinctes | donnée | des avis sur produit, boutique **et** livreur |

### 13 — Notifications

| # | Scénario | Genre | Ce qui le rend visible |
|---|---|---|---|
| 13.1 | Push désactivé | règle | tout est consultable dans l'application ; le push n'existe pas encore |
| 13.2 | Tous les rôles sont notifiables | donnée | 3 rôles différents ont reçu une notification |

### 14 — Admin et litiges

| # | Scénario | Genre | Ce qui le rend visible |
|---|---|---|---|
| 14.1 | Litige entre une cliente et un vendeur | donnée | 3 litiges en instruction, les deux versions côte à côte |
| 14.2 | Validation d'un nouveau vendeur | donnée | « L'Atelier Camille », en attente de validation |

### 15 — Sécurité et permissions

| # | Scénario | Genre | Ce qui le rend visible |
|---|---|---|---|
| 15.1 | Commande d'un autre | règle | `test_paiement.py::test_on_ne_paie_pas_la_commande_d_un_autre` — 404, jamais 403 |
| 15.2 | Livraison non attribuée | règle | `test_livreur.py` — 404 quand un autre livreur essaie |
| 15.3 | Gestionnaire et chiffre d'affaires | règle | `test_espaces_par_role.py` — refusé côté serveur, absent de l'interface |

---

## Au-delà des scénarios écrits

Ce qui n'est demandé nulle part mais sans quoi une démonstration sonne creux.
Ces contrôles portent un `+` dans `verifier_couverture` pour qu'on ne les
prenne jamais pour des numéros du dossier produit.

| Contrôle | Ce qu'il garantit |
|---|---|
| `+ factures` | des factures existent, donc l'écran imprimable a quelque chose à imprimer |
| `+ livraisons-terminees` | l'historique du livreur n'est pas vide |
| `+ avis-livreur` | la troisième cible d'avis est réellement utilisée |
| `+ compte-suspendu` | l'écran des utilisateurs montre les deux états |
| `+ litige-vendeur-entendu` | l'instruction contradictoire se voit (D-94) |
| `+ litige-rembourse` | un remboursement partiel, la vente tient encore |
| `+ litige-rejete` | le versement au vendeur a repris son cours |

---

## Comment s'en servir

```
python manage.py verifier_couverture            # dit ce qui manque
python manage.py verifier_couverture --strict   # sort en erreur : pour la CI
```

Si un scénario ressort **vide**, dans cet ordre :

```
DEMO_AUTORISEE=1 python manage.py seed_demo
DEMO_AUTORISEE=1 python manage.py seed_catalogue
DEMO_AUTORISEE=1 python manage.py seed_activite --refaire
```

`seed_catalogue` **repose** les cas limites même sur un catalogue déjà en
place — un produit remis en vente à la main pendant un essai redevient invisible,
une rupture retombe à zéro. Cette idempotence manquait, et un seul essai à
l'écran suffisait à perdre définitivement un scénario.
