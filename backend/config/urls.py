from django.contrib import admin
from django.urls import include, path

# Toute l'API est versionnee des le depart : le jour ou une charge utile doit
# changer sans casser une application mobile deja installee, /api/v2 cohabite
# avec /api/v1 au lieu de la remplacer.
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("coeur.urls")),
]
