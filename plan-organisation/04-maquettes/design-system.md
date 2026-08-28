# Design system — ce qui est commun, ce qui change par rôle

> Consolide les règles d'or 6 à 10, qui étaient dispersées dans plusieurs
> documents. Les valeurs ci-dessous sont **déjà appliquées** dans
> [maquettes.html](maquettes.html) : ce fichier documente ce que les maquettes
> montrent, pour que le code Vue le reprenne sans réinterprétation.

---

## 1. Le principe

**Une seule application, cinq peaux.** Les composants, les icônes, les
espacements, les libellés et les couleurs de sens sont identiques pour tout le
monde. Seule la **couleur d'accent** change selon le rôle, pour qu'on sache en
un coup d'œil dans quel espace on se trouve.

---

## 2. Couleurs d'accent par rôle

| Rôle | Couleur | Accent | Fond doux | Accent foncé |
|---|---|---|---|---|
| Client | Vert | `#16a34a` | `#e8f8ee` | `#0f7a34` |
| Vendeur | Bleu | `#2563eb` | `#eaf0ff` | `#1e40af` |
| Gestionnaire | Orange | `#ea580c` | `#fff2e8` | `#b8450a` |
| Livreur | Violet | `#7c3aed` | `#f3edff` | `#5b21b6` |
| Admin | Rouge | `#b91c1c` | `#fdebe9` | `#7f1414` |

L'accent est utilisé pour : l'élément de navigation actif, le bouton principal,
les badges de comptage, la barre de progression, les liens. **Jamais** pour un
message de succès, d'alerte ou d'erreur.

## 3. Couleurs de sens — identiques pour tous les rôles

| Sens | Couleur | Emploi |
|---|---|---|
| Succès | Vert `#16a34a` | Livré, payé, validé |
| Attente | Ambre `#f59e0b` | En préparation, en attente de validation |
| En cours | Bleu `#2563eb` | En livraison, en tournée |
| Erreur | Rouge `#dc2626` | Échec, annulation, litige |
| Neutre | Gris `#64748b` | Brouillon, archivé |

Un statut a **la même couleur partout** : sur le web, sur le mobile, dans la
liste et dans le détail. C'est ce qui rend une frise de suivi lisible sans
légende.

## 4. Couleurs de statut de commande

| Statut | Couleur de sens |
|---|---|
| `EN_ATTENTE_PAIEMENT` | Neutre |
| `PAYEE` | Succès |
| `EN_PREPARATION`, `PRETE` | Attente |
| `EXPEDIEE_ENTREPOT`, `RECUE_ENTREPOT` | En cours |
| `EN_LIVRAISON`, `EN_TOURNEE` | En cours |
| `LIVREE` | Succès |
| `ANNULEE`, `REMBOURSEE`, `ECHEC_LIVRAISON` | Erreur |

---

## 5. Icônes — mêmes symboles web et mobile (règle d'or n°7)

Un jeu unique, au trait, épaisseur constante. Recommandation : **Lucide**
(disponible en Vue, très complet, licence permissive) — ne pas réinventer.

| Concept | Icône | Concept | Icône |
|---|---|---|---|
| Catalogue | grille | Panier | panier |
| Produit | boîte | Commande | reçu |
| Livraison | camion | Course Express | vélo |
| Tournée | itinéraire | Entrepôt | entrepôt |
| Boutique | vitrine | Client | personne |
| Stock | pile | Alerte stock | triangle |
| Paiement | carte | Remboursement | flèche retour |
| Litige | bouclier | Avis | étoile |
| Notification | cloche | Paramètres | roue |

Un bouton-icône seul a **toujours** une infobulle et un libellé accessible.

---

## 6. Structure web

Voir le schéma dans [contrat-web.md](../03-contrats/contrat-web.md).
Points de rupture : sidebar repliée automatiquement sous 1200 px, panneau droit
devenant un tiroir superposé sous 1000 px, et bascule vers la disposition mobile
sous 768 px.

## 7. Structure mobile

Cinq onglets, le troisième étant le « + » qui déplie vers le bas. Voir
[contrat-mobile.md](../03-contrats/contrat-mobile.md). La densité vient de
l'empilement : feuilles glissantes, accordéons, appuis longs — jamais de texte
rétréci.

---

## 8. Composants communs à écrire une seule fois

| Composant | Emploi | Rôles |
|---|---|---|
| `CoquilleApp` | Sidebar + navbar + panneau droit, accent injecté par rôle | Tous les rôles web |
| `BadgeStatut` | Pastille colorée + libellé, à partir du code de statut | Tous |
| `FriseStatut` | Étapes franchies, étape courante, étapes à venir | Client, vendeur, admin |
| `ListeDonnees` | Tableau avec tri, pagination, boutons-icônes, état vide | Tous |
| `EtatVide` | Illustration, phrase, action | Tous |
| `PanneauDetail` | Panneau droit générique | Tous |
| `PopupConfirmation` | Titre, conséquence, motif si requis | Tous |
| `ChampMontant` | Affiche des centimes en euros, sans jamais faire d'arithmétique | Tous |
| `CarteLivraison` | Carte, position, itinéraire | Livreur, client, admin |

**Le composant est écrit une fois et thématisé par variable CSS.** Écrire un
tableau « vendeur » et un tableau « admin » est le début de la divergence.

---

## 9. Ce qu'on emprunte aux CMS marchands, et ce qu'on n'emprunte pas

> Réponse au bloc C-11 : *« que dis-tu de copier le dynamisme et la beauté des
> produits des CMS ? »* — oui, et c'est même la bonne source d'inspiration.
> Shopify, PrestaShop et WooCommerce ont dix ans d'avance sur nous en ergonomie
> marchande, pour une raison simple : chaque détail y a été mesuré en chiffre
> d'affaires. Mais on emprunte **ce qui se voit**, pas leur architecture.

### Ce qu'on reprend

| Emprunt | Où | Pourquoi ça se remarque |
|---|---|---|
| **Galerie produit** : grande image, vignettes dessous, zoom à la loupe, défilement au doigt sur mobile | Fiche produit | C'est le premier réflexe d'un acheteur — une image unique non zoomable fait « maquette d'école » |
| **Carte produit vivante** : légère élévation au survol, image qui grandit un peu, bouton d'ajout qui apparaît | Catalogue | Transforme une grille figée en catalogue |
| **Squelettes de chargement** plutôt que roue qui tourne | Toutes les listes | Le contenu semble arriver deux fois plus vite, à durée réelle identique |
| **Filtres à facettes** avec compteur par option, dans un tiroir sur mobile | Catalogue | Répond à la règle d'or n°6 (tiroirs, panneaux) tout en étant utile |
| **Panneau panier qui glisse** depuis la droite après un ajout, avec message éphémère | Toutes les pages client | Confirme l'ajout sans quitter la page |
| **Badges** : « Nouveau », « −20 % », « Bientôt épuisé », « Rupture » | Cartes et fiches | Un coup d'œil suffit à comprendre l'état d'un produit |
| **Barre d'achat collante** qui apparaît en défilant sur la fiche produit | Fiche produit | Le bouton d'achat n'est jamais hors de portée |
| **Fil d'Ariane** et **carrousel « produits similaires »** | Fiche produit | Deux composants gratuits qui font paraître le catalogue plus grand |
| **Micro-animations de 150 à 200 ms** sur les états et l'ouverture des panneaux | Partout | En dessous, ça saute ; au-dessus, ça traîne |
| **Aperçu rapide** en fenêtre depuis le catalogue | Catalogue | Compare deux produits sans perdre sa position de défilement |

### Ce qu'on n'emprunte surtout pas

Constructeur de pages par glisser-déposer, moteur de thèmes, système de greffons,
traduction dynamique de l'interface, éditeur de contenu enrichi côté
administration. **C'est là que ces outils deviennent des usines à gaz** : ils
existent parce qu'un CMS doit servir cent mille boutiques inconnues. Nous en
servons une, dont on connaît le modèle de données. Chacune de ces briques
coûterait des semaines et ne se verrait pas dans la démonstration.

### Comment on l'obtient sans tout redessiner

Règle d'or n°5 appliquée à l'interface ([D-26](../00-pilotage/journal-decisions.md)) :

- **Tailwind CSS** pour la mise en page et les variables de thème — c'est lui qui
  porte l'accent de couleur par rôle de la section 2.
- **PrimeVue** pour les composants que la règle d'or n°6 impose et qui coûtent
  très cher à écrire correctement : tableaux triables et paginés avec
  boutons-icônes, fenêtres, tiroirs, messages éphémères, onglets, calendriers,
  téléversement de fichiers, et sa galerie d'images — exactement la galerie
  produit décrite plus haut.
- **Lucide** pour les icônes (section 5), en remplacement du jeu par défaut de
  PrimeVue, pour que web et mobile partagent les mêmes symboles (règle d'or n°7).
- Ionic apporte déjà ses propres composants côté mobile : on n'y met pas
  PrimeVue, on garde seulement les mêmes icônes, les mêmes couleurs et le même
  vocabulaire.

Le tableau de la section 8 reste valable : ces bibliothèques fournissent la
mécanique, nos composants fournissent le sens métier. `ListeDonnees` enveloppe le
tableau de PrimeVue, il ne le remplace pas — et le jour où l'on change de
bibliothèque, un seul fichier bouge.

---

## 10. Typographie et espacement

Une seule famille sans empattement (système ou Inter). Échelle : 12 / 13 / 15 /
18 / 22 / 28 px. Espacements par multiples de 4 px. Rayon des angles : 8 px pour
les petits éléments, 12 px pour les cartes. Une seule ombre douce pour les
éléments flottants.

---

## 11. Rédaction des messages

- On s'adresse à l'utilisateur, pas au système : « Votre commande a été annulée »,
  jamais « L'opération a échoué avec le code 409 ».
- Un message d'erreur dit **ce qui s'est passé** et **ce qu'on peut faire**.
- Les libellés d'action sont des verbes à l'infinitif : « Valider la commande ».
- Le vocabulaire vient du [glossaire](../00-pilotage/glossaire.md). Une
  « sous-commande » ne devient jamais un « lot » dans un écran.
