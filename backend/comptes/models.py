"""Zone 1 du modele — comptes et roles.

Traduction directe de plan-organisation/02-modele/dictionnaire-donnees.md.
Le dictionnaire fait foi : si les deux divergent, c'est ici qu'il faut corriger.

Le principe qui structure toute la zone : UTILISATEUR porte l'authentification
(un e-mail unique dans toute la plateforme, un mot de passe, un statut de
compte) et se specialise en **un seul** profil metier. Sans lui, sept tables
porteraient chacune un e-mail, et rien ne garantirait leur unicite.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class TypeService(models.TextChoices):
    EXPRESS = "EXPRESS", "Express"
    STANDARD = "STANDARD", "Standard"


class Role(models.TextChoices):
    CLIENT = "CLIENT", "Client"
    VENDEUR = "VENDEUR", "Vendeur"
    GESTIONNAIRE = "GESTIONNAIRE", "Gestionnaire"
    LIVREUR = "LIVREUR", "Livreur"
    ADMIN = "ADMIN", "Administrateur"


class StatutCompte(models.TextChoices):
    ACTIF = "ACTIF", "Actif"
    EN_ATTENTE = "EN_ATTENTE_VALIDATION", "En attente de validation"
    SUSPENDU = "SUSPENDU", "Suspendu"
    DESACTIVE = "DESACTIVE", "Desactive"


class StatutValidation(models.TextChoices):
    EN_ATTENTE = "EN_ATTENTE", "En attente"
    VALIDE = "VALIDE", "Valide"
    REJETE = "REJETE", "Rejete"
    SUSPENDU = "SUSPENDU", "Suspendu"


class GestionnaireUtilisateur(BaseUserManager):
    """L'e-mail remplace le nom d'utilisateur, qui n'existe pas ici."""

    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Un utilisateur a toujours une adresse e-mail.")
        utilisateur = self.model(email=self.normalize_email(email), **extra)
        utilisateur.set_password(password)
        utilisateur.save(using=self._db)
        return utilisateur

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", Role.ADMIN)
        extra.setdefault("statut_compte", StatutCompte.ACTIF)
        return self.create_user(email, password, **extra)


class Utilisateur(AbstractUser):
    # AbstractUser impose un username : on le retire, l'e-mail suffit et il est
    # deja unique. Le garder obligerait a inventer une valeur a chaque creation.
    username = None
    first_name = None
    last_name = None

    email = models.EmailField("adresse e-mail", unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=30, blank=True)

    role = models.CharField(max_length=20, choices=Role.choices)
    statut_compte = models.CharField(
        max_length=25, choices=StatutCompte.choices, default=StatutCompte.ACTIF
    )
    date_inscription = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = GestionnaireUtilisateur()

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"
        ordering = ["-date_inscription"]

    def __str__(self):
        return f"{self.prenom} {self.nom} <{self.email}>"

    @property
    def peut_se_connecter(self):
        """Un compte suspendu ou desactive existe encore mais n'entre plus.

        On ne supprime jamais physiquement un compte (D-13) : c'est ce
        booleen qui fait la difference, pas l'absence de ligne.
        """
        return self.statut_compte in (StatutCompte.ACTIF, StatutCompte.EN_ATTENTE)


class Adresse(models.Model):
    """Entite partagee : un client, un vendeur ou un entrepot s'y rattachent.

    Decision D-21. Sans latitude/longitude des DEUX cotes du trajet, le
    filtrage Express par rayon (D-09) et les frais par bandes (D-11) sont
    inapplicables.
    """

    libelle = models.CharField(max_length=60, blank=True, help_text="Domicile, Bureau…")
    rue = models.CharField(max_length=200)
    complement = models.CharField(max_length=200, blank=True)
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=20)
    pays = models.CharField(max_length=60, default="France")

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    instructions_livraison = models.TextField(blank=True)

    zone = models.ForeignKey(
        "livraisons.ZoneLivraison", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="adresses",
    )

    class Meta:
        verbose_name = "adresse"

    def __str__(self):
        return f"{self.rue}, {self.code_postal} {self.ville}"

    @property
    def est_geocodee(self):
        return self.latitude is not None and self.longitude is not None


class Client(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="profil_client"
    )
    date_naissance = models.DateField(null=True, blank=True)
    consentement_marketing = models.BooleanField(default=False)
    adresses = models.ManyToManyField(Adresse, through="AdresseClient", related_name="clients")

    def __str__(self):
        return str(self.utilisateur)


class AdresseClient(models.Model):
    """Le carnet d'adresses. Une seule adresse principale par client."""

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    adresse = models.ForeignKey(Adresse, on_delete=models.CASCADE)
    est_principale = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["client", "adresse"], name="adresse_unique_par_client"),
            models.UniqueConstraint(
                fields=["client"], condition=models.Q(est_principale=True),
                name="une_seule_adresse_principale",
            ),
        ]

    def __str__(self):
        return f"{self.client_id} — {self.adresse_id}"


class Vendeur(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="profil_vendeur"
    )
    nom_boutique = models.CharField(max_length=150)
    # Le mode de service est porte par le VENDEUR, pas par le produit (D-08) :
    # c'est lui qui commande tout le flux de commande et de livraison.
    type_activite = models.CharField(max_length=10, choices=TypeService.choices)
    rayon_livraison_km = models.DecimalField(
        max_digits=5, decimal_places=2, default=5,
        help_text="Express uniquement : au-dela, la boutique n'apparait pas au catalogue.",
    )
    adresse = models.ForeignKey(
        Adresse, null=True, blank=True, on_delete=models.SET_NULL, related_name="boutiques"
    )
    siret = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    logo_url = models.URLField(blank=True)
    note_moyenne = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    statut_validation = models.CharField(
        max_length=15, choices=StatutValidation.choices, default=StatutValidation.EN_ATTENTE
    )
    compte_stripe_id = models.CharField(max_length=100, blank=True)
    taux_commission = models.DecimalField(
        max_digits=5, decimal_places=4, default=0.15,
        help_text="Part prelevee par la plateforme, en fraction (0.15 = 15 %).",
    )

    class Meta:
        verbose_name = "vendeur"

    def __str__(self):
        return self.nom_boutique

    @property
    def est_publiable(self):
        """Un vendeur non valide n'a aucun produit visible au catalogue (R-07)."""
        return self.statut_validation == StatutValidation.VALIDE


class TypeGestionnaire(models.TextChoices):
    STAFF_VENDEUR = "STAFF_VENDEUR", "Personnel d'un vendeur"
    STAFF_ENTREPOT = "STAFF_ENTREPOT", "Personnel d'un entrepot"


class Gestionnaire(models.Model):
    """Un seul role, deux types exclusifs (D-05).

    Employe par un vendeur, ou rattache a un entrepot de la plateforme —
    jamais les deux. La contrainte est posee en base, pas seulement en Python :
    une regle qui ne vit que dans le code finit par etre contournee.
    """

    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="profil_gestionnaire"
    )
    type_gestionnaire = models.CharField(max_length=20, choices=TypeGestionnaire.choices)
    vendeur = models.ForeignKey(
        Vendeur, null=True, blank=True, on_delete=models.CASCADE, related_name="personnel"
    )
    entrepot = models.ForeignKey(
        "livraisons.Entrepot", null=True, blank=True,
        on_delete=models.CASCADE, related_name="personnel",
    )
    date_embauche = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(type_gestionnaire="STAFF_VENDEUR",
                             vendeur__isnull=False, entrepot__isnull=True)
                    | models.Q(type_gestionnaire="STAFF_ENTREPOT",
                               vendeur__isnull=True, entrepot__isnull=False)
                ),
                name="gestionnaire_rattache_a_un_seul_cote",
            )
        ]

    def __str__(self):
        return f"{self.utilisateur} ({self.get_type_gestionnaire_display()})"


class Vehicule(models.TextChoices):
    VELO = "VELO", "Velo"
    SCOOTER = "SCOOTER", "Scooter"
    VOITURE = "VOITURE", "Voiture"
    CAMIONNETTE = "CAMIONNETTE", "Camionnette"


class StatutDisponibilite(models.TextChoices):
    DISPONIBLE = "DISPONIBLE", "Disponible"
    EN_COURSE = "EN_COURSE", "En course"
    HORS_LIGNE = "HORS_LIGNE", "Hors ligne"


class Livreur(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="profil_livreur"
    )
    vehicule = models.CharField(max_length=15, choices=Vehicule.choices, default=Vehicule.VELO)
    # Express : une course a la fois, trajet direct. Standard : des tournees
    # depuis un entrepot. Les deux ne se melangent pas.
    mode_livraison = models.CharField(max_length=10, choices=TypeService.choices)
    entrepot = models.ForeignKey(
        "livraisons.Entrepot", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="livreurs",
        help_text="Standard uniquement : l'entrepot de rattachement.",
    )
    statut_validation = models.CharField(
        max_length=15, choices=StatutValidation.choices, default=StatutValidation.EN_ATTENTE
    )
    statut_disponibilite = models.CharField(
        max_length=15, choices=StatutDisponibilite.choices, default=StatutDisponibilite.HORS_LIGNE
    )
    position_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    position_lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    note_moyenne = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "livreur"

    def __str__(self):
        return f"{self.utilisateur} ({self.get_mode_livraison_display()})"


class NiveauAdmin(models.TextChoices):
    ADMIN = "ADMIN", "Administrateur"
    SUPER_ADMIN = "SUPER_ADMIN", "Super administrateur"


class Administrateur(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="profil_admin"
    )
    niveau = models.CharField(max_length=15, choices=NiveauAdmin.choices, default=NiveauAdmin.ADMIN)

    class Meta:
        verbose_name = "administrateur"

    def __str__(self):
        return str(self.utilisateur)


# ═══════════════════════════════════════════════════════════════════════════
#  Le profil : ce qui se change seul, et ce qui se demande (D-77)
# ═══════════════════════════════════════════════════════════════════════════


class ChampSensible(models.TextChoices):
    """Les champs d'identite, geles. Repris du projet banque.

    Sur une place de marche, l'identite engage : un vendeur valide sur un nom
    ne doit pas pouvoir en changer seul apres coup. L'e-mail, le telephone et
    l'adresse, eux, se corrigent librement — ils n'engagent personne.
    """

    NOM = "NOM", "Nom"
    PRENOM = "PRENOM", "Prenom"
    DATE_NAISSANCE = "DATE_NAISSANCE", "Date de naissance"


class StatutDemande(models.TextChoices):
    EN_ATTENTE = "EN_ATTENTE", "En attente"
    ACCEPTEE = "ACCEPTEE", "Acceptee"
    REFUSEE = "REFUSEE", "Refusee"


class DemandeModification(models.Model):
    """Une demande de correction d'identite, arbitree par un administrateur.

    Elle porte le motif : sans lui, un administrateur devrait accepter ou
    refuser a l'aveugle, ce qui revient a tout accepter.
    """

    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name="demandes_modification"
    )
    motif = models.TextField(blank=True)
    statut = models.CharField(
        max_length=12, choices=StatutDemande.choices, default=StatutDemande.EN_ATTENTE
    )
    decide_par = models.ForeignKey(
        Utilisateur, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="demandes_arbitrees",
    )
    commentaire_decision = models.TextField(blank=True)
    date_demande = models.DateTimeField(auto_now_add=True)
    date_decision = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "demande de modification"
        verbose_name_plural = "demandes de modification"
        ordering = ["-date_demande"]

    def __str__(self):
        return f"Demande {self.pk} de {self.utilisateur_id} ({self.statut})"


class ChampDemande(models.Model):
    """Un champ dans une demande : ce qu'il vaut, ce qu'il devrait valoir.

    Une demande porte plusieurs champs — corriger « Benali » en « Ben Ali »
    change souvent le nom ET le prenom.
    """

    demande = models.ForeignKey(
        DemandeModification, on_delete=models.CASCADE, related_name="champs"
    )
    champ = models.CharField(max_length=20, choices=ChampSensible.choices)
    valeur_actuelle = models.CharField(max_length=150, blank=True)
    valeur_demandee = models.CharField(max_length=150)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["demande", "champ"], name="un_champ_par_demande")
        ]

    def __str__(self):
        return f"{self.champ} : {self.valeur_actuelle} -> {self.valeur_demandee}"


class Preferences(models.Model):
    """Les reglages de l'application, par compte.

    Separes du profil (D-76) : le profil dit QUI on est, les preferences disent
    COMMENT l'application se comporte. Les melanger produit un ecran fourre-tout
    que personne ne relit.
    """

    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="preferences"
    )

    # Canaux de notification. Le canal dans l'application est toujours actif :
    # une information critique n'a jamais un canal unique (scenario 12.1).
    notifications_email = models.BooleanField(default=True)
    notifications_push = models.BooleanField(default=True)
    courriels_promotionnels = models.BooleanField(default=False)

    # Confort d'affichage.
    densite = models.CharField(
        max_length=10,
        choices=[("COMPACTE", "Compacte"), ("NORMALE", "Normale")],
        default="NORMALE",
    )
    masquer_montants = models.BooleanField(
        default=False, help_text="Cache les montants a l'ecran, utile en public."
    )

    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "preferences"
        verbose_name_plural = "preferences"

    def __str__(self):
        return f"Preferences de {self.utilisateur_id}"
