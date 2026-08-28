# Contrat des médias — photos produit, logos, preuves

> Réponse au bloc C-5 : *« comment est-ce que ça doit se passer pour la photo du
> produit ? Est-ce que c'est moi qui dois aller chercher les images, les renommer
> et te les donner, ou tu peux aller les chercher sur Internet ? »*
>
> Réponse courte : **le vendeur téléverse ses photos depuis son ordinateur ou son
> téléphone, comme sur n'importe quelle boutique en ligne. Et pour les images de
> démonstration, tu n'as rien à faire — le script de peuplement va les chercher
> lui-même.** Le détail est ci-dessous.

---

## 1. Ce que le vendeur fait, à l'écran

Sur l'écran « nouveau produit », une zone de dépôt occupe le haut du formulaire.

1. Le vendeur **glisse ses fichiers** dedans, ou clique pour ouvrir le sélecteur
   de fichiers. Depuis un téléphone, le même bouton propose l'appareil photo.
2. Chaque image apparaît immédiatement en vignette, **avant tout envoi au
   serveur** — c'est ce qui donne l'impression de réactivité.
3. La première vignette porte l'étiquette « principale » : c'est elle qui sert au
   catalogue. Le vendeur peut **réordonner par glisser-déposer** ; la première
   position devient la photo principale.
4. Une croix supprime une image. Un bandeau indique « 3 photos sur 6 ».
5. Le produit ne peut pas être publié sans **au moins une photo**. Sans cette
   règle, un catalogue de démonstration devient une grille de rectangles gris.

**Limites, affichées avant l'erreur et non après** : six photos par produit,
5 Mo par fichier, formats JPEG, PNG et WebP, 600 × 600 pixels minimum. Un fichier
refusé le dit en clair (« cette image fait 8 Mo, la limite est 5 Mo »), jamais par
un message technique.

---

## 2. Ce que le navigateur fait avant d'envoyer

Deux traitements côté client, pour ne pas faire transiter 40 Mo sur une connexion
de téléphone :

- **Réduction** : toute image dont le plus grand côté dépasse 1 600 pixels est
  redimensionnée dans un `canvas` avant l'envoi.
- **Vérification** : type et taille contrôlés tout de suite.

Ces deux contrôles sont du confort, **jamais de la sécurité** : le serveur
revérifie tout, parce qu'un navigateur se contourne.

---

## 3. Ce que le serveur fait

1. **Vérifie le contenu réel du fichier**, pas son extension : Pillow ouvre
   l'image et refuse ce qui n'en est pas une (`.jpg` qui contient un script).
2. **Retire les métadonnées EXIF** — une photo prise au téléphone contient les
   coordonnées GPS du vendeur. Les publier serait une fuite de données, discrète
   et grave.
3. **Envoie l'original à Cloudinary** et ne garde en base que l'identifiant et
   l'URL.
4. **Ne fabrique aucune vignette** : les tailles sont demandées dans l'URL
   (`w_200` pour la liste, `w_600` pour la carte, `w_1400` pour le zoom, avec
   `f_auto,q_auto` qui sert du WebP ou de l'AVIF selon le navigateur). C'est la
   règle d'or n°5 : redimensionner et convertir sont déjà faits par le service,
   les refaire à la main coûterait du code, du processeur et du disque.

**Rien d'important ne vit jamais sur le disque de l'API.** Le conteneur Render
repart de zéro à chaque redéploiement ; une photo écrite sur son disque
disparaît sans prévenir ([D-19](../00-pilotage/journal-decisions.md)).

---

## 4. Où c'est stocké, et à quel prix

| Média | Où | Visibilité |
|---|---|---|
| Photos produit, logo de boutique | Cloudinary | Publique |
| Preuve de livraison (photo du colis déposé) | Cloudinary, dossier privé | Client, livreur concerné, admin |
| Pièces jointes d'un litige | Cloudinary, dossier privé | Parties du litige et admin |

**Coût** : l'offre gratuite de Cloudinary est calibrée bien au-delà d'un projet de
démonstration. Comme toutes les offres gratuites, elle bouge — à vérifier au
moment de créer le compte, pas sur la foi de ce document
([D-19](../00-pilotage/journal-decisions.md) applique la même prudence à
l'hébergement).

**Vie privée** : une preuve de livraison montre la porte d'entrée de quelqu'un.
Elle est servie par URL signée à durée limitée, jamais publique, et effacée au
bout de 90 jours. Ce point se dit très bien en entretien.

**En développement, aucune clé n'est nécessaire** : sans configuration
Cloudinary, le stockage bascule sur le disque local
(`MEDIA_ROOT`). Même interface, deux implémentations — c'est exactement le
principe du simulateur de la décision
[D-18](../00-pilotage/journal-decisions.md).

---

## 5. Ce que ça change dans le modèle

Nouvelle entité **`PHOTO_PRODUIT`** : `#id_photo`, *id_produit*, `url`, `ordre`,
`texte_alternatif`. Un produit a de une à six photos ordonnées.

`PRODUIT.image_principale_url` est **conservé volontairement** : c'est une copie
de l'URL de la photo d'ordre 1. Sans elle, afficher une grille de cinquante
produits demanderait cinquante jointures. C'est une dénormalisation assumée, mise
à jour à chaque réordonnancement.

`texte_alternatif` n'est pas décoratif : c'est ce que lit un lecteur d'écran, et
ce que voit un recruteur attentif à l'accessibilité. Rempli automatiquement avec
« *nom du produit* — *nom de la boutique* » si le vendeur le laisse vide.

---

## 6. Les endpoints

| Verbe | Chemin | Qui | Effet |
|---|---|---|---|
| `POST` | `/produits/{id}/photos` | Vendeur propriétaire | Envoi multipart, une ou plusieurs images |
| `PATCH` | `/produits/{id}/photos/ordre` | Vendeur propriétaire | Nouvel ordre, liste d'identifiants |
| `DELETE` | `/produits/{id}/photos/{idPhoto}` | Vendeur propriétaire | Suppression réelle du fichier |
| `POST` | `/livraisons/{id}/preuve` | Livreur assigné | Photo de preuve depuis le mobile |
| `POST` | `/litiges/{id}/pieces` | Client ou vendeur partie au litige | Jusqu'à trois pièces |

Une photo est un fichier, pas une donnée d'affaires : sa suppression est réelle,
contrairement à la règle de suppression logique
([D-13](../00-pilotage/journal-decisions.md)) qui protège les comptes, les
boutiques et les produits. Garder indéfiniment des fichiers que personne
n'affiche coûte du stockage sans rien prouver.

**Un vendeur ne peut téléverser que sur ses propres produits**, vérifié côté
serveur. Le nombre d'envois est plafonné par heure et par compte : c'est le
point d'entrée le plus évident pour saturer un espace de stockage gratuit.

---

## 7. Les images de démonstration — qui les fournit

**Toi, rien.** Le script `seed_demo` s'en charge :

1. Il lit `donnees-demo/catalogue.json`, une liste figée de produits (nom, prix,
   catégorie, boutique, **URL d'image**).
2. Il télécharge chaque image depuis une source **sous licence libre**
   (Unsplash, Pexels : usage libre, y compris commercial, attribution non exigée)
   et la fait passer par le **même circuit de téléversement** que celui d'un
   vendeur. Le peuplement teste donc la chaîne d'envoi au lieu de la contourner.
3. **Hors ligne, ou si une URL est morte** : Pillow fabrique une image de repli —
   un aplat de couleur avec le nom du produit. Le catalogue reste présentable,
   la démonstration ne casse jamais parce qu'un site tiers a bougé.
4. Les sources sont recopiées dans `donnees-demo/CREDITS.md`. Ce n'est pas exigé
   par la licence ; c'est une politesse, et ça se remarque.

**Si tu veux un catalogue à ton goût** — parce que tu préfères un univers
précis, ou des photos plus cohérentes entre elles — dépose tes fichiers dans
`donnees-demo/images/` en les nommant d'après l'identifiant du produit
(`bol-ramen.jpg`, `casque-audio.jpg`). Le script les préfère à tout
téléchargement. C'est une option, pas une corvée : sans rien faire, tu as un
catalogue complet.

**Ce que le script ne fera jamais** : parcourir le web au hasard pour ramasser
des images dont personne ne connaît la licence. La liste est figée, relue, et
versionnée avec le projet.

---

## 8. Ce qu'il ne faut pas faire, et pourquoi

| Tentation | Pourquoi c'est un piège |
|---|---|
| Stocker les images en base (`BYTEA`) | La base gonfle, les sauvegardes deviennent lourdes, chaque affichage passe par Django |
| Stocker sur le disque de l'API | Le disque de Render est effacé à chaque redéploiement |
| Fabriquer les vignettes soi-même | Cloudinary le fait dans l'URL, gratuitement et mieux |
| Accepter n'importe quelle taille | Une photo de 12 Mo par produit rend le catalogue inutilisable sur téléphone |
| Faire confiance à l'extension du fichier | C'est le moyen le plus classique de faire téléverser autre chose qu'une image |
| Servir les preuves de livraison en URL publique | Une adresse privée devient indexable |
