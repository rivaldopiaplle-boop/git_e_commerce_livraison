# Contrat Notifications et Agent IA

> Décision du bloc A-18 : les notifications et l'IA sont **planifiées dans les
> contrats, pas dans le MCD**. Elles consomment les données existantes, elles
> n'en imposent pas de nouvelles au modèle — sauf la table `NOTIFICATION`
> elle-même, qui reste nécessaire pour l'affichage in-app.

---

## 1. Principe fondateur

Une notification est un **canal complémentaire, jamais l'unique moyen d'être
informé** (scénario 13.1). Toute information critique reste consultable
activement dans l'application. Un client qui a coupé les notifications doit
pouvoir mener sa commande jusqu'au bout sans manquer une décision.

Corollaire de modélisation : l'in-app est **persistant** (une ligne en base),
l'e-mail et le push sont **volatils** (envoyés, pas rejouables).

---

## 2. Canaux

| Canal | Rôle | Palier | Implémentation |
|---|---|---|---|
| **In-app** | Toujours actif, sert d'historique | 1 | Table `NOTIFICATION` + cloche dans la navbar |
| **E-mail** | Informations importantes et froides | 1 | Service transactionnel, avec simulateur en développement |
| **Push** | Urgent et mobile | 2 | Firebase Cloud Messaging |
| **Appel masqué** | Livreur → client uniquement | 2 | Service tiers, simulé au MVP |

---

## 3. Matrice événement → canal → destinataire

| Événement | In-app | E-mail | Push | Destinataire |
|---|:-:|:-:|:-:|---|
| Compte créé | ✔ | ✔ | | L'intéressé |
| Compte vendeur/livreur validé ou rejeté | ✔ | ✔ | ✔ | L'intéressé |
| Compte suspendu | ✔ | ✔ | ✔ | L'intéressé |
| Commande confirmée | ✔ | ✔ | ✔ | Client |
| Nouvelle commande à préparer | ✔ | | ✔ | Vendeur, gestionnaire |
| Changement de statut de commande | ✔ | | ✔ | Client |
| **Annulation par le vendeur** | ✔ | **✔ fort** | ✔ | Client |
| Paiement échoué | ✔ | ✔ | | Client |
| Remboursement effectué | ✔ | ✔ | ✔ | Client |
| Course disponible à proximité | | | ✔ | Livreurs Express proches |
| Tournée affectée | ✔ | | ✔ | Livreur Standard |
| Livreur en route / arrivé | ✔ | | ✔ | Client |
| **Tentative échouée, client absent** | ✔ | ✔ | ✔ | Client |
| Colis reçu en entrepôt | ✔ | | | Client, vendeur |
| Colis attendu non reçu | ✔ | ✔ | | Vendeur |
| Stock bas | ✔ | | | Vendeur, gestionnaire |
| Produit de nouveau disponible | ✔ | ✔ | ✔ | Clients abonnés à l'alerte |
| Panier abandonné | | ✔ | | Client |
| Litige ouvert | ✔ | ✔ | | Admin, vendeur concerné |
| Litige résolu | ✔ | ✔ | ✔ | Client, vendeur |
| Commande sans livreur depuis trop longtemps | ✔ | ✔ | | Admin |
| Avis signalé comme abusif | ✔ | | | Admin |

Un « fort » signifie : envoyé même si l'utilisateur a réduit ses préférences.
Seuls trois événements sont forts — annulation vendeur, suspension de compte,
échec de livraison — parce qu'ils demandent une action et coûtent de l'argent.

---

## 4. Préférences utilisateur

L'utilisateur peut couper l'e-mail commercial (relance de panier, promotions) et
le push non critique. Il ne peut pas couper l'in-app, qui est son historique.
Une préférence est stockée par **catégorie** (transactionnel, logistique,
commercial), pas par événement : quinze cases à cocher ne sont jamais réglées.

---

## 5. Architecture d'envoi

Un changement d'état publie un **événement métier** (`commande.statut_change`,
`livraison.tentative_echouee`). Un service de notification s'y abonne, décide des
canaux d'après la matrice et les préférences, puis délègue à un **port** par
canal — chacun ayant une implémentation réelle et un simulateur
([D-18](../00-pilotage/journal-decisions.md)).

Conséquences concrètes : le code de commande ne connaît ni l'e-mail ni le push ;
ajouter un canal ne touche à aucun service métier ; et la démonstration
fonctionne sans compte Firebase ni fournisseur d'e-mail.

L'envoi est **asynchrone** : un e-mail lent ne doit jamais ralentir une réponse
d'API. Au palier 1, une file simple suffit (tâche différée Django) ; Celery n'est
justifié qu'au palier 2.

---

## 6. Agent IA — périmètre envisagé

Toujours non structurant pour le modèle : l'IA lit des données existantes.

| Piste | Valeur | Coût | Palier |
|---|---|---|---|
| **Assistant de support client** — répondre aux questions fréquentes (où est ma commande, comment annuler, politique de remboursement) avant escalade vers un humain | Élevée, très démontrable | Moyen | 2 |
| **Recommandations** « souvent achetés ensemble » | Moyenne | Faible | 2 |
| **Détection de comportement de paiement anormal** | Faible en démonstration | Moyen | 2 |
| **Estimation de délai apprise sur l'historique** | Bonne, originale | Élevé | Hors périmètre |

### Deux façons de le faire, et ce qu'elles coûtent

1. **Un classifieur entraîné localement** sur des questions étiquetées : gratuit,
   hors ligne, explicable, et **c'est exactement ce que le projet banque a fait
   avec succès**. L'assistant y est même documenté dans un fichier entier qui
   explique le modèle — un excellent sujet d'entretien, bien meilleur qu'un appel
   d'API que n'importe qui sait faire.
2. **Un appel à un modèle de langage** : plus impressionnant en démonstration,
   mais payant, dépendant du réseau, et il faut gérer les réponses inventées.

**Ma recommandation** : la première voie, avec une escalade vers l'admin quand la
confiance est trop basse — la même architecture que le projet banque, appliquée à
un domaine différent. Tu peux alors dire en entretien que tu as fait les deux
projets sans dépendre d'un fournisseur d'IA.

### Garde-fous, quel que soit le choix

L'assistant ne déclenche jamais d'action à conséquence financière (annuler,
rembourser) : il informe et propose, l'humain décide. Il ne voit que les données
de l'utilisateur connecté. Et il dit « je ne sais pas » plutôt que d'inventer :
c'est le point qui fait la différence entre un assistant utile et un gadget.
