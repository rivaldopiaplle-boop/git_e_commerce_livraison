# Le diagramme MCD — ce qui a été fait, et comment le maintenir

> Ce fichier remplace `mcd-a-corriger.md`, qui listait l'écart entre le diagramme
> et le modèle cible. **Cet écart est résorbé** : [mcd.html](mcd.html) a été
> régénéré au bloc C d'après [dictionnaire-donnees.md](dictionnaire-donnees.md).
> Il reste ici la façon de le modifier sans le casser.

---

## État actuel

| | Avant | Maintenant |
|---|---|---|
| Entités | 18 | **33** |
| Associations | 25 | **51** |
| Compte d'authentification commun | absent | `UTILISATEUR` + spécialisation en 5 profils |
| Adresse | rattachée au seul client | entité partagée client / vendeur / entrepôt |
| Photos produit | un champ `image_url` | entité `PHOTO_PRODUIT` ordonnée |
| Circuit Standard | absent du dessin | `SOUS_COMMANDE`, `ENTREPOT`, `TOURNEE`, `ARRET_TOURNEE` |
| Traçabilité | absente | `MOUVEMENT_STOCK`, `HISTORIQUE_STATUT`, `JOURNAL_AUDIT` |
| Argent | montants flottants | entiers en centimes, `REPARTITION_VENDEUR`, `REMBOURSEMENT` |

Le diagramme et le dictionnaire portent exactement les 33 mêmes entités. **En cas
de désaccord entre les deux, le dictionnaire fait foi** : c'est lui qui sera
traduit en modèles Django.

---

## Comment le fichier est construit

Tout le diagramme est produit par deux tableaux JavaScript en fin de fichier :

- **`ENTITIES`** — pour chaque entité : identifiant, zone de couleur, position
  `x`/`y`, liste d'attributs `[nom, type, estClePrimaire]` ;
- **`RELATIONS`** — pour chaque association : verbe, position, attributs portés,
  et `links` avec la cardinalité `(min,max)` de chaque branche ; `xor:true`
  dessine la contrainte d'exclusion en rouge pointillé.

Modifier le modèle revient à modifier ces deux tableaux, plus `ZONES` si on
ajoute une zone de couleur. **Rien d'autre n'est à toucher** : les boîtes, les
traits, les étiquettes de cardinalité et la légende se recalculent seuls.

---

## Les trois pièges quand on y touche

1. **Les boîtes ne se poussent pas entre elles.** Les positions sont absolues :
   deux entités aux mêmes coordonnées se superposent silencieusement. Un contrôle
   automatique est décrit plus bas.
2. **Une entité citée dans `RELATIONS` mais absente d'`ENTITIES` fait planter le
   dessin sans message** — le diagramme s'affiche à moitié.
3. **Les traits sont droits.** Sur 33 entités, certains traversent forcément une
   zone chargée. C'est pour ça que **les entités sont déplaçables à la souris** :
   glisser une boîte est le moyen le plus rapide de lire une partie du schéma, et
   la disposition d'origine revient au rechargement de la page.

---

## Contrôler le fichier après modification

Depuis `plan-organisation/02-modele/`, avec Node installé :

```bash
node -e "
const fs=require('fs'); const s=fs.readFileSync('mcd.html','utf8');
const js=s.slice(s.indexOf('<script>')+8, s.lastIndexOf('</script>'));
const E=eval(js.slice(js.indexOf('const ENTITIES'), js.indexOf('const RELATIONS'))+' ENTITIES');
const R=eval(js.slice(js.indexOf('const RELATIONS'), js.indexOf('/* ====',js.indexOf('const RELATIONS')))+' RELATIONS');
const ids=new Set(E.map(e=>e.id)); let n=0;
R.forEach(r=>r.links.forEach(([id])=>{ if(!ids.has(id)){console.log('entite inconnue:',r.id,id); n++;} }));
const b=e=>({x:e.x,y:e.y,w:210,h:36+17*e.attrs.length});
for(let i=0;i<E.length;i++) for(let j=i+1;j<E.length;j++){
  const a=b(E[i]),c=b(E[j]);
  if(a.x<c.x+c.w&&c.x<a.x+a.w&&a.y<c.y+c.h&&c.y<a.y+a.h){console.log('chevauchement:',E[i].id,E[j].id); n++;}
}
console.log(E.length+' entites, '+R.length+' associations, '+n+' probleme(s));
"
```

Ce contrôle a été passé après la régénération : **33 entités, 51 associations,
0 problème.**

---

## Ce qui est volontairement absent du dessin

Trois rattachements existent dans le modèle mais ne sont pas tracés, parce qu'ils
ajouteraient de longs traits sans rien apprendre :

- `MOUVEMENT_STOCK.auteur` → `UTILISATEUR` (traçabilité) ;
- `PROMOTION.vendeur` → `VENDEUR`, facultatif (vide = promotion plateforme) ;
- la cible d'un `AVIS`, portée par `cible` + `id_cible` : un avis vise **soit** un
  produit, **soit** une boutique, **soit** un livreur — jamais deux à la fois.

C'est écrit dans la légende du diagramme lui-même, pour que personne ne conclue à
un oubli.

---

## Si le modèle change encore

1. Modifier d'abord [dictionnaire-donnees.md](dictionnaire-donnees.md).
2. Reporter dans `ENTITIES` / `RELATIONS`.
3. Passer le contrôle ci-dessus.
4. Mettre à jour le sous-titre du diagramme (le compte d'entités et
   d'associations y est écrit en clair).
5. Noter la décision qui a motivé le changement dans
   [journal-decisions.md](../00-pilotage/journal-decisions.md).
