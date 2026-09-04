

### D-150 — Payer sans carte n'est pas payer

**Ton bloc O-5** : *« payer est validé sans carte, pas de demande de carte même
la première fois, et après c'est enregistré »*, *« l'argent est payé sans
reconfirmation »*, et *« je ne sais pas comment tu vas faire pour que je mette
la carte, mais que ça ne prenne pas beaucoup de temps — fais une réflexion en
profondeur »*.

C'était exact : le bouton créait une intention et la confirmait dans la foulée.
Aucune carte n'était demandée, jamais.

### La réflexion que tu demandais

Le premier réflexe serait de stocker un numéro de carte. **C'est exactement ce
qu'il ne faut pas faire**, et pas d'abord pour des raisons juridiques : un
numéro de carte en base est une dette permanente, qu'aucun chiffrement ne
solde. Toute la conception de Stripe et de ses concurrents tient dans une
idée : **on ne garde jamais le numéro, on garde un jeton qui le remplace**.

`paiements/cartes.py` fait donc ce que fait Stripe, avec un simulateur à la
place :

| Étape | Ce qui se passe |
|---|---|
| saisie | clé de Luhn, échéance future, cryptogramme de la bonne longueur, marque déduite du numéro — **tout est vérifié sans un seul appel réseau** |
| enregistrement | seuls **la marque, les quatre derniers chiffres et l'échéance** sont conservés |
| paiements suivants | un **jeton** remplace la carte |

Le jeton dérive du numéro par condensat : la même carte réenregistrée donne le
même jeton — donc pas de doublon — et il ne permet à personne de remonter au
numéro. Un test le vérifie champ par champ : aucun attribut de la table ne
contient les seize chiffres.

**En simulation, seuls les numéros de test sont acceptés.** C'est le test le
plus important du fichier : sur une démonstration mise en ligne, quelqu'un
finira par taper sa vraie carte, et il faut l'arrêter en le lui disant. La
liste des cartes d'essai est d'ailleurs **servie par l'API**, pas cachée dans un
commentaire — une démonstration qu'on ne sait pas essayer ne se démontre pas.

### « Que ça ne prenne pas beaucoup de temps »

La première fois : quatre champs, et l'erreur s'affiche **sous le champ
fautif** — « erreur » en haut du formulaire oblige à relire les quatre. Ensuite,
la carte apparaît en une ligne — « Visa •••• 4242 » — et il ne reste qu'à
confirmer. Le coût est payé une seule fois.

### La reconfirmation

`POST /commandes/{id}/paiement` refuse désormais sans carte, et **rend la carte
retenue**. C'est ce qui permet d'écrire *« Payer 24,90 € avec Visa •••• 4242 »*
là où le bouton disait « Payer » et ne disait rien.


### D-151 — Où va l'argent, enfin visible

**Ta remarque** : *« l'argent payé, on ne voit pas la distribution chez les
vendeurs différents qui interviennent dans la commande, la part du livreur,
celle de l'application ; rien n'existe réellement, encore moins synchronisé »*.

La répartition **existait** en base — `RepartitionVendeur` — et le vendeur
voyait sa part. **Personne ne voyait l'ensemble.** Or c'est précisément ce qui
rend une place de marché compréhensible : un paiement unique, plusieurs
destinataires.

`GET /commandes/{id}/repartition` rend la ventilation complète : chaque
boutique, le livreur, la plateforme. Deux règles la rendent fiable :

- **les montants sont lus, jamais recalculés.** Un écran qui recalcule finit
  toujours par afficher autre chose que ce qui a été versé ;
- **la somme des parts fait exactement le total payé.** La part de la
  plateforme est ce qui *reste*, et non un pourcentage recalculé : un écran qui
  ment d'un centime perd toute sa crédibilité. Un test l'exige.

L'administrateur a le même relevé, agrégé : `GET /admin/repartitions`.


### D-152 — Une commande prête n'arrivait chez aucun livreur

**Le trou le plus grave du bloc O**, et il ne se voyait pas.

**Rien ne créait de `Livraison` en dehors du jeu de démonstration.** Une
commande payée pour de vrai, préparée pour de vrai, marquée prête pour de vrai…
n'atteignait aucun livreur. Toutes les courses visibles dans l'application
venaient du peuplement.

C'est ce que tu décrivais de trois façons différentes, sans qu'aucune ne
paraisse être le même défaut :

- *« je n'ai pas vu de commande à livrer disponible quand le livreur est
  libre »* ;
- *« la distance du trajet et le prix pour vous ne sont pas vraiment calculés ou
  mis par l'admin, ça sort de nulle part »* ;
- *« je ne comprends pas d'où sort la tournée du livreur »*.

`livraisons/attribution.py` est le chaînon manquant, appelé au moment où la
commande passe à `PRETE`, et **idempotent** : un vendeur qui refait passer sa
part à prête n'engendre pas une deuxième course.

### « Ça sort de nulle part » : la distance et le tarif

Les deux sortaient effectivement de nulle part. La distance était **tirée au
hasard** entre 0,8 et 7,5 km par le peuplement, sans rapport avec les adresses ;
la rémunération suivait une formule enfouie dans un script.

- **la distance est calculée** — de la boutique (Express) ou de l'entrepôt
  (Standard) jusqu'au client, par haversine (D-25) majorée du même détour urbain
  que la carte (D-142). Deux facteurs différents feraient afficher deux
  distances différentes pour le même trajet ;
- **le barème est publié** dans `livraisons/tarifs.py`, en clair, et le **détail
  du calcul accompagne le montant** : « 1,50 € de base + 0,35 €/km × 4,35 km =
  3,02 € ». Un livreur doit pouvoir vérifier ce qu'on lui doit.

Sans coordonnées des deux côtés, on paie le **forfait minimum** et on le dit :
une distance fausse sur une fiche de paie est pire qu'une distance absente.

Une subtilité d'ordre : une course Standard naît à `PRETE`, donc **avant** que
le vendeur l'expédie, donc avant qu'un entrepôt soit rattaché. À ce moment-là on
ne peut que retenir l'entrepôt le plus proche du client. Quand le colis arrive
réellement, l'entrepôt n'est plus une hypothèse : le calcul est repris, et cette
fois il est juste. **Il ne bouge plus ensuite** — une rémunération qui change
après qu'un livreur a accepté est le meilleur moyen de perdre sa confiance.


### D-153 — La tournée se calcule, et le gestionnaire garde la main

**Ta description était la spécification** : *« les tournées doivent se calculer
seules en fonction des commandes — le gestionnaire demande le calcul en fonction
de ce qui est à sa disposition, peut le refaire quand il veut, et le résultat
peut différer après le départ ou la réception des colis. Et le gestionnaire doit
attribuer à un livreur juste, confirmer la réception des colis. »*

Le gestionnaire d'entrepôt ne pouvait **rien faire** : il consultait. Quatre
gestes existent maintenant, dans l'ordre d'une journée d'entrepôt :

1. **confirmer la réception** d'un colis. Sans ce geste, rien ne distinguait un
   colis en camion d'un colis sur l'étagère — et c'est pourtant la seule chose
   qui autorise à le charger ;
2. **calculer une tournée** avec ce qui est arrivé, autant de fois qu'il veut ;
3. **la confier à un livreur** ;
4. **la faire partir**.

Le calcul **ordonne, il ne décide pas**. L'ordre vient du **plus proche
voisin** : on part de l'entrepôt, on va au colis le plus proche, et ainsi de
suite. Pourquoi celui-là ? Parce que le problème du voyageur de commerce n'a pas
de solution exacte praticable au-delà d'une vingtaine d'arrêts, et que le plus
proche voisin donne un trajet de 20 à 25 % plus long que l'optimal **pour un
coût de calcul nul**. Sur quinze arrêts en ville, cela représente quelques
minutes : une bibliothèque d'optimisation serait une dépendance de plus pour un
gain que personne ne verrait.

Trois refus, et chacun évite une vraie erreur :

| Refus | Pourquoi |
|---|---|
| une tournée partie ne se recalcule pas | on ne réordonne pas les arrêts de quelqu'un qui roule |
| un livreur **Express** ne prend pas de tournée | c'est une journée perdue pour lui et pour les clients |
| une tournée ne part pas sans livreur | — |

La liste des livreurs proposés ne contient **que** des livreurs Standard
validés : proposer un choix qu'on refusera ensuite est une erreur qu'on laisse
faire.

Une permission nouvelle, `EstGestionnaireEntrepot` : vendeur et entrepôt sont
tous deux « gestionnaires » (D-05) et ne font pas le même métier. Sans elle, le
personnel d'une boutique pouvait monter une tournée.

**Et « expédier vers l'entrepôt » n'expédiait vers aucun entrepôt** :
`SousCommande.entrepot` n'était rempli que par le peuplement. Il est désormais
choisi — le plus proche du client — au moment de l'expédition, avec sa date.
Le plus proche à vol d'oiseau et non une table par code postal : une table est
juste le jour où on l'écrit et fausse dès qu'un entrepôt ouvre.


### D-154 — Un avis qu'il faut ouvrir une fiche pour lire n'aide personne

**Ta remarque** : *« je donne mon avis mais ça n'apparaît pas sur ce qui est vu
par les autres clients »*.

Les avis publics **existaient** et la fiche produit les affichait. Mais il
fallait **ouvrir la fiche** — autrement dit, la note n'aidait jamais à choisir
entre deux produits d'une liste, et c'est pourtant à ce moment-là qu'un avis
sert.

La note figure maintenant sur **chaque vignette**, web et mobile. Deux
précautions :

- **la note dit sur quoi elle porte.** Un produit neuf n'a pas encore d'avis mais
  sa boutique en a : on montre celle de la boutique **en l'écrivant**. La faire
  passer pour celle du produit serait un petit mensonge que les gens repèrent ;
- **les notes sont agrégées en une seule requête** pour toute la liste. Sans ce
  pré-calcul, soixante vignettes coûteraient soixante requêtes — et l'accueil se
  rafraîchit toutes les vingt secondes (D-146).
