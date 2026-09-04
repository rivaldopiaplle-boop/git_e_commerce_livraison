# État réel du code — ce qui existe, ce qui manque

> Vérification demandée au bloc H-11 : *« tu relis le dossier `plan-organisation`
> et tu vois si tout colle »*. Ce document est le **relevé du code réel**, pas
> une intention. Il est établi en listant les routes que l'API expose et les
> écrans que le front compile, puis en les confrontant au dossier de conception.
>
> Mis à jour le 4 septembre, après le relevé du mobile (bloc N).

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
| **D-12** confirmation par le serveur | `POST /paiements/confirmation`, ouverte et idempotente | 3 tests |
| **D-15** réservation à la commande, jamais au panier | `commandes/reservation.py`, seul auteur du compteur | 18 tests |
| **D-18** services externes derrière une interface | `PaiementSimule`, `AssistantSimule`, bascule par variable | 15 tests |
| **D-94** litige contradictoire | ouverture, réponse sous 48 h, arbitrage motivé, remboursement | 21 tests |
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
| **Le vrai Stripe** | Le parcours de paiement est **complet** avec le simulateur : intention, réservation, capture, répartition par vendeur, facture, remboursement du stock en cas de refus. `PaiementStripe` reste volontairement non implémenté : du code qu'on ne peut ni lancer ni tester donne une fausse impression d'avancement, et il faudrait le réécrire face à l'API réelle |
| **L'algorithme de tournée** | Les arrêts sont ordonnés en base ; le plus proche voisin ([D-44](journal-decisions.md)) s'écrira avec la tranche livraison |
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


---

## La tranche paiement, et le défaut qu'elle a révélé

Écrite en fin de bloc L, vérifiée deux fois : par un script qui parle à l'API
en réseau **et** lit la base directement — le seul moyen de prouver qu'une
réservation existe vraiment entre l'ouverture du paiement et sa capture — puis
par 18 tests permanents.

### Ce que le code fait maintenant

| Étape | Route | Ce qui bouge en base |
|---|---|---|
| Créer la commande | `POST /commandes` | `stock_reserve` **+n**, `stock_reserve_pose = vrai` |
| Ouvrir le paiement | `POST /commandes/{id}/paiement` | un `PAIEMENT` en attente ; **rien de plus** si la réserve tient déjà |
| Confirmer (serveur) | `POST /paiements/confirmation` | `stock_disponible` **−n**, `stock_reserve` **−n**, un `MOUVEMENT_STOCK` VENTE, une `REPARTITION_VENDEUR` par boutique, une `FACTURE`, commande `PAYEE` |
| Paiement refusé | même route | réserve rendue, commande **toujours payable** |
| Renoncer | `POST /commandes/{id}/paiement/abandonner` | réserve rendue tout de suite |
| Expiration | `manage.py liberer_reservations` | réserve rendue au bout de 10 minutes |

### Le défaut trouvé, et son étendue

`stock_reserve` était écrit à **deux endroits** — `commandes/decoupage.py` à la
création, `paiements/views.py` à l'ouverture du paiement — et relâché à un
seul. Chaque commande payée laissait une réserve fantôme, jamais rendue.

Corrigé au-delà du cas :

- **un seul module écrit ce compteur** (`commandes/reservation.py`,
  [D-99](journal-decisions.md)), et le drapeau `Commande.stock_reserve_pose`
  rend `poser`, `relacher` et `consommer` rejouables sans dégât ;
- **la migration `0003` répare les bases existantes** : elle lève le drapeau
  sur les commandes en attente, puis **recompte** chaque `stock_reserve` depuis
  les commandes qui le justifient. Sans elle, une base de développement aurait
  gardé ses fantômes pour toujours ;
- **`seed_activite` ne remet plus les compteurs à zéro** : il les recompte. Sa
  vieille règle — « aucune réservation n'est légitime tant que le paiement
  n'existe pas » — était devenue fausse le jour où le paiement a existé, et
  effacer une réservation valable ferait vendre deux fois le même exemplaire ;
- **la réservation expire** ([D-100](journal-decisions.md)), et `demarrer.py`
  applique l'expiration au lancement.

### Ce que les tests verrouillent

Une phrase : **le compteur revient toujours à sa valeur de départ**, quel que
soit le chemin — capture, refus, abandon, double abandon, webhook rejoué,
retour du client sur une commande abandonnée, ou stock parti entre-temps.


---

## Le cycle du litige, écrit en entier

Tu l'appelais *« le moins réfléchi »* au bloc L-8. Il l'était : l'écran
d'arbitrage était en lecture seule, et il ne pouvait pas être autre chose —
rembourser suppose un paiement à rembourser. Le paiement existe, donc le cycle
existe.

### Les quatre temps, et où ils vivent

| Temps | Route | Qui | Effet en base |
|---|---|---|---|
| Ouverture | `POST /commandes/{id}/litiges` | client | `LITIGE` **OUVERT**, échéance à +48 h, `REPARTITION_VENDEUR` → **BLOQUE**, vendeur notifié |
| Réponse | `POST /litiges/{id}/reponse` | vendeur | `reponse_vendeur`, statut **EN_COURS**, client notifié |
| Arbitrage | `POST /admin/litiges/{id}/arbitrer` | admin | **RESOLU** ou **REJETE**, `REMBOURSEMENT` écrit, versement débloqué |
| Notification | — | — | les **deux** parties reçoivent la même décision |

### Les trois garde-fous, et l'abus que chacun répare

1. **On ne tranche pas avant que le vendeur ait pu répondre** (409
   `vendeur_pas_encore_entendu`). Sans ce refus, la procédure contradictoire
   n'est qu'un décor. Passé le délai, on tranche quand même : un vendeur
   silencieux ne bloque pas un client indéfiniment.
2. **Une décision est toujours motivée**, y compris favorable au client (400
   `motivation_requise`). Elle doit s'expliquer six mois plus tard.
3. **On ne rembourse pas plus que ce qui a été payé**, remboursements
   antérieurs compris (400 `montant_invalide`).

### Ce qui manquait le plus, et qui n'était pas du code

**L'écran du vendeur n'existait pas.** Un client pouvait ouvrir un litige, un
administrateur pouvait le trancher, et la boutique n'avait aucun endroit où
donner sa version. `/espace/litiges-boutique` répare cela
([D-104](journal-decisions.md)).

### Ce que le jeu de démonstration montre

Les **cinq états** côte à côte, sans rien à fabriquer à la main : délai en
cours, délai dépassé, boutique entendue, résolu avec remboursement partiel,
rejeté — et le versement au vendeur cohérent avec chacun (`BLOQUE`,
`REMBOURSE`, `TRANSFERE`). Une première version les posait par rang dans la
liste des commandes livrées, et le cinquième état disparaissait en silence dès
qu'il y en avait moins de quatre ; le compte est désormais vérifié, et un
manque se dit à l'écran de peuplement.

### Ce qui reste

- **`POST /paiements/{id}/rembourser` en direct** (hors litige) : un
  remboursement commercial sans réclamation. Rien ne le demande aujourd'hui ;
- **les pièces jointes** : `preuves_urls` accepte des URL, mais aucun écran ne
  téléverse encore de photo. C'est le prolongement naturel du dossier.


---

## Les quatre dernières listes, converties

Tu demandais les boutons-symboles **sur toutes les listes de tous les rôles**
(bloc K-1). Le relevé du bloc K en laissait quatre : validations, litiges,
personnel, adresses. Les quatre passent désormais par `Liste.vue` — recherche,
tri, pagination, état vide rédigé, boutons-symboles encadrés.

La conversion n'a pas été qu'un habillage : **deux vrais défauts** sont
apparus en la faisant, et c'est en général ce qui arrive quand on regarde un
écran de près.

| Écran | Ce qui manquait vraiment | Corrigé par |
|---|---|---|
| **Litiges (admin)** | l'arbitrage n'existait pas — l'écran ne savait que lire | [D-94](journal-decisions.md), [D-103](journal-decisions.md) |
| **Litiges (vendeur)** | l'écran n'existait pas du tout | [D-104](journal-decisions.md) |
| **Mon personnel** | on créait des comptes sans jamais pouvoir en retirer un | [D-106](journal-decisions.md) |
| **Mes adresses** | on effaçait sans confirmation, et on ne pouvait pas corriger | [D-107](journal-decisions.md) |

### Le décompte des tests

| | Bloc K | Aujourd'hui |
|---|---|---|
| Backend | 89 | **136** |
| Front web | 50 | **57** |

Les 47 tests de plus portent tous sur ce qui vient d'être écrit : le paiement
et sa réservation (18 + 7), le cycle du litige (21), la gestion du personnel
(8).


---

## La couverture du jeu de données, désormais vérifiable

`python manage.py verifier_couverture` interroge la base réelle et rend
34 lignes, une par scénario illustrable. `coeur/tests/test_couverture.py` garde
le document et la commande synchronisés. La CI enchaîne les deux : elle peuple
une vraie base, puis appelle `verifier_couverture --strict`.

Ce second point vaut plus qu'il n'en a l'air : **les commandes de peuplement
n'étaient dans aucun test**. Elles écrivent en base, ce qu'un test ne fait pas,
et cassaient donc en silence — un champ renommé, une contrainte ajoutée, et la
démonstration ne se monte plus. On ne s'en apercevait que le jour où on en avait
besoin.

### Ce que le contrôle a trouvé le jour même

| Défaut | Ce qu'il coûtait | Corrigé par |
|---|---|---|
| `seed_catalogue` n'appliquait ses cas limites qu'à la création | un essai à l'écran effaçait un scénario **pour toujours** | [D-109](journal-decisions.md) |
| aucune boutique en attente de validation | l'écran de validation de l'admin était vide | `seed_demo` |
| aucune boutique ni aucun compte suspendu | deux scénarios sur trois de la section 10 invisibles | `seed_demo` |
| commander créait une adresse à chaque fois | 14 adresses identiques dans le carnet de Léa | [D-110](journal-decisions.md) |

### L'état actuel

Les 34 contrôles sont verts. Le tableau
[`donnees-demo/couverture.md`](../donnees-demo/couverture.md) couvre les
53 scénarios du dossier produit : **26 par une donnée**, **15 par une règle
testée**, **12 déclarés absents** avec leur raison.

Déclarer un scénario absent n'est pas un aveu de faiblesse : les douze le sont
pour deux raisons seulement — une tâche planifiée qu'on n'héberge pas au MVP
([D-19](journal-decisions.md)), ou un service payant qu'on ne branche pas
([D-18](journal-decisions.md)).


---

## Les médias d'une fiche produit

Le modèle prévoyait six photos depuis [D-24](journal-decisions.md), le
peuplement n'en posait **qu'une**. Chaque produit en a désormais **quatre**,
plus un aperçu animé.

| Média | Comment il est obtenu | Poids |
|---|---|---|
| Photo d'ensemble | téléchargée, ou fabriquée hors ligne | ~50 Ko |
| Détail, matière, mise en situation | **recadrages** de la photo source | ~35 Ko chacun |
| Aperçu animé | WebP animé, 8 images, lent zoom aller-retour | ~100 Ko |

Deux honnêtetés à garder en tête, et elles sont écrites dans le code :

- **les trois vues supplémentaires sont dérivées**, pas photographiées. Ce que
  la démonstration prouve, c'est que la galerie, ses vignettes, ses flèches et
  sa navigation au clavier fonctionnent ;
- **l'aperçu n'est pas une vidéo.** `ffmpeg` n'est pas disponible et le projet
  doit tourner sans dépendance externe ([D-112](journal-decisions.md)). Le
  champ `Produit.video_url` accepte les deux, et `apercu.genre` dit au front
  lequel il reçoit.

Total sur disque : **6,4 Mo** pour 25 produits, soit 125 fichiers. Le dossier
`backend/media/` n'est pas versionné ; en ligne, Cloudinary les sert
([D-19](journal-decisions.md)).

### Un défaut trouvé dans le même passage

Les écrans publics utilisaient les couleurs brutes de Tailwind là où tout le
reste du projet passe par les jetons de la maquette. Le badge du mode de
livraison s'écrivait `text-amber-300` sur `bg-amber-500/15` : **du clair sur du
clair**, exactement la maladie du bloc J. Les quatre écrans publics sont
convertis ([D-113](journal-decisions.md)).


---

## La coquille : ce qu'elle dit maintenant

| Élément | Avant | Maintenant |
|---|---|---|
| Barre latérale | 9 entrées à plat | 3 sections nommées, **pastilles** sur ce qui attend |
| Barre latérale repliée | des icônes muettes | un point sur les icônes et les sections concernées |
| Barre haute | « Espace vendeur » | fil d'Ariane `Espace vendeur › Vendre › Commandes reçues` |
| Recherche | un champ | le raccourci `/`, **écrit dans le champ** |

Les compteurs viennent d'un seul appel, `GET /moi/compteurs`, indexé par nom
de route. C'est ce qui garde la barre latérale bête : elle affiche
`compteurs[entree.route]` sans rien savoir des métiers.

### Ce que chaque rôle compte

| Rôle | Pastilles |
|---|---|
| Client | commandes à payer, litiges en cours |
| Vendeur | commandes à préparer, produits sous le seuil, litiges sans réponse |
| Personnel vendeur | commandes à préparer, stock — **jamais les litiges** ([D-04](journal-decisions.md)) |
| Gestionnaire entrepôt | colis reçus, tournées prêtes sans livreur |
| Livreur | courses en cours |
| Admin | validations, litiges **arbitrables**, demandes d'identité |

Le cloisonnement est vérifié par 10 tests : un vendeur ne compte que ses
commandes, et l'administrateur ne compte que les litiges qu'il a le droit de
trancher ([D-103](journal-decisions.md)).


---

## Le tableau de bord, les graphiques, et un bandeau rouge

### Le défaut le plus grave, et il ne se voyait dans aucun test

**PrimeVue 5 exige une clé de licence.** Sans elle, il injecte dans la page un
`<div>` fixe en bas à droite, fond rouge : « Invalid PrimeUI License ». Vérifié
dans le build de production, pas supposé.

Le projet est repassé en **PrimeVue 4 (MIT)** : mêmes composants, aucune clé,
aucune expiration ([D-117](journal-decisions.md)). Le build y gagne 42 Ko au
passage. Trois tests verrouillent la décision, dont un qui lit la bibliothèque
installée et échoue si le message y réapparaît.

### Le tableau de bord

Chaque indicateur est désormais un **lien**, et `Indicateur.route` n'est pas
facultatif dans le type : on ne peut plus ajouter un chiffre sans dire où il
mène ([D-118](journal-decisions.md)). Les alertes emmènent sur le bon
**onglet**, pas seulement sur le bon écran.

### Les graphiques

Trois, sur `Chart` de PrimeVue, là où il n'y avait qu'une courbe dessinée à la
main en `<div>` de hauteur variable :

| Graphique | Type | Ce qu'il répond |
|---|---|---|
| Chiffre d'affaires par jour | courbe, deux axes | montant **et** nombre de commandes |
| Part de chaque produit | anneau | ce qui fait vivre la boutique |
| Répartition des notes | barres horizontales | ce qu'une moyenne cache |

`src/graphiques.ts` porte les réglages communs — couleurs, grille, format des
infobulles. Trois graphiques réglés séparément finissent toujours par se
contredire.

### Une dépendance qui ne s'installait plus

`@vee-validate/zod` exige `zod` 3, le projet avait `zod` 4. L'application se
construisait — le fichier de verrou datait d'avant — mais **tout `npm install`
d'un nouveau paquet échouait**. Corrigé, et un test compare désormais la
contrainte déclarée par l'adaptateur à la version installée, sans coder aucun
numéro en dur ([D-120](journal-decisions.md)).

### La validation des formulaires, enfin branchée

`vee-validate` et `zod` étaient installés et **utilisés nulle part** — le
reproche exact du bloc K. `src/validation.ts` porte désormais les règles, et
deux écrans s'en servent : connexion et inscription.

| Ce qui change | Avant | Maintenant |
|---|---|---|
| Quand l'erreur apparaît | au retour du serveur | quand on quitte le champ |
| Un formulaire invalide | partait quand même | ne part pas |
| Où se pose l'erreur serveur | bandeau général | **sous le champ concerné** |
| La règle du mot de passe | 10 ici, 8 là, rien ailleurs | une seule définition |

Trois choses à ne pas perdre de vue :

- **le serveur reste seul juge.** Ces règles doublent les siennes pour le
  confort ; une validation qui n'existe que dans le navigateur ne protège de
  rien ;
- **`ChampTexte` marche des deux façons** — piloté par le formulaire avec un
  `nom`, `v-model` ordinaire sinon. La migration se fait écran par écran ;
- **la connexion ne vérifie pas la longueur du mot de passe** : il existe déjà,
  et lui reprocher sa forme quand quelqu'un essaie d'entrer est une façon de le
  perdre.

Reste à convertir : les formulaires de popup (adresse, création de compte
employé, réponse à un litige). Ils valident encore à la main, mais ils sont
courts et leurs règles sont dans `validation.ts`, prêtes à servir.


---

## L'adresse de livraison suit enfin la chaîne

Le client saisissait une adresse et des instructions, et **personne ne les
voyait ensuite**. Le vendeur ne savait même pas dans quelle ville partait son
colis.

`coeur/adresses.py` porte le cloisonnement, en une seule fonction appelée par
toutes les vues. Vérifié en direct sur les trois rôles :

| Rôle | Ce que l'API lui renvoie vraiment |
|---|---|
| Vendeur | `{ville: "Lyon", code_postal: "69002"}` |
| Entrepôt | `+ rue: "22 rue Sebastien Gryphe", zone: "Lyon et couronne"` |
| Livreur | `+ complement, instructions, latitude, longitude` |

Le rôle vient du **contexte du sérialiseur**, posé par la vue : sans cela la
même sérialisation servait le livreur et le gestionnaire d'entrepôt, et le
second recevait les instructions de porte du client.

Une nuance assumée par rapport à [D-74](journal-decisions.md) : l'entrepôt voit
la **rue**, que D-74 ne lui donnait pas. Monter une tournée sans les rues
reviendrait à ordonner les arrêts au hasard ([D-123](journal-decisions.md)).


---

## Le vendeur et son personnel

Tu disais qu'ils *« se marchent sur les pieds »*. En le vérifiant, le défaut
s'est révélé plus profond que l'affichage.

### Un défaut de modélisation

Faire avancer une préparation écrivait dans l'historique
`type_objet="COMMANDE"`, avec un **statut de préparation** et l'identifiant de
la **commande**. Sur une commande Standard à trois boutiques, les trois
vendeurs y écrivaient trois statuts sans rapport entre eux, sur la même ligne
d'objet ([D-124](journal-decisions.md)).

Corrigé au-delà du cas : `_synchroniser_commande` faisait passer la commande de
« payée » à « prête » **en silence**, contre [D-95](journal-decisions.md). Elle
écrit désormais sa propre ligne d'historique.

### Ce que chacun voit de l'autre

| Écran | Ce qui apparaît |
|---|---|
| Commandes reçues | « Nadia, il y a 2 h » sous chaque ligne déjà touchée |
| Mon personnel | commandes préparées, ajustements faits, dernière action |
| Barre latérale | la pastille descend quand l'un des deux a préparé |

Le compte se fait en **une requête pour toute la liste**. Une requête par ligne
serait invisible sur cinq commandes et insupportable sur trois cents.

Dix tests verrouillent l'ensemble, dont trois sur le cloisonnement : un vendeur
ne fait pas avancer la part d'une autre boutique (404), il ne voit que son
propre personnel, et une commande Standard ne passe « prête » que lorsque
**toutes** ses parts le sont.


---

## Le volume du jeu de démonstration

| | Bloc L | Bloc M |
|---|---|---|
| Comptes | 20 | **30** |
| Produits | 24 | **59** |
| Commandes | 15 | **85** |
| Livraisons | 14 | **70** |
| Avis | 7 | **30** |
| Mouvements de stock | 10 | **61** |

Les 15 commandes scénarisées sont **inchangées** : elles portent la couverture
des scénarios, et `verifier_couverture --strict` reste vert. Les 70 autres
remplissent autour, sur soixante jours avec une densité récente, et chacune
entraîne sa livraison et parfois un avis.

Vérifié sur base neuve : la chaîne complète `migrate → seed_admin → seed_demo`
(qui enchaîne lui-même catalogue et activité) produit les 85 commandes et passe
le contrôle de couverture.

### Les photos : ce qui a échoué, et ce qu'on affiche à la place

34 téléchargements tentés, **25 échecs**, et parmi les 9 réussites plusieurs
photos qui ne montraient pas le bon objet. Une photo fausse fait douter de tout
le catalogue ([D-131](journal-decisions.md)).

Le peuplement fabrique donc une vignette assumée — nom, univers, couleurs de la
maquette. Les 24 photos réelles vérifiées à l'œil au bloc J sont conservées.
`donnees-demo/images/<slug>.jpg` prime sur tout : déposer un fichier suffit à
remplacer une vignette.


---

## La documentation de lancement et de déploiement

Deux fichiers, écrits à partir de ce qui a été **vérifié en marche**, pas de ce
qui devrait marcher :

- `frontend-mobile/LISEZ-MOI.md` — une seule application mobile, deux rôles,
  du navigateur au téléphone à l'APK, avec les pièges dans l'ordre où on les
  rencontre ;
- `deploiement/LISEZ-MOI.md` — Neon, Render, Vercel, Cloudinary, l'APK, et une
  section entière de pièges dont chacun a réellement coûté du temps.

### Deux défauts trouvés en les écrivant

| Défaut | Ce qu'il coûtait | Corrigé par |
|---|---|---|
| Le port 5174 absent de `CORS_ORIGINS` | l'application mobile ne pouvait rien lire de l'API, **sans aucune erreur visible** | [D-133](journal-decisions.md) |
| Trois variables mal nommées dans `render.yaml` | mise en ligne servant un front vide, photos perdues au redéploiement | [D-134](journal-decisions.md) |

Le second est le plus sournois : **un nom de variable qui ne correspond pas
n'échoue jamais bruyamment.** La valeur par défaut s'applique, et rien ne le
signale.

`coeur/tests/test_variables_environnement.py` compare désormais dans les deux
sens ce que le code lit et ce que la configuration propose. Vérifié par
injection : sans les corrections, trois des quatre tests échouent et nomment les
cinq variables fautives.


---

## Le mobile, relevé écran par écran (bloc N)

**Ta demande N-5** : *« fais attention que le mobile a tout ce qui devait
avoir »*. Le relevé a été fait en confrontant les routes de l'API aux appels
réellement écrits dans `frontend-mobile/src`, pas en relisant les intentions.

### Ce qui manquait, et qui existe maintenant

| Manque | Gravité | Où c'est |
|---|---|---|
| **Commander** — le bouton du panier ne faisait que naviguer | **le parcours s'arrêtait au panier** | `vues/Commander.vue` |
| Donner son avis | le web l'avait, pas le téléphone | `vues/Commandes.vue` |
| Signaler un problème | idem | `vues/Commandes.vue` |
| Le reçu détaillé | idem | `vues/Commandes.vue` |
| Lire ses notifications | absent alors que c'est l'appareil qui les reçoit | `vues/Profil.vue` |
| Changer son mot de passe | absent | `vues/Profil.vue` |
| Le commutateur de notifications | **présent mais décoratif** | `vues/Profil.vue` |

Le dernier est le plus instructif : un `:checked="true"` sans gestionnaire. Il
basculait à l'écran, n'enregistrait rien, et revenait à sa position d'origine au
rechargement. Ni les types, ni la compilation, ni une relecture rapide ne
voient ce genre de manque.

### Ce qui était déjà complet

Le **livreur** a ses quatre gestes — accepter, récupérer, livrer, signaler une
absence — plus la disponibilité et la position. Ils passent tous par
`magasins/livreur.ts` et tapent les routes correspondantes de
`backend/livraisons/urls.py`. Rien ne manquait de ce côté.

### Vérifié en marche, pas seulement compilé

| Ce qui a été exercé contre l'API vivante | Résultat |
|---|---|
| Panier → commande → paiement, depuis le mobile | `RD-260904-8BB570` → `CAPTURE` → `PAYEE`, panier vidé |
| `GET` puis `POST /commandes/{id}/avis` | 3 cibles notables, note enregistrée et relue |
| `POST /commandes/{id}/litiges` | refus argumenté sous 20 caractères, `201 Ouvert` au-delà |
| `GET` / `PATCH /moi/parametres` | la bascule est relue après un aller-retour |
| `POST /moi/mot-de-passe` | mauvais ancien refusé, mot de passe faible refusé, changement puis retour |
| `GET /commandes/{id}/facture` | 4 commandes, tous statuts, lignes et total cohérents |

Les données de démonstration ont été **remises dans leur état d'origine** après
ces essais : le litige et les avis créés pour l'occasion ont été retirés, et la
répartition vendeur remise en `TRANSFERE`.

### Les gardes

`frontend-mobile/src/qualite.test.ts` — 32 tests. Ils ne montent pas d'écran :
ils **relisent la source**, parce que ce qu'on cherche est un manque, et qu'un
manque ne lève aucune erreur. Vérifiés par injection : en remettant le
commutateur décoratif et le bouton de panier qui navigue, deux tests échouent
et les nomment.

`npm test` tourne désormais dans la CI, aux côtés de la vérification des types
et de la compilation.


---

## Les médias du catalogue, après le bloc N-1

Relevé sur la base de démonstration, 59 produits :

| Nombre de vues | Produits |
|---|---|
| 1 seule photo | **35** |
| 2 vues | 9 |
| 3 vues | 9 |
| 4 vues | 5 |
| aucune (produit créé à la main sans image) | 1 |

**11 produits sur 59** ont un aperçu animé. Avant, c'était 58 sur 59, tous avec
exactement quatre vues.

Le dossier `backend/media/produits/` est passé de **8,9 Mo à 2,6 Mo** : les
recadrages et les zooms pesaient plus que le catalogue lui-même.

Vingt produits ont une **vraie photo** sous licence libre. Ils gardent cette
photo seule : on n'accole pas de schémas à une photographie. Les trente-huit
autres ont une vignette dessinée, et leurs vues complémentaires sont dessinées
dans le même langage visuel.

`catalogue/tests/test_medias_produit.py` — 7 tests — verrouille les trois
règles : le profil varie, une photographie reste seule, et deux vues ne se
ressemblent jamais comme deux recadrages. Le dernier compare réellement les
images pixel à pixel.


---

## Les services externes, service par service (bloc N)

| Service | Sans clé | Avec clé | Variable |
|---|---|---|---|
| Paiement | simulateur, aucun débit | Stripe en mode test | `STRIPE_SECRET_KEY` |
| **Assistant** | base de connaissances écrite à la main | **Mistral**, borné à cette base | `CLE_MODELE_IA` |
| **Itinéraire** | vol d'oiseau majoré, tracé en pointillés | **OpenRouteService**, vraies rues | `CLE_ITINERAIRE` |
| **Fond de carte** | **OpenFreeMap, sans clé** | style MapTiler ou autre | `VITE_STYLE_CARTE` |
| Photos | fichiers locaux | Cloudinary | trois variables |

`GET /api/v1/services` dit lequel tourne réellement, à l'écran. C'est utile en
entretien : la question « et le paiement, il marche vraiment ? » mérite une
réponse affichable, pas une explication embarrassée.

**Aucun de ces services n'est obligatoire.** Le projet se clone et se démontre
entièrement sans une seule clé (D-18), et chaque implémentation réelle retombe
sur son simulateur à la moindre panne — clé expirée, quota dépassé, réseau
coupé, réponse vide, format inattendu. Ces quatre cas sont testés pour
l'assistant comme pour l'itinéraire, sans jamais toucher le réseau (D-37).

### Ce que la carte a demandé de changer

Le gestionnaire d'entrepôt ne recevait pas les coordonnées des adresses : sans
elles, aucun arrêt ne pouvait être placé. Elles lui sont maintenant transmises,
et cela n'ouvre rien — il voit déjà la rue, qui en dit plus. Les instructions de
porte restent hors de sa vue, et deux tests le vérifient.

### Le poids

MapLibre pèse 982 ko. Chargé paresseusement, il n'arrive qu'au moment où une
carte s'affiche : l'écran des tournées est passé de **1 003 ko à 7 ko**.


---

## Un défaut trouvé par un test intermittent (bloc N)

La suite backend a échoué **une seule fois**, sur un test de paiement qui
passait depuis des semaines. La cause n'était pas dans le test.

Le simulateur de paiement refusait toute référence finissant par « 99 », alors
que la règle annoncée porte sur le **montant**. La référence étant un condensat
du numéro de commande, **une commande sur 256 était refusée au hasard** — dans
la démonstration comme dans les tests, sans aucune trace. Rejoué sur mille
numéros plausibles, l'ancien code en refuse deux.

Corrigé par [D-143](journal-decisions.md) : le refus est inscrit dans la
référence à l'ouverture, là où le montant est connu.

**Compte des tests à la fin du bloc N** : 225 backend, 107 front web, 39 mobile.
