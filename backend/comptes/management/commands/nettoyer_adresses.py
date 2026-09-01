"""Fusionner les adresses rigoureusement identiques d'un meme client.

Le defaut qui a rendu cette commande necessaire : passer commande en saisissant
une adresse **creait une nouvelle ligne a chaque fois**, meme si la meme figurait
deja au carnet. Trois achats depuis chez soi donnaient trois adresses
identiques, et le tunnel de commande proposait trois choix indiscernables.

La cause est corrigee dans `commandes/vues_commande.py`, qui reutilise
desormais une adresse identique. Cette commande repare ce qui a deja ete cree.

    python manage.py nettoyer_adresses
    python manage.py nettoyer_adresses --pour-de-vrai

**Elle ne supprime rien tant qu'on ne le demande pas.** Une commande passee
pointe vers son adresse de livraison : la fusionner mal reecrirait l'histoire
d'une livraison, ce qu'on ne fait pas a la legere. Sans `--pour-de-vrai`, elle
se contente de dire ce qu'elle ferait.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from comptes.models import Adresse, AdresseClient, Client


def _empreinte(adresse):
    """Ce qui fait que deux adresses sont « la meme » aux yeux d'un humain."""
    return (
        adresse.rue.strip().lower(),
        adresse.complement.strip().lower(),
        adresse.code_postal.strip(),
        adresse.ville.strip().lower(),
    )


class Command(BaseCommand):
    help = "Fusionne les adresses identiques d'un meme client."

    def add_arguments(self, analyseur):
        analyseur.add_argument(
            "--pour-de-vrai", action="store_true", dest="appliquer",
            help="Applique la fusion. Sans cette option, on ne fait que decrire.",
        )

    def handle(self, *args, **options):
        from commandes.models import Commande

        appliquer = options["appliquer"]
        fusionnees = 0

        for client in Client.objects.select_related("utilisateur").prefetch_related("adresses"):
            par_empreinte = {}
            for adresse in client.adresses.all().order_by("id"):
                par_empreinte.setdefault(_empreinte(adresse), []).append(adresse)

            for doublons in par_empreinte.values():
                if len(doublons) < 2:
                    continue

                # La plus ancienne fait foi : c'est celle que le client a
                # nommee lui-meme, les suivantes sont des copies machinales.
                gardee, *copies = doublons
                self.stdout.write(
                    f"  {client.utilisateur.email} : {len(copies)} copie(s) de "
                    f"« {gardee.rue}, {gardee.code_postal} {gardee.ville} »"
                )
                fusionnees += len(copies)

                if not appliquer:
                    continue

                with transaction.atomic():
                    for copie in copies:
                        # Les commandes d'abord : `adresse_livraison` est
                        # protege, et une commande sans adresse n'existe pas.
                        Commande.objects.filter(adresse_livraison=copie).update(
                            adresse_livraison=gardee
                        )
                        AdresseClient.objects.filter(adresse=copie).delete()
                        if not Adresse.objects.filter(pk=copie.pk).exclude(
                            commandes__isnull=True
                        ).exists():
                            Adresse.objects.filter(pk=copie.pk).delete()

        self.stdout.write("")
        if not fusionnees:
            self.stdout.write(self.style.SUCCESS("Aucun doublon d'adresse."))
        elif appliquer:
            self.stdout.write(self.style.SUCCESS(
                f"{fusionnees} adresse(s) en double fusionnee(s)."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"{fusionnees} adresse(s) en double. Relance avec --pour-de-vrai "
                f"pour les fusionner."
            ))
