"""Le catalogue : public en lecture, reserve au vendeur en ecriture.

Le point le plus structurant est le filtrage geographique (D-09) : les
produits d'un vendeur EXPRESS hors de son rayon de livraison ne sont pas
renvoyes du tout. Ce n'est pas un tri, c'est une absence — c'est ce qui rend
structurellement impossible une commande Express longue distance.
"""
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from coeur.geographie import distance_km
from comptes.models import StatutValidation, TypeService, Vendeur
from comptes.permissions import EstVendeur

from .models import Categorie, Produit
from .serializers import (
    BoutiqueSerializer,
    CategorieSerializer,
    ProduitDetailSerializer,
    ProduitEcritureSerializer,
    ProduitListeSerializer,
)


def _position(requete):
    """La position du visiteur, si elle est connue. Sinon (None, None)."""
    try:
        return float(requete.query_params["lat"]), float(requete.query_params["lon"])
    except (KeyError, TypeError, ValueError):
        return None, None


def _visibles():
    """Le catalogue public : produits visibles de vendeurs valides.

    Un vendeur non valide n'a aucun produit au catalogue (R-07), et un produit
    masque par son vendeur disparait sans etre supprime (D-13).
    """
    return (
        Produit.objects.select_related("vendeur", "vendeur__adresse", "categorie")
        .filter(est_visible=True, vendeur__statut_validation=StatutValidation.VALIDE)
    )


def _filtrer_par_rayon(produits, lat, lon):
    """Retire les produits Express hors du rayon, et calcule les distances.

    Sans position connue, les boutiques Express sont ecartees du resultat
    plutot que montrees a tort : mieux vaut un catalogue Standard complet
    qu'un restaurant a trois cents kilometres (D-22).
    """
    gardes, distances = [], {}

    for produit in produits:
        vendeur = produit.vendeur
        if vendeur.type_activite != TypeService.EXPRESS:
            gardes.append(produit)
            continue

        adresse = vendeur.adresse
        if lat is None or adresse is None:
            continue

        d = distance_km(lat, lon, adresse.latitude, adresse.longitude)
        if d is None or d > float(vendeur.rayon_livraison_km):
            continue

        distances[produit.id] = d
        gardes.append(produit)

    return gardes, distances


@api_view(["GET"])
@permission_classes([AllowAny])
def liste_produits(requete):
    """Le catalogue, avec ses facettes.

    Les compteurs de categories et de boutiques sont calcules **sur le
    resultat reellement filtre**, jamais sur la base entiere. Sinon on affiche
    « Plats 4 » a un visiteur parisien qui, lui, ne voit aucun plat : les
    boutiques Express lyonnaises sont hors de son rayon.
    """
    produits = _visibles()

    if service := requete.query_params.get("type_service"):
        produits = produits.filter(vendeur__type_activite=service)
    if recherche := requete.query_params.get("recherche"):
        produits = produits.filter(
            Q(nom__icontains=recherche) | Q(description__icontains=recherche)
        )
    if requete.query_params.get("disponible") == "1":
        produits = produits.filter(stock_disponible__gt=0)

    lat, lon = _position(requete)
    base, distances = _filtrer_par_rayon(list(produits[:400]), lat, lon)

    # Les facettes decrivent CE QUI RESTE apres le filtrage geographique et la
    # recherche, mais avant les filtres de categorie et de boutique — sinon
    # cliquer sur une categorie ferait disparaitre toutes les autres.
    facettes = _facettes(base)

    categorie = requete.query_params.get("categorie")
    boutique = requete.query_params.get("boutique")
    resultat = [
        produit for produit in base
        if (not categorie or (produit.categorie and produit.categorie.slug == categorie))
        and (not boutique or str(produit.vendeur_id) == str(boutique))
    ]

    serializer = ProduitListeSerializer(
        resultat, many=True, context={"request": requete, "distances": distances}
    )
    return Response({
        "data": serializer.data,
        "meta": {"total": len(resultat), "total_avant_filtres": len(base), "facettes": facettes},
    })


def _facettes(produits):
    """Compte par categorie et par boutique, groupe par univers.

    Le regroupement par univers repond a une remarque simple : sept categories
    a plat ne disent rien, alors que « Restauration » et « High-tech » se
    lisent d'un coup d'oeil.
    """
    par_categorie = {}
    par_boutique = {}

    for produit in produits:
        if produit.categorie:
            cle = produit.categorie.slug
            entree = par_categorie.setdefault(cle, {
                "slug": cle,
                "nom": produit.categorie.nom,
                "univers": (produit.categorie.parente.nom if produit.categorie.parente
                            else "Autres"),
                "nombre": 0,
            })
            entree["nombre"] += 1

        vendeur = produit.vendeur
        entree = par_boutique.setdefault(vendeur.id, {
            "id": vendeur.id,
            "nom": vendeur.nom_boutique,
            "type_service": vendeur.type_activite,
            "nombre": 0,
        })
        entree["nombre"] += 1

    univers = {}
    for categorie in par_categorie.values():
        univers.setdefault(categorie["univers"], []).append(categorie)

    return {
        "univers": [
            {
                "nom": nom,
                "nombre": sum(c["nombre"] for c in categories),
                "categories": sorted(categories, key=lambda c: -c["nombre"]),
            }
            for nom, categories in sorted(univers.items())
        ],
        "boutiques": sorted(par_boutique.values(), key=lambda b: -b["nombre"]),
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def detail_produit(requete, identifiant):
    try:
        produit = _visibles().prefetch_related("photos").get(pk=identifiant)
    except Produit.DoesNotExist:
        return Response(
            {"erreur": {"code": "introuvable", "message": "Ce produit n'existe pas ou n'est "
                                                          "plus au catalogue.", "details": {}}},
            status=status.HTTP_404_NOT_FOUND,
        )

    lat, lon = _position(requete)
    distances = {}
    if lat is not None and produit.vendeur.adresse:
        d = distance_km(lat, lon, produit.vendeur.adresse.latitude, produit.vendeur.adresse.longitude)
        if d is not None:
            distances[produit.id] = d

    return Response({"data": ProduitDetailSerializer(
        produit, context={"request": requete, "distances": distances}
    ).data})


@api_view(["GET"])
@permission_classes([AllowAny])
def liste_categories(requete):
    categories = Categorie.objects.annotate(
        nombre_produits=Count(
            "produits",
            filter=Q(produits__est_visible=True,
                     produits__vendeur__statut_validation=StatutValidation.VALIDE),
        )
    ).order_by("nom")
    return Response({"data": CategorieSerializer(categories, many=True).data})


@api_view(["GET"])
@permission_classes([AllowAny])
def liste_boutiques(requete):
    boutiques = (
        Vendeur.objects.select_related("adresse")
        .filter(statut_validation=StatutValidation.VALIDE)
        .annotate(nombre_produits=Count("produits", filter=Q(produits__est_visible=True)))
    )
    if service := requete.query_params.get("type_service"):
        boutiques = boutiques.filter(type_activite=service)

    lat, lon = _position(requete)
    gardes, distances = [], {}
    for boutique in boutiques:
        if boutique.type_activite == TypeService.EXPRESS:
            if lat is None or boutique.adresse is None:
                continue
            d = distance_km(lat, lon, boutique.adresse.latitude, boutique.adresse.longitude)
            if d is None or d > float(boutique.rayon_livraison_km):
                continue
            distances[boutique.id] = d
        gardes.append(boutique)

    return Response({"data": BoutiqueSerializer(
        gardes, many=True, context={"request": requete, "distances": distances}
    ).data})


@api_view(["GET", "POST"])
@permission_classes([EstVendeur])
def mes_produits(requete):
    """Le catalogue du vendeur : le sien, y compris ce qui est masque."""
    profil = getattr(requete.user, "profil_vendeur", None)
    if profil is None:
        return Response(
            {"erreur": {"code": "profil_absent", "message": "Aucune boutique rattachee.",
                        "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if requete.method == "POST":
        if profil.statut_validation != StatutValidation.VALIDE:
            return Response(
                {"erreur": {"code": "non_autorise",
                            "message": "Votre boutique doit etre validee avant de publier.",
                            "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ProduitEcritureSerializer(data=requete.data)
        serializer.is_valid(raise_exception=True)
        produit = serializer.save(vendeur=profil)
        return Response(
            {"data": ProduitDetailSerializer(produit, context={"request": requete}).data},
            status=status.HTTP_201_CREATED,
        )

    produits = Produit.objects.filter(vendeur=profil).select_related("vendeur", "categorie")
    return Response({"data": ProduitListeSerializer(
        produits, many=True, context={"request": requete}
    ).data})


@api_view(["PATCH", "DELETE"])
@permission_classes([EstVendeur])
def modifier_produit(requete, identifiant):
    profil = getattr(requete.user, "profil_vendeur", None)
    try:
        produit = Produit.objects.get(pk=identifiant, vendeur=profil)
    except Produit.DoesNotExist:
        # 404 et non 403 : repondre « interdit » revelerait qu'un produit
        # existe chez un autre vendeur.
        return Response(status=status.HTTP_404_NOT_FOUND)

    if requete.method == "DELETE":
        # Suppression logique (D-13) : le produit disparait du catalogue mais
        # les commandes passees continuent de le referencer.
        produit.est_visible = False
        produit.save(update_fields=["est_visible"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ProduitEcritureSerializer(produit, data=requete.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"data": ProduitDetailSerializer(
        produit, context={"request": requete}
    ).data})
