"""L'itineraire — les gardes du bloc N-5.

Ta demande : *« je veux une vraie API de carte sophistiquee. »* Elle existe, et
elle est facultative : sans cle, le calcul local prend le relais.

Ce qui est verifie ici :

  · **l'ordre des coordonnees.** GeoJSON attend [longitude, latitude] ;
    l'inverser est LA erreur classique des cartes, et elle ne se voit qu'a
    l'ecran, quand le trace part en Somalie ;
  · **le repli.** Aucune panne du fournisseur ne doit vider la carte ;
  · **l'honnetete du trace.** Un trajet estime ne se presente jamais comme un
    itineraire routier.

Aucun test ne touche le reseau (D-37).
"""
import io
import json
import urllib.error

import pytest
from rest_framework.test import APIClient

from coeur import services_carte
from coeur.services_carte import (
    FACTEUR_DETOUR,
    ItineraireParApi,
    ItineraireSimule,
    service_itineraire,
)
from comptes.models import Utilisateur

# Trois points reels de la demonstration, a Lyon.
BELLECOUR = (45.7578, 4.8320)
PART_DIEU = (45.7605, 4.8595)
VILLEURBANNE = (45.7719, 4.8902)


class FausseReponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def geojson(distance_metres, duree_secondes, trace):
    return FausseReponse(json.dumps({
        "features": [{
            "properties": {"summary": {"distance": distance_metres, "duration": duree_secondes}},
            "geometry": {"type": "LineString", "coordinates": trace},
        }],
    }).encode())


class TestLeCalculLocal:
    def test_deux_points_donnent_une_distance_et_une_duree(self):
        trajet = ItineraireSimule().calculer([BELLECOUR, PART_DIEU], "velo")

        assert trajet.distance_km > 0
        assert trajet.duree_minutes > 0
        assert trajet.simule is True

    def test_la_distance_majore_le_vol_d_oiseau(self):
        """Une rue ne va jamais tout droit : le detour urbain est integre."""
        from coeur.geographie import distance_km

        vol = distance_km(*BELLECOUR, *PART_DIEU)
        trajet = ItineraireSimule().calculer([BELLECOUR, PART_DIEU])

        assert trajet.distance_km == pytest.approx(vol * FACTEUR_DETOUR, rel=0.01)

    def test_le_velo_met_plus_longtemps_que_la_camionnette(self):
        velo = ItineraireSimule().calculer([BELLECOUR, VILLEURBANNE], "velo")
        voiture = ItineraireSimule().calculer([BELLECOUR, VILLEURBANNE], "voiture")

        assert velo.duree_minutes > voiture.duree_minutes
        assert velo.distance_km == voiture.distance_km

    def test_le_trace_est_en_longitude_latitude(self):
        """L'ordre de GeoJSON. L'inverser envoie le trace en Somalie."""
        trajet = ItineraireSimule().calculer([BELLECOUR, PART_DIEU])

        premier = trajet.trace[0]
        assert premier[0] == pytest.approx(BELLECOUR[1])  # longitude
        assert premier[1] == pytest.approx(BELLECOUR[0])  # latitude

    def test_un_seul_point_ne_fait_pas_un_trajet(self):
        trajet = ItineraireSimule().calculer([BELLECOUR])

        assert trajet.distance_km == 0
        assert trajet.trace == []

    def test_une_tournee_additionne_ses_segments(self):
        court = ItineraireSimule().calculer([BELLECOUR, PART_DIEU])
        long = ItineraireSimule().calculer([BELLECOUR, PART_DIEU, VILLEURBANNE])

        assert long.distance_km > court.distance_km


class TestLaFabrique:
    def test_sans_cle_c_est_le_calcul_local(self, monkeypatch):
        monkeypatch.delenv("CLE_ITINERAIRE", raising=False)
        assert isinstance(service_itineraire(), ItineraireSimule)

    def test_avec_cle_c_est_le_fournisseur(self, monkeypatch):
        monkeypatch.setenv("CLE_ITINERAIRE", "peu-importe")
        assert isinstance(service_itineraire(), ItineraireParApi)

    def test_une_cle_vide_ne_compte_pas(self, monkeypatch):
        monkeypatch.setenv("CLE_ITINERAIRE", "  ")
        assert isinstance(service_itineraire(), ItineraireSimule)


class TestLeFournisseur:
    @pytest.fixture
    def appel(self, monkeypatch):
        vus = []

        def faux_urlopen(requete, timeout=None):
            vus.append({
                "url": requete.full_url,
                "entetes": {c.lower(): v for c, v in requete.header_items()},
                "corps": json.loads(requete.data),
            })
            return geojson(3420.0, 780.0, [[4.832, 45.7578], [4.845, 45.759], [4.8595, 45.7605]])

        monkeypatch.setattr(services_carte, "urlopen", faux_urlopen)
        return vus

    def test_le_profil_velo_est_traduit(self, appel):
        ItineraireParApi("cle").calculer([BELLECOUR, PART_DIEU], "velo")

        assert "cycling-regular" in appel[0]["url"]

    def test_les_coordonnees_partent_en_longitude_latitude(self, appel):
        """Le fournisseur attend GeoJSON. Notre code parle latitude d'abord."""
        ItineraireParApi("cle").calculer([BELLECOUR, PART_DIEU], "voiture")

        envoyees = appel[0]["corps"]["coordinates"]
        assert envoyees[0] == [pytest.approx(BELLECOUR[1]), pytest.approx(BELLECOUR[0])]

    def test_la_cle_part_en_entete(self, appel):
        ItineraireParApi("cle-secrete").calculer([BELLECOUR, PART_DIEU])

        assert appel[0]["entetes"]["authorization"] == "cle-secrete"
        assert "cle-secrete" not in appel[0]["url"]

    def test_la_reponse_est_traduite_en_km_et_minutes(self, appel):
        trajet = ItineraireParApi("cle").calculer([BELLECOUR, PART_DIEU])

        assert trajet.distance_km == 3.42
        assert trajet.duree_minutes == 13
        assert trajet.simule is False
        assert len(trajet.trace) == 3

    @pytest.mark.parametrize("souci", [
        urllib.error.HTTPError("u", 403, "Forbidden", {}, None),
        urllib.error.HTTPError("u", 429, "Too Many Requests", {}, None),
        urllib.error.URLError("reseau coupe"),
        TimeoutError("trop lent"),
    ])
    def test_toute_panne_retombe_sur_le_calcul_local(self, monkeypatch, souci):
        def tombe(requete, timeout=None):
            raise souci

        monkeypatch.setattr(services_carte, "urlopen", tombe)
        trajet = ItineraireParApi("cle").calculer([BELLECOUR, PART_DIEU], "velo")

        assert trajet.simule is True
        assert trajet.distance_km > 0

    def test_une_charge_utile_inattendue_retombe_aussi(self, monkeypatch):
        monkeypatch.setattr(
            services_carte, "urlopen",
            lambda requete, timeout=None: FausseReponse(b'{"error": "quota"}'),
        )
        assert ItineraireParApi("cle").calculer([BELLECOUR, PART_DIEU]).simule is True


@pytest.mark.django_db
class TestLaRoute:
    @pytest.fixture
    def client_connecte(self):
        utilisateur = Utilisateur.objects.create_user(
            email="carte@exemple.fr", password="Demonstration!2026",
            nom="Carte", prenom="Test", role="CLIENT", statut_compte="ACTIF",
        )
        client = APIClient()
        client.force_authenticate(user=utilisateur)
        return client

    def test_un_visiteur_n_a_pas_acces(self):
        """Une route d'itineraire ouverte est un quota ouvert."""
        reponse = APIClient().post("/api/v1/itineraire", {"points": []}, format="json")

        assert reponse.status_code in (401, 403)

    def test_moins_de_deux_points_est_refuse_avec_un_message(self, client_connecte):
        reponse = client_connecte.post(
            "/api/v1/itineraire",
            {"points": [{"lat": 45.75, "lon": 4.83}]}, format="json",
        )

        assert reponse.status_code == 400
        assert reponse.json()["erreur"]["code"] == "points_insuffisants"

    def test_des_points_mal_formes_sont_ignores_sans_planter(self, client_connecte):
        reponse = client_connecte.post("/api/v1/itineraire", {"points": [
            {"lat": 45.7578, "lon": 4.8320},
            {"lat": "au nord", "lon": None},
            "pas un objet",
            {"lat": 45.7605, "lon": 4.8595},
        ]}, format="json")

        assert reponse.status_code == 200
        assert reponse.json()["data"]["distance_km"] > 0

    def test_le_trajet_dit_s_il_est_estime(self, client_connecte, monkeypatch):
        monkeypatch.delenv("CLE_ITINERAIRE", raising=False)
        reponse = client_connecte.post("/api/v1/itineraire", {
            "points": [{"lat": 45.7578, "lon": 4.8320}, {"lat": 45.7605, "lon": 4.8595}],
            "profil": "velo",
        }, format="json")

        donnees = reponse.json()["data"]
        assert donnees["simule"] is True
        assert donnees["fournisseur"] == "simulateur"
        assert donnees["duree_minutes"] > 0

    def test_une_tournee_trop_longue_est_tronquee_pas_refusee(self, client_connecte):
        """Un ecran ne doit pas casser parce qu'une tournee est inhabituelle."""
        points = [{"lat": 45.75 + rang / 1000, "lon": 4.83} for rang in range(60)]
        reponse = client_connecte.post(
            "/api/v1/itineraire", {"points": points}, format="json",
        )

        assert reponse.status_code == 200
        assert len(reponse.json()["data"]["trace"]) == 25
