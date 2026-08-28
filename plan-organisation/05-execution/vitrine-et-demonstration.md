# La vitrine — montrer ce projet à un recruteur en dix minutes

> Ta règle d'or n°3, qui n'était traitée nulle part dans le plan initial.
> Sur le projet banque, la vitrine a été pensée après coup et il a fallu lui
> consacrer un document entier pour s'en sortir. Ici, elle est prévue dès le
> plan et elle **contraint le code** : c'est la seule façon qu'elle existe.

---

## 1. La règle en une phrase

Un projet qu'on ne peut pas montrer en ligne, tout de suite, sans rien installer,
n'existe pas pour un recruteur. Un lien qui marche vaut mieux qu'un dépôt de dix
mille lignes.

---

## 2. Ce que la vitrine doit fournir

1. **Une URL publique** qui répond en moins de dix secondes.
2. **Des comptes de démonstration**, un par rôle, avec leurs identifiants
   **affichés sur la page de connexion** — pas cachés dans un README.
3. **Des données crédibles** : un catalogue vide ne se démontre pas.
4. **Un parcours scripté** de dix minutes, répété assez pour ne jamais hésiter.
5. **Un bandeau permanent** « environnement de démonstration — aucun paiement
   réel », par honnêteté et pour couper court à toute ambiguïté.

---

## 3. Les comptes de démonstration

| Rôle | Compte | Ce qu'il montre |
|---|---|---|
| Client | Léa | Le parcours d'achat complet |
| Vendeur Express | Karim | La réception et la préparation d'une commande |
| Gestionnaire | Nadia | Un rôle volontairement bridé — l'argument « permissions » |
| Livreur Express | Amine | Le mobile, la géolocalisation, la preuve de livraison |
| Admin | Fatou | La validation des comptes et la vue complète d'une commande |

Tous avec le même mot de passe de démonstration, affiché à l'écran. Un bouton
« se connecter comme… » sur la page de connexion évite de taper quoi que ce soit
devant quelqu'un.

---

## 4. Le jeu de données (`seed_demo`)

Trois boutiques (une Express, deux Standard), une vingtaine de produits avec
photos, quelques catégories, trois clients, deux livreurs, un entrepôt, et
surtout : **des commandes à tous les statuts**. Une livrée avec ses avis, une en
cours de livraison avec un livreur en route, une en préparation, une annulée avec
son remboursement, un litige ouvert, un produit en rupture avec des clients en
attente d'alerte.

C'est ce dernier point qui fait la différence : sans commandes historiques, tous
les écrans de suivi, de statistiques et d'arbitrage sont vides, donc invisibles.

La vitrine est **remise à zéro régulièrement** (tâche planifiée) pour que la
démonstration parte toujours du même état connu.

---

## 5. Le parcours de dix minutes

| Temps | Ce qu'on montre | Ce qu'on dit |
|---|---|---|
| 0–1 min | Le catalogue client, la position, une boutique qui disparaît quand on change d'adresse | « Le catalogue Express est filtré par rayon — c'est ce qui rend une commande longue distance structurellement impossible » |
| 1–3 min | Panier mixte, aperçu du découpage en trois commandes, paiement en mode test | « Un panier, plusieurs commandes, un seul paiement — voilà la règle et voilà le service qui l'applique » |
| 3–4 min | Basculer en vendeur : la commande vient d'arriver, on la prépare | « Chaque rôle a sa couleur, et il ne voit que ce qui le concerne » |
| 4–5 min | Basculer en gestionnaire : les mêmes commandes, sans les prix ni le chiffre d'affaires | « Et le serveur le refuse aussi, pas seulement l'interface — voici le test qui le prouve » |
| 5–7 min | Le mobile livreur : accepter, se déplacer, livrer avec photo | « Une vraie application installable, pas un site rétréci » |
| 7–8 min | Retour client : la frise se met à jour, l'avis devient possible | |
| 8–9 min | L'admin : validation d'un vendeur, vue complète d'une commande, journal d'audit | « Tout ce qui est sensible est tracé » |
| 9–10 min | L'onglet Actions de GitHub, la chaîne verte, le déploiement automatique | « Chaque poussée est vérifiée et déployée sans intervention » |

Les deux moments qui impressionnent le plus sont le **découpage du panier** et le
**refus côté serveur pour le gestionnaire** : ce sont ceux qui montrent qu'il y a
une réflexion, pas seulement des écrans.

---

## 6. Les questions qui vont venir, et les réponses

| Question | Réponse |
|---|---|
| « Pourquoi Django ici et NestJS sur ton autre projet ? » | Choix délibéré de couvrir deux écosystèmes ; le Django Admin est particulièrement rentable sur un projet à six rôles |
| « Comment gères-tu le dernier article en stock ? » | Pas de réservation au panier, verrou transactionnel au paiement, réservation courte pendant la saisie — et un test qui simule la concurrence |
| « Que se passe-t-il si Stripe ne répond pas ? » | La confirmation vient du webhook, la commande reste en attente, une vérification de rattrapage tourne |
| « Comment optimises-tu les tournées ? » | Par zone et ordre d'arrivée aujourd'hui ; c'est un problème connu de tournées de véhicules, prévu pour un solveur existant, et le point d'extension est déjà en place |
| « C'est déployé où ? » | Base sur Neon, API conteneurisée, front statique, publication automatique depuis `main` |
| « Qu'est-ce qui manque pour une vraie production ? » | Sauvegardes testées, haute disponibilité, coffre à secrets, alerte d'astreinte — et savoir le dire vaut mieux que prétendre le contraire |

---

## 7. Les pièges, appris à la dure

- **Un hébergement qui s'endort.** Quarante secondes d'écran blanc tuent une
  démonstration. Prévoir un réveil périodique, ou ouvrir l'onglet avant l'entretien.
- **Les e-mails.** En vitrine, tous les envois vont vers **une seule adresse**,
  le destinataire réel étant rappelé dans l'objet. On ne risque jamais d'écrire à
  un inconnu, et on peut montrer l'e-mail reçu.
- **Les données périmées.** Une commande « en livraison » depuis trois semaines
  décrédibilise tout : d'où la remise à zéro régulière.
- **Le mobile.** Prévoir soit un téléphone prêt avec l'application installée,
  soit une capture vidéo de trente secondes — ne jamais compter sur une
  installation en direct.
- **Le compte admin.** Ne jamais laisser un compte admin de démonstration avec
  un mot de passe trivial sur une instance qui contiendrait autre chose que des
  données factices.
