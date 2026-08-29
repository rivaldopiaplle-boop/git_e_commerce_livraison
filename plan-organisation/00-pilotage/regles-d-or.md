# Règles d'or — comment ce projet se conduit

> Les huit règles que tu as posées, reformulées en règles opposables : chaque
> document du dossier doit pouvoir être confronté à cette page. Si un document
> les contredit, c'est le document qui a tort.

## 1. Je suggère, je n'impose pas

Toute proposition de ma part arrive avec : ce que je recommande, pourquoi, et
ce que ça coûte si on choisit autrement. Une décision n'est actée que quand elle
est écrite dans [journal-decisions.md](journal-decisions.md) avec ta validation.
Tant qu'elle n'y est pas, elle vit dans [questions-ouvertes.md](questions-ouvertes.md).

## 2. Production et usage final d'abord, développement ensuite

Concrètement, avant d'écrire une ligne de code sur une fonctionnalité, on sait :
qui s'en sert, sur quel écran, ce qu'il voit quand ça se passe mal, et comment
ça se déploie. C'est pour ça que les contrats (dossier `03-contrats/`) et les
maquettes (`04-maquettes/`) précèdent le code, et que le déploiement est écrit
en semaine 1 et pas en semaine 10.

Conséquence pratique : **jamais d'écran sans état vide, sans état de chargement
et sans état d'erreur.** Un tableau vide qui ressemble à un bug est un bug.

## 3. Le projet doit se présenter à un recruteur en 10 minutes

Cette règle a un document dédié : [vitrine-et-demonstration.md](../05-execution/vitrine-et-demonstration.md).
Elle impose trois choses au projet lui-même, pas à la fin mais dès le début :

- une **URL publique** qui marche sans rien installer ;
- des **comptes de démonstration** pour chaque rôle, avec des données crédibles
  déjà en place (un catalogue vide ne se démontre pas) ;
- un **parcours de démonstration scripté** : la commande d'un client suivie
  jusqu'à la livraison, en changeant de rôle à l'écran.

## 4. On avance partout à la fois

Docker, backend, front web, front mobile, CI/CD et déploiement progressent
ensemble, par tranches verticales. Une tranche = un bout de fonctionnalité qui
traverse toute la pile, pas une couche entière terminée avant la suivante.

Ordre à l'intérieur d'une tranche : **modèle → endpoint + test → écran web →
écran mobile si le rôle est mobile.** Jamais un écran avant que son endpoint
existe et soit testé.

## 5. Ne jamais réinventer la roue

Avant d'écrire un mécanisme, on cherche s'il existe déjà : Django Admin plutôt
qu'un back-office maison, Stripe Connect plutôt qu'une répartition de paiement
codée à la main, un solveur de tournées existant plutôt qu'un algorithme
maison, `django-allauth`/`simplejwt` plutôt qu'une authentification artisanale.

Corollaire honnête : ne pas réinventer ne veut pas dire tout empiler. Chaque
dépendance ajoutée doit être justifiable en entretien en une phrase.

## 6. Un rôle est soit web, soit mobile — très rarement les deux

| Rôle         | Support                            | Pourquoi                                                       |
| ------------ | ---------------------------------- | -------------------------------------------------------------- |
| Client       | **Web + mobile** (seule exception) | On achète depuis les deux, c'est le métier                     |
| Vendeur      | Web                                | Gestion de catalogue, tableaux, stats — clavier et grand écran |
| Gestionnaire | Web                                | Poste fixe en boutique ou en entrepôt                          |
| Livreur      | Mobile                             | En mouvement, géolocalisation, appareil photo                  |
| Admin        | Web                                | Back-office, arbitrage, tableaux                               |

## 7. Web et mobile se ressemblent, sauf la disposition

Mêmes symboles, même logo, même vocabulaire, mêmes couleurs de statut. Ce qui
change : la disposition (sidebar au web / onglets en bas au mobile) et la
densité. Voir [design-system.md](../04-maquettes/design-system.md).

## 8. Une couleur dominante par rôle, tout le reste identique

| Rôle         | Couleur | Code      |
| ------------ | ------- | --------- |
| Client       | Vert    | `#16a34a` |
| Vendeur      | Bleu    | `#2563eb` |
| Gestionnaire | Sarcelle | `#0d9488` |
| Livreur      | Violet  | `#7c3aed` |
| Admin        | Rouge   | `#b91c1c` |

Ces couleurs sont déjà appliquées dans [maquettes.html](../04-maquettes/maquettes.html).
Elles ne teintent que l'accent (barre active, boutons primaires, badges), jamais
les couleurs de sens : succès, alerte, erreur et information restent les mêmes
pour tout le monde, sinon un rouge d'erreur chez l'admin devient illisible.

## 9. Structure web imposée

Sidebar rétractable à gauche · navbar en haut pour les informations
importantes · panneau droit rétractable (détail, panier, aide) · popups pour les
actions courtes · onglets dans le contenu · listes avec boutons-icônes pour
consulter et gérer.

## 10. Structure mobile imposée

Cinq onglets en bas, du plus important au moins important, le **3ᵉ est un « + »**
qui déplie vers le bas les actions de priorité moyenne. Icône + libellé dessous.
Tout est cliquable ou dépliable, les fonctions se cachent les unes derrière les
autres pour une interface dense.

## 11. Le bon design pattern, au bon moment

Un pattern n'est justifié que par un besoin de variation déjà identifié. Les
patterns retenus et **pourquoi** sont listés dans
[regles-metier.md](../01-produit/regles-metier.md) — pas de pattern décoratif.

## 12. s'inspirer mon project déja realisé et toujours fait mieux

inpire toi toujours du debut a la fin de se qu'on a fait dans C:\Users\HP\Desktop\vscode\trainning\Devops\banque-app
