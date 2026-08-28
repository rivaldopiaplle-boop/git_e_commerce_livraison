# Contrat Mobile

> Rôles concernés : **Client** (le seul rôle présent sur les deux supports) et
> **Livreur** (Express et Standard), qui n'existe **que** sur mobile.
> Vendeur, gestionnaire et admin restent web.
>
> La technologie exacte est encore ouverte — voir
> [Q-01](../00-pilotage/questions-ouvertes.md). Tout ce document est valable quel
> que soit le choix, parce qu'il parle de structure et de comportement.

---

## 1. Structure imposée (règle d'or n°10)

Cinq onglets en bas, du plus important au moins important. **Le troisième est un
« + »** qui déplie vers le bas les actions de priorité moyenne. Chaque onglet est
une icône avec son libellé dessous. Tout est cliquable ou dépliable ; les
fonctions secondaires se cachent derrière les principales pour une interface
dense (feuilles glissantes, accordéons, appuis longs).

```
┌──────────────────────────────┐
│  contenu                     │
│                              │
├──────────────────────────────┤
│  ◆      ◆      ✚      ◆    ◆ │
│ onglet onglet  plus  onglet  │
└──────────────────────────────┘
```

## 2. Client — accent vert `#16a34a`

| # | Onglet | Contenu |
|---|---|---|
| 1 | **Accueil** | Bandeau « Livrer à … », boutiques proches, catalogue |
| 2 | **Recherche** | Recherche, filtres, catégories |
| 3 | **✚** | Panier, favoris, codes promo, aide, parrainage |
| 4 | **Commandes** | En cours avec frise, historique |
| 5 | **Profil** | Adresses, moyens de paiement, notifications, paramètres |

Ce que le mobile fait mieux que le web, et qu'il faut exploiter :
géolocalisation pour le bandeau d'adresse, notifications push, appareil photo
pour ouvrir un litige avec une preuve, appel du livreur en un geste.

## 3. Livreur Express (Amine) — accent violet `#7c3aed`

| # | Onglet | Contenu |
|---|---|---|
| 1 | **Ma course** | La course en cours : carte, adresse, contact, bouton de statut |
| 2 | **Disponibles** | Les courses proches — **vide et expliqué s'il est déjà en course** (R-23) |
| 3 | **✚** | Historique, gains, aide, signaler un problème |
| 4 | **Notifications** | |
| 5 | **Profil** | Disponibilité (le bouton le plus important de l'application), véhicule, documents |

Écran de course en cours, dans l'ordre de lecture : à qui, où, quoi faire, un
seul bouton d'action principal. Le bouton change avec le statut : *J'ai récupéré*
→ *Je suis arrivé* → *Livré* / *Client absent*. Jamais de menu de statuts libre.

## 4. Livreur Standard (Julien) — accent violet `#7c3aed`

| # | Onglet | Contenu |
|---|---|---|
| 1 | **Ma tournée** | Liste ordonnée des arrêts, progression, distance restante |
| 2 | **Arrêt suivant** | Navigation, adresse, colis, contact, bouton de statut |
| 3 | **✚** | Historique, gains, aide, signaler un problème |
| 4 | **Notifications** | |
| 5 | **Profil** | Disponibilité, entrepôt de rattachement |

Un arrêt ne peut pas être sauté sans être déclaré (livré, absent, refusé).

## 5. Ce que le mobile doit gérer et que le web ignore

- **Perte de réseau.** Un livreur passe sous un porche : l'action est mise en
  file et rejouée au retour du réseau, avec un indicateur visible. Une
  déclaration de livraison ne doit jamais être perdue.
- **Batterie et position.** La position n'est envoyée que pendant une course
  active, à intervalle raisonnable (30 à 60 s), jamais en continu toute la journée.
- **Permissions refusées.** Position, notifications, appareil photo : chaque refus
  a un écran d'explication et un chemin de secours (saisie manuelle de l'adresse,
  consultation active des notifications).
- **Écran verrouillé et mains occupées.** Cibles tactiles larges, action
  principale unique, contraste fort en extérieur.

## 6. Cohérence avec le web (règle d'or n°7)

Mêmes icônes, mêmes libellés, mêmes couleurs de statut, même vocabulaire. Un
statut `EN_TOURNEE` s'affiche « En tournée » partout. Ce qui change : la
disposition (onglets contre sidebar) et la densité.

## 7. Ce qui est hors périmètre mobile

Aucune administration, aucune gestion de catalogue, aucune statistique de vente
sur mobile. Si le besoin apparaît, c'est le signe qu'un rôle a été mal découpé.
