# Questions ouvertes — ce qui reste à trancher

> Rangées par urgence : une question bloquante empêche d'écrire du code
> correctement ; une question différable peut attendre sans coût.
>
> Quand tu réponds, la question quitte cette page et devient une décision dans
> [journal-decisions.md](journal-decisions.md).

---

## Bloquantes — à trancher avant la première ligne de code

**Aucune.** Les six questions bloquantes ou importantes ont été tranchées au
bloc C (voir la liste en bas de page). Le développement peut commencer.

---

## Importantes — à trancher avant les écrans concernés

**Aucune.**

<details>
<summary>Q-13 — Colibri ou RivDinde ? — <b>tranchée au bloc F : RivDinde</b></summary>

### Q-13 — Colibri ou RivDinde ?
Les deux sont dessinés côte à côte dans
[identite-visuelle.html](../04-maquettes/identite-visuelle.html) : **Colibri**
(sections 1 à 6) et **RivDinde** (section 7, ta demande du bloc E-3).

| | Colibri | RivDinde |
|---|---|---|
| Ce que le nom dit | Cache « colis », évoque vitesse et précision | Porte ton prénom, unique, mémorable |
| Risque | Nom de marque répandu en France | « Dinde » s'emploie comme insulte légère en français |
| Le symbole à 16 px | Net — trois faces, une aile | Devient une tache : il faudra un second symbole simplifié |
| Ce qu'il reste à faire | Rien | Un vrai rendu 3D si tu veux le réalisme demandé (générateur d'images, Blender ou illustrateur) |

**Ma recommandation** : Colibri pour le nom, parce qu'il sera lu par un recruteur
avant d'être expliqué. Mais c'est ta décision, et RivDinde a pour lui une chose
que Colibri n'aura jamais : il est à toi. Une voie intermédiaire existe —
garder **RivDinde** comme nom et la dinde comme mascotte de la page d'accueil,
avec un symbole simple pour l'onglet et l'icône de l'application.
**Réponse au bloc F** : **RivDinde**, avec un logo fourni par toi. Voir
[D-30 révisée](journal-decisions.md).

</details>

---

## Différables — on peut coder sans

**Aucune.** Les trois dernières ont été tranchées au bloc I-6.

---

## Tranchées au bloc C — pour mémoire

| | Question | Décision |
|---|---|---|
| Q-01 | Technologie mobile | Ionic Vue + Capacitor — [D-20](journal-decisions.md) |
| Q-02 | L'entrepôt dans le MVP ? | Oui, avec tout le circuit Standard — [D-17 révisée](journal-decisions.md) |
| Q-03 | Hébergeur du backend | Render (conteneur) + Vercel (front) + Neon — [D-19](journal-decisions.md) |
| Q-04 | Adresse de boutique | `ADRESSE` entité partagée — [D-21](journal-decisions.md) |
| Q-05 | Catalogue Express du visiteur sans adresse | Bandeau « Livrer à … » — [D-22](journal-decisions.md) |
| Q-06 | Après une tentative de livraison échouée | Deux tentatives puis retour — [D-23](journal-decisions.md) |
| Q-07 | Retours de produits en bon état | Hors périmètre, assumé — [D-28](journal-decisions.md) *(bloc D)* |
| Q-08 | Afficher l'argent par rôle | Oui — [D-29](journal-decisions.md) *(bloc D)* |
| Q-09 | Périmètre de l'agent IA | Recommandations puis assistant, modèle par API — [D-43](journal-decisions.md) *(bloc I)* |
| Q-10 | Optimisation des tournées | Plus proche voisin dès le MVP — [D-44](journal-decisions.md) *(bloc I)* |
| Q-11 | Qui crée les promotions | Le vendeur et l'admin — [D-45](journal-decisions.md) *(bloc I)* |
| Q-12 | Multi-langue et multi-devise | Français et euro, assumé |

Trois sujets non posés en question mais tranchés au passage : les photos produit
([D-24](journal-decisions.md)), le géocodage ([D-25](journal-decisions.md)) et la
bibliothèque d'interface ([D-26](journal-decisions.md)).
