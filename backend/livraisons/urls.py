from django.urls import path

from . import views

urlpatterns = [
    # Entrepot — gestionnaire staff entrepot
    path("entrepots/colis", views.colis_recus, name="colis-recus"),
    path("entrepots/tournees", views.tournees_entrepot, name="tournees-entrepot"),
    path("entrepots/tableau-de-bord", views.tableau_de_bord_entrepot, name="tableau-entrepot"),

    # Livreur — lecture seule au web, l'action se fait sur le mobile (D-40)
    path("livreurs/mes-courses", views.mes_courses, name="mes-courses"),
    path("livreurs/tableau-de-bord", views.tableau_de_bord_livreur, name="tableau-livreur"),
]
