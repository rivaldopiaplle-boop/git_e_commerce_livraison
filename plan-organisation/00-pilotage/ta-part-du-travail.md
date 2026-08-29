# Ta part du travail

> **Tu as signalé que mes demandes étaient de plus en plus dures à trouver
> (bloc E-4). C'était vrai** — elles étaient noyées au milieu de la référence.
> Désormais : _tout ce que j'attends de toi tient dans le premier écran_, daté
> et numéroté. Le reste du fichier est de la documentation qu'on consulte, pas
> qu'on relit.

---

# ⬛ À FAIRE MAINTENANT — mis à jour le 30 août

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **1** | **`python demarrer.py`**, puis Ctrl+Maj+R dans le navigateur. Le jeu de données est déjà en place : 20 comptes, 5 boutiques, 15 commandes dans tous leurs états, des tournées, des litiges | 3 min | § J-7 plus bas |
| **2** | **Ouvre `/connexion` et `/inscription`.** Elles étaient blanc sur blanc — deux jetons de couleur avaient disparu du thème. Tout est passé en clair | 2 min | § J-1 |
| **3** | **Connecte-toi en `rachid@exemple.fr`** (entrepôt) puis **`julien@exemple.fr`** (livreur) : ces deux espaces n'existaient pas | 4 min | § J-4, J-6 |
| **4** | **Chez Karim, ouvre « Mon catalogue »** : les boutons font enfin leur travail, dont « déclarer une rupture » et « remettre en vente » | 3 min | § J-3 |
| **5** | **Puis « Stock » → bouton de ligne** : l'ajustement est passé en popup, avec la quantité réelle et un motif à choisir. L'historique est dans son propre onglet | 3 min | § J-3 |

Mot de passe commun : **`Demonstration!2026`**.

**Aucune information ne m'est nécessaire de ta part.** Je continue sur le
paiement, puis la livraison, comme tu l'as validé en J-10.

---

## Ce que tu as signalé, et ce qui a changé

| | Ton constat | Ce qui a été fait |
|---|---|---|
| **J-1** | « Créer un compte, Des boutiques deux rythmes, RivDinde… tout ça est en blanc et illisible » | **Ma faute, et la deuxième fois.** `PanneauMarque.vue` utilisait `bg-encre-2` et `border-encre-3`, deux jetons que j'avais supprimés du thème : l'aside n'avait plus de fond, et son texte blanc devenait invisible. Les écrans publics sont repassés en clair, comme le reste. **Et j'ai écrit le test qui rend l'erreur impossible** : il lit le thème, lit tous les écrans, et refuse toute classe qui ne mène à rien ([D-47](journal-decisions.md)) |
| **J-2** | « 530,80 € Total dépensé : ça sert à quoi ça ? » | À rien. Personne n'ouvre une application de livraison pour se faire rappeler ce qu'il a dépensé, et le chiffre ne déclenche aucune action. Retiré, remplacé par ce qui arrive et par son carnet d'adresses |
| **J-3** | « Les symboles/boutons sont très laids et ne font pas leur rôle » | Repris de la maquette : boutons-icônes **encadrés** de 28 px. Et surtout ils agissent : « voir » n'ouvre plus la fiche publique d'un produit masqué (page vide), « masquer » a enfin son inverse — **remettre en vente** —, et **« déclarer une rupture »** existe |
| **J-3** | « L'affichage de l'ajustement de stock n'est pas bon, soit les boutons, soit une popup » | **Popup**, comme la maquette la décrit : « Nouvelle quantité » et un motif à choisir. On compte ce qu'il y a sur l'étagère, on ne calcule pas de tête l'écart ([D-49](journal-decisions.md)) |
| **J-3** | « L'historique peut être mis à un meilleur endroit » | Sorti de sous la ligne : il a son propre onglet, en tableau, tous produits confondus |
| **J-3** | « Pizza napolitaine : j'ai fait une rupture de stock mais rien n'apparaît côté client » | **Tu n'avais pas fait de rupture.** Le mouvement enregistré est `RETOUR -2 → 26` : l'écran ne proposait qu'un écart, pas une mise à zéro, et il t'a laissé croire le contraire. Le stock de la pizza était toujours à 26. C'est corrigé au point précédent |
| **J-4** | « Espace livreur » | Il n'existait pas. Il montre maintenant ses courses, sa tournée du jour avec ses arrêts ordonnés, et ses gains. L'action reste sur le mobile ([D-40](journal-decisions.md)) : accepter une course une main sur le guidon ne se fait pas au clavier |
| **J-6** | « Il manque des sidebar, navbar, dashboard, onglets de tous les rôles venant de la maquette » | Reprises **entrée par entrée** de la maquette. 10 écrans créés : carnet d'adresses, personnel, statistiques, colis reçus, tournées, mes courses, boutiques, utilisateurs, litiges, journal d'audit. **Un test vérifie que chaque entrée de menu mène à une route réelle** |
| **J-7** | « Fais un vrai jeu de données très vaste » | 20 comptes, 5 boutiques dans 3 états, 2 entrepôts, 25 produits, **15 commandes — une par statut**, 14 livraisons dont une échouée après deux tentatives, 4 tournées de brouillon à terminée, 7 avis, 2 litiges. Plus les cas limites : produit retiré, stock bas, rupture, client parisien qu'aucune boutique Express ne livre |
| **J-9** | « Utilise la maquette et le plan, merde » | J'ai relu `maquettes.html`, `regles-d-or.md`, `roles-et-parcours.md`, `correspondance-ecrans.md` et le journal avant d'écrire une ligne. Le relevé décision par décision est dans [etat-reel.md](etat-reel.md) |

---

## Trois défauts que tu n'avais pas vus, et que la relecture a sortis

1. **Le gestionnaire recevait un 403 sur la liste des produits.** Son écran de
   stock — le seul de son métier — ne s'ouvrait pas du tout.
2. **Le gestionnaire recevait ton chiffre d'affaires** dans la réponse du
   serveur. L'interface le masquait ; masquer n'est pas une permission. Le champ
   ne quitte plus le serveur ([D-50](journal-decisions.md)).
3. **`stock_reserve` traînait à 3, 7 et 1** sur trois produits sans qu'aucun
   paiement soit en cours : « Bol de ramen », « Sac à dos » et « Tarte du jour »
   apparaissaient en rupture sans raison. Remis à zéro, et le peuplement le
   répare désormais tout seul.

Et **six photos ne montraient pas le bon produit** — une salade pour une
baguette, un tissu gris pour une huile d'olive, un petit-déjeuner anglais pour
du café en grains. Remplacées, revérifiées à l'œil sur planche-contact.

---

## Ce qui vient ensuite, dans l'ordre que tu as validé en J-10

1. **Le paiement** — écrivable en entier avec le simulateur, sans tes clés Stripe.
2. **La livraison et les tournées** — faire *avancer* ce que les écrans lisent déjà.
3. **Le paquet `partage/` et l'application mobile.**
4. **Le déploiement.**

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
