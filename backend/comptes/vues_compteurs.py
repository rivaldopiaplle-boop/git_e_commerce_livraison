"""Ce qui attend la personne connectee, entree de menu par entree de menu.

**Ta remarque, L-3** : la barre laterale et la barre haute ne disent rien. Elle
listait des noms d'ecrans, et rien de plus : il fallait ouvrir chacun pour
decouvrir qu'il y avait trois commandes a preparer et deux litiges en
souffrance.

Un seul appel, et il rend un dictionnaire **indexe par nom de route**. C'est
ce qui permet a la barre laterale de rester bete : elle affiche
`compteurs[entree.route]` sans rien savoir des metiers. Un ecran de plus dans
le menu ne demande rien ici tant qu'il n'a rien a compter.

Trois choix qui evitent des ennuis :

  · **un seul appel, pas un par entree.** Neuf requetes au chargement de
    chaque page pour afficher neuf pastilles serait absurde ;
  · **seulement ce qui APPELLE UNE ACTION.** « 137 produits au catalogue »
    n'est pas une pastille, c'est une statistique : une pastille qui ne
    descend jamais a zero cesse d'etre lue au bout de deux jours ;
  · **rien pour un visiteur.** Il n'a rien en attente, et l'appel n'est meme
    pas tente.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Role, StatutValidation


def _pour_client(profil):
    from commandes.models import Commande, StatutCommande

    return {
        # Une commande creee et jamais payee immobilise du stock (D-15) : c'est
        # la pastille la plus utile de tout le projet.
        "mes-commandes": Commande.objects.filter(
            client=profil, statut_actuel=StatutCommande.EN_ATTENTE_PAIEMENT
        ).count(),
        "paiement": Commande.objects.filter(
            client=profil, statut_actuel=StatutCommande.EN_ATTENTE_PAIEMENT
        ).count(),
    }


def _pour_vendeur(vendeur):
    from django.db.models import F

    from catalogue.models import Produit
    from commandes.models import SousCommande, StatutPreparation
    from engagement.models import Litige, StatutLitige

    return {
        "vendeur-commandes": SousCommande.objects.filter(
            vendeur=vendeur, statut_preparation=StatutPreparation.A_PREPARER
        ).count(),
        # Ce qui est sous le seuil d'alerte ou en rupture : le vendeur doit
        # reapprovisionner avant de perdre une vente.
        "vendeur-catalogue": Produit.objects.filter(
            vendeur=vendeur, est_visible=True, stock_disponible__lte=F("seuil_alerte")
        ).count(),
        "vendeur-litiges": Litige.objects.filter(
            commande__sous_commandes__vendeur=vendeur,
            statut__in=[StatutLitige.OUVERT, StatutLitige.EN_COURS],
            date_reponse_vendeur__isnull=True,
        ).distinct().count(),
    }


def _pour_entrepot(entrepot):
    from commandes.models import SousCommande, StatutCommande
    from livraisons.models import StatutTournee, Tournee

    return {
        "entrepot-colis": SousCommande.objects.filter(
            entrepot=entrepot, commande__statut_actuel=StatutCommande.RECUE_ENTREPOT
        ).count(),
        # Une tournee prete sans livreur, c'est une livraison qui n'avance pas
        # et que personne ne voit (scenario 9.2).
        "entrepot-tournees": Tournee.objects.filter(
            entrepot=entrepot, statut=StatutTournee.PRETE, livreur__isnull=True
        ).count(),
    }


def _pour_livreur(livreur):
    from livraisons.models import Livraison, StatutLivraison

    return {
        "livreur-courses": Livraison.objects.filter(
            livreur=livreur,
            statut_livraison__in=[
                StatutLivraison.ATTRIBUEE,
                StatutLivraison.RECUPEREE,
                StatutLivraison.EN_ROUTE,
            ],
        ).count(),
    }


def _pour_admin():
    from comptes.models import Livreur, Vendeur
    from engagement.models import Litige, StatutLitige

    from .models import DemandeModification, StatutDemande

    en_attente = StatutValidation.EN_ATTENTE
    return {
        "admin-validations": (
            Vendeur.objects.filter(statut_validation=en_attente).count()
            + Livreur.objects.filter(statut_validation=en_attente).count()
        ),
        # Seuls les litiges REELLEMENT arbitrables : ceux dont le vendeur a
        # parle, ou dont le delai est passe. Compter les autres afficherait un
        # travail que l'administrateur n'a pas le droit de faire (D-103).
        "admin-litiges": sum(
            1
            for dossier in Litige.objects.filter(
                statut__in=[StatutLitige.OUVERT, StatutLitige.EN_COURS]
            )
            if dossier.arbitrable
        ),
        "admin-demandes": DemandeModification.objects.filter(
            statut=StatutDemande.EN_ATTENTE
        ).count(),
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mes_compteurs(requete):
    """Les pastilles de la barre laterale, en un appel."""
    utilisateur = requete.user
    compteurs = {}

    if profil := getattr(utilisateur, "profil_client", None):
        compteurs.update(_pour_client(profil))

    if vendeur := getattr(utilisateur, "profil_vendeur", None):
        compteurs.update(_pour_vendeur(vendeur))

    if gestionnaire := getattr(utilisateur, "profil_gestionnaire", None):
        # Le personnel voit ce qui le concerne, jamais l'argent (D-04). Les
        # commandes a preparer, oui ; les litiges, non — ils se repondent par
        # le proprietaire de la boutique.
        if gestionnaire.vendeur_id:
            metiers = _pour_vendeur(gestionnaire.vendeur)
            metiers.pop("vendeur-litiges", None)
            compteurs.update(metiers)
        if gestionnaire.entrepot_id:
            compteurs.update(_pour_entrepot(gestionnaire.entrepot))

    if livreur := getattr(utilisateur, "profil_livreur", None):
        compteurs.update(_pour_livreur(livreur))

    if utilisateur.role == Role.ADMIN:
        compteurs.update(_pour_admin())

    # Une pastille a zero n'est pas une pastille : on ne l'envoie pas, et le
    # front n'a donc rien a filtrer.
    return Response({"data": {cle: n for cle, n in compteurs.items() if n}})
