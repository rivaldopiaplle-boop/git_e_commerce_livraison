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
