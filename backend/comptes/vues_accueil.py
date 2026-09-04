"""L'accueil, en UN seul appel — O-1, O-2, O-5.

Ton reproche : *« les onglets menus sont très peu remplis, surtout le premier
onglet accueil et son équivalent »*, et *« tu ne t'es pas inspiré des vraies
applications d'e-commerce et de livraison »*.

Il était juste. L'accueil du client montrait **trois tuiles** : deux compteurs
et un bouton vers le catalogue. Aucune vraie application de livraison ne
ressemble à ça — elles montrent toutes, dans cet ordre : où l'on est livré, ce
qui est en cours, ce qu'on cherche, et ce qu'on peut commander tout de suite.

**Pourquoi un seul point d'entrée** plutôt que huit appels depuis l'écran :

  · sur un téléphone en 4G, huit allers-retours font huit fois la latence, et
    l'écran se remplit par morceaux dans le désordre ;
  · l'accueil se rafraîchit en fond toutes les vingt secondes (O-5). Huit
    appels toutes les vingt secondes, ce serait huit fois trop.

Le même point sert le client et le livreur : c'est le rôle connecté qui décide
du contenu, jamais un paramètre venu de l'écran. Un écran qui demande
« donne-moi le tableau de bord livreur » est un écran à qui l'on peut mentir.
"""
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from coeur.adresses import LIVREUR, adresse_pour
from coeur.geographie import distance_km

# Ce qu'on montre d'un coup : assez pour remplir un ecran, pas assez pour
# faire une requete lourde a chaque rafraichissement de fond.
COMBIEN_PRODUITS = 8
COMBIEN_BOUTIQUES = 8


def _produits(requete, produits):
    from catalogue.serializers import ProduitListeSerializer
    from catalogue.views import notes_publiques

    # Les notes en une seule requete : sans elle, huit vignettes couteraient
    # huit requetes, et l'accueil se recharge toutes les vingt secondes.
    return ProduitListeSerializer(
        produits, many=True,
        context={"request": requete, "notes": notes_publiques(produits)},
    ).data


def _accueil_client(requete, profil):
    from catalogue.models import Categorie
    from catalogue.views import _visibles
    from commandes.models import Commande, StatutCommande
    from commandes.services import panier_courant
    from comptes.models import Adresse

    # ── Où l'on est livré ────────────────────────────────────────────────
    #
    # En tête, parce que c'est cette adresse qui décide des boutiques Express
    # visibles (D-09) : un catalogue qui change sans qu'on sache pourquoi est
    # le meilleur moyen de faire croire que l'application est cassée.
    principale = (
        Adresse.objects.filter(adresseclient__client=profil, adresseclient__est_principale=True)
        .first()
        if profil else None
    )
    if principale is None and profil is not None:
        principale = Adresse.objects.filter(adresseclient__client=profil).first()

    # ── Ce qui est en cours ──────────────────────────────────────────────
    #
    # Une seule commande, la plus avancée : c'est celle qu'on guette. Les
    # autres sont à un onglet de distance.
    en_cours = (
        Commande.objects.filter(client=profil)
        .exclude(statut_actuel__in=[
            StatutCommande.LIVREE, StatutCommande.ANNULEE, StatutCommande.REMBOURSEE,
        ])
        .select_related("livraison")
        .prefetch_related("sous_commandes__vendeur")
        .order_by("-date_commande")
        .first()
        if profil else None
    )

    panier = panier_courant(requete.user, "", creer=False)
    lignes = list(panier.lignes.select_related("produit")) if panier else []

    catalogue = list(_visibles()[:60])
    lat = float(principale.latitude) if principale and principale.latitude else None
    lon = float(principale.longitude) if principale and principale.longitude else None

    # ── Les boutiques Express qui livrent VRAIMENT chez soi ──────────────
    boutiques = []
    vus = set()
    for produit in catalogue:
        vendeur = produit.vendeur
        if vendeur.id in vus or vendeur.type_activite != "EXPRESS":
            continue
        vus.add(vendeur.id)
        adresse = vendeur.adresse
        ecart = distance_km(lat, lon, adresse.latitude, adresse.longitude) if adresse else None
        boutiques.append({
            "id": vendeur.id,
            "nom": vendeur.nom_boutique,
            "ville": adresse.ville if adresse else "",
            "distance_km": ecart,
            "type_service": vendeur.type_activite,
        })
    boutiques.sort(key=lambda b: (b["distance_km"] is None, b["distance_km"] or 0))

    # ── Ce qu'on a déjà commandé ─────────────────────────────────────────
    #
    # « Commander à nouveau » est l'entrée la plus utilisée des applications de
    # livraison, et de loin : on recommande ce qu'on a aimé.
    deja = []
    if profil is not None:
        identifiants = list(
            Commande.objects.filter(client=profil)
            .values_list("sous_commandes__lignes__produit_id", flat=True)
            .distinct()[:20]
        )
        par_id = {produit.id: produit for produit in catalogue}
        deja = [par_id[i] for i in identifiants if i in par_id][:COMBIEN_PRODUITS]

    commandes = Commande.objects.filter(client=profil) if profil else Commande.objects.none()

    return {
        "role": "CLIENT",
        "adresse": (
            {"id": principale.id, "libelle": principale.libelle,
             "ville": principale.ville, "code_postal": principale.code_postal}
            if principale else None
        ),
        "panier": {
            "articles": sum(ligne.quantite for ligne in lignes),
            "total_centimes": sum(
                ligne.quantite * ligne.prix_capture_centimes for ligne in lignes
            ),
            "apercu": [ligne.produit.nom for ligne in lignes[:3] if ligne.produit_id],
        },
        "commande_en_cours": (
            {
                "id": en_cours.id,
                "numero_commande": en_cours.numero_commande,
                "type_service": en_cours.type_service,
                "statut_actuel": en_cours.statut_actuel,
                "montant_total_centimes": en_cours.montant_total_centimes,
                "boutiques": [
                    sous.vendeur.nom_boutique for sous in en_cours.sous_commandes.all()
                ],
                # Le code que le livreur demandera a la porte. Il etait genere
                # et n'apparaissait NULLE PART cote client (O-5).
                "code_confirmation": getattr(
                    getattr(en_cours, "livraison", None), "code_confirmation", ""
                ),
            }
            if en_cours else None
        ),
        "compteurs": {
            "en_cours": commandes.exclude(statut_actuel__in=[
                StatutCommande.LIVREE, StatutCommande.ANNULEE, StatutCommande.REMBOURSEE,
            ]).count(),
            "livrees": commandes.filter(statut_actuel=StatutCommande.LIVREE).count(),
            "total_depense_centimes": commandes.aggregate(
                total=Sum("montant_total_centimes")
            )["total"] or 0,
        },
        "categories": [
            {"slug": categorie.slug, "nom": categorie.nom,
             "univers": categorie.parente.nom if categorie.parente_id else "Autres",
             "nombre": categorie.nombre}
            # Pas de filtre sur la parente : c'est le nombre de produits qui
            # ecarte les univers, puisqu'aucun produit ne s'y rattache
            # directement. Filtrer sur `parente__isnull=False` ecartait aussi
            # les categories a plat, qui existent des qu'on cree un produit a
            # la main sans choisir d'univers.
            for categorie in Categorie.objects.select_related("parente")
            .annotate(nombre=Count("produits"))
            .filter(nombre__gt=0).order_by("-nombre")[:10]
        ],
        "boutiques_express": boutiques[:COMBIEN_BOUTIQUES],
        "a_commander_de_nouveau": _produits(requete, deja),
        "populaires": _produits(requete, catalogue[:COMBIEN_PRODUITS]),
    }


def _accueil_livreur(requete, profil):
    from livraisons.models import Livraison, StatutLivraison
    from livraisons.vues_livreur import courses_proposables

    aujourdhui = timezone.now().date()
    faites = Livraison.objects.filter(
        livreur=profil, statut_livraison=StatutLivraison.LIVREE,
        date_reelle__date=aujourdhui,
    )
    en_cours = (
        Livraison.objects.filter(livreur=profil)
        .exclude(statut_livraison__in=[StatutLivraison.LIVREE, StatutLivraison.ECHOUEE])
        .select_related("commande", "adresse_livraison")
        .first()
    )
    # Le MEME calcul que l'ecran « A proximite » (O-5). Deux comptages separes
    # finiraient par annoncer « 7 courses » ici et « aucune course » la-bas,
    # ce qui s'est exactement produit avant cette correction.
    proposables, raison = courses_proposables(profil)

    return {
        "role": "LIVREUR",
        "mode": profil.mode_livraison,
        # Un livreur pas encore valide voyait un tableau de bord vide sans
        # comprendre pourquoi, et l'API lui refusait ses courses en 403.
        "statut_validation": profil.statut_validation,
        "disponibilite": profil.statut_disponibilite,
        # La journee, et pas seulement le cumul de toujours : c'est ce qu'un
        # livreur regarde le matin et le soir.
        "aujourdhui": {
            "courses": faites.count(),
            "gains_centimes": faites.aggregate(
                total=Sum("remuneration_livreur_centimes")
            )["total"] or 0,
            "distance_km": float(faites.aggregate(total=Sum("distance_km"))["total"] or 0),
        },
        "course_en_cours": (
            {
                "id": en_cours.id,
                "client": f"{en_cours.commande.client.utilisateur.prenom} "
                          f"{en_cours.commande.client.utilisateur.nom}".strip(),
                "statut_livraison": en_cours.statut_livraison,
                "libelle_statut": en_cours.get_statut_livraison_display(),
                "adresse": adresse_pour(LIVREUR, en_cours.adresse_livraison),
                "remuneration_centimes": en_cours.remuneration_livreur_centimes,
            }
            if en_cours else None
        ),
        "disponibles": len(proposables),
        "raison_indisponibilite": raison,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def accueil(requete):
    """Tout ce que l'écran d'accueil affiche, selon le rôle connecté."""
    client = getattr(requete.user, "profil_client", None)
    if client is not None:
        return Response({"data": _accueil_client(requete, client)})

    livreur = getattr(requete.user, "profil_livreur", None)
    if livreur is not None:
        return Response({"data": _accueil_livreur(requete, livreur)})

    # Les autres rôles n'ont pas d'accueil mobile (D-40) : le dire vaut mieux
    # qu'un objet vide, qui ferait chercher un bogue.
    return Response({"data": {"role": getattr(requete.user, "role", ""), "mobile": False}})
