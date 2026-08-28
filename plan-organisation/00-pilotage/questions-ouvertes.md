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

**Aucune.** Les deux dernières ont été tranchées au bloc D : tu suis les
recommandations (retours de produits hors périmètre, argent visible par rôle).

---

## Différables — on peut coder sans

### Q-09 — Périmètre exact de l'agent IA
Acté au bloc A : planifié dans les contrats, absent du modèle de données. Reste
à choisir entre assistant de support, recommandations et détection de fraude —
et à décider si c'est un modèle appelé par API (coût, clé, réseau) ou un
classifieur simple entraîné en local, comme sur le projet banque.

### Q-10 — Optimisation réelle des tournées
Le regroupement fin (problème de tournées de véhicules) est en palier 2, avec un
solveur existant. Le MVP attribue par zone et ordre d'arrivée.

### Q-11 — Promotions : qui les crée, cumul, ciblage
Le bloc A ne traite que « expiré » et « non cumulable ». Qui crée une promotion
— le vendeur pour sa boutique, l'admin pour la plateforme, les deux ? — n'est
pas tranché. Le modèle prévoit déjà les deux cas (`PROMOTION.vendeur` facultatif,
vide = promotion plateforme).

### Q-12 — Multi-langue et multi-devise
Non traité. Recommandation : français et euro uniquement, assumé.

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

Trois sujets non posés en question mais tranchés au passage : les photos produit
([D-24](journal-decisions.md)), le géocodage ([D-25](journal-decisions.md)) et la
bibliothèque d'interface ([D-26](journal-decisions.md)).
