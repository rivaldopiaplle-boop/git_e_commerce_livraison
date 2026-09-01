from django.urls import path

from . import views, vues_assistant

urlpatterns = [
    path("sante", views.sante, name="sante"),

    # L'assistant et les recommandations (D-43), servis par le simulateur
    # tant qu'aucune cle de modele n'existe (D-18).
    path("assistant", vues_assistant.demander, name="assistant"),
    path("recommandations", vues_assistant.recommandations, name="recommandations"),
    path("services", vues_assistant.etat_services, name="etat-services"),
]
