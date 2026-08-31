# Journal des décisions

> Une décision entre ici quand elle est tranchée. Elle en sort seulement si on
> la révise explicitement (on garde alors la trace de l'ancienne). Format :
> décision, pourquoi, ce que ça coûte, où ça se voit dans le projet.
>
> Les décisions D-01 à D-14 viennent du bloc A, D-15 à D-18 de la réorganisation
> (validées au bloc C), D-19 à D-27 du bloc C, D-28 à D-30 du bloc D.
> **Plus aucune décision n'est en attente de validation.**

---

## Décisions actées

### D-01 — Le premier admin est créé hors du web
Aucun formulaire public « devenir admin ». Le compte admin fondateur est créé
par une commande de gestion exécutée une fois au déploiement (`seed_admin`).
Les admins suivants sont créés par un admin depuis le back-office.
**Pourquoi** : un formulaire d'auto-inscription admin est une faille évidente.
**Voir** : [roles-et-parcours.md](../01-produit/roles-et-parcours.md).

### D-02 — Chaque rôle a un mode d'entrée différent
Client : auto-inscription libre. Livreur : auto-inscription puis validation
admin. Vendeur : candidature **ou** invitation admin, puis validation admin.
Gestionnaire staff vendeur : créé par son vendeur, jamais d'auto-inscription.
Gestionnaire staff entrepôt : créé par un admin. Admin : créé par un admin.
**Pourquoi** : le niveau de confiance requis n'est pas le même selon le rôle.

### D-03 — Le catalogue est consultable sans compte
Le compte n'est exigé qu'au moment de payer. Panier invité possible, fusionné
avec le panier du compte à la connexion.
**Coût** : il faut gérer un panier anonyme (cookie/session) et sa fusion.

### D-04 — Vendeur ≠ Gestionnaire
Le vendeur est propriétaire (prix, CA, responsabilité). Le gestionnaire est du
personnel opérationnel, sans accès aux prix ni au CA. Relation employeur →
employé, pas relation avec la plateforme.

### D-05 — Un seul rôle Gestionnaire, deux types
`type_gestionnaire` ∈ { `STAFF_VENDEUR`, `STAFF_ENTREPOT` }, exclusif. Le type
détermine qui l'a créé et ce qu'il voit.
**Pourquoi** : deux modèles séparés dupliqueraient l'authentification et les
écrans pour une différence qui tient à un périmètre de données.

### D-06 — Rupture de stock : bouton gelé + alerte de retour
Stock à 0 → « Ajouter au panier » grisé, non cliquable, accompagné de
« Être alerté quand disponible ». Le produit reste visible sauf masquage vendeur.

### D-07 — Annulation vendeur : motif obligatoire, notification forte
Push **et** email au client, remboursement automatique déclenché.

### D-08 — Le mode de service est porté par le vendeur
`type_activite` ∈ { `EXPRESS`, `STANDARD` } sur le vendeur. Une boutique qui
voudrait les deux ouvre deux boutiques.
**Pourquoi** : option simple, retenue explicitement au bloc A-21. Porter le mode
au niveau du produit rendrait le découpage du panier bien plus complexe.
**Coût** : un vendeur mixte (restaurant qui vend aussi du matériel) doit gérer
deux comptes boutique.

### D-09 — Catalogue Express filtré par rayon géographique
Un client ne voit jamais une boutique Express hors de son rayon. C'est ce
filtrage — et non les frais de livraison — qui rend structurellement impossible
la commande Express longue distance.
Standard : catalogue sans restriction de distance.
**Correction** de l'affirmation initiale « le catalogue est commun quel que soit
le service » : la **donnée** est commune (une seule table produit), c'est
l'**affichage** qui diffère.

### D-10 — Un panier produit N commandes (`CommandeSplitter`)
Au passage en caisse : lignes groupées par vendeur ; chaque vendeur Express
donne une commande indépendante ; tous les vendeurs Standard sont regroupés en
**une** commande multi-vendeur, décomposée en sous-commandes à la préparation.
Un seul checkout client, réparti par Stripe Connect.

### D-11 — Frais de livraison par bandes, pas au mètre près
Express : frais quasi-fixe par tranche de distance dans le rayon couvert.
Standard : frais par zone + seuil de livraison gratuite au-delà d'un montant,
pour inciter à grouper les achats sans jamais l'imposer.

### D-12 — Paiement : Stripe + Stripe Connect, confirmation par webhook
La confirmation définitive vient du webhook serveur-à-serveur, jamais du retour
navigateur. La répartition multi-vendeurs est faite par Stripe Connect, pas par
du code maison (règle d'or n°5).

### D-13 — Suppression toujours logique
Un compte, une boutique ou un produit ne sont jamais supprimés physiquement :
statut `SUSPENDU` / `DESACTIVE`, avec journal d'audit de qui a changé quoi.

### D-14 — Stack : Django + Vue obligatoires
Backend Python/Django + DRF, front web Vue 3 + Vite. Choix acté pour diversifier
par rapport au projet banque (NestJS/React) et multiplier l'apprentissage.
Le **mobile** a été tranché au bloc C : Ionic Vue + Capacitor (D-20), « Vue
Native » n'étant pas un produit vivant.

---

## Décisions issues de la réorganisation, validées au bloc C

### D-15 — Le panier n'affiche jamais un stock diminué
Le stock affiché est le stock réel, identique pour tout le monde, y compris pour
qui a déjà l'article dans son panier. La disponibilité est revérifiée sous verrou
transactionnel au moment du paiement, et une réservation courte (≈10 min) est
posée à la création de l'intention de paiement.
**Pourquoi** : la formulation du bloc A (« elle voit 0 alors qu'elle l'a dans son
panier ») produit une interface incompréhensible — le client croit que l'article
qu'il tient est épuisé. Le comportement décrit ici est celui de la quasi-totalité
des sites marchands : pas de réservation au panier, verrou au paiement.
**Voir** : [regles-metier.md](../01-produit/regles-metier.md).

### D-16 — Livraison MVP sans temps réel WebSocket
Le suivi de commande et de livraison se fait par interrogation périodique
(*polling*) côté client au MVP ; les WebSockets (Django Channels) passent en V2.
**Pourquoi** : Channels impose un serveur ASGI **et** un Redis, ce qui multiplie
le coût et la fragilité de l'hébergement gratuit pour un confort d'affichage.
**Coût** : latence de quelques secondes sur le suivi — invisible pour le client,
et cela reste démontrable en entretien.

### D-17 — ~~Express d'abord, Standard ensuite~~ → **révisée au bloc C**
**Décision d'origine (abandonnée)** : ne faire que l'Express au premier palier.
**Décision retenue** : le circuit **Standard, l'entrepôt et les tournées font
partie du MVP**, au même titre que l'Express (bloc C-7 et C-13).
**Pourquoi** : sans entrepôt, ni les produits Standard ni les livreurs Standard
n'ont de sens — le circuit ne tient pas debout à moitié. Et c'est précisément le
double régime qui rend le projet intéressant à raconter en entretien ; le couper
en deux revenait à risquer de ne montrer que la moitié banale.
**Coût** : le MVP est plus gros. On le compense par un **ordre de construction**
(l'Express est terminé avant que le Standard commence) sans que le périmètre du
MVP change. Voir [perimetre-et-mvp.md](../01-produit/perimetre-et-mvp.md).

### D-18 — Les services externes payants sont derrière une interface, avec un simulateur
Stripe, l'envoi d'e-mails, les notifications push et l'appel masqué client/livreur
sont appelés à travers une interface interne, avec deux implémentations : la
vraie et un **simulateur** utilisable hors ligne et en démonstration.
**Pourquoi** : c'est exactement ce qui a sauvé le projet banque (`simulateur-reseau`),
ça rend la démonstration recruteur possible sans dépendre d'un compte payant, et
c'est un excellent sujet d'entretien (inversion de dépendance, testabilité).

---

## Décisions issues du bloc C

### D-19 — Hébergement : Vercel pour le front, Render pour l'API, Neon pour la base
Tu proposais Vercel pour les deux, Render en repli. Voici l'état réel :

| | Ce que Vercel fait du Django | Ce que Render en fait |
|---|---|---|
| Exécution | Fonction sans état, redémarrée à chaque appel | Conteneur Docker qui tourne en continu |
| Fichiers envoyés | Disque effacé à chaque appel → **les photos produit disparaissent** | Disque effacé aussi au redémarrage, mais on n'en dépend pas |
| Tâches de fond, `migrate` | Impossible depuis l'hébergeur | Commande au démarrage du conteneur |
| Durée maximale d'une requête | ~10 s en offre gratuite | Pas de coupure de ce type |
| Mise en veille | Aucune | **Après 15 min sans trafic**, réveil ~1 min |

**Décision** : front Vue sur **Vercel** (c'est exactement son métier), API Django
en **conteneur Docker sur Render**, base sur **Neon**, images sur **Cloudinary**.
Tu avais écarté Render au départ ; tu l'as rouvert au bloc C-1, et c'est
aujourd'hui le seul hébergeur gratuit qui exécute un conteneur Django complet
sans carte bancaire.
**Le vrai piège n'est pas Render, c'est la mise en veille** : le jour de
l'entretien, une API endormie donne une page blanche pendant une minute. Parade
écrite dans [contrat-deploiement.md](../03-contrats/contrat-deploiement.md) :
une tâche GitHub Actions qu'on active **le jour de la démonstration seulement**
réveille l'API toutes les dix minutes, et le front affiche « réveil du serveur… »
au lieu d'une page morte.
**Coût** : aucun en euros. La contrainte est que rien de durable ne doit vivre
sur le disque de l'API — ce qui est de toute façon la bonne pratique.
**Réversibilité** : l'API est un conteneur Docker standard, sans rien de propre à
Render. Changer d'hébergeur coûte une journée, pas une réécriture.

### D-20 — Mobile : Ionic Vue + Capacitor
Tu valides la recommandation de Q-01. Vue 3 standard, application Android
réellement installable (`.apk`), accès GPS / caméra / notifications par des
greffons Capacitor maintenus.
**Pourquoi pas NativeScript-Vue** : écosystème trop mince pour la géolocalisation
continue du livreur, risque réel de blocage de plusieurs semaines.
**En entretien** : « pourquoi Capacitor et pas du natif » est une bonne question
à laquelle tu auras une bonne réponse — coût de possession contre gain de rendu.

### D-21 — ADRESSE est une entité partagée
Une seule table `ADRESSE`, rattachable à un client (carnet d'adresses), à un
vendeur (adresse de boutique) et à un entrepôt.
**Pourquoi** : le filtrage Express par rayon (D-09) et les frais par bandes
(D-11) exigent une latitude et une longitude **des deux côtés** du trajet. Sans
adresse de boutique, ces deux décisions sont inapplicables.
**Où c'est écrit exactement** : [dictionnaire-donnees.md](../02-modele/dictionnaire-donnees.md),
zone 1, section `ADRESSE` — et désormais dessiné dans
[mcd.html](../02-modele/mcd.html) (associations A6 `POSSEDER`, A7 `SE_SITUER_A`,
A44 `IMPLANTER`).

### D-22 — Le visiteur choisit sa ville dans un bandeau « Livrer à … »
Tant qu'aucune position n'est connue, le catalogue Standard s'affiche
normalement et le bloc Express invite à saisir une ville, avec proposition de
géolocalisation du navigateur. Jamais de catalogue Express vide sans explication.

### D-23 — Deux tentatives de livraison gratuites, puis retour
Après deux tentatives infructueuses : retour au vendeur (Express) ou à l'entrepôt
(Standard), remboursement du produit, frais de livraison retenus. Le client est
prévenu à chaque tentative et peut reprogrammer entre les deux. Point relais en
palier 2.

### D-24 — Photos produit : envoyées par le vendeur, stockées chez Cloudinary
Le vendeur téléverse ses images depuis son ordinateur ou son téléphone (glisser-
déposer ou sélecteur de fichiers), jusqu'à six par produit, la première servant
de vignette. La base ne stocke **que des URL**, jamais les binaires. Détail
complet du parcours, des formats et des tailles :
[contrat-medias.md](../03-contrats/contrat-medias.md).
**Conséquence sur le modèle** : nouvelle entité `PHOTO_PRODUIT` (un produit a
plusieurs photos ordonnées) — c'était un manque du modèle précédent.
**Pour les images de démonstration, tu n'as rien à faire** : le script de
peuplement va chercher lui-même des photos sous licence libre (Unsplash, Pexels)
à partir d'une liste figée, avec repli sur une image générée si la machine est
hors ligne. Si tu veux un catalogue à ton goût, tu peux déposer tes propres
fichiers dans `donnees-demo/images/` et ils prendront le dessus.

### D-25 — Géocodage gratuit : Nominatim, distances calculées en local
Transformer une adresse en latitude/longitude passe par **Nominatim**
(OpenStreetMap), gratuit, sans carte bancaire, appelé une seule fois à la
création ou à la modification d'une adresse — jamais à chaque affichage. La
distance entre deux points est calculée localement (formule de haversine), sans
appel réseau.
**Pourquoi pas Google Maps** : exige une carte bancaire dès l'inscription pour
un besoin que trente lignes de code couvrent ici.
**Limite assumée** : la distance à vol d'oiseau n'est pas la distance routière.
Pour des bandes de frais (D-11), c'est suffisant — et c'est une limite qui se
dit très bien en entretien.

### D-26 — Interface : Tailwind CSS + PrimeVue, en s'inspirant des CMS marchands
Réponse au bloc C-11. On reprend des CMS marchands **ce qui se voit** — galerie
d'images avec zoom, cartes produit vivantes, chargement par squelettes, filtres à
facettes, panneau panier qui glisse, badges, micro-animations — et **rien de leur
architecture** (pas de constructeur de pages, pas de moteur de thèmes, pas de
système de greffons : c'est là que ces outils deviennent des usines à gaz).
Pour ne pas redessiner à la main les tableaux, fenêtres, tiroirs et notifications
que la règle d'or n°6 impose : **PrimeVue** (gratuit, complet, très bon pour les
back-offices) posé sur **Tailwind CSS**, icônes **Lucide**.
Le détail est dans [design-system.md](../04-maquettes/design-system.md).

### D-27 — Un seul endroit pour ce que j'attends de toi
Réponse au bloc C-6. Un fichier unique,
[ta-part-du-travail.md](ta-part-du-travail.md) : ce que tu dois installer, créer,
décider et vérifier, dans l'ordre, avec la commande exacte. Mes questions restent
dans [questions-ouvertes.md](questions-ouvertes.md), tes demandes restent dans
`questions.txt`. Trois fichiers, trois usages, aucun recouvrement — un dossier de
plus n'apporterait rien qu'un endroit où chercher.

---

## Décisions issues du bloc D

### D-28 — Les retours de produits en bon état sont hors périmètre
Le litige couvre le produit défectueux, non conforme ou jamais reçu. Le retour
d'un article en bon état (droit de rétractation) n'est **pas** traité : il
demanderait un circuit complet — demande, étiquette de retour, réception,
contrôle, remboursement — pour une mécanique qui ne se voit pas en démonstration.
**Tranche [Q-07](questions-ouvertes.md) fermée** : tu suis la recommandation.
**Comment on l'assume** : c'est écrit dans les limites connues de
[perimetre-et-mvp.md](../01-produit/perimetre-et-mvp.md). En entretien, « je ne
l'ai pas fait, et voici pourquoi » vaut mieux qu'un circuit à moitié fait.

### D-29 — Chaque rôle voit l'argent qui le concerne
Le vendeur lit « vous touchez 8,50 €, la plateforme retient 1,50 € » sur chaque
commande ; le livreur lit « cette course vous rapporte 4,20 € » ; l'admin voit la
commission encaissée. **Tranche [Q-08](questions-ouvertes.md) fermée**.
**Pourquoi** : les montants existent déjà dans le modèle (`taux_commission`,
`montant_commission_centimes`, `remuneration_livreur_centimes`) — les afficher ne
coûte que des écrans. Et une plateforme où l'on ne voit jamais d'argent ne
ressemble pas à une plateforme.

### D-30 — ~~Le produit s'appelle Colibri~~ → **le produit s'appelle RivDinde**
Les quatre premières lettres écrivent **coli**s ; l'oiseau est à la fois le plus
rapide et le seul qui sache faire du surplace — l'Express et le Standard dans un
seul mot français, qui se prononce et s'écrit sans hésiter.
La marque, son relief, ses déclinaisons et ses règles d'usage sont dans
[identite-visuelle.html](../04-maquettes/identite-visuelle.html), avec trois
autres noms rendus dans le même logo pour comparer.
**Réserve honnête** : « Colibri » est un nom de marque répandu en France et
`colibri.fr` est certainement pris — sans conséquence pour un projet de
portfolio.
**Ce qui attend ta validation** : le nom n'est appliqué qu'à l'identité visuelle
et au README. La propagation au reste du dossier et au code est une seule
opération, faite le jour où tu dis oui — ou avec un autre nom, à coût identique.

**Bloc F — tranché : c'est RivDinde**, et tu as fourni le logo toi-même : une
dinde en rendu 3D perchée sur un « R » en peluche, exactement ce que tu décrivais
au bloc E-3 et que le dessin vectoriel ne pouvait pas rendre.

Ce que ça implique, et qui est fait :
- La marque a **deux objets** : la mascotte pour les grandes surfaces, et un
  **monogramme « R »** en SVG pour l'onglet du navigateur et l'icône de
  l'application — une dinde détaillée devient une tache à 16 pixels.
- Le logo fourni pesait **1,98 Mo sans transparence** : inutilisable tel quel.
  Il est décliné en 512, 256 et 192 pixels au format WebP — **28 Ko** pour la
  version affichée, soixante-dix fois plus léger, sans perte visible.
- La palette de la marque est **échantillonnée dans le logo lui-même** :
  `#2a160f` (le fond, 74 % de l'image), `#ea8c2a` et `#d46f1d` (l'orange du
  mot), `#9e5329` et `#592d19` (le brun de la peluche).
- Le nom est propagé partout : code, conteneurs, base de données, intégration
  continue, documents. 59 occurrences.
- La source haute définition est rangée dans
  `04-maquettes/marque/rivdinde-logo-source.png` : c'est d'elle qu'on
  régénérera toute déclinaison future.

**Pourquoi pas Colibri, pour mémoire** : je le recommandais parce qu'il cache
« colis » et qu'il ne prête pas à sourire. Tu as choisi un nom qui porte ton
prénom et dont tu avais déjà l'image en tête — c'est un argument que je n'avais
pas, et c'est ta décision.

### D-31 — Le compte administrateur est créé par `seed_admin`, appelé au démarrage
La commande `python manage.py seed_admin` applique la décision
[D-01](#d-01--le-premier-admin-est-créé-hors-du-web) : elle crée le compte
fondateur en base, hors de toute interface web. Elle est **idempotente**, et
**ne touche jamais au mot de passe d'un compte existant** — sans quoi chaque
`demarrer.py` changerait le mot de passe de l'admin.
Sans `ADMIN_MOT_DE_PASSE` et en développement, elle engendre un mot de passe fort
et l'affiche **une seule fois** ; hors développement, elle refuse de démarrer
plutôt que d'écrire un mot de passe dans les journaux de l'hébergeur.
**Pourquoi cette décision existe** : au bloc E-5, `/admin/` demandait des
identifiants que personne ne possédait. `demarrer.py` appelle désormais la
commande à chaque lancement, pour que le cas ne se reproduise jamais.

### D-32 — Le Django Admin est un outil de développement, pas l'interface du produit
`/admin/` est le back-office engendré par Django, activé en deux lignes et
**écrit par personne**. Il sert à inspecter et corriger des données pendant le
développement, à dépanner en exploitation, et à montrer le modèle en trente
secondes en entretien.
**Ce qu'il n'est pas** : l'interface du produit. Les écrans des cinq rôles sont
ceux de l'application Vue et de l'application Ionic, décrits dans
[contrat-web.md](../03-contrats/contrat-web.md) et
[contrat-mobile.md](../03-contrats/contrat-mobile.md), avec la sidebar, le
panneau droit et les cinq onglets qu'imposent les règles d'or 6 à 8.
**Pourquoi ce n'est pas une entorse à la règle d'or n°5** : c'est l'inverse.
Un back-office technique gratuit et sécurisé qui apparaît en deux lignes, s'en
priver pour coder des écrans que personne ne verra serait réinventer la roue.
**En production** : conservé, réservé aux comptes `is_superuser`, jamais lié
depuis le produit. Explication complète dans
[de-nestjs-react-a-django-vue.md](../05-execution/de-nestjs-react-a-django-vue.md) § 5.

### D-33 — La page d'accueil est le catalogue, et elle est publique
Trois niveaux d'accès, portés par chaque route : **public** (catalogue, fiche
produit, page « rejoindre »), **auth** (connexion, inscription) et **privé**
(les espaces de travail). Après connexion, un **client revient sur la vitrine**
— c'est là qu'il commande ; les autres rôles entrent dans leur espace.
**Pourquoi cette décision existe** : j'avais mis l'accueil derrière la
connexion, ce qui contredisait frontalement [D-03](#d-03--le-catalogue-est-consultable-sans-compte).
Tu l'as relevé au bloc G-4 : *« le visiteur qui devient client, est-ce qu'il a
cette page ? […] la première page est fausse »*. Un futur client, un futur
vendeur et un futur livreur arrivent tous sur la même page publique, regardent,
puis décident de s'inscrire. Aucune plateforme marchande ne fait autrement.
**Ce que ça a entraîné** : une enveloppe publique (en-tête, bandeau
« Livrer à … », recherche, pied de page), une page **Rejoindre** qui explique à
un futur vendeur ou livreur ce qu'il gagne et ce qu'on lui demande avant de lui
présenter un formulaire, et **seize tests** qui verrouillent les règles d'accès.

### D-34 — Le panier existe avant le compte, et il suit le visiteur
Un visiteur sans compte remplit son panier : il est identifie par une clé qu'il
engendre lui-même et garde dans son navigateur. **À la connexion, le serveur
fusionne ce panier avec celui du compte.** Application directe de
[D-03](#d-03--le-catalogue-est-consultable-sans-compte) — sans cette fusion, un
visiteur qui remplit son panier puis s'inscrit le retrouve vide, et il ne
revient pas.
**Ce que le panier montre déjà** : le prix **courant** et non celui capturé à
l'ajout, avec un avertissement si le prix a changé (R-05) ; le nombre de
boutiques, parce qu'un panier multi-boutique donnera plusieurs commandes
([D-10](#d-10--un-panier-produit-n-commandes-commandesplitter)) et qu'il vaut
mieux le dire au panier qu'à la surprise du paiement ; et un refus net quand le
stock ne suit pas.

### D-35 — Les compteurs de facettes se calculent sur le résultat filtré
Les nombres affichés à côté de chaque catégorie et de chaque boutique décrivent
**ce qui est réellement visible**, après le filtrage géographique et la
recherche. Ils sont calculés par le serveur et renvoyés dans `meta.facettes`.
**Pourquoi** : un visiteur parisien voyait « Plats 4 » alors qu'aucun plat ne lui
était livrable — les boutiques Express lyonnaises étant hors de son rayon
([D-09](#d-09--catalogue-express-filtré-par-rayon-géographique)). Un compteur qui
ment est pire que pas de compteur.
**Effet de bord voulu** : les catégories sont regroupées en **univers**
(Restauration, High-tech) grâce à la réflexivité déjà prévue au modèle. Sept
catégories à plat ne se lisent pas ; deux univers, oui.

### D-36 — En cas de conflit, l'usage des CMS marchands l'emporte sur les règles d'or
Tes règles d'or 6 à 8 décrivent l'interface que tu avais en tête au départ :
sidebar rétractable, navbar, panneau droit, onglets, cinq onglets en bas sur
mobile. **Elles restent la règle par défaut.** Mais quand l'une d'elles entre en
conflit avec la façon dont les plateformes marchandes font réellement les
choses, c'est l'usage marchand qui gagne — sans qu'on ait à reposer la question.
**Ta formulation, bloc H-4** : *« le CMS est supérieur aux règles d'or, retiens
ça fortement. »*
**Pourquoi c'est juste** : ces plateformes ont mesuré chaque détail en chiffre
d'affaires. Leur ergonomie n'est pas affaire de goût, et un recruteur reconnaît
immédiatement une interface qui suit ces codes.
**Ce que ça a déjà changé** : la page d'accueil est le catalogue et non un
tableau de bord ; le panier est un panneau qui glisse avec un compteur dans
l'en-tête, pas une page ; la recherche est instantanée et centrale ; les filtres
sont à facettes avec compteurs.
**Ce qu'on n'emprunte toujours pas** : leur architecture — constructeurs de
pages, moteurs de thèmes, systèmes de greffons.

### D-37 — Un test ne touche jamais le réseau
Toute la suite force le stockage local des images, même quand des clés
Cloudinary sont présentes dans `backend/.env` (`conftest.py`).
**Pourquoi cette décision existe** : dès que tu as renseigné tes clés, trois
tests se sont mis à téléverser pour de vrai — et à échouer. Un test doit passer
dans un train, dans une chaîne d'intégration sans secrets, et donner le même
résultat à chaque exécution.

### D-38 — Une seule coquille pour tout le site
Sidebar rétractable à gauche, navbar en haut, panneau rétractable à droite : la
même structure habille **le catalogue public et les espaces de travail**. Un
visiteur, un client et un vendeur voient le même cadre ; seul le contenu change.
Un visiteur porte l'accent vert du client, puisque c'est ce qu'il s'apprête à
devenir.
**Pourquoi cette décision existe** : j'avais construit la vitrine avec une
disposition en-tête + pied de page, différente de celle des espaces. Ton
constat, bloc H-6 puis H-8 : *« le catalogue et l'espace client sont trop
différents […] fais-moi un truc cohérent, du début à la fin. »*
**Ce que ça a supprimé** : cinq composants devenus inutiles — la coquille les
remplace tous.

### D-39 — Le panneau de droite est stable, pas surgissant
Il occupe une colonne de la page et se **replie en bande** où le compteur du
panier reste visible. Ce n'est jamais une fenêtre qui apparaît par-dessus la
page avec un voile.
**Ta formulation, bloc H-7** : *« le panier est une fenêtre qui apparaît à
droite et redisparaît, alors que ça devait être stable mais rétractable. »*

### D-40 — Chaque rôle sur son support, et un seul
| Rôle | Support |
|---|---|
| Client | **Web et mobile** — il achète sur les deux |
| Livreur | **Mobile uniquement** — une main sur le guidon |
| Vendeur, gestionnaire, admin | **Web uniquement** — ce sont des postes de travail |

**Ta formulation, bloc H-9** : *« le livreur est mobile, le client mobile plus
web, et le reste web. »* L'espace web d'un livreur affiche donc un bandeau qui
le renvoie à l'application mobile, plutôt que des écrans à moitié utiles.

### D-41 — La maquette fait foi pour l'interface
 est **la référence**, pas une inspiration parmi
d'autres : sidebar claire de 210 px sur fond , navbar de 56 px avec
recherche en pastille et bloc avatar, panneau droit de 300 px, et le vocabulaire
de contenu — cartes à en-tête, lignes, badges, KPI, onglets soulignés,
boutons-icônes dans les listes.
**Ce que ça retire à [D-36](#d-36--en-cas-de-conflit-lusage-des-cms-marchands-lemporte-sur-les-règles-dor)** :
l'emprunt aux CMS marchands se limite désormais à **l'affichage d'un produit**.
Ta formulation, bloc I-2 : *« enlève tout ce qui concerne le CMS, sauf leur
intervention sur un produit ; utilise exactement le même modèle que la maquette.
Ça nous a gâté le travail. »*
**Deux règles nommées, à ne pas réessayer** : aucun filtre dans la sidebar —
ils vont au-dessus de la grille ; et la sidebar comme la navbar ne défilent
jamais, seul le contenu défile.

### D-42 — La reconnaissance automatique d'un compte attend la production
Un vendeur ou un client déjà inscrit ne sera reconnu d'une visite à l'autre
qu'au déploiement. **En développement, on doit pouvoir enchaîner plusieurs
comptes** pour tester les cinq rôles — c'est ta remarque du bloc I-2, et elle
est juste : une session collante rendrait la démonstration pénible.

### D-43 — Agent IA : recommandations d'abord, assistant de support ensuite
Tu as répondu au bloc I-6 : *« option A et B si les deux sont possibles à la
fois, sinon B, et un modèle API »*. Les deux sont possibles — ils ne partagent
rien — donc les deux, dans cet ordre :

1. **Recommandations** « souvent achetés ensemble », alimentées par l'historique
   de commandes. C'est le plus visible en démonstration et le moins risqué.
2. **Assistant de support** : répondre aux questions fréquentes — où est ma
   commande, comment annuler — avant escalade vers un humain.

**Modèle appelé par API**, comme tu l'as tranché. Conséquence à assumer : une
clé, un coût à l'appel, et une dépendance réseau. L'appel passe donc par une
interface avec simulateur ([D-18](#d-18--les-services-externes-payants-sont-derrière-une-interface-avec-un-simulateur)),
pour que la démonstration tienne sans compte actif.
**Ferme [Q-09](questions-ouvertes.md).**

### D-44 — Les tournées sont optimisées dès le MVP
Tu as écrit : *« c'est pour le MVP, sinon le livreur Standard fonctionne
comment ? »* La remarque est juste — une tournée non ordonnée n'est pas une
tournée, c'est une liste.

Au MVP : ordonnancement par **plus proche voisin** depuis l'entrepôt, calculé en
local avec la formule de haversine déjà écrite ([D-25](#d-25--géocodage-gratuit--nominatim-distances-calculées-en-local)).
Simple, sans dépendance, et déjà très supérieur à un ordre d'arrivée.
Le solveur de tournées de véhicules (OR-Tools) reste en palier 2 : il apporte
quelques pour cent sur des tournées de trente arrêts, pas sur des tournées de
cinq. **Ferme [Q-10](questions-ouvertes.md).**

### D-45 — Les promotions sont créées par le vendeur ET par l'admin
Ta réponse au bloc I-6 : *« les deux »*. Le modèle le prévoyait déjà —
`PROMOTION.vendeur` est facultatif, vide signifiant « promotion plateforme ».
Un vendeur ne crée que des promotions sur sa boutique ; un admin en crée pour
toute la plateforme. **Ferme [Q-11](questions-ouvertes.md).**

### D-46 — Le panneau droit dépend du rôle
Le panier n'a de sens que pour qui achète. Un vendeur, un gestionnaire ou un
admin voient à la même place, avec le même comportement rétractable, un
**panneau d'activité** : changements de statut, alertes, notifications.
**Ta remarque, bloc I-7** : *« Espace vendeur, livreur, gestionnaire, admin :
son panneau droit c'est le panier, pourquoi ? »* — et la question suivante,
*« tu es sûr que c'est ce qui se passe dans les vrais e-commerce ? »*, valait
aussi pour la navigation : **un back-office ne renvoie pas au catalogue
public**. Ces entrées ont été retirées des espaces vendeur et admin.

### D-47 — Un test refuse les classes CSS qui ne mènent à rien

Une classe utilitaire Tailwind qui pointe vers un jeton absent du thème ne
produit **aucun style** : ni erreur, ni avertissement. Deux fois de suite, un
renommage dans `style.css` a ainsi rendu un écran illisible — texte blanc sur
fond blanc — sans qu'aucun test ne bronche.

`frontend-web/src/jetons.test.ts` lit le thème, lit tous les écrans, et échoue
sur toute couleur ou toute classe de composant qui n'existe pas. Un second test
vérifie que **chaque entrée de barre latérale mène à une route déclarée**.

**Ta formulation, bloc J-1** : *« tous ça sont en blanc et illisible ».*
**Pourquoi** : la seule protection contre une erreur invisible est une
vérification automatique ; l'œil ne repasse pas sur quarante écrans.

### D-48 — Les écrans de connexion et d'inscription sont clairs, comme le reste

Ils étaient écrits pour un fond sombre hérité d'une version précédente. La
maquette est claire, et il n'y a **qu'une seule identité visuelle** : le fond
`#f4f5f8`, l'encre `#0f1420`, et l'orange de la marque réservé aux boutons qui
parlent de la plateforme elle-même.

### D-49 — Le stock se corrige en quantité réelle, dans une popup

La maquette décrit une popup « Ajustement de stock » avec **Nouvelle quantité**
et un **motif** à choisir. C'est ainsi qu'on fait un inventaire : on compte ce
qu'il y a sur l'étagère, on ne calcule pas de tête l'écart avec ce que l'écran
affiche. Le serveur accepte les deux formes (`nouvelle_quantite` ou `quantite`)
et déduit l'écart, qu'il trace.

Corollaire : **« Mettre en rupture » est une action à part entière**, dans la
liste du catalogue comme dans la popup. Déclarer un produit épuisé est le geste
le plus fréquent d'un commerçant ; l'obliger à saisir « -26 » n'avait pas de
sens.

### D-50 — Le personnel ne reçoit pas le chiffre d'affaires, le serveur s'en assure

[D-04](#d-04--vendeur--gestionnaire) l'interdisait déjà, mais le tableau de bord
renvoyait `revenu_centimes` à tout le monde et l'interface le masquait. **Masquer
n'est pas une permission.** Le champ ne quitte plus le serveur quand l'appelant
est un gestionnaire, et un test le vérifie.

Le même passage a corrigé l'inverse : le personnel recevait un **403 sur la
liste des produits**, donc son écran de stock — le seul de son métier — ne
s'ouvrait pas.

### D-51 — Le jeu de données de démonstration couvre tous les états

`seed_activite` crée des commandes dans **chacun de leurs statuts**, des
livraisons dans chacun des leurs, des tournées de brouillon à terminée, des
avis publiés et signalés, des litiges ouverts et résolus, des notifications lues
et non lues.

**Ta formulation, bloc J-7** : *« fais un vrai jeu de données très vaste avec
toutes les possibilités et éventualités ».*
**Pourquoi** : un écran confronté pour la première fois à un cas le jour de la
démonstration est un écran qui casse. Et un tableau de bord qui n'affiche que
des zéros ne se montre pas à un recruteur.

### D-52 — Une seule liste pour tout le projet, avec ses boutons-symboles

Chaque écran réinventait sa liste : l'un en tableau, l'autre en lignes, un
troisième avec un dépliant. Trois grammaires pour une seule idée, et des
boutons d'action présents une fois sur deux.

`frontend-web/src/composants/Liste.vue` reprend `Tableau.tsx` du projet banque :
colonnes déclarées, recherche, tri, pagination, état vide rédigé, et surtout
des **boutons-symboles en fin de ligne pour consulter et gérer**.
`ActionLigne.vue` garantit les trois choses qu'on oublie une fois sur deux :
infobulle, libellé accessible, état désactivé qui reste survolable.

**Ta formulation, bloc K-1** : *« les listes sont mal gérées ; les boutons sous
forme de symboles pour consulter et gérer les données comme le projet banque,
au lieu d'une liste déroulante — ici je suis sérieux, je veux les symboles pour
toutes les listes du projet, tous les rôles. »* C'est aussi la règle d'or n°9,
posée dès le bloc A.

### D-53 — Le panneau droit appartient à l'écran en cours

Il affichait la même chose partout, donc rien d'utile nulle part. Repris de
`useVolet` du projet banque : chaque écran **dépose** dans le volet ce qui
mérite d'être gardé près de l'œil — le colis consulté, les arrêts d'une
tournée, le détail d'une commande avec son unique bouton d'avancement. Sans
contribution de l'écran, le volet retombe sur l'activité récente.

**Ta formulation, bloc K-1** : *« le panneau droit des autres rôles n'a rien,
pourquoi ? »* — parce qu'aucun écran ne le nourrissait.

### D-54 — Un panier ne se bloque jamais tout entier

Une seule ligne devenue indisponible faisait échouer l'aperçu de commande en
409. L'écran affichait « votre panier est vide » alors que le panneau latéral
montrait quinze articles, et rien ne disait quoi enlever. C'est ce qui se
cachait derrière *« le bouton passer la commande ne fonctionne pas »* (K-1).

Désormais : l'**aperçu est tolérant** — il liste nommément ce qui bloque et
chiffre le reste —, la **création reste stricte** — on ne facture rien
d'indisponible —, et une route `POST /panier/nettoyer` retire les articles
fautifs d'un geste.

### D-55 — Le panier disparaît avec la session

Le panier restait affiché après déconnexion : les articles du compte qui venait
de partir s'affichaient encore à la personne suivante devant la machine. Le
serveur, lui, renvoyait bien un panier vide. La déconnexion vide désormais le
magasin et régénère la clé de panier du navigateur.

### D-56 — On ne note que ce qu'on a reçu, et seulement sa propre commande

L'avis n'existait nulle part alors que la table était en base depuis le début
(K-1 : *« le client ne peut pas donner son avis »*). Il est servi par
`GET/POST /commandes/{id}/avis`, avec quatre refus vérifiés côté serveur :
commande non livrée (409), commande d'un autre client (404), cible absente de
la commande (400), note hors de 1–5 (400). Le client note la boutique, chaque
produit reçu et le livreur — jamais autre chose.

### D-57 — PrimeVue est enregistré, et la stack suit celle du projet banque

[D-26](#d-26--interface--tailwind-css--primevue-en-sinspirant-des-cms-marchands)
impose PrimeVue depuis le bloc C, et pour une raison précise : *« pour ne pas
redessiner à la main les tableaux, fenêtres, tiroirs et notifications que la
règle d'or n°6 impose »*. J'avais laissé PrimeVue **installé mais non
enregistré**, en arguant du poids de son thème, puis j'ai redessiné à la main
les quatre choses qu'il devait fournir.

**Ta formulation, bloc K** : *« tu n'utilises pas les équivalents de MUI, hot,
hook, react router, rien n'est beau, rien ne ressemble au projet existant. »*

La correspondance appliquée, tirée de `banque-app/frontend-web/package.json` :

| Projet banque (React) | RivDinde (Vue) |
|---|---|
| `@mui/material` | **PrimeVue**, thème `Aura` dérivé sur les jetons de la maquette |
| `@tanstack/react-query` | **`@tanstack/vue-query`** |
| `react-hot-toast` | **service `Toast` de PrimeVue**, derrière `useNotification()` |
| `react-hook-form` + `zod` | **`vee-validate` + `zod`** |
| `react-router-dom` | `vue-router` — déjà en place |

**Ce que ça coûte** : le paquet passe de 166 à 479 Ko (132 Ko compressés). Le
compte est honnête, et c'est le prix d'une interface qui ressemble à quelque
chose de connu plutôt qu'à un assemblage maison.

**Ce que ça rapporte** : le tri, la pagination, le piège de focus des fenêtres,
le retour du focus au bouton d'origine, les rôles ARIA et la navigation au
clavier ne sont plus à écrire — ni à oublier.

La couleur primaire du thème pointe sur `--accent`, la variable posée par la
coquille selon le rôle : un tableau, une fenêtre et un toast prennent donc
automatiquement le bleu du vendeur ou le rouge de l'admin, sans qu'aucun
composant ne sache quel rôle est connecté ([règle d'or n°8](regles-d-or.md)).

### D-58 — Une colonne triable déclare un champ, jamais un comparateur

La première version de `Liste.vue` passait un comparateur à `sortFunction`.
**Cette option n'existe pas dans PrimeVue 5** : l'attribut partait dans le DOM,
et le tri ne faisait **rien** — sans erreur, sans avertissement. Une colonne
qui ne trie pas ressemble exactement à une colonne qui trie.

Une colonne déclare donc `champTri`, la propriété réelle de la ligne sur
laquelle trier, et le type l'impose. Un test clique l'en-tête et vérifie que
les lignes **changent effectivement d'ordre**, dans les deux sens.

C'est la même famille d'erreur que les jetons CSS absents ([D-47](#d-47--un-test-refuse-les-classes-css-qui-ne-mènent-à-rien)) :
une chose qui ne produit ni exception ni test rouge doit être protégée par une
vérification automatique, jamais par de l'attention.

### D-59 — La ligne entière est cliquable

*« Ce n'est pas cliquable, c'est bizarre »* (bloc K). Seul le petit bouton en
bout de ligne réagissait ; le reste de la ligne était inerte, ce qui donne une
impression d'écran mort. Cliquer une ligne fait désormais la même chose que son
bouton « consulter », la ligne sélectionnée porte l'accent du rôle en filet à
gauche, et les boutons d'action arrêtent la propagation pour ne pas déclencher
les deux à la fois. Un test le vérifie.

---

# Bloc L — les décisions

> Chaque remarque du bloc L, y compris les sous-remarques, a sa décision ici.
> Elles sont écrites **avant** le code, comme demandé en L-13.

## L-A — Les règles transversales

### D-60 — Trois niveaux d'interaction, et un seul choix possible à chaque fois

Tu demandais une règle plutôt qu'un arbitrage écran par écran. La voici, et
elle s'applique partout sans exception :

| Ce que l'action demande | Ce qu'on ouvre |
|---|---|
| Rien de plus que le geste (marquer lu, ajouter au panier, accepter une course) | **Rien** — exécution directe, un toast pour confirmer |
| Voir un peu plus sans perdre sa place (aperçu produit, aperçu adresse, résumé d'une validation) | **Popup** |
| Un contenu riche à plusieurs sous-parties (détail de commande, litige, fiche d'un gestionnaire) | **Page dédiée**, avec onglets internes |
| Un geste **irréversible** ou coûteux (supprimer, suspendre, rejeter, annuler) | **Popup de confirmation** qui explique la conséquence, jamais un simple « OK ? » |

**Ta formulation, L-2 et L-3** : *« les symboles-boutons irréversibles comme
supprimer doivent avoir une fenêtre popup qui explique bien les conséquences
pour une reconfirmation »*, et *« l'œil pour consulter, au lieu d'ouvrir une
popup, sélectionne — ce qui ne sert à rien »*.

**Ce que ça change concrètement** : l'œil n'est plus un sélecteur. Il ouvre un
aperçu en popup quand le contenu est court, ou navigue vers une page quand il
est riche. Le volet de droite garde son rôle — il montre ce sur quoi on
travaille — mais il n'est plus la *seule* réponse au clic sur l'œil.

### D-61 — Rien ne se supprime : on suspend, on désactive, on archive

**Ta formulation, L-2 et L-3** : *« certains trucs soi-disant supprimables
devraient être juste suspendus ou désactivés »*.

La règle du projet était déjà la suppression logique ([D-13](#d-13--suppression-toujours-logique)) ;
elle devient une règle d'interface :

| Objet | Ce que fait le bouton | Pourquoi |
|---|---|---|
| Produit | **Retirer de la vente**, réversible | Des commandes passées le référencent |
| Compte (tous rôles) | **Suspendre**, réversible | Ses commandes et ses traces restent |
| Adresse | **Retirer du carnet** — l'adresse elle-même survit | Des commandes livrées y pointent |
| Boutique, livreur | **Suspendre**, réversible | Idem |
| Avis | **Masquer** (modération), jamais effacer | Une modération doit pouvoir s'expliquer |
| Ligne de panier, brouillon de tournée | **Supprimer** vraiment | Rien n'en dépend |

Un bouton rouge n'existe que pour les deux dernières lignes de ce tableau.

### D-62 — Toute action se propage à ceux qu'elle concerne

**Ta formulation, L-7** : *« tu n'as pas pensé aux autres pour que cette partie
soit synchronisée »*, et la même remarque en L-3, L-4, L-6.

C'est le trou de conception le plus profond du bloc L, et il est unique :
**une action changeait une ligne en base et s'arrêtait là**. Trois mécanismes le
comblent, aucun n'est inventé pour l'occasion :

1. **Un événement métier par action sensible.** Valider un vendeur, suspendre un
   compte, ajuster un stock, faire avancer une commande, trancher un litige :
   chacun émet un événement capté par des abonnés (patron Observateur). Les
   abonnés écrivent le journal d'audit, créent les notifications, et invalident
   les caches concernés.
2. **Une notification à chaque partie concernée**, avec le lien vers l'écran où
   agir — jamais un silence après une décision.
3. **Le rafraîchissement côté destinataire.** Au MVP, par interrogation
   périodique ([D-16](#d-16--livraison-mvp-sans-temps-réel-websocket) l'a déjà
   tranché contre les WebSockets) : les écrans de travail relisent leur file
   toutes les trente secondes via `@tanstack/vue-query`, qui sait déjà le faire.

### D-63 — Une suspension coupe l'accès immédiatement

Un jeton JWT reste valide jusqu'à son expiration : suspendre un compte ne le
déconnectait pas. C'est une faille, pas un détail d'ergonomie.

À chaque requête authentifiée, la permission `EstActif` relit le statut du
compte en base — elle le faisait déjà — et le front, recevant un 403 au code
`compte_suspendu`, bascule sur un écran dédié qui explique la situation au lieu
d'une page morte.

### D-64 — Chaque KPI et chaque ligne mène quelque part

**Ta formulation, L-3** : *« le dashboard n'est pas cliquable, n'est pas joli »*.

Un chiffre isolé qu'on ne peut qu'admirer est un élément mort qui trompe l'œil.
Chaque tuile de tableau de bord ouvre **la liste correspondante, filtre déjà
appliqué** : cliquer « 3 commandes à préparer » ouvre les commandes reçues
filtrées sur « à préparer », jamais l'écran générique.

---

## L-1 — Le visiteur non connecté

### D-65 — L'alerte de retour en stock exige un compte

Tu as tranché contre ma recommandation, et ton choix se défend : *« non,
l'inscription est mieux »*. Un courriel seul ouvre la porte au spam
d'inscription, et l'alerte n'a de valeur que si on peut ensuite acheter. Le
bouton mène donc à l'inscription, en gardant le produit en mémoire pour
inscrire l'alerte juste après.

### D-66 — La barre latérale d'un visiteur ne montre que ce qu'il peut faire

Tu as validé l'option B : pas d'entrées grisées avec un cadenas, mais une
barre latérale **plus courte**, plus un bouton « Se connecter / S'inscrire ».
Une entrée grisée est une fausse promesse de contenu caché.

Si un visiteur force une URL privée, il est envoyé vers la connexion **et
revient là où il allait** une fois connecté — jamais renvoyé à l'accueil, ce
qui l'obligerait à refaire son chemin.

### D-67 — Les pages « Devenir vendeur » et « Devenir livreur » sont deux vitrines

**Ta formulation, L-1** : *« je veux de vraies frames ou librairies qui font ça
très joli, très spécial »*.

Deux pages publiques distinctes, sur le modèle « Vendre sur Amazon » : une
promesse en haut, trois arguments chiffrés, les étapes de la candidature, une
foire aux questions, et le formulaire en bas. Elles restent peu mises en avant
dans la navigation — l'immense majorité des visiteurs viennent acheter.

Les composants viennent de PrimeVue (accordéon pour la FAQ, étapes pour le
parcours, cartes) : rien n'est redessiné à la main.

### D-68 — Le catalogue navigue par produit, la page Boutiques navigue par vendeur

Les deux logiques coexistent dans toutes les vraies places de marché, et l'une
ne remplace pas l'autre : on cherche « un burger », ou on cherche « tout ce que
vend Chez Karim ». La page Boutiques applique le **même filtre géographique**
que le catalogue pour les boutiques Express, sans quoi elle promettrait des
boutiques qui ne livrent pas.

### D-69 — Grille verticale pour chercher, carrousel horizontal pour découvrir

Si l'utilisateur est censé tout regarder → **vertical**. S'il est censé n'en
retenir que deux ou trois en passant → **horizontal**. Le catalogue principal
n'est donc jamais horizontal, et une section de trois recommandations n'est
jamais en grille.

### D-70 — Un code promo générique s'applique au panier invité

Il ne dépend d'aucun historique : rien ne justifie d'exiger un compte. Un code
nominatif ou de fidélité, lui, exige la connexion — il est rattaché à une
personne.

---

## L-2 — Le client connecté

### D-71 — Les avis sont publics, et visibles par tout le monde

**Ta formulation** : *« les autres ne voient pas son avis »*, *« l'admin et le
vendeur ne voient pas l'avis »*. Vérifié : la fiche produit publique ne
renvoyait ni `avis` ni `note_moyenne`, et aucun écran d'administration ne les
listait. Un avis qu'on est seul à voir n'est pas un avis.

Trois endroits l'affichent désormais :

- **la fiche produit publique** : note moyenne, répartition par étoile, et les
  avis eux-mêmes — c'est ce qu'un acheteur lit avant d'acheter ;
- **l'espace vendeur** : les avis qui le concernent, avec la possibilité de
  **signaler** un avis abusif à l'administration, jamais de le supprimer ;
- **l'espace admin** : la file de modération, où un avis signalé est masqué ou
  rétabli avec un motif.

### D-72 — On note ce qui compose la commande, et l'écran dit pourquoi

**Ta formulation** : *« il peut donner un avis sur Julien alors que le produit
est pour TechSophie »*.

Vérification faite, le livreur proposé **est bien celui de cette commande** : le
serveur ne propose que des cibles rattachées à la commande, et refuse les
autres. Le défaut est donc d'affichage : les trois cibles étaient alignées à
plat, si bien qu'un nom de personne apparaissait à côté d'un nom de boutique
sans que rien n'explique le lien.

L'écran regroupe désormais les cibles en trois sections nommées — **La
boutique**, **Les produits reçus**, **La livraison** — et la section livraison
précise « Sonia vous a livré cette commande le 28 août ».

### D-73 — La note se donne avec un composant de notation, pas cinq boutons

**Ta formulation** : *« il est obligé de donner soit 5 soit laisser à 4 »*.

Cinq boutons dessinés à la main, dont l'état actif se lit uniquement au
remplissage, ne se comprennent pas : on ne sait pas si on a cliqué. Le composant
`Rating` de PrimeVue s'en charge — survol, clic, effacement, clavier, libellé
accessible — et il affiche la note choisie en toutes lettres à côté.

### D-74 — L'adresse de livraison suit la commande jusqu'au livreur

**Ta formulation** : *« mes adresses : ces informations ne sont pas utilisées
par le vendeur, l'entrepôt, le gestionnaire ni le livreur, pourquoi ? »*

La question est juste, et le défaut réel. L'adresse et ses **instructions de
livraison** sont maintenant reprises :

| Qui | Ce qu'il en voit | Pourquoi pas plus |
|---|---|---|
| Vendeur, gestionnaire | Ville et code postal | Il prépare un colis, il n'a pas à connaître l'étage de quelqu'un |
| Gestionnaire d'entrepôt | Ville, code postal, **zone** | C'est la zone qui décide de la tournée |
| Livreur | **Adresse complète et instructions** | C'est lui qui sonne à la porte |
| Admin | Tout, en cas de litige | Il arbitre |

Le cloisonnement n'est pas une pudeur : une adresse complète diffusée à toute
la chaîne est une donnée personnelle exposée sans nécessité.

### D-75 — Le détail d'une commande est une page, l'ajout d'une adresse une popup

Application directe de [D-60](#d-60--trois-niveaux-dinteraction-et-un-seul-choix-possible-à-chaque-fois) :
une commande porte une frise de suivi, une facture et un litige potentiel — trop
riche pour une popup. Une adresse tient en cinq champs.

### D-76 — Profil et Paramètres restent deux écrans distincts

Tu as tranché contre ma recommandation de les fusionner : *« profil et
paramètres doivent être différents et ressembler au projet banque »*. C'est
d'ailleurs ce que fait le projet banque, avec deux entrées séparées.

- **Profil** : qui je suis. Identité **gelée**, coordonnées modifiables.
- **Paramètres** : comment l'application se comporte. Mot de passe, sécurité,
  notifications, affichage, données.

### D-77 — L'identité ne se modifie que par une demande validée

Repris du projet banque, et c'est ce qui donne au profil son sérieux : nom,
prénom et date de naissance sont **gelés**. Les changer passe par une demande
motivée, visible dans le volet de droite avec son état, et validée par un
administrateur. L'e-mail, le téléphone et l'adresse restent modifiables
directement.

**Pourquoi c'est juste ici aussi** : sur une place de marché, l'identité engage
— un vendeur validé sur un nom ne doit pas pouvoir en changer seul.

### D-78 — La facture s'imprime par le navigateur, rien de plus

Ton doute était fondé : *« je ne suis pas sûr que ce soit une bonne idée »*.
Une feuille de style `@media print` et `window.print()` suffisent — le
navigateur propose lui-même « Enregistrer en PDF ». Aucune dépendance, aucun
travail serveur. Une génération PDF côté serveur (WeasyPrint) reste possible
plus tard si la facture doit être envoyée par courriel.

Rien d'autre ne s'imprime côté client : ni une liste de commandes, ni des avis.

---

## L-3 — Le vendeur

### D-79 — Le catalogue et le stock ne font qu'un écran

**Ta formulation** : *« Mon catalogue et Stock se marchent sur les pieds, si tu
organises bien on peut fusionner »*, et *« deux fois le bouton corriger le
stock »*.

Tu as raison : ce sont deux vues du même objet. Un seul écran **Catalogue**,
avec des onglets — *En vente*, *Stock et alertes*, *Retirés*, *Historique* — et
**un seul** bouton de correction de stock par ligne. La rupture se déclare
depuis la popup de correction, où elle a sa place, plutôt que par un second
bouton qui ouvre la même popup.

### D-80 — Le vendeur voit ce que son personnel a fait, et réciproquement

**Ta formulation, L-3 et L-4** : *« le vendeur et le gestionnaire se marchent
sur les pieds, ne sont pas complémentaires, et les actions de l'un ne sont pas
mises à jour chez l'autre »*, et *« il est tellement inutile »*.

Vérifié : les deux tableaux de bord affichaient les mêmes compteurs, et aucun ne
disait **qui** avait agi. Ce qui est ajouté :

- chaque mouvement de stock et chaque changement de statut portent leur auteur,
  et l'écran l'affiche — « ajusté par Nadia, il y a deux heures » ;
- le vendeur a, dans **Mon personnel**, l'activité de chaque employé : commandes
  préparées, ajustements faits, dernière connexion ;
- le gestionnaire voit **ce que le vendeur a changé** qui le concerne : un
  produit retiré de la vente, un prix modifié, une commande annulée ;
- les deux files se rafraîchissent seules : préparer une commande la fait
  disparaître de l'écran de l'autre sans qu'il ait à recharger.

### D-81 — La chaîne d'une commande suit le métier, pas une machine abstraite

**Ta formulation** : *« la chaîne n'est pas trop comme dans la réalité »*.

Les statuts existants restaient justes, mais l'écran les présentait comme une
suite d'étiquettes. Trois corrections :

- **le vocabulaire suit le circuit** : un restaurant « met en préparation » puis
  « signale prête » ; un vendeur Standard « prépare le colis » puis « l'expédie
  vers l'entrepôt ». Le même statut technique, deux mots différents ;
- **le temps compte** : une commande à préparer affiche depuis combien de temps
  elle attend, et passe en alerte au-delà du délai annoncé au client ;
- **l'annulation exige un motif** ([D-07](#d-07--annulation-vendeur--motif-obligatoire-notification-forte))
  et une confirmation qui explique ce qui va se passer côté client.

### D-82 — Le bon de préparation s'imprime, la facture client aussi

Ici l'impression a un vrai usage : quelqu'un doit **tenir le papier** —
un ticket de cuisine pour Karim, une étiquette d'expédition pour un colis
Standard. Même solution que la facture : feuille de style dédiée et
`window.print()`, ce qui marche aussi bien sur une imprimante thermique de
cuisine que sur une imprimante de bureau.

### D-83 — Les statistiques sont des graphiques, et ils sont cliquables

**Ta formulation** : *« il n'y a pas assez de graphes statistiques »*.

Quatre graphiques, tous fournis par le composant `Chart` de PrimeVue (qui
embarque Chart.js) — aucun graphique dessiné à la main :

- le chiffre d'affaires par jour, sur la période choisie ;
- la répartition des ventes par catégorie ;
- les dix meilleures ventes en barres horizontales ;
- l'évolution de la note moyenne.

Un point cliqué renvoie vers les commandes du jour correspondant. Un bouton
**Exporter en CSV** accompagne la période — un vendeur veut ces chiffres dans
son tableur, pas sur papier.

### D-84 — Changer le SIRET ou le type d'activité redéclenche une validation

Ce sont les deux informations sur lesquelles l'admin a validé la boutique. Les
laisser changer en silence viderait la validation de son sens : la modification
est enregistrée, la boutique repasse **en attente**, et ses produits restent
visibles pendant l'examen — on ne punit pas un commerçant pour une mise à jour
administrative.

---

## L-4 et L-5 — Les gestionnaires

### D-85 — Une seule interface, adaptée au type de gestionnaire

Tu me demandais de trancher entre deux interfaces distinctes et une interface
adaptative. **Une seule**, qui change ses entrées selon `type_gestionnaire` :
ils partagent la couleur, la disposition et la moitié des écrans, et deux
maquettes à tenir à jour finiraient par diverger.

| Position | Staff vendeur | Staff entrepôt |
|---|---|---|
| 1 | Vue d'ensemble | Vue d'ensemble |
| 2 | À préparer | Colis reçus |
| 3 | Stock | Tournées |
| 4 | Expéditions | Expéditions au départ |
| 5 | Profil | Profil |

Même position, même fonction logique : ce qui rend un écran compréhensible sans
le réapprendre.

### D-86 — Le gestionnaire d'entrepôt construit vraiment ses tournées

**Ta formulation, L-5** : *« tu as fait un brouillon ; réfléchis sérieusement à
ce qu'il doit faire, il est amené à faire quoi et comment ? »*

Son métier, en quatre gestes, dans cet ordre :

1. **Réceptionner** un colis déposé par un vendeur — il confirme l'arrivée
   physique, ce qui fait passer la sous-commande de « expédiée » à « reçue » ;
2. **Trier** par zone : les colis reçus se regroupent par zone de livraison,
   parce que c'est la zone qui décide de la tournée ;
3. **Monter une tournée** : il choisit une zone, l'application propose les colis
   éligibles, il en retire ou en ajoute, et l'ordre des arrêts est **calculé**
   par plus proche voisin ([D-44](#d-44--les-tournées-sont-optimisées-dès-le-mvp))
   — il peut le corriger à la main, c'est lui qui connaît le terrain ;
4. **Affecter** la tournée à un livreur rattaché à son entrepôt, ce qui la rend
   visible sur le téléphone de celui-ci.

Ce qu'il ne fait jamais : modifier une commande, un prix, ou l'ordre d'une
tournée déjà commencée.

### D-87 — Deux bouts de la même chaîne portent deux noms

Le gestionnaire d'un vendeur **expédie** vers l'entrepôt ; celui de l'entrepôt
**réceptionne**. Même colis, deux comptes, deux écrans, et un rapprochement
automatique : un colis expédié sans réception au bout de 48 heures remonte comme
anomalie chez les deux.

---

## L-6 — Le livreur

### D-88 — L'application mobile existe, et c'est du Vue

Ta phrase est juste : *« je n'ai rien pu tester, tu refuses de faire la partie
mobile »*. Elle est faite, avec **Ionic Vue + Capacitor** comme
[D-20](#d-20--mobile--ionic-vue--capacitor) le prévoyait — donc en réutilisant
les magasins Pinia, le client d'API et les types déjà écrits, extraits dans un
paquet `partage/`.

### D-89 — Cinq onglets, la même position pour la même fonction dans les deux modes

| Position | Express | Standard |
|---|---|---|
| 1 | Vue d'ensemble | Vue d'ensemble |
| 2 | Mes courses | Ma tournée |
| 3 | **+** (historique, gains, aide) | **+** (historique, gains, aide) |
| 4 | À proximité | Prochain arrêt |
| 5 | Profil et disponibilité | Profil et disponibilité |

La bascule entre les deux est **automatique**, déduite de `mode_livraison` :
jamais un réglage que le livreur doit penser à changer.

### D-90 — « Prochain arrêt » n'est pas une liste

C'est un écran plein : l'arrêt suivant, la navigation, le bouton livré ou
absent, le contact client. Un livreur n'a pas besoin de rouvrir sa tournée
entière dix fois par jour pour savoir où il va maintenant.

### D-91 — Le livreur Standard est payé à l'arrêt

Tu me laissais trancher. **À l'arrêt** : c'est plus juste — une tournée de dix
arrêts ne vaut pas une tournée de trois — et cela reste lisible si l'écran
affiche « 6 arrêts × 1,80 € = 10,80 € » plutôt qu'un total sec.

### D-92 — Un gain est bloqué tant qu'un litige est ouvert sur sa commande

Il est acquis à la confirmation de livraison, mais **suspendu** si un litige
s'ouvre, et débloqué à la décision. Verser puis reprendre serait bien pire.

---

## L-7 et L-8 — L'administration

### D-93 — L'admin gère, il ne fait pas que consulter

**Ta formulation** : *« tu n'as pensé qu'à la consultation »*. Vérifié : aucune
route de gestion n'existait pour les boutiques ni les livreurs. Ce qu'il peut
faire désormais, chaque action étant tracée et notifiée :

| Sur | Actions |
|---|---|
| Boutique | valider, refuser avec motif, **suspendre**, réactiver, exiger une nouvelle validation |
| Livreur | valider, refuser avec motif, suspendre, réactiver, rattacher à un entrepôt |
| Compte | suspendre, réactiver, forcer une réinitialisation de mot de passe |
| Avis | masquer, rétablir |
| Litige | instruire, trancher, rembourser |

### D-94 — Un litige a deux parties, et chacune s'exprime

**Ta formulation** : *« litige, c'est le moins réfléchi : le système, la
logique, la synchronisation, comment on provoque un litige, comment on se
défend, comment on rétorque »*.

Le cycle, du début à la fin :

1. **Ouverture** — le client décrit le problème et joint ses preuves, depuis sa
   commande livrée. La partie mise en cause **et** l'admin sont notifiés.
2. **Instruction** — la partie mise en cause a **48 heures** pour répondre avec
   sa version et ses preuves. Les deux versions restent côte à côte : aucune
   n'écrase l'autre. Sans réponse dans le délai, le dossier part à l'arbitrage
   avec la seule version du plaignant — on ne bloque jamais indéfiniment.
3. **Décision** — l'admin tranche avec les deux versions sous les yeux, et sa
   décision **déclenche** l'action : remboursement total ou partiel, ou rejet
   motivé.
4. **Notification finale** aux deux parties, avec la justification.

Effets sur le reste : le versement au vendeur ou au livreur est suspendu tant
que le litige est ouvert ; un remboursement emprunte le **même chemin** qu'une
annulation ; et la note moyenne n'est affectée que si le litige est tranché en
défaveur — un signalement infondé ne doit pénaliser personne.

### D-95 — Le journal d'audit ne s'écrit jamais à la main

**Ta formulation** : *« aucune gestion, système et logique mauvaise, pas de
synchronisation »*.

Chaque action sensible **émet** son entrée, par le même mécanisme d'événements
que [D-62](#d-62--toute-action-se-propage-à-ceux-quelle-concerne). Une entrée
répond à six questions : **qui** (acteur et rôle), **quoi** (action), **sur
quoi** (objet visé), **avant et après** (valeurs), **quand**, **pourquoi**
(motif). Aucune n'est modifiable ni supprimable.

Qui le lit : l'admin en entier ; un vendeur uniquement **ses** actions et celles
de son personnel. Filtrable par acteur, type et période, exportable en CSV.
Jamais imprimable — un registre n'est pas un document ponctuel.

---

## L-9 à L-17 — La méthode

### D-96 — Le jeu de données rend visible chaque scénario

**Ta formulation, L-15** : *« crée autant de données que possible pour rendre
visible chaque scénario et chaque décision »*.

Le peuplement ne cherche pas le volume mais la **couverture** : pour chaque
scénario de `01-produit/scenarios.md` et chaque décision de ce journal qui se
voit à l'écran, au moins une donnée l'illustre. Un fichier de correspondance
`donnees-demo/couverture.md` dit quelle donnée illustre quel scénario, et un
test échoue si un scénario n'a plus d'illustration.

### D-97 — Aucune fonctionnalité n'est retirée pour en ajouter une autre

**Ta formulation, L-14** : *« ne fais jamais moins bien que ce que tu as déjà
fait : soit tu prends le meilleur, soit ils sont complémentaires »*.

Quand une remarque conduit à refaire un écran, ce qui existait est **repris ou
remplacé par mieux**, jamais perdu en route. Fusionner catalogue et stock
([D-79](#d-79--le-catalogue-et-le-stock-ne-font-quun-écran)) garde les onglets,
l'historique et la popup de correction ; ils changent de place, ils ne
disparaissent pas.

### D-98 — Devant une idée jamais vue ailleurs, on fait comme les vrais sites

**Ta formulation, L-14** : *« si une idée, tu n'as jamais vu ça sur un vrai
site, tu fais comme c'est sur les vrais sites »*.

C'est la règle qui a manqué au bloc J, où j'ai inventé un tableau, une fenêtre
et des notifications maison au lieu de prendre ceux qui existaient. Devant un
doute d'ergonomie : regarder ce que font Amazon, Uber Eats ou Shopify, et faire
pareil — l'originalité en interface est presque toujours une régression.
