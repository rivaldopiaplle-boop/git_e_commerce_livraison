"""L'assistant par API — les gardes du bloc N-4.

Tu proposes ta cle Mistral. `AssistantParApi` levait `NotImplementedError` :
il fallait donc l'ecrire avant que ta cle serve a quelque chose.

Ce qui est verifie ici tient en une phrase : **l'assistant ne doit jamais
laisser un visiteur sans reponse, ni inventer un delai de livraison.** Aucun
test ne touche le reseau (D-37) — la fenetre d'appel est remplacee.
"""
import io
import json
import urllib.error

import pytest

from coeur import services_externes
from coeur.services_externes import AssistantParApi, AssistantSimule, assistant


class FausseReponse(io.BytesIO):
    """Ce que `urlopen` rend : un objet qu'on lit et qui se ferme."""

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def reponse_de(texte):
    return FausseReponse(
        json.dumps({"choices": [{"message": {"content": texte}}]}).encode()
    )


@pytest.fixture
def modele(monkeypatch):
    """L'assistant par API, avec un reseau sous controle."""
    appels = []

    def faux_urlopen(requete, timeout=None):
        appels.append({
            "url": requete.full_url,
            "entetes": {cle.lower(): valeur for cle, valeur in requete.header_items()},
            "corps": json.loads(requete.data),
            "delai": timeout,
        })
        return reponse_de("Votre commande Express arrive en moins de quarante minutes.")

    monkeypatch.setattr(services_externes, "urlopen", faux_urlopen)
    return AssistantParApi("cle-de-test"), appels


class TestLaFabrique:
    def test_sans_cle_c_est_le_simulateur(self, monkeypatch):
        monkeypatch.delenv("CLE_MODELE_IA", raising=False)
        assert isinstance(assistant(), AssistantSimule)

    def test_avec_cle_c_est_le_modele(self, monkeypatch):
        monkeypatch.setenv("CLE_MODELE_IA", "peu-importe")
        choisi = assistant()
        assert isinstance(choisi, AssistantParApi)
        assert choisi.nom == "mistral"

    def test_une_cle_vide_ne_compte_pas(self, monkeypatch):
        """Une variable posee mais laissee vide est le cas le plus courant."""
        monkeypatch.setenv("CLE_MODELE_IA", "   ")
        assert isinstance(assistant(), AssistantSimule)


class TestLAppel:
    def test_la_cle_part_en_entete_pas_dans_l_adresse(self, modele):
        """Une cle dans l'URL finit dans les journaux du fournisseur."""
        assistant_api, appels = modele
        assistant_api.repondre("Quand arrive ma commande ?")

        appel = appels[0]
        assert appel["entetes"]["authorization"] == "Bearer cle-de-test"
        assert "cle-de-test" not in appel["url"]

    def test_le_modele_ne_recoit_que_la_base_de_connaissances(self, modele):
        """Il n'a acces ni a la base, ni aux commandes de qui que ce soit."""
        assistant_api, appels = modele
        assistant_api.repondre("Quand arrive ma commande ?", {"role": "CLIENT"})

        consigne = appels[0]["corps"]["messages"][0]["content"]
        for _, connaissance in AssistantSimule.CONNAISSANCES:
            assert connaissance in consigne
        assert "CLIENT" in consigne

    def test_la_consigne_interdit_d_inventer(self, modele):
        """Le risque numero un d'un modele branche sur un catalogue."""
        assistant_api, appels = modele
        assistant_api.repondre("Ma commande arrive quand exactement ?")

        consigne = appels[0]["corps"]["messages"][0]["content"].lower()
        assert "n'invente" in consigne
        assert "delai" in consigne

    def test_la_reponse_est_bornee_et_peu_creative(self, modele):
        assistant_api, appels = modele
        assistant_api.repondre("Bonjour")

        corps = appels[0]["corps"]
        assert corps["temperature"] <= 0.3
        assert corps["max_tokens"] <= 400
        assert appels[0]["delai"] <= 10

    def test_la_reponse_se_presente_comme_une_reponse_de_machine(self, modele):
        assistant_api, _ = modele
        reponse = assistant_api.repondre("Quand arrive ma commande ?")

        assert reponse.simule is False
        assert reponse.sources == ["modele mistral-small-latest"]
        assert "quarante minutes" in reponse.texte


class TestLeRepli:
    """Aucune panne ne doit rendre l'assistant muet."""

    @pytest.mark.parametrize("souci", [
        urllib.error.HTTPError("u", 401, "Unauthorized", {}, None),
        urllib.error.HTTPError("u", 429, "Too Many Requests", {}, None),
        urllib.error.URLError("reseau coupe"),
        TimeoutError("trop lent"),
    ])
    def test_toute_panne_retombe_sur_le_simulateur(self, monkeypatch, souci):
        def tombe(requete, timeout=None):
            raise souci

        monkeypatch.setattr(services_externes, "urlopen", tombe)
        reponse = AssistantParApi("cle").repondre("Quand arrive ma commande ?")

        assert reponse.simule is True
        assert "suivi de votre commande" in reponse.texte.lower()

    def test_une_reponse_vide_retombe_aussi(self, monkeypatch):
        """Un modele peut rendre 200 avec un contenu vide. Ce n'est pas une reponse."""
        monkeypatch.setattr(services_externes, "urlopen",
                            lambda requete, timeout=None: reponse_de("   "))
        reponse = AssistantParApi("cle").repondre("Quand arrive ma commande ?")

        assert reponse.simule is True
        assert reponse.texte

    def test_une_charge_utile_inattendue_retombe_aussi(self, monkeypatch):
        """Un format qui change ne doit pas remonter une trace a l'ecran."""
        monkeypatch.setattr(
            services_externes, "urlopen",
            lambda requete, timeout=None: FausseReponse(b'{"erreur": "quota"}'),
        )
        assert AssistantParApi("cle").repondre("Bonjour").simule is True


class TestLesRecommandations:
    def test_le_modele_ne_recommande_pas(self, monkeypatch):
        """Une recommandation est une requete, pas un travail de modele.

        Si l'appel reseau etait tente ici, ce test echouerait : `urlopen` est
        remplace par une fonction qui refuse.
        """
        def interdit(*_, **__):
            raise AssertionError("Le modele a ete appele pour recommander.")

        monkeypatch.setattr(services_externes, "urlopen", interdit)
        catalogue = [{"id": rang, "categorie": rang % 3} for rang in range(1, 13)]
        choisis = AssistantParApi("cle").recommander([catalogue[0]], catalogue, combien=4)

        # Le produit deja vu ne se recommande pas a lui-meme, et les proposes
        # partagent sa categorie : c'est le comportement du simulateur, donc
        # c'est bien lui qui a repondu.
        assert choisis
        assert all(produit["id"] != 1 for produit in choisis)
        assert {produit["categorie"] for produit in choisis} == {catalogue[0]["categorie"]}
