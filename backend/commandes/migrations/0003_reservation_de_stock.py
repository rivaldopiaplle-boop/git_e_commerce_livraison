"""Le drapeau de reservation, et la reprise des commandes deja en base.

Ajouter le champ ne suffit pas : les commandes creees avant cette migration
tiennent une reservation bien reelle, et un defaut a `False` la rendrait
invisible. Elle ne serait alors jamais relachee — le stock resterait bloque
pour toujours — et une nouvelle tentative de paiement la poserait une seconde
fois. La deuxieme operation repare donc l'existant.
"""
from django.db import migrations, models


def lever_le_drapeau(apps, schema_editor):
    """Une commande en attente de paiement tient sa reservation : on le dit."""
    Commande = apps.get_model("commandes", "Commande")
    Commande.objects.filter(statut_actuel="EN_ATTENTE_PAIEMENT").update(
        stock_reserve_pose=True
    )


def recompter_les_reserves(apps, schema_editor):
    """Recaler chaque compteur sur la somme des commandes qui le justifient.

    Le compteur `stock_reserve` etait ecrit a deux endroits avant ce
    correctif — a la creation de la commande et a l'ouverture du paiement — et
    relache une seule fois. Les bases existantes portent donc des reserves
    fantomes qui font passer pour epuises des produits qui ne le sont pas.
    """
    Commande = apps.get_model("commandes", "Commande")
    Produit = apps.get_model("catalogue", "Produit")

    attendu = {}
    for commande in Commande.objects.filter(stock_reserve_pose=True).prefetch_related(
        "sous_commandes__lignes"
    ):
        for sous_commande in commande.sous_commandes.all():
            for ligne in sous_commande.lignes.all():
                if ligne.produit_id:
                    attendu[ligne.produit_id] = attendu.get(ligne.produit_id, 0) + ligne.quantite

    for produit in Produit.objects.all():
        juste = min(attendu.get(produit.id, 0), produit.stock_disponible)
        if produit.stock_reserve != juste:
            produit.stock_reserve = juste
            produit.save(update_fields=["stock_reserve"])


def ne_rien_defaire(apps, schema_editor):
    """Redescendre le drapeau n'a pas de sens : on ne perd rien a ne rien faire."""


class Migration(migrations.Migration):

    dependencies = [
        ("commandes", "0002_initial"),
        ("catalogue", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="commande",
            name="stock_reserve_pose",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(lever_le_drapeau, ne_rien_defaire),
        migrations.RunPython(recompter_les_reserves, ne_rien_defaire),
    ]
