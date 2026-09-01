from django.urls import path

from . import views

urlpatterns = [
    # Le paiement, servi par le simulateur tant qu'aucune cle Stripe n'existe.
    path("commandes/<int:identifiant>/paiement", views.ouvrir_intention,
         name="ouvrir-intention"),
    path("commandes/<int:identifiant>/paiement/abandonner", views.abandonner,
         name="abandonner-paiement"),
    path("commandes/<int:identifiant>/facture", views.ma_facture, name="ma-facture"),

    # La confirmation vient du SERVEUR, jamais du navigateur (D-12). En
    # production, c'est Stripe qui appelle ce chemin.
    path("paiements/confirmation", views.confirmer, name="confirmer-paiement"),
]
