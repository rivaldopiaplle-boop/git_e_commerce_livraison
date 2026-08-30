# État réel du code — ce qui existe, ce qui manque

> Vérification demandée au bloc H-11 : *« tu relis le dossier `plan-organisation`
> et tu vois si tout colle »*. Ce document est le **relevé du code réel**, pas
> une intention. Il est établi en listant les routes que l'API expose et les
> écrans que le front compile, puis en les confrontant au dossier de conception.
>
> Généré le 30 août, après le premier lot du bloc K.

---

## Ce qui colle

| Décision | Où c'est appliqué | Vérifié par |
|---|---|---|
| **D-01** admin hors du web | `seed_admin`, aucune route publique | 3 tests |
| **D-02** entrée par rôle | inscription client actif, vendeur et livreur en attente | 4 tests |
| **D-03** catalogue et panier sans compte | routes publiques, panier à clé de session, fusion à la connexion | 10 tests |
| **D-04** vendeur ≠ gestionnaire | le personnel ajuste le stock, jamais les prix ni le CA | 5 tests |
| **D-05** deux types de gestionnaire | staff vendeur et staff entrepôt ont des menus et des écrans distincts | smoke API |
| **D-06** rupture : bouton gelé + alerte | fiche produit, et « mettre en rupture » côté vendeur | 2 tests |
| **D-09** rayon Express | absent du catalogue au-delà du rayon | 4 tests |
| **D-10** découpage du panier | `commandes/decoupage.py` | 13 tests |
| **D-11** frais par bandes | `frais_livraison_centimes` | via le découpage |
| **D-13** suppression logique | retirer un produit le masque, et on peut le remettre en vente | 2 tests |
| **D-15** réservation au paiement | `stock_reserve`, jamais décrémenté à l'ajout | 2 tests |
| **D-19** rien de durable sur le disque | Cloudinary actif, repli local documenté | manuel |
| **D-21** adresse partagée | `ADRESSE` reliée client / vendeur / entrepôt, carnet d'adresses client | smoke API |
| **D-24** photos | vérification du contenu réel, EXIF retiré, WebP | 6 tests |
| **D-25** haversine local | `coeur/geographie.py`, aucun appel réseau | 4 tests |
| **D-26** Tailwind + Lucide | tout le front | build |
| **D-29** l'argent visible par rôle | le vendeur voit sa part et la commission, le livreur ses gains | 1 test + smoke |
| **D-32** Django Admin = outil | `/admin/`, jamais lié depuis le produit | — |
| **D-33** accueil = catalogue public | route `/` publique | 16 tests |
| **D-34** panier avant le compte | clé de session, fusion | 10 tests |
| **D-35** facettes sur le résultat filtré | `meta.facettes` | manuel |
| **D-36** CMS sur le contenu, règles d'or sur la structure | une seule coquille | 2 tests |
| **D-38** une seule coquille | catalogue et espaces partagent la même | 2 tests |
| **D-39** panneau droit stable | replié en bande, jamais surgissant | manuel |
| **D-40** un support par rôle | l'espace livreur web sert au suivi et aux gains, pas à l'action | manuel |
| **D-41** la maquette fait foi | sidebar claire, navbar 56 px, filtres dans le contenu, popups | manuel |
| **D-42** session non collante en développement | on enchaîne les comptes librement | manuel |
| **D-43** agent IA planifié | rien en base, prévu derrière une interface | — |
| **D-44** tournées optimisées dès le MVP | arrêts ordonnés en base et à l'écran ; l'algorithme reste à écrire | seed |
| **D-45** promotions vendeur et plateforme | trois promotions de démonstration, dont une expirée | seed |
| **D-46** panneau droit selon le rôle | panier pour qui achète, activité sinon — et l'activité affiche vraiment quelque chose | manuel |
| **D-47** garde-fou sur les jetons CSS | `jetons.test.ts` | 2 tests |
| **D-48** écrans publics en clair | connexion, inscription, attente | 2 tests |
| **D-49** stock en quantité réelle, dans une popup | `nouvelle_quantite` + motif | 3 tests |
| **D-50** le CA ne quitte pas le serveur pour le personnel | `tableau_de_bord_vendeur` | 2 tests |
| **D-51** jeu de données couvrant tous les états | `seed_activite` | manuel |
| **D-52** une seule liste, avec ses boutons-symboles | `Liste.vue` + `ActionLigne.vue`, 10 écrans | 5 tests |
| **D-53** le volet appartient à l'écran | `Volet.vue` + `stores/volet.ts` | manuel |
| **D-54** un panier ne se bloque jamais tout entier | aperçu tolérant, création stricte | 3 tests |
| **D-55** le panier disparaît avec la session | `panier.reinitialiser()` à la déconnexion | manuel |
| **D-56** on ne note que ce qu'on a reçu | `GET/POST /commandes/{id}/avis` | 4 tests |

**131 tests** : 89 backend, 42 front. **34 routes d'API vérifiées une par une**,
avec le rôle attendu et les refus attendus.

### L'interface suit la maquette, pas les CMS

La sidebar est claire (`#fbfbfd`, 210 px, repliée à 64 px), la navbar fait 56 px
avec sa recherche en pastille et son bloc avatar, le panneau droit fait 300 px.
Ni l'une ni l'autre ne défile — seul le contenu défile. **Les filtres sont hors
de la sidebar** et vivent au-dessus de la grille. Les **popups** de la maquette
existent enfin (`Popup.vue`), et les listes utilisent ses **boutons-icônes
encadrés** de 28 px. Ce qui reste des CMS marchands se limite à l'affichage d'un
produit : carte avec survol, galerie, badges d'état.

---

## Ce qui existe, écran par écran

| Rôle | Écrans | État |
|---|---|---|
| Visiteur | catalogue, fiche produit, boutiques, rejoindre, panier, préparation de commande | **fait** |
| Client | + suivi de commandes, **carnet d'adresses**, compte | **fait** |
| Vendeur | tableau de bord à onglets, commandes reçues, catalogue, stock, **personnel**, **statistiques** | **fait** |
| Gestionnaire staff vendeur | à préparer, stock, vue d'ensemble — le CA est **grisé et refusé** | **fait** |
| Gestionnaire staff entrepôt | vue d'ensemble, **colis reçus**, **tournées** | **fait** |
| Livreur | vue d'ensemble, **mes courses, ma tournée, mes gains** (lecture seule) | **fait au web** ; l'action est mobile ([D-40](journal-decisions.md)) |
| Admin | tableau de bord, validations, **boutiques et livreurs**, **utilisateurs**, **litiges**, **journal d'audit** | **fait** |

**56 routes d'API**, **27 écrans web**. Toutes les entrées de barre latérale
mènent à une route réelle : un test le vérifie rôle par rôle.

### Le jeu de données de démonstration

`python manage.py seed_demo` crée 20 comptes, 5 boutiques dans 3 états de
validation, 2 entrepôts, 25 produits, puis `seed_activite` ajoute :

- **15 commandes**, une par statut du modèle, Express et Standard, dont une
  commande Standard multi-vendeur et un panier abandonné avant paiement ;
- **14 livraisons**, dont une échouée après deux tentatives ([D-23](journal-decisions.md)) ;
- **4 tournées** — brouillon, prête, en cours, terminée — avec leurs arrêts ordonnés ;
- **7 avis** dont un signalé, **2 litiges** dont un résolu, des notifications
  lues et non lues, des mouvements de stock sur douze produits ;
- des cas limites voulus : produit retiré de la vente, stock sous le seuil,
  rupture franche, client parisien qu'aucune boutique Express ne livre.

---

## Ce qui manque, et pourquoi c'est assumé

| Manque | Pourquoi ce n'est pas encore là |
|---|---|
| **Paiement Stripe** | La commande se crée et réserve le stock ; le débit viendra brancher `PAIEMENT` et `REPARTITION_VENDEUR`, déjà modélisés et déjà peuplés par le jeu de démonstration. C'est le prochain gros morceau |
| **Faire avancer une livraison ou une tournée** | Les écrans lisent, ils n'agissent pas encore. Une livraison naît d'une commande payée : le paiement passe devant |
| **L'algorithme de tournée** | Les arrêts sont ordonnés en base ; le plus proche voisin ([D-44](journal-decisions.md)) s'écrira avec la tranche livraison |
| **Application mobile** | Ionic + Capacitor, décidé en [D-20](journal-decisions.md) |
| **Paquet `partage/`** | Le code commun aux deux fronts n'a de sens qu'une fois le second front existant |
| **Arbitrage d'un litige** | Rembourser suppose un paiement à rembourser |
| **Envoi réel des notifications** | Elles existent en base et s'affichent dans la cloche et le panneau droit ; l'e-mail et le push viendront avec le service de notification |
| **Géocodage d'une adresse saisie** | Nominatim décidé ([D-25](journal-decisions.md)), pas encore appelé : les adresses de démonstration sont déjà géocodées |

---

## Les défauts trouvés au bloc J, et corrigés

1. **Les écrans publics étaient illisibles.** `PanneauMarque.vue` utilisait
   `bg-encre-2` et `border-encre-3`, deux jetons supprimés du thème : l'aside
   n'avait plus de fond, et tout son texte était blanc sur blanc. Même maladie
   que `.champ` au bloc I. D'où [D-47](journal-decisions.md), qui rend l'erreur
   impossible à commettre en silence.
2. **Le gestionnaire recevait un 403 sur la liste des produits** — son écran de
   stock ne s'ouvrait pas.
3. **Le gestionnaire recevait le chiffre d'affaires** dans la charge utile du
   tableau de bord, contre [D-04](journal-decisions.md).
4. **Le catalogue vendeur ne connaissait ni `est_visible` ni le stock exact** :
   un produit masqué ne pouvait plus être remis en vente.
5. **`stock_reserve` traînait à 3, 7 et 1** sur trois produits sans qu'aucun
   paiement soit en cours : ils apparaissaient en rupture sans raison.
6. **Six photos ne montraient pas le bon produit** (une salade pour une
   baguette, un tissu gris pour une huile d'olive) — remplacées et revérifiées
   à l'œil, planche-contact à l'appui.
