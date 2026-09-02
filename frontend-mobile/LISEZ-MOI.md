# Lancer l'application mobile — client et livreur

> **Il n'y a qu'UNE application mobile, pas deux.** C'est le même code qui sert
> le client et le livreur : la barre d'onglets change selon le rôle du compte
> connecté. Se connecter en `lea@exemple.fr` donne l'application du client, se
> connecter en `amine@exemple.fr` donne celle du livreur.
>
> Ce n'est pas une économie de moyens, c'est la décision
> [D-20](../plan-organisation/00-pilotage/journal-decisions.md) : deux
> applications à maintenir pour deux rôles qui partagent la connexion, le
> profil, les notifications et le client d'API, c'est deux fois le travail pour
> la moitié du résultat. Le vendeur, l'entrepôt et l'administrateur ne sont pas
> sur mobile du tout ([D-40](../plan-organisation/00-pilotage/journal-decisions.md)) :
> on ne gère pas un catalogue sur un écran de six pouces.

---

## Le plus simple : dans le navigateur du poste

```
python demarrer.py
```

Il lance tout : la base, l'API, le front web (5173) et le mobile (**5174**).
Ouvre `http://localhost:5174`, puis **réduis la fenêtre au format téléphone**
(F12 → l'icône téléphone/tablette, ou Ctrl+Maj+M sur Chrome et Firefox).

Sans ce mode, la barre d'onglets du bas et le bouton central « + » sont là mais
la mise en page respire mal : elle est faite pour 390 pixels de large, pas
pour 1920.

Pour ne lancer que le mobile :

```
cd frontend-mobile
npm install        # la première fois seulement
npm run dev
```

### Les deux rôles, et ce qui change entre eux

| | Client | Livreur Express | Livreur Standard |
|---|---|---|---|
| Compte | `lea@exemple.fr` | `amine@exemple.fr` | `julien@exemple.fr` |
| Onglet 1 | Accueil | Aujourd'hui | Aujourd'hui |
| Onglet 2 | Recherche | Ma course | Ma tournée |
| **Bouton central** | Panier, adresses, boutiques | Gains, historique, aide | Gains, historique, aide |
| Onglet 4 | Commandes | À proximité | Prochain arrêt |
| Onglet 5 | Profil | Profil | Profil |

Mot de passe pour tous : **`Demonstration!2026`**.

Deux choses à regarder, parce qu'elles ne se devinent pas :

- **la même position dans la barre garde la même fonction logique** d'un rôle à
  l'autre. Le deuxième onglet, c'est toujours « ce que je fais maintenant » :
  chercher pour un client, livrer pour un livreur. Quelqu'un qui change de rôle
  ne réapprend pas où sont les choses ;
- **le bouton central surélevé** n'est pas un onglet de plus. Il ouvre une
  feuille par le bas — c'est le geste des applications de livraison, et il
  évite une barre à sept entrées illisible.

---

## Sur un vrai téléphone (même réseau Wi-Fi)

C'est là que ça devient intéressant : le tactile, le défilement, la
géolocalisation. Et c'est là que se trouvent tous les pièges.

### 1. Trouver l'adresse de la machine sur le réseau

`python demarrer.py` l'affiche au démarrage. Sinon :

```
ipconfig            # Windows  → « Adresse IPv4 » de la carte Wi-Fi
ip addr | grep inet # Linux
ipconfig getifaddr en0   # macOS
```

Disons `192.168.1.13`.

### 2. Dire à l'application où joindre l'API

```
cd frontend-mobile
copy .env.example .env      # Windows   (cp sur Linux/macOS)
```

puis, dans `.env` :

```
VITE_API_URL=http://192.168.1.13:8000/api/v1
```

**`localhost` ne marche pas depuis un téléphone.** Pour lui, `localhost`, c'est
lui-même : il cherchera une API sur le téléphone, ne trouvera rien, et
l'application restera vide sans message d'erreur clair.

### 3. Ouvrir depuis le téléphone

```
http://192.168.1.13:5174
```

---

## Les pièges, dans l'ordre où on les rencontre

### « La page ne s'ouvre même pas »

**Le pare-feu Windows bloque les connexions entrantes.** C'est le premier
obstacle, et il ne dit rien : le téléphone attend, puis abandonne.

Autorise `python.exe` et `node.exe` sur les **réseaux privés** — Windows le
propose au premier lancement, et on clique « Annuler » par réflexe. Pour
rattraper : Pare-feu Windows Defender → Autoriser une application.

Vérifie aussi que tu es bien sur **le même réseau Wi-Fi** : un téléphone en 4G
ou sur le Wi-Fi invité ne voit pas la machine.

### « Vite a démarré, mais sur un autre port »

Si 5174 est déjà pris — une instance oubliée, `demarrer.py` déjà lancé — Vite
prend **5175 sans prévenir**, et l'adresse que tu tapes sur le téléphone ne
mène nulle part. Lis la ligne `Network:` que Vite affiche : c'est elle qui fait
foi, pas ce que tu attendais.

### « La page s'affiche, mais tout est vide »

C'est le piège le plus coûteux, parce que **rien n'apparaît côté serveur** :
l'API répond parfaitement, et le navigateur jette la réponse avant que le code
ne la voie.

Deux causes, à vérifier dans cet ordre :

1. **`ALLOWED_HOSTS`** — Django refuse une requête dont l'en-tête `Host` n'est
   pas déclaré, avec un 400 sec. En développement (`DEBUG=true`), le projet
   accepte tout : rien à faire. En ligne, c'est une autre affaire ;
2. **CORS** — le navigateur exige que l'API déclare accepter l'origine
   `http://192.168.1.13:5174`. Le projet accepte automatiquement les plages
   d'adresses privées en développement (`192.168.x`, `10.x`, `172.16-31.x`) sur
   les ports 5173, 5174 et 8100. **Uniquement en développement** : autoriser un
   motif large en ligne reviendrait à laisser n'importe quel site lire les
   réponses de l'API avec tes jetons.

> Ce piège a réellement coûté une demi-journée au bloc H, sur le front web. Le
> port du mobile manquait encore au bloc M : `test_cors.py` verrouille
> désormais les deux.

### « L'API répond, mais la connexion échoue »

Vérifie que l'API écoute sur **toutes** les interfaces :

```
python manage.py runserver 0.0.0.0:8000
```

`runserver` tout court n'écoute que `127.0.0.1` — donc uniquement la machine
elle-même. `demarrer.py` utilise déjà la bonne forme.

### « La géolocalisation ne marche pas »

Attendu, et ce n'est pas un bogue. **Les navigateurs refusent la géolocalisation
sur une origine non sécurisée**, et `http://192.168.1.13:5174` en est une. Seul
`localhost` échappe à la règle.

Trois façons de s'en sortir :

| Où | Géolocalisation | Pour quoi faire |
|---|---|---|
| Navigateur du poste, `localhost` | ✅ | vérifier les écrans « À proximité » et « Prochain arrêt » |
| Navigateur du téléphone, IP locale | ❌ | tout le reste |
| **Application installée** (Capacitor) | ✅ | la géolocalisation native, sans HTTPS |

Les écrans concernés le disent à l'écran plutôt que de rester vides : ils
proposent de saisir une position à la main.

---

## En application installée (Android)

C'est le seul moyen d'avoir la géolocalisation native et le rendu réel.

```
cd frontend-mobile
npm run build
npx cap add android      # la première fois seulement
npx cap sync android
npx cap open android     # Android Studio prend le relais
```

`npm run android` enchaîne les trois dernières.

### Ce qu'il faut avoir installé

- **Android Studio** (avec le SDK Android et un appareil virtuel, ou un
  téléphone en mode développeur) ;
- un **JDK 17** — Android Studio en embarque un ; si `npx cap open` se plaint,
  c'est presque toujours `JAVA_HOME` qui pointe ailleurs.

### Le rechargement à chaud sur le téléphone

Par défaut, l'application installée contient un paquet **figé** : chaque
modification demande `npm run build && npx cap sync`. Pour garder le
rechargement à chaud, décommente dans `capacitor.config.ts` :

```ts
server: {
  url: 'http://192.168.1.13:5174',   // l'IP de TA machine
  cleartext: true,
}
```

**À recommenter avant de fabriquer l'APK que tu distribues** : sinon
l'application cherchera une machine de développement qui n'existe plus, et
n'affichera rien du tout chez la personne qui l'installe.

`cleartext: true` autorise le HTTP en clair, qu'Android bloque par défaut. Cela
n'a de sens qu'en développement, pour la même raison.

---

## Ce que le mobile ne fait pas, et pourquoi

| Rôle | Sur mobile ? | Pourquoi |
|---|---|---|
| Client | **oui** | il commande dans le métro |
| Livreur | **oui** | accepter et confirmer se font une main sur le guidon |
| Vendeur | non | on ne gère pas un catalogue et des prix sur six pouces |
| Entrepôt | non | monter une tournée demande un écran large |
| Admin | non | arbitrer un litige suppose de lire deux versions côte à côte |

Ce n'est pas un manque : c'est
[D-40](../plan-organisation/00-pilotage/journal-decisions.md). L'espace web du
livreur existe quand même, mais en **lecture seule** — suivi et gains. Agir se
fait sur le téléphone.
