"""Rendre a la vente le stock que des paniers abandonnes retiennent encore.

A lancer regulierement en production, et au demarrage en developpement — c'est
ce que fait `demarrer.py`. Sans elle, un client qui cree une commande puis
ferme son onglet immobilise ses articles indefiniment, et le catalogue affiche
« epuise » sans que personne ne comprenne pourquoi.

    python manage.py liberer_reservations
    python manage.py liberer_reservations --minutes 60
"""
from django.core.management.base import BaseCommand

from commandes import reservation


class Command(BaseCommand):
    help = "Libere le stock reserve par des commandes jamais payees."

    def add_arguments(self, analyseur):
        analyseur.add_argument(
            "--minutes", type=int, default=reservation.DUREE_MINUTES,
            help="Age a partir duquel une reservation est consideree abandonnee.",
        )

    def handle(self, *args, **options):
        liberees = reservation.liberer_les_expirees(options["minutes"])
        if liberees:
            self.stdout.write(self.style.SUCCESS(
                f"{liberees} commande(s) abandonnee(s) : stock rendu a la vente."
            ))
        else:
            self.stdout.write("Aucune reservation expiree.")
