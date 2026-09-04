# Ta part du travail

> **Tu as signalé que mes demandes étaient de plus en plus dures à trouver
> (bloc E-4). C'était vrai** — elles étaient noyées au milieu de la référence.
> Désormais : _tout ce que j'attends de toi tient dans le premier écran_, daté
> et numéroté. Le reste du fichier est de la documentation qu'on consulte, pas
> qu'on relit.

---

# ⬛ À FAIRE MAINTENANT — bloc O, 4 septembre

> **Le contrôle de fin de bloc est fait** : 30 vérifications passées sur 30,
> confrontées au code et non au souvenir. Le détail est dans `etat-reel.md`.

## Ce qui n'existait pas du tout, et qui existe maintenant

**Le trou le plus grave du bloc, et il ne se voyait pas** : rien ne créait de
livraison en dehors du jeu de démonstration. Une commande payée, préparée et
marquée prête n'arrivait **chez aucun livreur**. C'est ce que tu décrivais de
trois façons — pas de course disponible, une distance qui sort de nulle part, et
une tournée dont on ignore l'origine.

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **1** | **Commande complète.** `lea@exemple.fr` → un produit → panier → « Passer commande ». Il te demande **une carte** : prends `4242 4242 4242 4242`, `12/30`, `123`. Une reconfirmation dit le montant **et** la carte | 4 min | D-150 |
| **2** | **N'entre jamais ta vraie carte** : essaie `4111 1111 1111 1111`, elle est refusée en te disant pourquoi | 1 min | D-150 |
| **3** | **`olivier@exemple.fr`** (Maison Perrin) → Commandes reçues → fais avancer ta commande jusqu'à **Expédiée** | 2 min | D-152 |
| **4** | **`rachid@exemple.fr`** (entrepôt Lyon-Est) → **Colis reçus** → confirme la réception de ce colis | 1 min | D-153 |
| **5** | **Tournées → « Calculer une tournée ».** Elle se monte avec ce qui est arrivé, dans l'ordre du plus proche voisin, avec sa distance | 2 min | D-153 |
| **6** | **Recalcule-la** : le résultat peut différer. Puis **confie-la** — la liste ne propose que des livreurs Standard — et **fais-la partir** | 3 min | D-153 |
| **7** | **`julien@exemple.fr`** sur mobile → « Ma tournée ». L'arrêt est là, avec la carte. Et le client voit sa commande passer « en tournée » **tout seul** | 3 min | D-146 |

## L'argent, qui n'existait qu'à moitié

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **8** | **Sur une commande payée → « Mon reçu ».** Chaque boutique, le livreur, la plateforme : **la somme des parts fait exactement le total** | 2 min | D-151 |
| **9** | **Mobile, historique du livreur → une course.** Le calcul est écrit : « 1,50 € de base + 0,35 €/km × 4,35 km ». Plus rien ne sort de nulle part | 2 min | D-152 |

## Ce qui ne bougeait jamais

**Ta remarque soulignée quatre fois.** L'API était bien synchronisée — je l'ai
vérifié, même compte, mêmes données depuis les deux origines. Le défaut était
entièrement côté écran : chaque vue chargeait ses données **une seule fois**, et
Ionic ne démonte jamais ses vues.

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **10** | **Ouvre le web et le mobile côte à côte, même compte.** Ajoute un article sur le web, va sur l'onglet Panier du mobile : il est là | 3 min | D-146 |
| **11** | **Laisse « Mes commandes » ouvert sur le mobile** pendant que tu fais avancer la commande depuis le vendeur. Le suivi avance **tout seul** | 3 min | D-146 |

## Le mobile, refait

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **12** | **L'accueil client.** Adresse, recherche, commande en cours **avec son code de remise**, catégories, boutiques proches, « commander à nouveau », les plus demandés. Tout est cliquable | 3 min | D-148 |
| **13** | **Recherche → le bouton de filtres.** Un panneau monte du bas : mode, catégories groupées par univers, boutiques, stock. Les filtres retenus restent en pastilles | 2 min | D-157 |
| **14** | **Mes commandes.** Les cartes sont **repliées**, sauf celle en cours. Ouvre-en une : reçu, avis, signalement, en trois boutons de même taille | 2 min | D-156 |
| **15** | **Mon reçu → « Imprimer ou enregistrer ».** Le navigateur propose « Enregistrer en PDF », et rien de l'application n'apparaît sur la feuille | 2 min | D-156 |
| **16** | **Signale un problème, puis reste sur la commande.** Le dossier s'affiche dessous, avec le délai de la boutique | 2 min | D-155 |
| **17** | **Profil → Aide.** Les questions sont **celles du client**. Connecte-toi en `amine@exemple.fr` : ce sont celles d'un livreur Express, pas d'un Standard | 2 min | D-159 |
| **18** | **`julien@exemple.fr` → prochain arrêt → « Personne à l'adresse ».** L'écran te dit que l'arrêt **repasse en fin de tournée**, et l'arrêt suivant s'affiche | 2 min | D-155 |

## Ce que tu peux vérifier au passage

- **les vraies photos passent devant** au catalogue, les produits sans image en
  dernier (O-6, D-149) ;
- **la note se lit sur la vignette**, avant d'ouvrir la fiche, et elle dit si
  elle porte sur le produit ou sur la boutique (D-154) ;
- **la carte est cliquable** : tape une pastille sur « À proximité », la course
  s'ouvre ; sur « Ma tournée », l'arrêt s'ouvre (D-142, O-5) ;
- **la barre d'onglets ne touche plus celle d'Android** (O-3, D-158).

---

# 🗂 Bloc N, 4 septembre

## `demarrer.py` lance enfin le mobile — et te le dit s'il n'y arrive pas

**Ta trace N-6 disait deux choses, pas une.** La première : `vite` n'était pas
installé côté mobile. La seconde, plus grave : le démarreur affichait
**« Tout tourne »** avant de signaler l'échec. Un démarreur qui ment sur son
propre résultat est pire qu'un démarreur absent.

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **1** | **`python demarrer.py`.** Les trois adresses s'affichent, dont `http://localhost:5174` | 2 min | D-138 |
| **2** | **Pour voir la correction à l'œuvre** : `rd /s /q frontend-mobile
ode_modules` puis relance. Il réinstalle au lieu de te laisser avec `'vite' n'est pas reconnu` | 4 min | D-138 |

## ⚠ Deux clés à prendre, et une réponse à ta question sur Mistral

**N-4 — oui, je veux bien ta clé Mistral.** Mais **ne me l'écris pas** : colle-la
toi-même dans `backend/.env`, à la ligne `CLE_MODELE_IA=`. Ce fichier n'est pas
versionné et la CI échoue si un `.env` arrive sur le dépôt. Ne la mets ni dans
`questions.txt`, ni dans un message. Une fois posée, l'assistant passe tout seul
du simulateur au vrai modèle — rien d'autre à toucher.

**N-5 — la carte : une seule clé vaut la peine d'être prise, et elle est
gratuite sans carte bancaire.**

| Ce que c'est | Quoi prendre | Où la coller |
|---|---|---|
| **Le fond de carte** | **rien** — OpenFreeMap s'affiche sans clé | — |
| Un rendu plus soigné *(facultatif)* | une URL de style MapTiler | `frontend-web/.env` → `VITE_STYLE_CARTE` |
| **L'itinéraire routier** | **`openrouteservice.org`** — inscription gratuite, 2 000 requêtes/jour, **aucune carte bancaire** | `backend/.env` → `CLE_ITINERAIRE` |

Google, Mapbox et HERE exigent tous un moyen de paiement pour délivrer une clé.
OpenRouteService non, il est bâti sur OpenStreetMap, et il connaît le profil
**vélo** — ce qui compte ici, puisque la moitié des courses sont des livraisons
Express à vélo.

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **14** | **`rachid@exemple.fr` → Tournées → clique une tournée.** Le volet de droite montre les arrêts **sur une carte**, dans leur ordre | 2 min | D-142 |
| **15** | **Mobile, `julien@exemple.fr` → Ma tournée.** La même carte, au pouce | 2 min | D-142 |
| **16** | **Mobile, `amine@exemple.fr` → À proximité.** Les courses libres sur une carte : deux courses à 2,4 km ne se valent pas quand l'une part à l'opposé | 2 min | D-142 |
| **17** | **Regarde le tracé.** Il est en **pointillés** et l'écran écrit « trajet estimé ». Prends la clé OpenRouteService, relance, et il passe en trait plein avec la vraie durée | 5 min | D-142 |
| **18** | **`GET /api/v1/services`** te dit lequel de chaque service tourne pour de vrai | 1 min | D-18 |

## Les quatre vues et la vidéo : le zoom a disparu

**Ta remarque N-1 était juste et je ne la discute pas** : c'était la photo
d'origine, recadrée trois fois, puis un lent zoom sur cette même photo. Et
cinquante-huit produits l'avaient tous, à l'identique.

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **10** | **Ouvre cinq fiches produit au hasard.** Elles n'ont plus le même nombre de vues : la plupart n'en ont qu'**une** | 3 min | D-140 |
| **11** | **Cherche « Sirop de sureau » ou « Curry de légumes ».** Quatre vues **différentes** — le colis, la fiche en bref, la mise en situation — et un aperçu qui **fait le tour** au lieu de zoomer | 2 min | D-140 |
| **12** | **Ouvre « Coffret d'épices » ou « Ordinateur portable ».** Ceux-là ont une **vraie photo**, et elle reste **seule** : je n'accole pas de schémas à une photographie | 2 min | D-140 |
| **13** | **Si tu veux de vraies photos multi-angles** : dépose-les dans `donnees-demo/images/` sous `<slug>-2.jpg`, `-3`, `-4`, puis `python manage.py seed_catalogue`. Tes fichiers priment sur mes dessins | — | D-140 |

## Le mobile pouvait remplir un panier, pas commander

**Ta demande N-5** : *« fais attention que le mobile a tout ce qui devait
avoir »*. Le trou le plus grave ne se voyait pas — le bouton « Passer commande »
**naviguait** vers la liste des commandes au lieu de commander.

Ouvre `http://localhost:5174`, réduis la fenêtre au format téléphone
(Ctrl+Maj+M), connecte-toi en **`lea@exemple.fr` / `Demonstration!2026`**.

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **3** | **Recherche → un produit → Ajouter → Panier → Passer commande.** Tu arrives sur un écran qui montre le découpage, l'adresse et le total — et le bouton **paie vraiment** | 3 min | D-139 |
| **4** | **Commandes → une commande livrée → « Donner mon avis ».** Tu notes la boutique, chaque produit reçu, et le livreur | 2 min | D-139 |
| **5** | **La même carte → « Signaler un problème ».** Motif, récit, et le compte à rebours de 48 heures du vendeur démarre | 2 min | D-139 |
| **6** | **N'importe quelle commande payée → « Mon reçu ».** Les mêmes chiffres que la facture du web | 1 min | D-139 |
| **7** | **Profil → « Notifications poussées ».** Bascule-le, quitte l'écran, reviens : **il a gardé ta position**. Avant, il ne parlait à personne | 2 min | D-139 |
| **8** | **Profil → « Mes notifications ».** La pastille rouge montre les non-lues, la liste s'ouvre, et le compteur retombe | 1 min | D-139 |
| **9** | **Profil → « Changer mon mot de passe ».** Essaie avec un mauvais mot de passe actuel : il refuse en le disant | 2 min | D-139 |

> Le mobile a maintenant ses propres tests — 32 gardes qui relisent la source et
> échouent si un commutateur redevient décoratif ou si un bouton se remet à
> naviguer au lieu d'agir. Elles tournent dans la CI.

---

# 🗂 Bloc M, 2 septembre

## ⚠ Le bouton invisible : trouvé, expliqué, corrigé

**Ta remarque M-2 était le symptôme d'un vrai défaut**, et il touchait toutes
les popups du projet.

`--accent` — la couleur de ton rôle — n'était posée que sur le grand `<div>` de
l'application. Or **PrimeVue accroche ses popups au `<body>`**, donc en dehors.
Dans une popup, le bouton principal perdait donc son fond et restait écrit en
blanc… sur le fond blanc de la fenêtre.

C'était la maladie du bloc J revenue par la bande. Sauf que cette fois le
garde-fou ne pouvait pas la voir : la classe existait, la couleur aussi — c'est
la **portée** qui manquait.

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **1** | **`python demarrer.py`**, puis Ctrl+Maj+R | 2 min | — |
| **2** | **Léa → Mes adresses → corbeille.** Le bouton « Retirer du carnet » est **visible**, dans le vert de ton rôle | 1 min | D-126 |
| **3** | **`karim@exemple.fr` → Mon personnel → bouton d'alimentation.** Le bouton de confirmation est en **bleu vendeur**, pas seulement visible : il porte la couleur du rôle | 1 min | D-126 |
| **4** | **`admin@rivdinde.local` → Litiges → arbitrer.** Le bouton est en **rouge admin**. Un bouton bleu chez l'admin serait pire qu'un bouton invisible : tu croirais être dans le mauvais espace | 1 min | D-126 |

## L'œil ouvre enfin une popup

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **5** | **N'importe quelle liste, n'importe quel rôle → clique l'œil.** Une popup s'ouvre avec le détail, et **la liste reste derrière** : tu ne perds pas ta place | 2 min | D-127 |
| **6** | **Ferme la popup.** Le panneau de droite montre **le même détail** — il est écrit une seule fois, à un seul endroit | 2 min | D-127 |
| **7** | **Survole l'œil sur cinq écrans différents.** L'infobulle commence toujours par « Consulter ». Un écran disait « Suivre » — un même symbole doit promettre la même chose partout | 2 min | D-128 |

Les onze écrans sont convertis. Un test parcourt tous les `.vue` et échoue si
un œil se remet à promettre autre chose, ou s'il cesse d'ouvrir.

## Beaucoup plus de données pour tout essayer

**Ta demande M-0.** La couverture était garantie depuis le bloc L — chaque
scénario avait de quoi se montrer — mais pas le **volume** : aucune liste
n'atteignait sa deuxième page, et le graphe des ventes tenait sur trois barres.

| | Avant | Maintenant |
|---|---|---|
| Comptes | 20 | **30** |
| Produits | 24 | **59** |
| Commandes | 15 | **85** |
| Livraisons | 14 | **70** |
| Avis | 7 | **30** |

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **8** | **Sur la vitrine, choisis « Livrer à » → Lyon.** 50 produits, trois univers, des facettes qui écartent vraiment | 2 min | D-130 |
| **9** | **`karim@exemple.fr` → Statistiques.** La courbe a **quinze jours** de ventes, 8 avis, une vraie note moyenne. Avant : trois barres | 3 min | D-130 |
| **10** | **→ Commandes reçues.** 33 sous-commandes : la liste pagine, le tri par montant sert enfin à quelque chose | 2 min | D-130 |
| **11** | **`julien@exemple.fr` → Mes courses.** 70 livraisons, dont 55 terminées : son historique n'est plus vide | 2 min | D-130 |

### Ce que je n'ai pas réussi, et que je préfère te dire

J'ai voulu **34 vraies photos de plus**. J'ai regardé le résultat sur une
planche-contact avant de te le livrer, et c'était mauvais : **25 téléchargements
ont échoué**, et sur les 9 photos obtenues, un « poke bowl » était une tasse
posée sur un clavier et un « écran 27 pouces » montrait l'intérieur d'un
magasin.

Une photo fausse fait douter de tout le catalogue — c'est ce que tu m'avais
reproché au bloc J. J'ai donc fabriqué une **vignette assumée** : nom du
produit, univers, aux couleurs de la maquette. Elle ne ment sur rien.

**Si tu veux de vraies photos**, dépose tes fichiers dans
`plan-organisation/donnees-demo/images/` en les nommant d'après le produit
(`poke-bowl-saumon.jpg` par exemple) : le peuplement les prend en priorité sur
tout le reste.

## Les deux guides que tu demandais (M-4)

| Fichier | Ce qu'il couvre |
|---|---|
| `frontend-mobile/LISEZ-MOI.md` *(dépôt privé)* | lancer le mobile, dans le navigateur et sur un vrai téléphone, en client **et** en livreur |
| [`deploiement/LISEZ-MOI.md`](../../deploiement/LISEZ-MOI.md) | la mise en ligne, étape par étape, avec une section entière de pièges |

**Une précision sur ta formulation** : tu parles des « deux mobile client et
livreur ». Il n'y en a **qu'une**. C'est le même code : la barre d'onglets
change selon le rôle du compte connecté. `lea@exemple.fr` donne l'application
du client, `amine@exemple.fr` celle du livreur Express, `julien@exemple.fr`
celle du livreur Standard.

### ⚠ Deux défauts trouvés en écrivant ces guides

Les deux auraient cassé quelque chose sans jamais lever d'erreur.

**1. L'application mobile ne pouvait pas parler à l'API.** Le port 5174
manquait aux origines autorisées : le navigateur jetait chaque réponse avant
que le code ne la voie. Écran vide, journaux serveur parfaitement propres.

**2. Trois variables de déploiement portaient le mauvais nom.** `render.yaml`
posait `DJANGO_ALLOWED_HOSTS` au lieu de `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`
au lieu de `CORS_ORIGINS`, et `CLOUDINARY_URL` au lieu des trois variables
attendues. Une variable mal nommée ne provoque aucune erreur : la valeur par
défaut s'applique. **Ta mise en ligne aurait servi un front vide**, et tu
aurais cherché du côté du réseau.

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **12** | **Ouvre `http://localhost:5174`** et réduis la fenêtre au format téléphone (Ctrl+Maj+M). Connecte-toi en `lea@`, puis en `amine@` : la barre d'onglets change | 4 min | D-135 |
| **13** | **Depuis ton téléphone, même Wi-Fi** : suis le guide mobile. Si ça bloque, la section « pièges » est dans l'ordre où on les rencontre | 10 min | D-133 |
| **14** | **Lis la section « pièges » du guide de déploiement** avant de mettre en ligne. Chacun a coûté du temps sur ce projet | 5 min | — |

## Les deux dépôts (M-3)

C'est fait, et dans l'ordre que tu conseillais : **le complet d'abord sur le
privé**, la rétrogradation du public ensuite.

| Dépôt | Contenu | État |
|---|---|---|
| `git_e_commerce_livraison_v2` *(privé)* | tout, mobile compris | ✅ poussé |
| `git_e_commerce_livraison` *(public)* | tout **sauf** `frontend-mobile/` | ✅ poussé |

Le public garde l'API, le front web, les 176 tests backend, les 107 tests
front, le dossier de conception et les guides. Il perd le dossier
`frontend-mobile/`, et c'est tout : aucun test, aucun code d'API, aucune
décision.

**Les décisions D-20 et D-40 restent écrites** dans le dossier de conception, et
le README public dit franchement que l'application mobile existe et vit
ailleurs. Effacer la trace d'un choix d'architecture parce que le code est
ailleurs falsifierait le dossier — et c'est le dossier qu'un recruteur lit en
premier.

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **15** | **Ouvre les deux dépôts sur GitHub** et compare. Le public n'a plus `frontend-mobile/`, le reste est identique | 3 min | D-136 |
| **16** | **Lis `plan-organisation/00-pilotage/deux-depots.md`** : les quatre commandes pour livrer la prochaine fois, et le piège à éviter | 3 min | D-136 |

**Le piège, en une phrase** : ne travaille **jamais** sur la branche
`public-sans-mobile`. Tout ce qui y serait écrit disparaîtrait au prochain
rebase. Le travail se fait sur `main`, toujours.

Mot de passe commun : **`Demonstration!2026`**.

---

## Ce que tu as signalé, et où j'en suis

| | Ton constat | Où ça en est |
|---|---|---|
| **K-1** | « Le bouton passer la commande ne fonctionne pas » | **Corrigé, et la cause n'était pas le bouton.** Un seul article retiré de la vente faisait échouer tout l'aperçu : l'écran disait « votre panier est vide » pendant que le panneau montrait quinze articles. Vérifié de bout en bout : la commande aboutit (201) |
| **K-1** | « Le client ne peut pas donner son avis » | **Fait.** On note la boutique, chaque produit reçu et le livreur — et seulement après livraison (R-06). Quatre refus vérifiés : commande non livrée, commande d'un autre, cible hors commande, note hors bornes |
| **K-1** | « Quand je me déconnecte, son panier est toujours visible » | **Corrigé.** C'était un défaut côté navigateur : le serveur renvoyait bien un panier vide, mais l'écran gardait l'ancien affiché. Le panier se vide et la clé de session est régénérée |
| **K-1** | « Le panneau droit des autres rôles n'a rien, pourquoi ? » | Parce qu'aucun écran ne le nourrissait. Repris de `useVolet` du projet banque : **chaque écran y dépose ce qu'il a sélectionné** — le colis consulté, les arrêts d'une tournée, le détail d'une commande avec son bouton d'avancement |
| **K-1** | « Les listes sont mal gérées, je veux les symboles pour consulter et gérer, pour toutes les listes, tous les rôles » | **Une seule liste pour tout le projet** (`Liste.vue`, reprise de `Tableau.tsx` du projet banque) : recherche, tri, pagination, état vide rédigé, boutons-symboles encadrés. **7 écrans convertis** — colis, tournées, commandes reçues, catalogue, stock, utilisateurs, mes commandes, mes courses, boutiques, journal. **Il en reste 4** : validations, litiges, personnel, adresses |
| **K-1** | « Colis reçus : on ne peut même pas consulter » | **Fait**, et ton intuition sur « gérer » était la bonne : un magasinier réceptionne, il ne modifie pas une commande. Les actions sont consulter et localiser |
| **K-2** | « Les tournées, je ne sais pas où regarder » | `rachid@exemple.fr` → **Tournées**. Elles étaient dans un dépliant qu'il fallait deviner ; c'est maintenant une liste, et les arrêts s'ouvrent dans le volet |
| **K-4, K-5** | « Relis le bloc A », « regarde le projet banque » | **Fait avant d'écrire une ligne.** Les listes, le volet de droite et les boutons-symboles viennent directement de là |

---

## Ce que je n'ai PAS encore fait du bloc K, et dans quel ordre je le prends

Je te le dis franchement plutôt que de te laisser le découvrir :

1. **Profil et paramètres** (K-3) — le modèle du projet banque : champs d'identité
   **gelés** avec demande de modification validée, coordonnées libres, et un vrai
   écran de paramètres (mot de passe, sécurité, notifications, affichage).
2. **Les 4 dernières listes** à convertir : validations, litiges, personnel, adresses.
3. **Le jeu de données des autres rôles** (K-1) — il est riche côté client, plus
   maigre côté entrepôt et livreur.
4. **Plusieurs photos et une courte vidéo par produit** (K-1).
5. **Sidebar, navbar et onglets plus riches** (K-2).
6. **`demarrer.py` et la CI/CD** (K-6).

Puis le paiement, comme convenu en J-10.

---

# Référence

_Ce qui suit ne se relit pas : on vient y chercher une réponse précise._

## Comment on communique, en trois fichiers

| Fichier                                        | Qui écrit | Ce qu'on y met                                                                                   |
| ---------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------ |
| `questions.txt`                                | **Toi**   | Tes demandes, tes doutes, tes corrections. Ta boîte d'entrée, dans ton style, sans mise en forme |
| **Ce fichier, tout en haut**                   | Moi       | Ce que tu dois faire de tes mains, daté, dans le premier écran                                   |
| [questions-ouvertes.md](questions-ouvertes.md) | Moi       | Mes questions à toi, classées par urgence, avec ma recommandation                                |
| [journal-decisions.md](journal-decisions.md)   | Moi       | Ce qui est tranché, et pourquoi                                                                  |

---

## A. Les outils — **tu as déjà tout**

Vérifié sur ta machine : Python **3.14.7**, Node **25.8.2**, npm **11.11.1**,
Docker **29.7.2**, VS Code **1.135**.

Un point à connaître : **Git Bash voit encore un vieux Python 3.8** installé il
y a des années, alors que PowerShell voit le 3.14. `demarrer.py` détecte le cas
et repart tout seul avec le bon interpréteur — tu peux lancer depuis l'un ou
l'autre.

> **Piège PowerShell** rencontré au passage : `where` y est un alias de
> `Where-Object`, d'où tes sorties vides. Pour localiser un exécutable :
> `where.exe python` ou `Get-Command python`.

**Android Studio n'est pas à installer maintenant** — plusieurs gigaoctets, et
il ne sert qu'à la tranche 7 pour fabriquer le `.apk`. Je te préviendrai ici.

---

## B. Le dépôt Git

Déjà fait : dépôt initialisé, branche `main`, distant déclaré vers
`rivaldopiaplle-boop/git_e_commerce_livraison`, `plan-organisation/` mis en
index.

**Le premier envoi est fait** : commit `55d6899`, poussé, 66 fichiers suivis —
dont `.github/workflows/ci.yml`, donc l'intégration continue s'est exécutée au
moins une fois. La commande, pour les prochaines fois :

```powershell
git add .
git commit -m "ce que ce lot change"
git push
```

Avant d'envoyer, **regarde `git status`** : aucun fichier `.env` ne doit
apparaître. J'ai vérifié qu'ils sont ignorés, mais une seconde de contrôle vaut
mieux qu'une clé à révoquer.

**Dépôt public dès le début, jamais un secret dedans.** Une clé publiée sur
GitHub est détectée et exploitée en quelques heures : c'est automatisé.

---

## C. Les comptes de services

| Service                 | À quoi ça sert              | Quand      | Carte bancaire ? |
| ----------------------- | --------------------------- | ---------- | ---------------- |
| **GitHub**              | Dépôt, intégration continue | fait       | Non              |
| **Neon**                | Base PostgreSQL en ligne    | Tranche 1  | Non              |
| **Cloudinary**          | Photos produit              | Tranche 2  | Non              |
| **Stripe**              | Paiement, en **mode test**  | Tranche 5  | Non en mode test |
| **Resend** ou **Brevo** | E-mails réels               | Tranche 8  | Non              |
| **Render**              | Hébergement de l'API        | Tranche 11 | Non              |
| **Vercel**              | Hébergement du front        | Tranche 11 | Non              |

Aucun ne demande de carte bancaire pour ce dont on a besoin. **Si l'un t'en
demande une, arrête-toi et dis-le-moi** : l'offre aura changé, on choisira
autre chose.

### Où vont les clés

```
Clé obtenue chez le service
        │
        ├──►  backend/.env                  (ignoré par Git, jamais envoyé)
        └──►  GitHub → Settings → Secrets   (intégration et déploiement)
```

`backend/.env` est créé automatiquement par `demarrer.py`, copié depuis
**`backend/.env.example`** — le fichier que tu m'as désigné au bloc D-3, dans la
forme exacte de celui de ton projet banque : versionné, chaque variable
expliquée, **aucune valeur**.

**Ne colle jamais une clé dans notre conversation ni dans `questions.txt`.** Je
n'en ai pas besoin : je travaille avec les noms, pas les valeurs. Si une clé est
publiée par accident, va la révoquer chez le service — la retirer d'un commit ne
suffit pas, l'historique reste.

---

## D. Ce que tu vérifies, à chaque tranche

Mon travail n'est pas fini parce que le code existe : il est fini quand **tu** as
vu le test de sortie passer. Les onze tests sont dans
[demarrage-projet.md](../05-execution/demarrage-projet.md).

```powershell
python demarrer.py
```

**Une seule commande** qui monte la base, prépare l'environnement, migre, crée le
compte administrateur et lance l'API et le front. C'est l'enseignement direct du
projet banque : le jour où démarrer demande six commandes dans le bon ordre, on
ne relance plus le projet après trois semaines — et on ne le montre pas à un
recruteur.

|                    |                                      |
| ------------------ | ------------------------------------ |
| Front web          | <http://localhost:5173>              |
| API                | <http://localhost:8000/api/v1/sante> |
| Administration     | <http://localhost:8000/admin/>       |
| Courriels capturés | <http://localhost:8026>              |

```powershell
python demarrer.py --etat        # ce qui tourne, ce qui répond
python demarrer.py --sans-web    # l'API seule
python demarrer.py --arreter     # arrêter les conteneurs
```

Les ports (5433, 1026, 8026) sont **décalés exprès** : le projet banque occupe
5432, 1025 et 8025 sur ta machine, et les deux doivent pouvoir tourner ensemble.

**Ce que je te demande à chaque fois** : lancer, cliquer, et me dire ce qui te
paraît faux, laid ou incompréhensible. Tu es le premier utilisateur ; ce que tu
ne comprends pas, un recruteur ne le comprendra pas non plus.

---

## E. Au déploiement (tranche 11)

1. Créer les comptes Render et Vercel, connectés à ton GitHub.
2. Recopier les variables d'environnement dans les deux interfaces — je te
   donnerai la liste, nom par nom.
3. Vérifier que l'URL publique répond, avec les comptes de démonstration.
4. **Le jour de l'entretien** : activer la tâche de réveil de l'API une heure
   avant, la désactiver après. La raison est dans
   [contrat-deploiement.md](../03-contrats/contrat-deploiement.md) — le service
   gratuit s'endort au bout de quinze minutes et met une minute à repartir.
5. Dérouler la démonstration de dix minutes **au moins une fois en entier, à
   voix haute, seul**, avant de la faire devant quelqu'un.

---

## F. Ce que tu n'as pas à faire

- Chercher, renommer ou fournir des images de produits
  ([D-24](journal-decisions.md) — le script de peuplement s'en charge ; tu peux
  déposer les tiennes, c'est une option, pas une corvée).
- Écrire du `docker-compose.yml`, des `Dockerfile`, des fichiers d'intégration.
- Créer la structure, les modèles, les migrations.
- Rédiger la documentation.
- Traduire les décisions en code : c'est à ça que sert tout ce dossier.

---

## G. Historique de ce que tu as déjà fait

| Quand  | Quoi                                                                                                             |
| ------ | ---------------------------------------------------------------------------------------------------------------- |
| Bloc C | Tranché l'hébergement, le mobile, l'entrepôt dans le MVP, l'adresse partagée                                     |
| Bloc D | Validé mes recommandations sur les retours produit et l'affichage de l'argent                                    |
| Bloc D | Initialisé le dépôt, la branche `main`, le distant GitHub                                                        |
| Bloc E | Signalé le `.env`, l'absence d'extension Vue, l'admin sans identifiants — les trois sont réglés                  |
| Bloc F | Commité **et poussé** la tranche 0, créé les comptes Neon, Cloudinary et Stripe, choisi le nom et fourni le logo |
