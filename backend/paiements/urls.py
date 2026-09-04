from django.urls import path

from . import views, vues_cartes

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

    # Le carnet de cartes (O-5). Le numero complet ne touche jamais la base :
    # un jeton le remplace, comme chez tous les fournisseurs de paiement.
    path("moi/cartes", vues_cartes.mes_cartes, name="mes-cartes"),
    path("moi/cartes/<int:identifiant>", vues_cartes.retirer_carte, name="retirer-carte"),

    # Ou va l'argent d'une commande : les vendeurs, le livreur, la plateforme.
    path("commandes/<int:identifiant>/repartition", vues_cartes.repartition,
         name="repartition-commande"),
    path("admin/repartitions", vues_cartes.repartitions_a_verser,
         name="admin-repartitions"),
]
