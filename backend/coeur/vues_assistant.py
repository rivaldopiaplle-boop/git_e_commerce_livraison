"""L'assistant et les recommandations, servis par l'interface de D-18.

Aucune cle n'est necessaire : le simulateur repond a partir de ce que la base
sait deja. Le jour ou une cle de modele arrive, `CLE_MODELE_IA` la designe et
ces vues ne changent pas d'une ligne.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .services_externes import assistant


@api_view(["POST"])
@permission_classes([AllowAny])
def demander(requete):
    """Poser une question a l'assistant.

    Ouvert aux visiteurs : les questions les plus frequentes — delais,
    ruptures, comment ca marche — arrivent AVANT la creation du compte.
    Exiger un compte pour y repondre reviendrait a refuser d'aider quelqu'un
    qui hesite a acheter.
    """
    question = str(requete.data.get("question", "")).strip()
    if not question:
        return Response({"data": {"texte": "Posez votre question.", "sources": [],
                                  "simule": True}})

    # Le contexte donne a l'assistant de quoi etre precis quand il le peut :
    # qui demande, et depuis quel ecran.
    contexte = {
        "role": getattr(requete.user, "role", None) if requete.user.is_authenticated else None,
        "ecran": requete.data.get("ecran"),
    }

    reponse = assistant().repondre(question, contexte)
    return Response({"data": {
        "texte": reponse.texte,
        "sources": reponse.sources,
        "simule": reponse.simule,
    }})


@api_view(["GET"])
@permission_classes([AllowAny])
def recommandations(requete):
    """« Ceux qui ont regarde ceci ont aussi regarde. »

    Sans historique — un visiteur qui arrive — on rend les meilleures ventes
    plutot que rien, et on le DIT : appeler « recommande pour vous » ce qui
    est en realite « ce qui se vend le plus » est un petit mensonge que les
    gens reperent.
    """
    from catalogue.serializers import ProduitListeSerializer
    from catalogue.views import _visibles

    vus = [
        int(valeur) for valeur in str(requete.query_params.get("vus", "")).split(",")
        if valeur.strip().isdigit()
    ][:10]

    catalogue_visible = list(
        _visibles().select_related("categorie", "vendeur")[:120]
    )
    en_dictionnaires = [
        {"id": produit.id, "categorie": produit.categorie_id} for produit in catalogue_visible
    ]
    produits_vus = [entree for entree in en_dictionnaires if entree["id"] in vus]

    choisis = assistant().recommander(produits_vus, en_dictionnaires, combien=6)
    identifiants = [entree["id"] for entree in choisis]
    par_identifiant = {produit.id: produit for produit in catalogue_visible}
    retenus = [par_identifiant[i] for i in identifiants if i in par_identifiant]

    return Response({"data": {
        # Le titre change avec la situation : c'est ce qui rend la section
        # honnete plutot que decorative.
        "titre": "Parce que vous avez regardé" if produits_vus else "Les plus demandés",
        "produits": ProduitListeSerializer(
            retenus, many=True, context={"request": requete}
        ).data,
        "personnalise": bool(produits_vus),
    }})


@api_view(["GET"])
@permission_classes([AllowAny])
def etat_services(requete):
    """Quels services externes tournent en vrai, et lesquels sont simules.

    Utile en entretien : la question « et le paiement, il marche vraiment ? »
    merite une reponse honnete affichable a l'ecran, pas une explication
    embarrassee.
    """
    from .services_carte import service_itineraire
    from .services_externes import fournisseur_de_paiement

    return Response({"data": {
        "paiement": fournisseur_de_paiement().nom,
        "assistant": assistant().nom,
        "itineraire": service_itineraire().nom,
        "explication": (
            "Les services payants sont derriere une interface, avec un simulateur "
            "(D-18) : le projet se demontre entierement sans cle, et le jour ou une "
            "cle arrive, un seul fichier change."
        ),
    }})
