# État réel du code — ce qui existe, ce qui manque

> Vérification demandée au bloc H-11 : *« tu relis le dossier `plan-organisation`
> et tu vois si tout colle »*. Ce document est le **relevé du code réel**, pas
> une intention. Il est établi en listant les routes que l'API expose et les
> écrans que le front compile, puis en les confrontant au dossier de conception.
>
> Généré le 29 août, après la mise en cohérence des blocs G, H et I.

---

## Ce qui colle

| Décision | Où c'est appliqué | Vérifié par |
|---|---|---|
| **D-01** admin hors du web | `seed_admin`, aucune route publique | 3 tests |
| **D-02** entrée par rôle | inscription client actif, vendeur et livreur en attente | 4 tests |
| **D-03** catalogue et panier sans compte | routes publiques, panier à clé de session, fusion à la connexion | 10 tests |
| **D-04** vendeur ≠ gestionnaire | le personnel ajuste le stock, jamais les prix | 2 tests |
| **D-06** rupture : bouton gelé + alerte | fiche produit | — |
| **D-09** rayon Express | absent du catalogue au-delà du rayon | 4 tests |
| **D-10** découpage du panier | `commandes/decoupage.py` | 13 tests |
| **D-11** frais par bandes | `frais_livraison_centimes` | via le découpage |
| **D-13** suppression logique | retirer un produit le masque | 1 test |
| **D-15** réservation au paiement | `stock_reserve`, jamais décrémenté à l'ajout | 2 tests |
| **D-19** rien de durable sur le disque | Cloudinary actif, repli local documenté | manuel |
| **D-21** adresse partagée | `ADRESSE` reliée client / vendeur / entrepôt | migration |
| **D-24** photos | vérification du contenu réel, EXIF retiré, WebP | 6 tests |
| **D-25** haversine local | `coeur/geographie.py`, aucun appel réseau | 4 tests |
| **D-26** Tailwind + Lucide | tout le front | build |
| **D-29** l'argent visible par rôle | le vendeur voit sa part et la commission | manuel |
| **D-32** Django Admin = outil | `/admin/`, jamais lié depuis le produit | — |
| **D-33** accueil = catalogue public | route `/` publique | 16 tests |
| **D-34** panier avant le compte | clé de session, fusion | 10 tests |
| **D-35** facettes sur le résultat filtré | `meta.facettes` | manuel |
| **D-36** | CMS sur le contenu, regles d'or sur la structure | une seule coquille | 2 tests |
| **D-38** | une seule coquille | catalogue et espaces partagent la meme | 2 tests |
| **D-39** | panneau droit stable | replie en bande, jamais surgissant | manuel |
| **D-40** | un support par role | bandeau mobile cote livreur | manuel |
| **D-41** | la maquette fait foi | sidebar claire, navbar 56 px, filtres dans le contenu | manuel |
| **D-42** | session non collante en developpement | on enchaine les comptes librement | manuel |

**93 tests** : 73 backend, 20 front.

### L'interface suit la maquette, pas les CMS

Reprise au bloc I-2 : la sidebar est claire (`#fbfbfd`, 210 px, repliée à
64 px), la navbar fait 56 px avec sa recherche en pastille et son bloc avatar,
le panneau droit fait 300 px. Ni l'une ni l'autre ne défile — seul le contenu
défile. **Les filtres sont sortis de la sidebar** et vivent au-dessus de la
grille. Ce qui reste des CMS marchands se limite à l'affichage d'un produit :
carte avec survol, galerie, badges d'état.

---

## Ce qui existe, écran par écran

| Rôle | Écran | État |
|---|---|---|
| Visiteur | Catalogue, fiche produit, boutiques, rejoindre, panier, préparation de commande | **fait** |
| Client | Tout ce qui précède, plus le suivi de commandes | **fait** |
| Vendeur | Catalogue, fiche produit à trois onglets, photos, stock, commandes reçues | **fait** |
| Gestionnaire | Stock et commandes à préparer (mêmes écrans, droits réduits) | **fait** |
| Admin | Validations des vendeurs et livreurs | **fait** |
| Livreur | — | **mobile uniquement** ([D-40](journal-decisions.md)) |

**34 routes d'API**, **14 écrans web**.

---

## Ce qui manque, et pourquoi c'est assumé

| Manque | Pourquoi ce n'est pas encore là |
|---|---|
| **Paiement Stripe** | La commande se crée et réserve le stock ; le débit viendra brancher `PAIEMENT` et `REPARTITION_VENDEUR`, déjà modélisés. C'est le prochain gros morceau |
| **Livraison et tournées** | `LIVRAISON`, `TOURNEE`, `ARRET_TOURNEE` existent en base, sans code métier. Dépend du paiement : une livraison naît d'une commande payée |
| **Application mobile** | Le livreur travaille sur son téléphone ; lui faire un espace web serait du travail perdu. Ionic + Capacitor, décidé en [D-20](journal-decisions.md) |
| **Notifications et e-mails** | La table `NOTIFICATION` existe ; le canal in-app s'affichera dans le panneau droit, déjà en place |
| **Avis, litiges, promotions, factures** | Palier 2 assumé ([perimetre-et-mvp.md](../01-produit/perimetre-et-mvp.md)) |
| **Géocodage d'une adresse saisie** | Nominatim décidé ([D-25](journal-decisions.md)), pas encore appelé : les adresses de démonstration sont déjà géocodées |
| **Écrans gestionnaire d'entrepôt** | Dépendent des tournées |

---

## Les écarts trouvés en relisant le dossier

Trois documents décrivaient un état qui n'était plus vrai. Corrigés :

1. **`contrat-web.md`** annonçait un tunnel de commande « palier 1 » sans dire
   qu'il existe désormais — mis à jour.
2. **`correspondance-ecrans.md`** listait tous les écrans « à faire » alors que
   quatorze existent — mis à jour.
3. **`contrat-api.md`** ne mentionnait ni les routes de photos, ni celles de
   stock, ni `apercu-commandes` — complété.

Le **MCD et le dictionnaire de données n'ont pas bougé** : les 33 entités
prévues sont toutes en base, et aucune n'a dû être inventée en cours de route.
C'est le meilleur signe que la conception tenait.
