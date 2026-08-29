from django.urls import path

from . import views

urlpatterns = [
    path("produits", views.liste_produits, name="liste-produits"),
    path("produits/<int:identifiant>", views.detail_produit, name="detail-produit"),
    path("categories", views.liste_categories, name="liste-categories"),
    path("boutiques", views.liste_boutiques, name="liste-boutiques"),

    path("vendeurs/produits", views.mes_produits, name="mes-produits"),
    path("vendeurs/produits/<int:identifiant>", views.modifier_produit, name="modifier-produit"),
]
