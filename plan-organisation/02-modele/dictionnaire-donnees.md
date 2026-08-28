# Dictionnaire de données — le modèle cible

> Ce document est la **référence** du modèle : c'est lui qui doit être traduit en
> modèles Django, et c'est d'après lui que le diagramme
> [mcd.html](mcd.html) a été régénéré au bloc C — les deux sont désormais
> alignés (voir [mcd-maintenance.md](mcd-maintenance.md)). En cas de doute,
> **c'est ce dictionnaire qui fait foi**, jamais le dessin.
>
> Convention : `#` clé primaire, *italique* clé étrangère, **gras** attribut
> structurant (une règle métier en dépend).
> Tous les montants sont des **entiers en centimes**. Toutes les dates sont en
> UTC. Palier : dans quel palier du [périmètre](../01-produit/perimetre-et-mvp.md)
> l'entité est nécessaire.

---

## Zone 1 — Comptes et rôles

### UTILISATEUR — palier 1
Le compte d'authentification, **commun à tous les rôles**. C'est ce qui manquait
au modèle précédent : sans lui, sept tables portent chacune un e-mail et un mot
de passe, et rien ne garantit qu'un e-mail est unique dans la plateforme.

| Attribut | Type | Note |
|---|---|---|
| `#id_utilisateur` | INT | |
| `email` | VARCHAR unique | Identifiant de connexion |
| `mot_de_passe_hash` | VARCHAR | |
| `nom`, `prenom` | VARCHAR | |
| `telephone` | VARCHAR | |
| **`role`** | ENUM | `CLIENT`, `VENDEUR`, `GESTIONNAIRE`, `LIVREUR`, `ADMIN` |
| `statut_compte` | ENUM | `ACTIF`, `EN_ATTENTE_VALIDATION`, `SUSPENDU`, `DESACTIVE` |
| `date_inscription`, `derniere_connexion` | DATETIME | |

En Django : `AbstractUser` étendu, plus un profil par rôle en relation 1–1. Le
rôle vit sur l'utilisateur ; les données métier vivent sur le profil.

### CLIENT — palier 1
Profil d'un utilisateur `CLIENT` : `#id_client`, *id_utilisateur* (1–1),
`date_naissance`, `consentement_marketing`.

### VENDEUR — palier 1
| Attribut | Type | Note |
|---|---|---|
| `#id_vendeur` | INT | |
| *id_utilisateur* | INT | 1–1, le propriétaire |
| `nom_boutique` | VARCHAR | |
| **`type_activite`** | ENUM | `EXPRESS` \| `STANDARD` — commande tout le flux |
| **`rayon_livraison_km`** | DECIMAL | Express uniquement : au-delà, invisible au catalogue |
| *id_adresse* | INT | **Adresse de la boutique — absente du modèle précédent, sans elle le filtrage par rayon est impossible** |
| `siret`, `description`, `logo_url` | VARCHAR | |
| `note_moyenne` | DECIMAL | Dénormalisé, recalculé |
| `statut_validation` | ENUM | `EN_ATTENTE`, `VALIDE`, `REJETE`, `SUSPENDU` |
| **`compte_stripe_id`** | VARCHAR | Compte Stripe Connect, requis pour être payé |
| **`taux_commission`** | DECIMAL | Part prélevée par la plateforme |

### GESTIONNAIRE — palier 1 (staff vendeur) / palier 2 (staff entrepôt)
| Attribut | Type | Note |
|---|---|---|
| `#id_gestionnaire` | INT | |
| *id_utilisateur* | INT | 1–1 |
| **`type_gestionnaire`** | ENUM | `STAFF_VENDEUR` \| `STAFF_ENTREPOT` |
| *id_vendeur* | INT | Renseigné **si et seulement si** `STAFF_VENDEUR` |
| *id_entrepot* | INT | Renseigné **si et seulement si** `STAFF_ENTREPOT` |
| `date_embauche` | DATE | |

Contrainte **XOR** : exactement un des deux rattachements est renseigné.

### LIVREUR — palier 1
`#id_livreur`, *id_utilisateur* (1–1), `vehicule` (ENUM `VELO`, `SCOOTER`,
`VOITURE`, `CAMIONNETTE`), **`mode_livraison`** (`EXPRESS` \| `STANDARD`),
*id_entrepot* (Standard uniquement, son rattachement), `statut_validation`,
`statut_disponibilite` (`DISPONIBLE`, `EN_COURSE`, `HORS_LIGNE`),
`position_lat` / `position_lon` (dernière position connue), `note_moyenne`.

### ADMIN — palier 1
`#id_admin`, *id_utilisateur* (1–1), `niveau` (ENUM `ADMIN`, `SUPER_ADMIN`).
**Absent du modèle précédent alors que c'est le rôle qui valide tout le reste.**

### ADRESSE — palier 1
Entité **partagée** : un client, un vendeur ou un entrepôt s'y rattachent.

`#id_adresse`, `libelle`, `rue`, `complement`, `ville`, `code_postal`, `pays`,
**`latitude`**, **`longitude`**, `instructions_livraison` (« code portail »,
« laisser devant la porte »), *id_zone_livraison*.

`ADRESSE_CLIENT` porte le rattachement d'un client à ses adresses, avec
`est_principale`.

---

## Zone 2 — Catalogue

### CATEGORIE — palier 1
`#id_categorie`, `nom`, `slug`, `description`, *id_categorie_parente* (réflexif).

### PRODUIT — palier 1
`#id_produit`, *id_vendeur*, *id_categorie*, `nom`, `description`,
**`prix_unitaire_centimes`** (INT), `image_principale_url`, `poids_grammes`,
**`stock_disponible`** (INT), **`stock_reserve`** (INT, réservations de paiement
en cours), `seuil_alerte`, `est_visible` (BOOL, masquage vendeur),
`date_ajout`, `date_maj`.

Stock réellement commandable = `stock_disponible − stock_reserve` (règles R-01 à R-03).

`image_principale_url` est une **copie** de l'URL de la photo d'ordre 1 : une
dénormalisation assumée, qui évite cinquante jointures pour afficher une grille
de cinquante produits. Voir [contrat-medias.md](../03-contrats/contrat-medias.md).

### PHOTO_PRODUIT — palier 1
Un produit a de une à six photos ordonnées — **manque du modèle précédent**, qui
n'en prévoyait qu'une seule et rendait toute fiche produit crédible impossible.
`#id_photo`, *id_produit*, `url`, `ordre` (INT, 1 = principale),
`texte_alternatif` (accessibilité, rempli automatiquement si laissé vide).
Parcours de téléversement, formats et stockage :
[contrat-medias.md](../03-contrats/contrat-medias.md) ([D-24](../00-pilotage/journal-decisions.md)).

### MOUVEMENT_STOCK — palier 1
Trace de tout changement de stock — **absent du modèle précédent** alors que le
scénario 4.4 l'exige.
`#id_mouvement`, *id_produit*, *id_utilisateur* (auteur), `type`
(`VENTE`, `REAPPRO`, `AJUSTEMENT`, `ANNULATION`, `RETOUR`), `quantite` (signée),
**`motif`** (obligatoire si `AJUSTEMENT`), `stock_apres`, `date_mouvement`.

### ALERTE_DISPONIBILITE — palier 1
Le « Être alerté quand disponible » de la décision D-06.
`#id_alerte`, *id_produit*, *id_utilisateur*, `date_demande`, `date_notification`,
`statut` (`EN_ATTENTE`, `NOTIFIEE`, `ANNULEE`).

---

## Zone 3 — Panier et commande

### PANIER — palier 1
`#id_panier`, *id_client* (nullable — panier invité), `cle_session` (pour
l'invité), `date_creation`, `date_maj`, `statut` (`ACTIF`, `CONVERTI`, `ABANDONNE`).

### LIGNE_PANIER — palier 1
`#id_ligne_panier`, *id_panier*, *id_produit*, `quantite`,
`prix_capture_centimes` (prix au moment de l'ajout, sert à détecter un changement
de prix — R-05), `date_ajout`.

### COMMANDE — palier 1
Une commande = **un seul mode de service**.

| Attribut | Type | Note |
|---|---|---|
| `#id_commande` | INT | |
| `numero_commande` | VARCHAR unique | Lisible par un humain |
| *id_client* | INT | |
| *id_adresse_livraison* | INT | Copie figée de l'adresse au moment de la commande |
| *id_panier_origine* | INT | Traçabilité du découpage |
| **`type_service`** | ENUM | `EXPRESS` \| `STANDARD` |
| `statut_actuel` | ENUM | Voir la machine à états ci-dessous |
| `montant_produits_centimes`, `montant_livraison_centimes`, `montant_remise_centimes`, `montant_total_centimes` | INT | |
| `date_commande`, `date_livraison_estimee` | DATETIME | |

### SOUS_COMMANDE — palier 1
La part d'une commande Standard revenant à un vendeur : **absente du modèle
précédent**, alors que c'est ce que le vendeur prépare et voit.
`#id_sous_commande`, *id_commande*, *id_vendeur*, `statut_preparation`,
`montant_vendeur_centimes`, `montant_commission_centimes`, `date_expedition_entrepot`.

Pour une commande Express, il y a exactement une sous-commande — ce qui permet
d'écrire un seul code pour les deux cas.

### LIGNE_COMMANDE — palier 1
`#id_ligne_commande`, *id_sous_commande*, *id_produit*, `nom_produit_capture`,
`prix_unitaire_centimes`, `quantite`, `sous_total_centimes`.
Le nom et le prix sont **recopiés** : une commande passée ne change jamais, même
si le produit est renommé ou supprimé.

### HISTORIQUE_STATUT — palier 1
`#id_historique`, `type_objet` (`COMMANDE` \| `LIVRAISON`), `id_objet`,
`statut_avant`, `statut_apres`, *id_utilisateur*, `commentaire`, `date_changement`.

### Machine à états d'une commande

`EN_ATTENTE_PAIEMENT` → `PAYEE` → `EN_PREPARATION` → `PRETE`
→ *(Standard)* `EXPEDIEE_ENTREPOT` → `RECUE_ENTREPOT` → `EN_TOURNEE`
→ *(Express)* `EN_LIVRAISON`
→ `LIVREE` · et depuis plusieurs états : `ANNULEE`, `REMBOURSEE`, `ECHEC_LIVRAISON`.

---

## Zone 4 — Paiement

### PAIEMENT — palier 1
`#id_paiement`, *id_commande*, `montant_centimes`, `methode`,
`statut_paiement` (`EN_ATTENTE`, `AUTORISE`, `CAPTURE`, `ECHOUE`, `REMBOURSE`),
`reference_stripe`, `date_paiement`.

### REPARTITION_VENDEUR — palier 1
La trace de ce que Stripe Connect a reversé à qui. Sans elle, aucun audit
possible sur une commande multi-vendeur.
`#id_repartition`, *id_paiement*, *id_sous_commande*, *id_vendeur*,
`montant_vendeur_centimes`, `montant_commission_centimes`, `reference_transfert_stripe`, `statut`.

### REMBOURSEMENT — palier 1
`#id_remboursement`, *id_paiement*, `montant_centimes`, `motif`,
`type` (`TOTAL`, `PARTIEL`), *id_utilisateur* (qui l'a déclenché),
`reference_stripe`, `date`.

### FACTURE — palier 1
`#id_facture`, *id_commande*, `numero_facture`, `date_emission`,
`montant_ht_centimes`, `montant_ttc_centimes`, `taux_tva`, `url_pdf`.

### PROMOTION — palier 1
`#id_promotion`, `code`, *id_vendeur* (nullable : promotion plateforme si vide),
`type_reduction` (`POURCENTAGE`, `MONTANT`, `FRAIS_LIVRAISON`), `valeur`,
`montant_minimum_centimes`, `date_debut`, `date_fin`, `quantite_max`,
`quantite_utilisee`, `cumulable` (BOOL).
`UTILISATION_PROMOTION` : *id_promotion*, *id_commande*, `montant_applique_centimes`.

---

## Zone 5 — Livraison

### ZONE_LIVRAISON — palier 1
`#id_zone`, `nom`, `polygone_gps` (GEOJSON ou liste de codes postaux au MVP),
*id_entrepot* (l'entrepôt qui dessert la zone), `frais_base_centimes`,
`seuil_gratuite_centimes`.

### ENTREPOT — palier 1
`#id_entrepot`, `nom`, *id_adresse*, `capacite`, `est_actif`.
Appartient à la plateforme, jamais à un vendeur (voir A-19).

### LIVRAISON — palier 1
`#id_livraison`, *id_commande* (1–1), *id_livreur* (nullable tant que non
attribuée), *id_tournee* (Standard uniquement), *id_adresse_livraison*,
`statut_livraison`, `distance_km`, `frais_calcules_centimes`,
`remuneration_livreur_centimes`, `date_attribution`, `date_prise_en_charge`,
`date_estimee`, `date_reelle`, `code_confirmation`.

### TOURNEE — palier 1
**Absente du modèle précédent** : sans elle, un livreur Standard n'a que des
livraisons isolées, ce qui contredit tout le flux Standard.
`#id_tournee`, *id_entrepot*, *id_livreur*, *id_gestionnaire_createur*,
*id_zone*, `statut` (`BROUILLON`, `PRETE`, `AFFECTEE`, `EN_COURS`, `TERMINEE`),
`date_creation`, `date_debut`, `date_fin`, `nombre_arrets`, `distance_totale_km`.

### ARRET_TOURNEE — palier 1
`#id_arret`, *id_tournee*, *id_livraison*, **`ordre`** (rang de passage),
`statut` (`A_FAIRE`, `LIVRE`, `ECHOUE`, `REPORTE`), `heure_estimee`, `heure_reelle`.

### TENTATIVE_LIVRAISON — palier 1
`#id_tentative`, *id_livraison*, `numero_tentative`, `resultat`
(`LIVREE`, `CLIENT_ABSENT`, `ADRESSE_INTROUVABLE`, `REFUSEE`),
`commentaire`, **`preuve_url`** (photo de dépôt ou signature), `date_tentative`,
`position_lat`, `position_lon`.

---

## Zone 6 — Relation client

### AVIS — palier 1
`#id_avis`, *id_client*, *id_commande* (garantit qu'on ne note que ce qu'on a
reçu), **`cible`** (`PRODUIT`, `VENDEUR`, `LIVREUR`), `id_cible`, `note` (1–5),
`commentaire`, `date_avis`, `statut_moderation`.
Trois cibles au lieu de deux : la note d'une **boutique** manquait.

### LITIGE — palier 1
`#id_litige`, *id_commande*, *id_client*, *id_admin_traitant*,
`motif` (`NON_CONFORME`, `ENDOMMAGE`, `INCOMPLET`, `NON_RECU`), `description`,
`preuves_urls`, `statut` (`OUVERT`, `EN_COURS`, `RESOLU`, `REJETE`),
`resolution`, `montant_rembourse_centimes`, `date_ouverture`, `date_resolution`.

### NOTIFICATION — palier 1
`#id_notification`, ***id_utilisateur*** (et non « client » : tous les rôles sont
notifiables), `type`, `titre`, `contenu`, `lien_action`, `canal`
(`IN_APP`, `EMAIL`, `PUSH`), `date_envoi`, `date_lecture`, `statut_envoi`.

### JOURNAL_AUDIT — palier 1
`#id_audit`, *id_utilisateur*, `action`, `type_objet`, `id_objet`,
`donnees_avant`, `donnees_apres`, `adresse_ip`, `date_action`.
Exigé par la décision D-13 (aucune suppression physique, tout est tracé).

---

## Contraintes transverses à ne pas oublier

1. **XOR gestionnaire** : rattaché à un vendeur **ou** à un entrepôt, jamais aux deux.
2. **XOR livreur** : un livreur Express n'a pas d'entrepôt ; un livreur Standard en a un.
3. **Une commande Express n'a qu'une sous-commande**, donc qu'un vendeur.
4. **Une commande Standard passe forcément par un entrepôt** avant livraison.
5. **`stock_disponible − stock_reserve ≥ 0`** en permanence.
6. **Un avis exige une commande livrée** appartenant au client qui note.
7. **Un vendeur non validé n'a aucun produit visible** au catalogue.
8. **Une livraison a un livreur unique à un instant donné**, et seul lui peut la faire évoluer.
9. **Aucune ligne n'est supprimée physiquement** : statut plus journal d'audit.
