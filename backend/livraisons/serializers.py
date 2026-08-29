"""Ce que les ecrans de logistique lisent : colis, tournees, courses."""
from rest_framework import serializers

from .models import ArretTournee, Livraison, Tournee


def _adresse(adresse):
    if adresse is None:
        return None
    return {
        "id": adresse.id,
        "libelle": adresse.libelle,
        "rue": adresse.rue,
        "code_postal": adresse.code_postal,
        "ville": adresse.ville,
        "instructions": adresse.instructions_livraison,
    }


class LivraisonSerializer(serializers.ModelSerializer):
    """Une livraison telle qu'un livreur ou un gestionnaire la lit.

    Le nom du client et la remuneration sont recopies ici plutot que laisses
    a l'ecran : un livreur qui doit croiser trois appels pour savoir chez qui
    il va et ce que la course lui rapporte n'ouvrira pas l'application deux
    fois (D-29).
    """

    numero_commande = serializers.CharField(source="commande.numero_commande", read_only=True)
    type_service = serializers.CharField(source="commande.type_service", read_only=True)
    statut_commande = serializers.CharField(source="commande.statut_actuel", read_only=True)
    libelle_statut = serializers.CharField(source="get_statut_livraison_display", read_only=True)
    client = serializers.SerializerMethodField()
    adresse = serializers.SerializerMethodField()
    boutiques = serializers.SerializerMethodField()
    nombre_tentatives = serializers.SerializerMethodField()

    class Meta:
        model = Livraison
        fields = [
            "id", "numero_commande", "type_service", "statut_livraison", "libelle_statut",
            "statut_commande", "client", "adresse", "boutiques", "distance_km",
            "remuneration_livreur_centimes", "code_confirmation", "date_estimee",
            "date_reelle", "nombre_tentatives",
        ]

    def get_client(self, livraison):
        utilisateur = livraison.commande.client.utilisateur
        return f"{utilisateur.prenom} {utilisateur.nom}".strip()

    def get_adresse(self, livraison):
        return _adresse(livraison.adresse_livraison)

    def get_boutiques(self, livraison):
        return [
            sous_commande.vendeur.nom_boutique
            for sous_commande in livraison.commande.sous_commandes.all()
        ]

    def get_nombre_tentatives(self, livraison):
        return livraison.tentatives.count()


class ArretSerializer(serializers.ModelSerializer):
    livraison = LivraisonSerializer(read_only=True)
    libelle_statut = serializers.CharField(source="get_statut_display", read_only=True)

    class Meta:
        model = ArretTournee
        fields = ["id", "ordre", "statut", "libelle_statut", "heure_estimee", "livraison"]


class TourneeSerializer(serializers.ModelSerializer):
    arrets = ArretSerializer(many=True, read_only=True)
    libelle_statut = serializers.CharField(source="get_statut_display", read_only=True)
    entrepot = serializers.CharField(source="entrepot.nom", read_only=True)
    zone = serializers.SerializerMethodField()
    livreur = serializers.SerializerMethodField()

    class Meta:
        model = Tournee
        fields = [
            "id", "entrepot", "zone", "livreur", "statut", "libelle_statut",
            "nombre_arrets", "distance_totale_km", "date_creation", "date_debut",
            "date_fin", "arrets",
        ]

    def get_zone(self, tournee):
        return tournee.zone.nom if tournee.zone_id else None

    def get_livreur(self, tournee):
        if not tournee.livreur_id:
            return None
        utilisateur = tournee.livreur.utilisateur
        return {
            "id": tournee.livreur_id,
            "nom": f"{utilisateur.prenom} {utilisateur.nom}".strip(),
            "vehicule": tournee.livreur.get_vehicule_display(),
        }
