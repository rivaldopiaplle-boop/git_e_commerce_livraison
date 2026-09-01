"""Les chemins suivent 03-contrats/contrat-api.md, au caractere pres.

Un contrat qui n'est pas respecte par le code n'est plus un contrat.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views, vues_espaces, vues_gestion, vues_profil

urlpatterns = [
    path("auth/inscription/client", views.inscription_client, name="inscription-client"),
    path("auth/inscription/vendeur", views.inscription_vendeur, name="inscription-vendeur"),
    path("auth/inscription/livreur", views.inscription_livreur, name="inscription-livreur"),
    path("auth/connexion", views.connexion, name="connexion"),
    path("auth/rafraichir", TokenRefreshView.as_view(), name="rafraichir"),

    path("moi", views.moi, name="moi"),

    path("vendeurs/gestionnaires", views.creer_gestionnaire, name="creer-gestionnaire"),

    path("admin/tableau-de-bord", views.tableau_de_bord_admin, name="tableau-de-bord-admin"),
    path("moi/tableau-de-bord", views.tableau_de_bord_client, name="tableau-client"),
    path("admin/validations", views.validations_en_attente, name="validations"),
    path("admin/vendeurs/<int:identifiant>/valider", views.valider_vendeur, name="valider-vendeur"),
    path("admin/vendeurs/<int:identifiant>/rejeter", views.rejeter_vendeur, name="rejeter-vendeur"),
    path("admin/livreurs/<int:identifiant>/valider", views.valider_livreur, name="valider-livreur"),
]

# ── Les ecrans que la maquette prevoit, servis par vues_espaces.py ──────
urlpatterns += [
    # Client
    path("moi/adresses", vues_espaces.mes_adresses, name="mes-adresses"),
    path("moi/adresses/<int:identifiant>", vues_espaces.modifier_adresse, name="modifier-adresse"),
    path("moi/notifications", vues_espaces.mes_notifications, name="mes-notifications"),
    path("moi/notifications/lues", vues_espaces.marquer_notifications_lues, name="notifs-lues"),

    # Vendeur
    path("vendeurs/personnel", vues_espaces.mon_personnel, name="mon-personnel"),
    # Le vendeur creait des comptes sans jamais pouvoir en retirer un :
    # un employe qui partait gardait son acces indefiniment.
    path("vendeurs/personnel/<int:identifiant>/basculer",
         vues_gestion.basculer_employe, name="basculer-employe"),
    path("vendeurs/statistiques", vues_espaces.statistiques_vendeur, name="statistiques-vendeur"),
    path("vendeurs/avis", vues_espaces.avis_recus, name="avis-recus"),

    # Admin
    path("admin/utilisateurs", vues_espaces.utilisateurs, name="admin-utilisateurs"),
    path("admin/utilisateurs/<int:identifiant>/suspendre", vues_espaces.suspendre,
         name="admin-suspendre"),
    path("admin/boutiques", vues_espaces.boutiques_admin, name="admin-boutiques"),
    path("admin/livreurs", vues_espaces.livreurs_admin, name="admin-livreurs"),
    path("admin/litiges", vues_espaces.litiges, name="admin-litiges"),
    path("admin/journal", vues_espaces.journal_audit, name="admin-journal"),
    path("admin/validations/resume", vues_espaces.resume_validations, name="admin-resume"),
]

# -- Profil et parametres (D-76, D-77) -----------------------------------
urlpatterns += [
    path("moi/profil", vues_profil.mon_profil, name="mon-profil"),
    path("moi/demandes-modification", vues_profil.demander_modification,
         name="demander-modification"),
    path("moi/mot-de-passe", vues_profil.changer_mot_de_passe, name="changer-mot-de-passe"),
    path("moi/parametres", vues_profil.mes_parametres, name="mes-parametres"),

    path("admin/demandes-modification", vues_profil.demandes_a_arbitrer,
         name="demandes-a-arbitrer"),
    path("admin/demandes-modification/<int:identifiant>", vues_profil.arbitrer_demande,
         name="arbitrer-demande"),
]

# -- La gestion, cote administration (D-93) ------------------------------
urlpatterns += [
    path("admin/vendeurs/<int:identifiant>/decision", vues_gestion.decider_vendeur,
         name="decider-vendeur"),
    path("admin/livreurs/<int:identifiant>/decision", vues_gestion.decider_livreur,
         name="decider-livreur"),
    path("admin/comptes/<int:identifiant>/basculer", vues_gestion.basculer_compte,
         name="basculer-compte"),
]
