"""Ce qu'un livreur FAIT — et qui n'existait que sur le papier.

**Ta remarque, L-6** : *« je n'ai rien pu tester, tu refuses de faire la partie
mobile »*. Les ecrans web du livreur etaient en lecture seule, ce que D-40
justifie : accepter une course, confirmer une remise et signaler une absence se
font une main sur le guidon, avec la position et l'appareil photo. Mais
« l'action est sur le mobile » ne veut rien dire tant que l'API ne l'accepte
nulle part.

Quatre regles tenues cote serveur, pas dans l'interface :

  1. **Une course a la fois en Express.** Un livreur qui en accepte une
     deuxieme laisse la premiere refroidir. C'est une contrainte du metier,
     pas un confort d'affichage.
  2. **L'attribution fait foi** (scenario 14.2). On ne valide que la livraison
     qui nous est attribuee, quoi qu'on declare avoir fait physiquement.
  3. **Le code du client est la preuve** que le bon colis est arrive a la
     bonne personne. Sans lui, n'importe qui pourrait marquer « livre ».
  4. **Deux tentatives, puis retour** (D-23).
"""
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from coeur.evenements import Evenement, emettre
from coeur.geographie import distance_km
from commandes.models import HistoriqueStatut, StatutCommande
from comptes.models import StatutDisponibilite, TypeService
from comptes.permissions import EstLivreurValide

from .models import (
    ArretTournee,
    Livraison,
    ResultatTentative,
    StatutArret,
    StatutLivraison,
    TentativeLivraison,
)
from .serializers import LivraisonSerializer

# Au-dela de cette distance, une course Express n'est plus proposee : le
# livreur ferait plus de route pour aller chercher que pour livrer.
RAYON_PROPOSITION_KM = 8


def _profil(requete):
    return getattr(requete.user, "profil_livreur", None)


def _refus(code, message, statut=status.HTTP_409_CONFLICT):
    return Response(
        {"erreur": {"code": code, "message": message, "details": {}}}, status=statut
    )


def _ma_livraison(requete, identifiant):
    """La livraison attribuee a CE livreur, ou None.

    Le filtre par livreur n'est pas un confort d'affichage : c'est la regle
    « l'attribution fait foi ». Un livreur qui appelle l'identifiant d'une
    course voisine recoit 404, pas la course.
    """
    return (
        Livraison.objects.select_related("commande", "commande__client__utilisateur")
        .filter(pk=identifiant, livreur=_profil(requete))
        .first()
    )


@api_view(["POST"])
@permission_classes([EstLivreurValide])
def changer_disponibilite(requete):
    """Se declarer disponible, ou raccrocher.

    On ne raccroche pas au milieu d'une course : la personne qui attend son
    repas n'a pas a subir un changement d'humeur.
    """
    profil = _profil(requete)
    cible = requete.data.get("statut")
    if cible not in StatutDisponibilite.values:
        return _refus("statut_inconnu", "Statut de disponibilite inconnu.",
                      status.HTTP_400_BAD_REQUEST)

    en_course = Livraison.objects.filter(
        livreur=profil,
        statut_livraison__in=[StatutLivraison.ATTRIBUEE, StatutLivraison.RECUPEREE,
                              StatutLivraison.EN_ROUTE],
    ).exists()
    if cible == StatutDisponibilite.HORS_LIGNE and en_course:
        return _refus("course_en_cours",
                      "Terminez votre course en cours avant de raccrocher.")

    profil.statut_disponibilite = cible
    profil.save(update_fields=["statut_disponibilite"])
    return Response({"data": {"statut_disponibilite": profil.statut_disponibilite}})


@api_view(["GET"])
@permission_classes([EstLivreurValide])
def livraisons_disponibles(requete):
    """Les courses Express a prendre, les plus proches d'abord.

    Elles sont masquees tant qu'une course est en cours : proposer la suivante
    a quelqu'un qui roule deja, c'est l'inviter a en accepter deux.
    """
    profil = _profil(requete)
    if profil.mode_livraison != TypeService.EXPRESS:
        return Response({"data": []})

    if Livraison.objects.filter(
        livreur=profil,
        statut_livraison__in=[StatutLivraison.ATTRIBUEE, StatutLivraison.RECUPEREE,
                              StatutLivraison.EN_ROUTE],
    ).exists():
        return Response({"data": []})

    candidates = (
        Livraison.objects.filter(
            statut_livraison=StatutLivraison.A_ATTRIBUER,
            livreur__isnull=True,
            commande__type_service=TypeService.EXPRESS,
        )
        .select_related("commande", "commande__client__utilisateur", "adresse_livraison")
        .prefetch_related("commande__sous_commandes__vendeur")
    )

    # Le plus proche d'abord, quand on sait ou est le livreur. Sinon on rend
    # tout : mieux vaut une liste non triee qu'une liste vide.
    if profil.position_lat is not None and profil.position_lon is not None:
        avec_distance = []
        for livraison in candidates:
            adresse = livraison.adresse_livraison
            ecart = distance_km(
                profil.position_lat, profil.position_lon, adresse.latitude, adresse.longitude
            )
            if ecart is None or ecart <= RAYON_PROPOSITION_KM:
                avec_distance.append((ecart if ecart is not None else 999, livraison))
        candidates = [livraison for _, livraison in sorted(avec_distance, key=lambda p: p[0])]

    return Response({"data": LivraisonSerializer(candidates, many=True).data})


@api_view(["POST"])
@permission_classes([EstLivreurValide])
@transaction.atomic
def accepter_livraison(requete, identifiant):
    """Prendre une course.

    Le verrou `select_for_update` n'est pas un exces de prudence : deux
    livreurs qui appuient au meme instant sur la meme course, c'est le cas
    normal aux heures de pointe. Sans lui, les deux partent.
    """
    profil = _profil(requete)

    if profil.mode_livraison == TypeService.EXPRESS and Livraison.objects.filter(
        livreur=profil,
        statut_livraison__in=[StatutLivraison.ATTRIBUEE, StatutLivraison.RECUPEREE,
                              StatutLivraison.EN_ROUTE],
    ).exists():
        return _refus("deja_en_course",
                      "Vous avez deja une course en cours : terminez-la d'abord.")

    livraison = (
        Livraison.objects.select_for_update()
        .select_related("commande", "commande__client__utilisateur")
        .filter(pk=identifiant)
        .first()
    )
    if livraison is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if livraison.livreur_id is not None:
        return _refus("deja_prise", "Cette course vient d'etre prise par quelqu'un d'autre.")

    livraison.livreur = profil
    livraison.statut_livraison = StatutLivraison.ATTRIBUEE
    livraison.date_attribution = timezone.now()
    livraison.save(update_fields=["livreur", "statut_livraison", "date_attribution"])

    profil.statut_disponibilite = StatutDisponibilite.EN_COURSE
    profil.save(update_fields=["statut_disponibilite"])

    emettre(Evenement(
        nom="COURSE_ACCEPTEE",
        acteur=requete.user,
        type_objet="LIVRAISON",
        id_objet=livraison.id,
        titre="Un livreur a pris votre commande en charge",
        message=(f"{requete.user.prenom} arrive avec votre commande "
                 f"{livraison.commande.numero_commande}."),
        lien="/mes-commandes",
        apres={"statut_livraison": livraison.statut_livraison},
        destinataires=[livraison.commande.client.utilisateur],
    ))

    return Response({"data": LivraisonSerializer(livraison).data})


@api_view(["POST"])
@permission_classes([EstLivreurValide])
def recuperer_colis(requete, identifiant):
    """Confirmer qu'on a le colis en main, et partir.

    Cette etape existe parce que « en route » et « attribuee » ne sont pas la
    meme chose pour le client : entre les deux, il attend que le restaurant
    finisse, pas que le livreur roule.
    """
    livraison = _ma_livraison(requete, identifiant)
    if livraison is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if livraison.statut_livraison != StatutLivraison.ATTRIBUEE:
        return _refus("etape_inattendue", "Cette course n'est pas en attente de retrait.")

    livraison.statut_livraison = StatutLivraison.EN_ROUTE
    livraison.date_prise_en_charge = timezone.now()
    livraison.save(update_fields=["statut_livraison", "date_prise_en_charge"])

    commande = livraison.commande
    commande.statut_actuel = StatutCommande.EN_LIVRAISON
    commande.save(update_fields=["statut_actuel"])
    HistoriqueStatut.objects.create(
        type_objet="COMMANDE", id_objet=commande.id,
        statut_avant=StatutCommande.PRETE, statut_apres=commande.statut_actuel,
        utilisateur=requete.user, commentaire="Colis recupere par le livreur",
    )

    emettre(Evenement(
        nom="COMMANDE_EN_ROUTE", acteur=requete.user, type_objet="LIVRAISON",
        id_objet=livraison.id,
        titre="Votre commande est en route",
        message=f"Gardez votre code de remise a portee : {livraison.code_confirmation}.",
        lien="/mes-commandes",
        apres={"statut_livraison": livraison.statut_livraison},
        destinataires=[commande.client.utilisateur],
    ))

    return Response({"data": LivraisonSerializer(livraison).data})


@api_view(["POST"])
@permission_classes([EstLivreurValide])
def confirmer_livraison(requete, identifiant):
    """Confirmer la remise, avec le code donne par le client.

    Le code est la preuve que le bon colis est arrive a la bonne personne.
    Sans lui, n'importe qui pourrait marquer « livre » depuis son canape — et
    la plateforme n'aurait rien a opposer a un client qui n'a rien recu.
    """
    livraison = _ma_livraison(requete, identifiant)
    if livraison is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if livraison.statut_livraison == StatutLivraison.LIVREE:
        return _refus("deja_livree", "Cette livraison est deja confirmee.")

    code = str(requete.data.get("code", "")).strip()
    if livraison.code_confirmation and code != livraison.code_confirmation:
        return _refus("code_incorrect",
                      "Le code ne correspond pas. Demandez-le au client.",
                      status.HTTP_400_BAD_REQUEST)

    livraison.statut_livraison = StatutLivraison.LIVREE
    livraison.date_reelle = timezone.now()
    livraison.save(update_fields=["statut_livraison", "date_reelle"])

    TentativeLivraison.objects.create(
        livraison=livraison,
        numero_tentative=livraison.tentatives.count() + 1,
        resultat=ResultatTentative.LIVREE,
        commentaire="Remis en main propre, code verifie.",
        position_lat=requete.data.get("position_lat"),
        position_lon=requete.data.get("position_lon"),
    )

    commande = livraison.commande
    avant = commande.statut_actuel
    commande.statut_actuel = StatutCommande.LIVREE
    commande.save(update_fields=["statut_actuel"])
    HistoriqueStatut.objects.create(
        type_objet="COMMANDE", id_objet=commande.id,
        statut_avant=avant, statut_apres=commande.statut_actuel,
        utilisateur=requete.user, commentaire="Livraison confirmee par le code client",
    )

    # L'arret de tournee suit, s'il y en a un.
    ArretTournee.objects.filter(livraison=livraison).update(
        statut=StatutArret.LIVRE, heure_reelle=timezone.now()
    )

    profil = _profil(requete)
    if not Livraison.objects.filter(
        livreur=profil,
        statut_livraison__in=[StatutLivraison.ATTRIBUEE, StatutLivraison.RECUPEREE,
                              StatutLivraison.EN_ROUTE],
    ).exists():
        profil.statut_disponibilite = StatutDisponibilite.DISPONIBLE
        profil.save(update_fields=["statut_disponibilite"])

    emettre(Evenement(
        nom="COMMANDE_LIVREE", acteur=requete.user, type_objet="LIVRAISON",
        id_objet=livraison.id,
        titre="Votre commande est livree",
        message="Vous pouvez maintenant donner votre avis sur la boutique et la livraison.",
        lien="/mes-commandes",
        avant={"statut_livraison": StatutLivraison.EN_ROUTE},
        apres={"statut_livraison": livraison.statut_livraison},
        destinataires=[commande.client.utilisateur],
    ))

    return Response({"data": LivraisonSerializer(livraison).data})


@api_view(["POST"])
@permission_classes([EstLivreurValide])
def signaler_absence(requete, identifiant):
    """Personne a l'adresse. Deux tentatives gratuites, puis retour (D-23).

    Le comptage est cote serveur : un livreur presse pourrait declarer trois
    absences en trois minutes, et le colis repartirait sans que personne
    n'ait rien tente.
    """
    livraison = _ma_livraison(requete, identifiant)
    if livraison is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    numero = livraison.tentatives.count() + 1
    TentativeLivraison.objects.create(
        livraison=livraison,
        numero_tentative=numero,
        resultat=ResultatTentative.CLIENT_ABSENT,
        commentaire=str(requete.data.get("commentaire", ""))[:500],
        position_lat=requete.data.get("position_lat"),
        position_lon=requete.data.get("position_lon"),
    )

    derniere = numero >= 2
    if derniere:
        livraison.statut_livraison = StatutLivraison.ECHOUEE
        livraison.save(update_fields=["statut_livraison"])

        commande = livraison.commande
        avant = commande.statut_actuel
        commande.statut_actuel = StatutCommande.ECHEC_LIVRAISON
        commande.save(update_fields=["statut_actuel"])
        HistoriqueStatut.objects.create(
            type_objet="COMMANDE", id_objet=commande.id,
            statut_avant=avant, statut_apres=commande.statut_actuel,
            utilisateur=requete.user,
            commentaire="Deux tentatives sans reponse : retour a l'expediteur",
        )
        ArretTournee.objects.filter(livraison=livraison).update(statut=StatutArret.ECHOUE)

        profil = _profil(requete)
        profil.statut_disponibilite = StatutDisponibilite.DISPONIBLE
        profil.save(update_fields=["statut_disponibilite"])

    emettre(Evenement(
        nom="LIVRAISON_ABSENCE", acteur=requete.user, type_objet="LIVRAISON",
        id_objet=livraison.id,
        titre=("Votre colis repart" if derniere else "Nous vous avons manque"),
        message=(
            "Deux passages sans reponse : votre colis retourne chez le vendeur. "
            "Contactez le support pour convenir d'une nouvelle livraison."
            if derniere else
            f"Tentative {numero} sur 2. Un avis de passage a ete depose ; "
            f"nous repasserons."
        ),
        lien="/mes-commandes",
        apres={"tentative": numero, "statut_livraison": livraison.statut_livraison},
        destinataires=[livraison.commande.client.utilisateur],
    ))

    return Response({"data": {
        **LivraisonSerializer(livraison).data,
        "tentative": numero,
        "derniere_tentative": derniere,
    }})


@api_view(["POST"])
@permission_classes([EstLivreurValide])
def signaler_position(requete):
    """La position du livreur, pour proposer les courses les plus proches.

    Elle n'est pas conservee dans un historique : seule la derniere compte.
    Un journal des deplacements d'une personne n'a aucun usage ici, et il
    serait la donnee la plus sensible du projet.
    """
    profil = _profil(requete)
    try:
        profil.position_lat = float(requete.data["latitude"])
        profil.position_lon = float(requete.data["longitude"])
    except (KeyError, TypeError, ValueError):
        return _refus("position_invalide", "Latitude et longitude attendues.",
                      status.HTTP_400_BAD_REQUEST)
    profil.save(update_fields=["position_lat", "position_lon"])
    return Response({"data": {"enregistree": True}})
