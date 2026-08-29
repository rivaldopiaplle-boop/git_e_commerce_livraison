from django.urls import path

from . import views

urlpatterns = [
    path("panier", views.voir_panier, name="voir-panier"),
    path("panier/lignes", views.ajouter_ligne, name="ajouter-ligne"),
    path("panier/lignes/<int:identifiant>", views.modifier_ligne, name="modifier-ligne"),
]
