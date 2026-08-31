# `partager/` — ce que les deux fronts ont en commun

Le projet a **deux interfaces** : le web (Vue 3 + Vite) et le mobile (Ionic
Vue + Capacitor, décidé en D-20). Elles ne partagent ni leur disposition ni
leurs écrans — c'est la règle d'or n°7 : *« web et mobile se ressemblent, sauf
la disposition »*.

Mais elles partagent tout le reste, et le dupliquer serait la garantie que les
deux versions divergent au troisième correctif :

| Dossier | Ce qu'il contient | Pourquoi c'est commun |
|---|---|---|
| `src/types/` | Les types du domaine — commande, produit, livraison, rôle | Ils décrivent l'API, qui est la même pour les deux |
| `src/api/` | Le client HTTP, le jeton, la clé de panier, l'enveloppe d'erreur | Le jour où l'un des quatre change, un seul fichier bouge |
| `src/metier/` | Les règles d'affichage : montants, statuts, couleurs de rôle, étapes de suivi | Un statut ne doit pas s'appeler « Prête » au web et « Prêt » au mobile |

## Ce qui n'est **pas** ici, et pourquoi

- **Les composants.** PrimeVue au web, les composants Ionic au mobile : ce ne
  sont pas les mêmes primitives, et forcer un composant commun produirait un
  compromis mauvais des deux côtés.
- **Les magasins Pinia.** Ils dépendent du stockage local, qui n'est pas le
  même dans un navigateur et dans une application installée.
- **Le routeur.** Cinq onglets en bas au mobile, une barre latérale au web.

## Comment on l'utilise

Chaque front déclare un alias vers ce dossier dans sa configuration Vite :

```ts
resolve: { alias: { '@partage': fileURLToPath(new URL('../partager/src', import.meta.url)) } }
```

puis importe normalement :

```ts
import { creerClient } from '@partage/api'
import { euros, ETAPES_SUIVI } from '@partage/metier'
import type { Commande } from '@partage/types'
```

Pas de compilation intermédiaire, pas de publication : les deux fronts
compilent le TypeScript source. C'est le montage le plus simple qui marche, et
le seul qui ne demande pas de reconstruire le paquet à chaque modification.
