# Ta part du travail

> **Tu as signalé que mes demandes étaient de plus en plus dures à trouver
> (bloc E-4). C'était vrai** — elles étaient noyées au milieu de la référence.
> Désormais : _tout ce que j'attends de toi tient dans le premier écran_, daté
> et numéroté. Le reste du fichier est de la documentation qu'on consulte, pas
> qu'on relit.

---

# ⬛ À FAIRE MAINTENANT — mis à jour le 1er septembre (2ᵉ lot)

Deux gros morceaux depuis ce matin : **le paiement**, et **le cycle complet du
litige** — celui que tu appelais *« le moins réfléchi »* au bloc L-8. Il est
maintenant écrit de bout en bout, avec ses trois rôles.

## Le paiement

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **1** | **`python demarrer.py`**, puis Ctrl+Maj+R | 2 min | — |
| **2** | **Léa → panier → « Continuer vers le paiement »**, puis **Payer** | 3 min | D-101 |
| **3** | **Refais-le, mais clique « Renoncer »**. Le produit est **immédiatement** re-commandable | 3 min | D-100 |
| **4** | **Icône de document** sur une commande payée → **Imprimer**. Barre latérale, barre haute et boutons disparaissent de la feuille | 3 min | D-102 |

## Le litige, dans les trois rôles — fais-le dans cet ordre

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **5** | **Léa → Mes commandes → icône bouclier rouge** sur une commande livrée. Choisis un motif, raconte, envoie | 3 min | D-94 |
| **6** | **`karim@exemple.fr` → Litiges** (nouvelle entrée dans la barre latérale). Le bandeau te dit combien de dossiers attendent **ta** version, et la colonne « Votre réponse » compte les heures restantes | 4 min | D-104 |
| **7** | **Donne ta version**, puis va sur `admin@exemple.fr` → **Litiges** | 3 min | — |
| **8** | **Essaie d'arbitrer le dossier « Réponse attendue avant… »** : le bouton est **gris**, et l'infobulle te dit jusqu'à quand la boutique a la parole | 2 min | D-103 |
| **9** | **Arbitre celui dont le délai est dépassé** : lui, tu peux le trancher sans la seconde version, et la popup te le dit franchement | 3 min | D-103 |
| **10** | **Rembourse partiellement** un dossier : coche « rembourser une partie seulement ». La commande reste **livrée** — un article manquant sur cinq ne renverse pas toute la vente | 3 min | — |

Le jeu de démonstration te pose **les cinq états** d'un litige côte à côte :
délai en cours, délai dépassé, boutique entendue, résolu avec remboursement,
rejeté. Tu n'as rien à fabriquer à la main pour les voir.

## Les quatre dernières listes — c'est fini

Tu m'avais demandé les boutons-symboles **sur toutes les listes de tous les
rôles**. Il en restait quatre au bloc K ; les quatre y sont.

| # | Ce que je te demande | Temps | Détail |
|---|---|---|---|
| **11** | **`karim@exemple.fr` → Mon personnel.** C'est maintenant la liste du projet, et surtout : tu peux **suspendre un employé**. Tu ne pouvais pas — quelqu'un qui partait gardait son accès au stock pour toujours | 4 min | D-106 |
| **12** | **Suspends `rachid@exemple.fr`, puis essaie de te connecter avec.** La porte est vraiment fermée, pas juste le menu masqué | 2 min | D-106 |
| **13** | **Léa → Mes adresses.** Tu peux enfin **corriger** une adresse au lieu de l'effacer et la retaper, et **retirer** demande confirmation — avant, un seul clic suffisait | 3 min | D-107 |
| **14** | **Regarde la barre latérale de chaque rôle** : « Commandes reçues », « Vue d'ensemble », « Tournées », « Demandes d'identité ». Elles étaient toutes écrites sans accents | 1 min | D-105 |

Mot de passe commun : **`Demonstration!2026`**.

---

## Le défaut que j'ai trouvé en écrivant le paiement

Je te le dis parce qu'il expliquait sans doute des choses que tu as vues sans
comprendre : **du stock était réservé deux fois pour une même commande**, une
fois à sa création, une fois à l'ouverture du paiement — et rendu une seule
fois. Au bout de quelques essais, des produits parfaitement disponibles
s'affichaient **« épuisé »** sans raison visible.

Trois choses ont été faites, pas une :

1. **Un seul module écrit désormais ce compteur** (`commandes/reservation.py`).
   Poser, relâcher et consommer sont rejouables sans dégât — c'est ce qu'exige
   un webhook de paiement, qui réessaie quand il doute d'avoir été reçu.
2. **Une réservation expire au bout de dix minutes.** `demarrer.py` libère au
   lancement ce qu'une session interrompue retenait encore : ta base de la
   veille ne te ment plus le lendemain.
3. **18 tests** verrouillent la règle : quel que soit le chemin — capture,
   refus, abandon, webhook rejoué, retour du client — le compteur revient
   toujours à sa valeur de départ.

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
