"""Les routes du cycle de litige — D-94."""
from django.urls import path

from . import vues_litiges

urlpatterns = [
    # Le client
    path("commandes/<int:identifiant>/litiges", vues_litiges.ouvrir, name="ouvrir-litige"),
    path("mes-litiges", vues_litiges.mes_litiges, name="mes-litiges"),

    # Le vendeur
    path("vendeurs/litiges", vues_litiges.litiges_du_vendeur, name="litiges-vendeur"),
    path("litiges/<int:identifiant>/reponse", vues_litiges.repondre, name="repondre-litige"),

    # L'administrateur
    path("admin/litiges/<int:identifiant>/arbitrer", vues_litiges.arbitrer,
         name="arbitrer-litige"),
]
