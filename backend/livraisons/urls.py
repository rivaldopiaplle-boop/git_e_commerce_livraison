from django.urls import path

from . import views, vues_entrepot, vues_livreur

urlpatterns = [
    # Entrepot — gestionnaire staff entrepot
    path("entrepots/colis", views.colis_recus, name="colis-recus"),
    path("entrepots/tournees", views.tournees_entrepot, name="tournees-entrepot"),
    path("entrepots/tableau-de-bord", views.tableau_de_bord_entrepot, name="tableau-entrepot"),

    # Ce que le gestionnaire d'entrepot FAIT (O-5). Il ne faisait que
    # consulter : les tournees venaient toutes du jeu de demonstration.
    path("entrepots/colis/<int:identifiant>/reception", vues_entrepot.confirmer_reception,
         name="confirmer-reception"),
    path("entrepots/tournees/calculer", vues_entrepot.calculer_tournee,
         name="calculer-tournee"),
    path("entrepots/tournees/<int:identifiant>/livreur", vues_entrepot.attribuer_tournee,
         name="attribuer-tournee"),
    path("entrepots/tournees/<int:identifiant>/depart", vues_entrepot.faire_partir,
         name="faire-partir-tournee"),
    path("entrepots/livreurs", vues_entrepot.livreurs_disponibles,
         name="livreurs-pour-tournee"),

    # Livreur — lecture seule au web, l'action se fait sur le mobile (D-40)
    path("livreurs/mes-courses", views.mes_courses, name="mes-courses"),
    path("livreurs/tableau-de-bord", views.tableau_de_bord_livreur, name="tableau-livreur"),

    # Ce que le livreur FAIT, et qui n'existe que sur mobile (D-40) : accepter
    # une course, confirmer une remise, signaler une absence.
    path("livreurs/disponibilite", vues_livreur.changer_disponibilite,
         name="changer-disponibilite"),
    path("livreurs/position", vues_livreur.signaler_position, name="signaler-position"),
    path("livreurs/disponibles", vues_livreur.livraisons_disponibles,
         name="livraisons-disponibles"),
    path("livreurs/livraisons/<int:identifiant>/accepter", vues_livreur.accepter_livraison,
         name="accepter-livraison"),
    path("livreurs/livraisons/<int:identifiant>/recuperer", vues_livreur.recuperer_colis,
         name="recuperer-colis"),
    path("livreurs/livraisons/<int:identifiant>/livrer", vues_livreur.confirmer_livraison,
         name="confirmer-livraison"),
    path("livreurs/livraisons/<int:identifiant>/absence", vues_livreur.signaler_absence,
         name="signaler-absence"),
]
