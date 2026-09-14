from datetime import timezone
from decimal import Decimal
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from decimal import Decimal
from django.conf import settings
from edumax import settings
from django.db import models
from django.db import models
from django.utils import timezone

# ==================== UTILISATEUR ====================
class Utilisateur(AbstractUser):
    SUPER_ADMIN = 'super_admin'
    ADMIN_ECOLE = 'admin_ecole'
    ENSEIGNANT = 'enseignant'
    ETUDIANT = 'etudiant'
    
    ROLE_CHOICES = [
        (SUPER_ADMIN, 'Super Administrateur'),
        (ADMIN_ECOLE, 'Administrateur École'),
        (ENSEIGNANT, 'Enseignant'),
        (ETUDIANT, 'Étudiant'),
    ]
    
    prenom = models.CharField(max_length=100, verbose_name='Prénom')
    telephone = models.CharField(max_length=20, blank=True, null=True)
    pays = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True)
    email_valide = models.BooleanField(default=False)
    date_inscription = models.DateTimeField(auto_now_add=True)
    date_certification = models.DateTimeField(null=True, blank=True)
    is_eleve = models.BooleanField(default=False)
    is_professeur = models.BooleanField(default=False)
    date_activation_auto = models.DateTimeField(null=True, blank=True)
    validation_automatique = models.BooleanField(default=False, help_text="Active la publication automatique sans validation manuelle")
    certifie = models.BooleanField(default=False)
    date_inscription = models.DateTimeField(auto_now_add=True)
    paiement_desactive = models.BooleanField(default=False)  # Super admin peut désactiver l'obligation de paiement
    
    
    
    def __str__(self):
        return f"{self.prenom} {self.username}"


# ==================== ABONNEMENT ====================
class Abonnement(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    max_etudiants = models.IntegerField(default=100)
    max_cours = models.IntegerField(default=50)
    stockage_gb = models.IntegerField(default=5)
    ordre = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nom


# ==================== ÉCOLE ====================
class Ecole(models.Model):
    nom = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    description = models.TextField()
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    ville = models.CharField(max_length=100)
    pays = models.CharField(max_length=100, default="Cameroun")
    quartier = models.CharField(max_length=200, blank=True, null=True)
    numero_agrement = models.CharField(max_length=100, blank=True, null=True)
    abonnement = models.ForeignKey(Abonnement, on_delete=models.SET_NULL, null=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    facebook = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    youtube = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    banniere = models.ImageField(upload_to='ecoles/bannieres/', blank=True, null=True)
    admin_ecole = models.OneToOneField(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='ecole_admin')
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nom


# ==================== ENSEIGNANT ÉCOLE ====================
class EnseignantEcole(models.Model):
    enseignant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='enseignant_ecoles')
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, related_name='enseignants')
    date_affectation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['enseignant', 'ecole']


# ==================== FILIÈRE ====================
class Filiere(models.Model):
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, related_name='filieres')
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    ordre = models.IntegerField(default=0)
    public = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['ecole', 'nom']
        ordering = ['ordre', 'nom']
    
    def __str__(self):
        return f"{self.ecole.nom} - {self.nom}"


# ==================== SPÉCIALITÉ ====================
class Specialite(models.Model):
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='specialites')
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    cle_inscription = models.CharField(max_length=50, unique=True, blank=True)
    ordre = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['filiere', 'nom']
        ordering = ['ordre', 'nom']
    
    def save(self, *args, **kwargs):
        if not self.cle_inscription:
            self.cle_inscription = f"{slugify(self.filiere.ecole.nom)}_{slugify(self.filiere.nom)}_{slugify(self.nom)}_{uuid.uuid4().hex[:8]}".upper()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.filiere.nom} - {self.nom}"


# ==================== INSCRIPTION ÉTUDIANT ====================
class InscriptionEtudiant(models.Model):
    etudiant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='inscriptions')
    specialite = models.ForeignKey(Specialite, on_delete=models.CASCADE, related_name='inscriptions')
    date_inscription = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['etudiant', 'specialite']


# ==================== COURS PROGRAMME ====================
class CoursProgramme(models.Model):
    specialite = models.ForeignKey(Specialite, on_delete=models.CASCADE, related_name='cours_programmes')
    titre = models.CharField(max_length=200)
    description = models.TextField()
    objectifs = models.TextField(blank=True, null=True)
    enseignant = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='cours_assignes')
    actif = models.BooleanField(default=True)
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='cours_crees')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    statut = models.CharField(max_length=20, default='en_cours')
    mode_programmation = models.CharField(max_length=20, default='recurrent')
    
    class Meta:
        ordering = ['date_debut', 'titre']
    
    def __str__(self):
        return self.titre


# ==================== SÉANCE BASE ====================
class SeanceBase(models.Model):
    TYPE_VISIO = 'visio'
    TYPE_ASYNCHRONE = 'asynchrone'
    TYPE_INTEGRATION = 'integration'
    TYPE_CORRECTION = 'correction'
    
    TYPE_CHOICES = [
        (TYPE_VISIO, 'Visioconférence'),
        (TYPE_ASYNCHRONE, 'Séance asynchrone'),
        (TYPE_INTEGRATION, 'Activité d\'intégration'),
        (TYPE_CORRECTION, 'Séance de correction'),
    ]
    
    STATUT_BROUILLON = 'brouillon'
    STATUT_PUBLIE = 'publie'
    STATUT_TERMINE = 'termine'
    
    STATUT_CHOICES = [
        (STATUT_BROUILLON, 'Brouillon'),
        (STATUT_PUBLIE, 'Publié'),
        (STATUT_TERMINE, 'Terminé'),
    ]
    
    cours = models.ForeignKey(CoursProgramme, on_delete=models.CASCADE, related_name='seances')
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    objectifs = models.TextField(blank=True)
    type_seance = models.CharField(max_length=20, choices=TYPE_CHOICES)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=STATUT_BROUILLON)
    ordre = models.IntegerField(default=0)
    duree_estimee = models.IntegerField(default=60)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_publication = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='seances_crees')
    cours = models.ForeignKey('CoursProgramme', on_delete=models.CASCADE, related_name='seances')
    class Meta:
        ordering = ['ordre', 'date_creation']
    
    def __str__(self):
        return self.titre
    
    def publier(self):
        from django.utils import timezone
        self.statut = self.STATUT_PUBLIE
        self.date_publication = timezone.now()
        self.save()


# ==================== SÉANCE VISIO ====================
class SeanceVisio(models.Model):
    seance          = models.OneToOneField('SeanceBase', on_delete=models.CASCADE, related_name='visio')
    meeting_id      = models.CharField(max_length=100, unique=True, blank=True)
    lien_enseignant = models.URLField(blank=True, null=True)
    lien_etudiant   = models.URLField(blank=True, null=True)
    est_active      = models.BooleanField(default=False)
    date_debut      = models.DateTimeField(blank=True, null=True)
    date_fin        = models.DateTimeField(blank=True, null=True)
    enregistrement_url = models.URLField(blank=True, null=True)
    enregistrement_disponible_jusqua = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Séance visio"

    def __str__(self):
        return f"Visio — {self.seance.titre}"

    def demarrer(self):
        self.est_active = True
        self.date_debut  = timezone.now()
        self.save(update_fields=['est_active', 'date_debut'])

    def terminer(self):
        """MÉTHODE MANQUANTE — ajoutée. Termine la visio et fixe la
        date d'expiration de l'enregistrement (30 jours par défaut)."""
        from datetime import timedelta
        self.est_active = False
        self.date_fin   = timezone.now()
        if self.enregistrement_url and not self.enregistrement_disponible_jusqua:
            self.enregistrement_disponible_jusqua = timezone.now() + timedelta(days=30)
        self.save(update_fields=['est_active', 'date_fin', 'enregistrement_disponible_jusqua'])

    def enregistrement_valide(self):
        """MÉTHODE MANQUANTE — ajoutée. Vérifie si l'enregistrement
        existe encore et n'est pas expiré."""
        if not self.enregistrement_url:
            return False
        if self.enregistrement_disponible_jusqua and timezone.now() > self.enregistrement_disponible_jusqua:
            return False
        return True

    @property
    def duree_ecoulee_minutes(self):
        if not self.date_debut:
            return 0
        fin = self.date_fin or timezone.now()
        return int((fin - self.date_debut).total_seconds() / 60)


# ==================== AUTRES MODÈLES NÉCESSAIRES ====================
class PresenceSeance(models.Model):
    seance = models.ForeignKey(SeanceBase, on_delete=models.CASCADE, related_name='presences')
    etudiant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    present = models.BooleanField(default=False)
    vu = models.BooleanField(default=False)
    date_vu = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ['seance', 'etudiant']


class ProgressionEtudiantSeance(models.Model):
    seance = models.ForeignKey(SeanceBase, on_delete=models.CASCADE, related_name='progressions')
    etudiant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    vu = models.BooleanField(default=False)
    date_vu = models.DateTimeField(blank=True, null=True)
    date_debut = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['seance', 'etudiant']


class Notification(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications')
    titre = models.CharField(max_length=200)
    message = models.TextField()
    lien = models.CharField(max_length=500, blank=True, null=True)
    lu = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_creation']


class ImageEcole(models.Model):
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, related_name='galerie_images')
    image = models.ImageField(upload_to='ecoles/galerie/')
    titre = models.CharField(max_length=200, blank=True, null=True)
    ordre = models.IntegerField(default=0)
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['ordre', '-date_ajout']
    
# ==================== CLASSES MANQUANTES ====================

class ParticipantCoursProgramme(models.Model):
    """Participant à un cours"""
    cours = models.ForeignKey(CoursProgramme, on_delete=models.CASCADE, related_name='participants')
    etudiant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    bloque = models.BooleanField(default=False)
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['cours', 'etudiant']


class DepotPresentation(models.Model):
    """Dépôt de présentation par un étudiant"""
    seance = models.ForeignKey(SeanceBase, on_delete=models.CASCADE, related_name='depots')
    etudiant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    fichier = models.FileField(upload_to='presentations/')
    lien_video = models.URLField(blank=True, null=True)
    date_depot = models.DateTimeField(auto_now_add=True)
    note = models.FloatField(blank=True, null=True)
    feedback = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['seance', 'etudiant']




class Conversation(models.Model):
    """Conversation privée entre deux utilisateurs."""
    participants     = models.ManyToManyField('Utilisateur', related_name='conversations')
    date_creation    = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    # Utilisateurs qui ont "supprimé" la conv de leur côté
    supprimes_par   = models.ManyToManyField(
        'Utilisateur', related_name='conversations_supprimees', blank=True
    )

    class Meta:
        ordering = ['-date_modification']

    def __str__(self):
        noms = ', '.join(p.username for p in self.participants.all()[:2])
        return f"Conv({noms})"

    def get_non_lus_pour(self, utilisateur):
        return self.messages.filter(lu=False).exclude(expediteur=utilisateur).count()

    def get_autre_participant(self, utilisateur):
        return self.participants.exclude(id=utilisateur.id).first()

class Forum(models.Model):
    """
    Forum — trois types :
    - 'plateforme' : ouvert à tous les utilisateurs inscrits
    - 'ecole'      : réservé aux membres d'une école spécifique
    - 'specialite' : réservé aux étudiants d'une spécialité
    """
    TYPE_PLATEFORME  = 'plateforme'
    TYPE_ECOLE       = 'ecole'
    TYPE_SPECIALITE  = 'specialite'

    TYPE_CHOICES = [
        (TYPE_PLATEFORME, 'Forum général plateforme'),
        (TYPE_ECOLE,      'Forum d\'école'),
        (TYPE_SPECIALITE, 'Forum de spécialité'),
    ]

    type_forum   = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_PLATEFORME)
    nom          = models.CharField(max_length=200, verbose_name="Nom du forum")
    description  = models.TextField(blank=True)
    icone        = models.CharField(max_length=50, default='fas fa-comments', verbose_name="Classe icône FontAwesome")
    couleur      = models.CharField(max_length=7, default='#1e3a8a', verbose_name="Couleur (hex)")

    # Liens optionnels
    ecole        = models.ForeignKey(
        'Ecole', on_delete=models.CASCADE, null=True, blank=True, related_name='forums'
    )
    specialite   = models.ForeignKey(
        'Specialite', on_delete=models.SET_NULL, null=True, blank=True, related_name='forums'
    )

    # Gestion
    actif        = models.BooleanField(default=True)
    ordre        = models.IntegerField(default=0)
    cree_par     = models.ForeignKey(
        'Utilisateur', on_delete=models.SET_NULL, null=True, blank=True, related_name='forums_crees'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    moderation    = models.BooleanField(default=False, verbose_name="Modération activée (messages en attente)")
    lecture_seule = models.BooleanField(default=False, verbose_name="Lecture seule (aucun nouveau message)")
    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Forum"
        verbose_name_plural = "Forums"

    def __str__(self):
        return f"{self.get_type_forum_display()} — {self.nom}"

    def peut_voir(self, utilisateur):
        """Vérifie si l'utilisateur peut voir ce forum."""
        if not utilisateur.is_authenticated:
            return False
        if self.type_forum == self.TYPE_PLATEFORME:
            return True
        if self.type_forum == self.TYPE_ECOLE:
            return (
                utilisateur.role == 'super_admin' or
                (self.ecole and (
                    utilisateur.ecoles_admin.filter(id=self.ecole.id).exists() or
                    utilisateur.ecoles_enseignant.filter(id=self.ecole.id).exists() or
                    utilisateur.inscriptions.filter(specialite__filiere__ecole=self.ecole).exists()
                ))
            )
        if self.type_forum == self.TYPE_SPECIALITE:
            return (
                utilisateur.role == 'super_admin' or
                utilisateur.role == 'admin_ecole' or
                (self.specialite and (
                    utilisateur.cours_enseignant.filter(specialite=self.specialite).exists() or
                    utilisateur.inscriptions.filter(specialite=self.specialite).exists()
                ))
            )
        return False

    def peut_poster(self, utilisateur):
        """Vérifie si l'utilisateur peut poster dans ce forum."""
        if self.lecture_seule:
            return False
        return self.peut_voir(utilisateur)

    def peut_moderer(self, utilisateur):
        """Vérifie si l'utilisateur peut modérer ce forum."""
        if utilisateur.role == 'super_admin':
            return True
        if self.type_forum in [self.TYPE_ECOLE, self.TYPE_SPECIALITE]:
            if utilisateur.role == 'admin_ecole' and self.ecole:
                return utilisateur.ecoles_admin.filter(id=self.ecole.id).exists()
        return False

    @property
    def nb_messages(self):
        return self.messages.filter(est_cache=False).count()

    @property
    def dernier_message(self):
        return self.messages.filter(est_cache=False).select_related('auteur').order_by('-date_creation').first()

    def get_sujet_jour(self, date=None):
        """Récupère le sujet du jour pour ce forum"""
        from django.utils import timezone
        if date is None:
            date = timezone.now().date()
        
        try:
            return self.sujets_jour.filter(date=date, actif=True).first()
        except:
            return None
    # Dans models.py, classe Forum
    def get_participants(self):
        """Retourne tous les utilisateurs qui ont accès à ce forum"""
        from .models import Utilisateur
        
        if self.type_forum == 'plateforme':
            return Utilisateur.objects.filter(is_active=True)
        
        elif self.type_forum == 'ecole' and self.ecole:
            return Utilisateur.objects.filter(
                models.Q(ecole_admin=self.ecole) |
                models.Q(enseignant_ecoles__ecole=self.ecole) |
                models.Q(inscriptions__specialite__filiere__ecole=self.ecole)
            ).distinct()
        
        elif self.type_forum == 'specialite' and self.specialite:
            return Utilisateur.objects.filter(
                models.Q(enseignant_ecoles__specialites=self.specialite) |
                models.Q(inscriptions__specialite=self.specialite)
            ).distinct()
        
        return Utilisateur.objects.none()

    def get_derniers_messages(self, limit=50, avant=None):
        """Récupère les derniers messages non masqués"""
        qs = self.messages.filter(est_cache=False).select_related('auteur')
        if avant:
            qs = qs.filter(date_creation__lt=avant)
        return qs.order_by('-date_creation')[:limit]

    def get_messages_depuis(self, message_id):
        """Récupère les messages plus récents qu'un ID donné (pour polling)"""
        return self.messages.filter(
            id__gt=message_id, 
            est_cache=False
        ).select_related('auteur').order_by('date_creation')

class MessagePrive(models.Model):
    """Message dans une conversation privée."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    expediteur   = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='messages_envoyes')
    contenu      = models.TextField()
    lu           = models.BooleanField(default=False)
    date_envoi   = models.DateTimeField(auto_now_add=True)
    modifie      = models.BooleanField(default=False)
    date_modification = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['date_envoi']

    def __str__(self):
        return f"{self.expediteur.username}: {self.contenu[:40]}"


class MessageForum(models.Model):
    """Message direct dans un forum - comme WhatsApp"""
    forum = models.ForeignKey('Forum', on_delete=models.CASCADE, related_name='messages')
    auteur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='messages_forum')
    contenu = models.TextField(verbose_name="Contenu")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    # Modération
    est_cache = models.BooleanField(default=False, verbose_name="Message masqué")
    moderateur = models.ForeignKey('Utilisateur', null=True, blank=True, on_delete=models.SET_NULL, 
                                   related_name='messages_moderes', verbose_name="Modéré par")
    motif_cache = models.CharField(max_length=255, blank=True, verbose_name="Motif du masquage")
    date_moderation = models.DateTimeField(null=True, blank=True, verbose_name="Date de modération")
    
    # Signalements
    signalements = models.ManyToManyField('Utilisateur', related_name='messages_signales', blank=True)
    nb_signalements = models.IntegerField(default=0, verbose_name="Nombre de signalements")
    
    class Meta:
        ordering = ['date_creation']
        verbose_name = "Message forum"
        verbose_name_plural = "Messages forum"
    
    def __str__(self):
        return f"{self.auteur.username}: {self.contenu[:50]}"
    
    def masquer(self, moderateur, motif=""):
        """Masquer un message (modération)"""
        self.est_cache = True
        self.moderateur = moderateur
        self.motif_cache = motif
        self.date_moderation = timezone.now()
        self.save()
    
    def ajouter_signalement(self, utilisateur):
        """Ajouter un signalement"""
        if utilisateur not in self.signalements.all():
            self.signalements.add(utilisateur)
            self.nb_signalements = self.signalements.count()
            self.save()
            return True
        return False


class ProgressionEtudiant(models.Model):
    """Progression globale d'un étudiant dans un cours"""
    etudiant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='progressions_globales')
    cours = models.ForeignKey(CoursProgramme, on_delete=models.CASCADE, related_name='progressions_globales')
    seances_terminees = models.ManyToManyField(SeanceBase, blank=True)
    date_debut = models.DateTimeField(auto_now_add=True)
    date_derniere_activite = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['etudiant', 'cours']
    
    @property
    def progression(self):
        total = self.cours.seances.count()
        if total == 0:
            return 0
        terminees = self.seances_terminees.count()
        return int((terminees / total) * 100)


class Cours(models.Model):
    """Ancien modèle Cours (gardé pour compatibilité)"""
    specialite = models.ForeignKey(Specialite, on_delete=models.CASCADE, related_name='cours_anciens')
    titre = models.CharField(max_length=200)
    description = models.TextField()
    ordre = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['ordre', 'date_creation']
    
    def __str__(self):
        return self.titre


class Seance(models.Model):
    """Ancien modèle Seance (gardé pour compatibilité)"""
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='seances_anciennes')
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    type_seance = models.CharField(max_length=20, default='fichier')
    ordre = models.IntegerField(default=0)
    fichier = models.FileField(upload_to='cours/fichiers/', blank=True, null=True)
    lien_video = models.URLField(blank=True, null=True)
    lien_visio = models.URLField(blank=True, null=True)
    visio_date = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['ordre']
    
    def __str__(self):
        return self.titre

# ==================== MODÈLES POUR ACTIVITÉ D'INTÉGRATION ====================

class ExerciceIntegration(models.Model):
    """Exercice pour une activité d'intégration"""
    NIVEAU_FACILE = 1
    NIVEAU_MOYEN = 2
    NIVEAU_DIFFICILE = 3
    NIVEAU_EXPERT = 4
    
    NIVEAU_CHOICES = [
        (NIVEAU_FACILE, 'Facile'),
        (NIVEAU_MOYEN, 'Moyen'),
        (NIVEAU_DIFFICILE, 'Difficile'),
        (NIVEAU_EXPERT, 'Expert'),
    ]
    
    MODE_VISIBLE = 'visible'
    MODE_MASQUE = 'masque'
    
    MODE_CORRECTION_CHOICES = [
        (MODE_VISIBLE, 'Correction visible immédiatement'),
        (MODE_MASQUE, 'Correction masquée (mode évaluation)'),
    ]
    
    seance = models.ForeignKey('SeanceBase', on_delete=models.CASCADE, null=True, blank=True, related_name='exercices_integration')
    titre = models.CharField(max_length=200, verbose_name="Titre de l'exercice")
    enonce = models.TextField(verbose_name="Énoncé")
    fichier_enonce = models.FileField(upload_to='seances/exercices/enonces/', blank=True, null=True)
    
    niveau = models.IntegerField(choices=NIVEAU_CHOICES, default=NIVEAU_MOYEN, verbose_name="Niveau de difficulté")
    points = models.FloatField(default=10, verbose_name="Points")
    ordre = models.IntegerField(default=0, verbose_name="Ordre")
    ordre = models.IntegerField(default=0, verbose_name="Ordre")
    mode_correction = models.CharField(max_length=10, choices=MODE_CORRECTION_CHOICES, default=MODE_VISIBLE, verbose_name="Mode de correction")
    correction_texte = models.TextField(blank=True, verbose_name="Correction détaillée")
    correction_fichier = models.FileField(upload_to='seances/exercices/corrections/', blank=True, null=True)
    reponses_attendues = models.JSONField(default=list, blank=True, verbose_name="Réponses attendues (format JSON)")
    
    class Meta:
        ordering = ['ordre']
    
    def __str__(self):
        return f"{self.titre} ({self.get_niveau_display()})"
    
    def correction_visible(self):
        return self.mode_correction == self.MODE_VISIBLE


class CorrectionSeance(models.Model):
    """Séance de correction - lie des devoirs/exercices à corriger"""
    seance = models.OneToOneField('SeanceBase', on_delete=models.CASCADE, related_name='correction_seance') 
    date_correction = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Correction: {self.seance.titre}"


class NotificationVisio(models.Model):
    """Notification pour les étudiants quand une visio démarre"""
    seance_visio = models.ForeignKey('SeanceVisio', on_delete=models.CASCADE, related_name='notifications')
    etudiant = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='notifications_visio')
    envoyee = models.BooleanField(default=False)
    date_envoi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['seance_visio', 'etudiant']
    
    def __str__(self):
        return f"{self.etudiant.username} - {self.seance_visio.seance.titre}"
    
class SeanceProgrammee(models.Model):
    """Modèle pour compatibilité"""
    cours = models.ForeignKey('CoursProgramme', on_delete=models.CASCADE)
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type_seance = models.CharField(max_length=30, default='asynchrone')
    duree_estimee = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.titre
# ==================== EXERCICES D'APPLICATION ====================

class Exercice(models.Model):
    TYPE_QCM           = 'qcm'
    TYPE_VRAI_FAUX     = 'vrai_faux'
    TYPE_TEXTE_TROUS   = 'texte_trous'
    TYPE_REPONSE_COURTE = 'reponse_courte'
    TYPE_REDACTION     = 'redaction'
    TYPE_DEPOT_FICHIER = 'depot_fichier'
    TYPE_CODE          = 'code'
    TYPE_ETUDE_CAS     = 'etude_cas'

    TYPE_CHOICES = [
        (TYPE_QCM,            'QCM'),
        (TYPE_VRAI_FAUX,      'Vrai / Faux'),
        (TYPE_TEXTE_TROUS,    'Texte à trous'),
        (TYPE_REPONSE_COURTE, 'Réponse courte'),
        (TYPE_REDACTION,      'Rédaction'),
        (TYPE_DEPOT_FICHIER,  'Dépôt de fichier'),
        (TYPE_CODE,           'Code'),
        (TYPE_ETUDE_CAS,      'Étude de cas'),
    ]

    CONTEXT_CHOICES = [
        ('session',     "Exercice d'application (séance)"),
        ('homework',    'Devoir'),
        ('integration', "Activité d'intégration"),
    ]

    seance         = models.ForeignKey('SeanceBase', on_delete=models.CASCADE,
                         null=True, blank=True, related_name='exercices')
    titre          = models.CharField(max_length=200)
    consignes      = models.TextField()
    type_exercice  = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_QCM)
    duree          = models.PositiveIntegerField(default=30, help_text="Durée en minutes")
    points         = models.PositiveIntegerField(default=10)
    est_publie     = models.BooleanField(default=False)
    date_creation  = models.DateTimeField(auto_now_add=True)

    # Contexte
    context_type   = models.CharField(max_length=20, choices=CONTEXT_CHOICES, default='session')
    due_date       = models.DateTimeField(null=True, blank=True)
    started_at     = models.DateTimeField(null=True, blank=True)
    results_published = models.BooleanField(default=False)
    configuration  = models.JSONField(default=dict, blank=True)

    # Lancement & correction
    est_lance             = models.BooleanField(default=False)
    lance_a               = models.DateTimeField(null=True, blank=True)
    resultats_publies     = models.BooleanField(default=False)
    correction_publiee    = models.BooleanField(default=False)

    # Options QCM
    multi_reponse                 = models.BooleanField(default=False)
    melanger_questions            = models.BooleanField(default=True)
    melanger_reponses             = models.BooleanField(default=True)
    afficher_note_immediate       = models.BooleanField(default=True)
    afficher_correction_immediate = models.BooleanField(default=False)
    nb_tentatives_max             = models.PositiveIntegerField(default=1,
        help_text="0 = tentatives illimitées")

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Exercice"

    def __str__(self):
        return f"{self.titre} ({self.get_type_exercice_display()})"

    @property
    def nb_questions(self):
        return self.questions.count()

    @property
    def total_points(self):
        return sum(q.points for q in self.questions.all())

    def peut_etre_passe_par(self, utilisateur):
        """Vérifie si un étudiant peut passer cet exercice."""
        if not self.est_lance:
            return False
        if self.nb_tentatives_max > 0:
            nb_tentatives = SoumissionExercice.objects.filter(
                exercice=self, etudiant=utilisateur
            ).count()
            if nb_tentatives >= self.nb_tentatives_max:
                return False
        return True

# ==================== DEVOIRS ====================

class Devoir(models.Model):
    """Devoir avec choix du mode de correction"""
    
    # Définir les types d'exercice directement ici
    TYPE_QCM = 'qcm'
    TYPE_VRAI_FAUX = 'vrai_faux'
    TYPE_TEXTE_TROUS = 'texte_trous'
    TYPE_REPONSE_COURTE = 'reponse_courte'
    TYPE_REDACTION = 'redaction'
    TYPE_FICHIER = 'fichier'
    TYPE_CODE = 'code'
    TYPE_ETUDE_CAS = 'etude_cas'
    
    TYPE_CHOICES = [
        (TYPE_QCM, 'QCM'),
        (TYPE_VRAI_FAUX, 'Vrai/Faux'),
        (TYPE_TEXTE_TROUS, 'Texte à trous'),
        (TYPE_REPONSE_COURTE, 'Réponse courte'),
        (TYPE_REDACTION, 'Rédaction'),
        (TYPE_FICHIER, 'Dépôt fichier'),
        (TYPE_CODE, 'Code'),
        (TYPE_ETUDE_CAS, 'Étude de cas'),
    ]
    
    MODE_CORRECTION_INDEPENDANT = 'independant'
    MODE_CORRECTION_SEANCE = 'seance'
    
    MODE_CORRECTION_CHOICES = [
        (MODE_CORRECTION_INDEPENDANT, 'Correction indépendante'),
        (MODE_CORRECTION_SEANCE, 'Rattaché à une séance de correction'),
    ]
    
    seance = models.ForeignKey('SeanceBase', on_delete=models.CASCADE, related_name='devoirs')
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    consignes = models.TextField()
    date_debut = models.DateTimeField()
    date_limite = models.DateTimeField()
    
    # Mode de correction
    mode_correction = models.CharField(max_length=20, choices=MODE_CORRECTION_CHOICES, default=MODE_CORRECTION_INDEPENDANT)
    seance_correction = models.ForeignKey('SeanceBase', on_delete=models.SET_NULL, null=True, blank=True, related_name='devoirs_a_corriger')
    
    # Statut
    est_publie = models.BooleanField(default=False)
    correction_publiee = models.BooleanField(default=False)
    type_exercice = models.CharField(max_length=20, choices=TYPE_CHOICES, default='qcm')  # Changement ici
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.titre


class SoumissionDevoir(models.Model):
    """Soumission d'un étudiant à un devoir"""
    devoir = models.ForeignKey(Devoir, on_delete=models.CASCADE, related_name='soumissions')
    etudiant = models.ForeignKey('Utilisateur', on_delete=models.CASCADE)
    reponse_texte = models.TextField(blank=True)
    fichier = models.FileField(upload_to='devoirs/soumissions/', blank=True, null=True)
    date_soumission = models.DateTimeField(auto_now_add=True)
    note = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    fichier_corrige = models.FileField(upload_to='devoirs/corrections/', blank=True, null=True)
    
    class Meta:
        unique_together = ['devoir', 'etudiant']
    



class Question(models.Model):
    TYPE_QCM       = 'qcm'
    TYPE_MULTI     = 'multi'
    TYPE_VRAI_FAUX = 'vrai_faux'
    TYPE_TEXTE     = 'texte_libre'

    TYPE_Q_CHOICES = [
        (TYPE_QCM,       'QCM — une seule réponse'),
        (TYPE_MULTI,     'Choix multiples'),
        (TYPE_VRAI_FAUX, 'Vrai / Faux'),
        (TYPE_TEXTE,     'Texte libre'),
    ]

    exercice      = models.ForeignKey(Exercice, on_delete=models.CASCADE, related_name='questions')
    texte         = models.TextField()
    type_question = models.CharField(max_length=20, choices=TYPE_Q_CHOICES, default=TYPE_QCM)
    explication   = models.TextField(blank=True, help_text="Affiché après la correction")
    image         = models.ImageField(upload_to='exercices/questions/', blank=True, null=True)
    ordre         = models.PositiveIntegerField(default=0)
    points        = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Question"

    def __str__(self):
        return f"Q{self.ordre} — {self.exercice.titre}"

    @property
    def bonne_reponse(self):
        return self.reponses.filter(est_correcte=True).first()

    @property
    def bonnes_reponses(self):
        return self.reponses.filter(est_correcte=True)

class SoumissionExercice(models.Model):
    STATUS_CHOICES = [
        ('en_cours',     'En cours'),
        ('termine',      'Terminé'),
        ('temps_ecoule', 'Temps écoulé'),
    ]

    etudiant        = models.ForeignKey('Utilisateur', on_delete=models.CASCADE,
                          related_name='soumissions_exercices')
    exercice        = models.ForeignKey(Exercice, on_delete=models.CASCADE,
                          related_name='soumissions')
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_cours')
    date_debut      = models.DateTimeField(auto_now_add=True)
    date_soumission = models.DateTimeField(null=True, blank=True)
    note            = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    note_sur        = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback        = models.TextField(blank=True)
    nb_tentative    = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-date_debut']
        verbose_name = "Soumission"

    def __str__(self):
        return f"{self.etudiant.username} — {self.exercice.titre}"

    @property
    def pourcentage(self):
        if self.note_sur and self.note_sur > 0:
            return round(float(self.note) / float(self.note_sur) * 100)
        return 0

    @property
    def mention(self):
        p = self.pourcentage
        if p >= 90: return 'Excellent'
        if p >= 75: return 'Bien'
        if p >= 60: return 'Assez bien'
        if p >= 50: return 'Passable'
        return 'Insuffisant'

    @property
    def mention_color(self):
        p = self.pourcentage
        if p >= 75: return 'success'
        if p >= 50: return 'warning'
        return 'danger'



class Answer(models.Model):
    """Réponse possible pour une question."""
    question    = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='reponses')
    texte       = models.CharField(max_length=500)
    est_correcte = models.BooleanField(default=False)
    ordre       = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Réponse possible"

    def __str__(self):
        return f"{'✓' if self.est_correcte else '✗'} {self.texte[:50]}"
    
class ReponseEtudiant(models.Model):
    soumission       = models.ForeignKey(SoumissionExercice, on_delete=models.CASCADE,
                           related_name='reponses')
    question         = models.ForeignKey(Question, on_delete=models.CASCADE)
    reponse_choisie  = models.ForeignKey(Answer, on_delete=models.SET_NULL,
                           null=True, blank=True, related_name='reponses_uniques')
    reponses_choisies = models.ManyToManyField(Answer, blank=True,
                           related_name='reponses_multiples')
    reponse_texte    = models.TextField(blank=True)
    est_correcte     = models.BooleanField(default=False)
    points_obtenus   = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Réponse étudiant"

    def __str__(self):
        return f"{self.soumission.etudiant.username} → Q{self.question.ordre}"

# ==================== FORMATIONS ====================

class ConditionVente(models.Model):
    """Conditions globales définies par le super admin"""
    commission_pourcentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    actif = models.BooleanField(default=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Commission: {self.commission_pourcentage}%"


class Coupon(models.Model):
    """Code promo pour réduction"""
    code = models.CharField(max_length=50, unique=True)
    reduction_pourcentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    reduction_fixe = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    validite_debut = models.DateTimeField()
    validite_fin = models.DateTimeField()
    utilisations_max = models.IntegerField(default=1)
    utilisations_count = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)
    
    def est_valide(self):
        from django.utils import timezone
        return (self.actif and 
                timezone.now() >= self.validite_debut and 
                timezone.now() <= self.validite_fin and
                self.utilisations_count < self.utilisations_max)
    
    def __str__(self):
        return self.code

# models.py
class CentreInteret(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    ordre = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['ordre', 'nom']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nom
    
class Formation(models.Model):
    
    # ── Statuts ──
    STATUT_CHOICES = [
        ('brouillon',   'Brouillon'),
        ('en_attente',  'En attente de validation'),
        ('publie',      'Publié'),
        ('refuse',      'Refusé'),
        ('suspendu',    'Suspendu'),
    ]

    NIVEAU_CHOICES = [
        ('debutant',       'Débutant'),
        ('intermediaire',  'Intermédiaire'),
        ('avance',         'Avancé'),
        ('expert',         'Expert'),
        ('tous_niveaux',   'Tous niveaux'),
    ]

    LANGUE_CHOICES = [
        ('fr',  'Français'),
        ('en',  'Anglais'),
        ('ar',  'Arabe'),
        ('es',  'Espagnol'),
        ('pt',  'Portugais'),
    ]

    # ── Informations générales ──
    titre              = models.CharField(max_length=200, verbose_name="Titre")
    slug               = models.SlugField(unique=True, blank=True)
    description_courte = models.CharField(max_length=300, verbose_name="Description courte")
    description_longue = models.TextField(blank=True, verbose_name="Description longue")
    resume             = models.CharField(max_length=200, blank=True, help_text="Accroche pour l'accueil")

    # ── Médias ──
    image_cover        = models.ImageField(upload_to='formations/covers/', blank=True, null=True)
    video_presentation = models.FileField(upload_to='formations/videos/', blank=True, null=True,
                                          help_text="Vidéo de présentation (aperçu gratuit)")

    # ── Pédagogie ──
    niveau     = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default='tous_niveaux', verbose_name="Niveau")
    langue     = models.CharField(max_length=5,  choices=LANGUE_CHOICES, default='fr',           verbose_name="Langue")
    duree      = models.CharField(max_length=50, blank=True, help_text="Ex: 4h30, 3 semaines",   verbose_name="Durée")
    nb_modules = models.PositiveIntegerField(default=0, verbose_name="Nombre de modules")

    # Objectifs (un par ligne dans le champ, splitté à l'affichage)
    objectifs    = models.TextField(blank=True, verbose_name="Objectifs pédagogiques (un par ligne)")
    prerequis    = models.TextField(blank=True, verbose_name="Prérequis (un par ligne)")
    public_cible = models.TextField(blank=True, verbose_name="Pour qui ? (un par ligne)")

    # ── Prix & promotions ──
    prix          = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Prix (FCFA)")
    prix_original = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        verbose_name="Prix original (avant promo)", help_text="Laisser vide si pas de promo")

    # ── Relations ──
    createur         = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='formations_crees')
    ecole            = models.ForeignKey('Ecole', on_delete=models.SET_NULL, null=True, blank=True, related_name='formations')
    centres_interet  = models.ManyToManyField('CentreInteret', blank=True, related_name='formations')
    cours            = models.ManyToManyField('CoursProgramme', blank=True, related_name='formations')

    # ── Statut & validation ──
    statut          = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    validation_auto = models.BooleanField(default=False)
    certifiee       = models.BooleanField(default=False, verbose_name="Formation certifiée")
    mise_en_avant   = models.BooleanField(default=False, verbose_name="Mettre en avant sur l'accueil")
    valide_par      = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                        on_delete=models.SET_NULL, related_name='formations_validees')
    date_validation = models.DateTimeField(null=True, blank=True)
    raison_refus    = models.TextField(blank=True, verbose_name="Raison du refus (si refusée)")

    # ── Dates ──
    date_creation    = models.DateTimeField(auto_now_add=True)
    date_publication = models.DateTimeField(null=True, blank=True)
    date_modification = models.DateTimeField(auto_now=True)

    # ── Statistiques ──
    nb_ventes    = models.IntegerField(default=0,  verbose_name="Nombre de ventes")
    nb_avis      = models.IntegerField(default=0,  verbose_name="Nombre d'avis")
    note_moyenne = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'))
    revenu_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    nb_vues      = models.PositiveIntegerField(default=0, verbose_name="Nombre de vues")

    class Meta:
        ordering = ['-date_publication', '-date_creation']
        verbose_name = "Formation"
        verbose_name_plural = "Formations"

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        # Génération du slug unique
        if not self.slug:
            base_slug = slugify(self.titre)
            slug = base_slug
            counter = 1
            while Formation.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    # ── Propriétés utiles dans les templates ──
    @property
    def objectifs_liste(self):
        """Retourne les objectifs sous forme de liste (split par ligne)."""
        return [o.strip() for o in self.objectifs.splitlines() if o.strip()]

    @property
    def prerequis_liste(self):
        return [p.strip() for p in self.prerequis.splitlines() if p.strip()]

    @property
    def public_cible_liste(self):
        return [p.strip() for p in self.public_cible.splitlines() if p.strip()]

    @property
    def est_gratuite(self):
        return self.prix == 0

    @property
    def a_promotion(self):
        return self.prix_original and self.prix_original > self.prix

    @property
    def pourcentage_reduction(self):
        if self.a_promotion:
            return int(100 - (self.prix / self.prix_original * 100))
        return 0

    # ── Méthodes métier ──
    def publier(self):
        from django.utils import timezone
        self.statut = 'publie'
        self.date_publication = timezone.now()
        self.save(update_fields=['statut', 'date_publication'])

    def suspendre(self, raison=''):
        self.statut = 'suspendu'
        if raison:
            self.raison_refus = raison
        self.save(update_fields=['statut', 'raison_refus'])

    def refuser(self, raison=''):
        self.statut = 'refuse'
        self.raison_refus = raison
        self.save(update_fields=['statut', 'raison_refus'])

    def mettre_a_jour_note(self):
        from django.db.models import Avg
        data = Avis.objects.filter(formation=self).aggregate(
            moyenne=Avg('note'), total=models.Count('id')
        )
        self.note_moyenne = round(data['moyenne'] or 0, 2)
        self.nb_avis = data['total'] or 0
        self.save(update_fields=['note_moyenne', 'nb_avis'])

    def incrementer_vues(self):
        Formation.objects.filter(pk=self.pk).update(nb_vues=models.F('nb_vues') + 1)

    def get_niveau_display_fr(self):
        return dict(self.NIVEAU_CHOICES).get(self.niveau, self.niveau)



class FichierFormation(models.Model):
    """Fichier inclus dans le pack de formation"""
    TYPE_VIDEO = 'video'
    TYPE_PDF = 'pdf'
    TYPE_DOC = 'document'
    TYPE_AUTRE = 'autre'
    
    TYPE_CHOICES = [
        (TYPE_VIDEO, 'Vidéo'),
        (TYPE_PDF, 'PDF'),
        (TYPE_DOC, 'Document (Word, etc.)'),
        (TYPE_AUTRE, 'Autre'),
    ]
    
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='fichiers')
    fichier = models.FileField(upload_to='formations/fichiers/')
    titre = models.CharField(max_length=200)
    type_fichier = models.CharField(max_length=20, choices=TYPE_CHOICES)
    taille = models.BigIntegerField(default=0, help_text="Taille en octets")
    ordre = models.IntegerField(default=0)
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['ordre']
    
    def __str__(self):
        return f"{self.titre} ({self.get_type_fichier_display()})"


class Avis(models.Model):
    """Avis d'un acheteur sur une formation"""
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='avis')
    utilisateur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='avis')
    note = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    commentaire = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['formation', 'utilisateur']
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.formation.titre} - {self.note}/5"


class AchatFormation(models.Model):
    STATUT_EN_ATTENTE = 'en_attente'
    STATUT_CONFIRME = 'confirme'
    STATUT_ECHOUE = 'echoue'
    STATUT_REMBOURSE = 'rembourse'
    
    STATUT_CHOICES = [
        (STATUT_EN_ATTENTE, 'En attente de paiement'),
        (STATUT_CONFIRME, 'Confirmé'),
        (STATUT_ECHOUE, 'Échoué'),
        (STATUT_REMBOURSE, 'Remboursé'),
    ]
    
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='achats')
    acheteur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='achats_formations')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    
    prix_original = models.DecimalField(max_digits=10, decimal_places=2)
    reduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    prix_net = models.DecimalField(max_digits=10, decimal_places=2)
    
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    revenu_createur = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=STATUT_EN_ATTENTE)
    
    # Paiement
    reference_paiement = models.CharField(max_length=100, unique=True, blank=True)
    type_paiement = models.CharField(max_length=20, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    data_paiement = models.JSONField(default=dict)
    
    date_achat = models.DateTimeField(auto_now_add=True)
    date_confirmation = models.DateTimeField(null=True, blank=True)
    
    # Acceptation des conditions
    conditions_acceptees = models.BooleanField(default=False)
    date_acceptation_conditions = models.DateTimeField(null=True, blank=True)
    ip_acceptation = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        unique_together = ['formation', 'acheteur']
    
    def __str__(self):
        return f"{self.acheteur.username} - {self.formation.titre}"
    
    def confirmer(self):
        from django.utils import timezone
        self.statut = self.STATUT_CONFIRME
        self.date_confirmation = timezone.now()
        self.save()
        
        # Mettre à jour les stats
        self.formation.nb_ventes += 1
        self.formation.revenu_total += self.prix_net
        self.formation.save()
    
    def a_acces(self):
        return self.statut == self.STATUT_CONFIRME


class AcceptationConditionsPublication(models.Model):
    """Traçabilité de l'acceptation des conditions avant publication"""
    utilisateur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE)
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE)
    version_conditions = models.CharField(max_length=20)
    date_acceptation = models.DateTimeField(auto_now_add=True)
    ip_adresse = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.formation.titre} - {self.date_acceptation}"

# ========== SIGNALEMENT FORMATION ==========
class SignalementFormation(models.Model):
    MOTIFS = [
        ('arnaque', 'Arnaque / Fausse formation'),
        ('contenu_illegal', 'Contenu illégal'),
        ('droit_auteur', 'Violation des droits d\'auteur'),
        ('publicite_trompeuse', 'Publicité trompeuse'),
        ('autre', 'Autre'),
    ]
    formation = models.ForeignKey('Formation', on_delete=models.CASCADE, related_name='signalements')
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    motif = models.CharField(max_length=50, choices=MOTIFS)
    description = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    traite = models.BooleanField(default=False)
    commentaire_traitement = models.TextField(blank=True)

    class Meta:
        unique_together = [['formation', 'utilisateur']]

    def __str__(self):
        return f"Signalement {self.formation.titre} par {self.utilisateur.username}"


# ========== RÈGLES DE VENTE (éditables) ==========
class RegleVente(models.Model):
    RUBRIQUES = [
        ('conditions', 'Conditions de vente'),
        ('contenu', 'Contenu des formations'),
        ('revenus', 'Revenus et reversements'),
        ('certification', 'Certification des comptes'),
    ]
    rubrique = models.CharField(max_length=20, choices=RUBRIQUES)
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    ordre = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['rubrique', 'ordre']

    def __str__(self):
        return f"{self.get_rubrique_display()} - {self.titre}"
    
class ValidationAutomatiqueLog(models.Model):
    """Log chaque publication automatique pour traçabilité."""
    utilisateur  = models.ForeignKey('Utilisateur', on_delete=models.CASCADE)
    formation    = models.ForeignKey(Formation, on_delete=models.CASCADE)
    ip_adresse   = models.GenericIPAddressField(null=True, blank=True)
    date_log     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AutoPub — {self.utilisateur.username} — {self.formation.titre}"
# ==================== PARAMÈTRES MESSAGERIE ====================

class ParametresMessagerie(models.Model):
    """Paramètres globaux pour la messagerie (polling intelligent)"""
    
    # Paramètres principaux
    polling_actif = models.BooleanField(default=True, verbose_name="Polling actif")
    intervalle_polling = models.IntegerField(default=30, help_text="Secondes", verbose_name="Intervalle polling")
    
    # Nettoyage automatique
    supprimer_messages_apres_jours = models.IntegerField(default=30, verbose_name="Supprimer messages après (jours)")
    supprimer_conversations_vides_apres_jours = models.IntegerField(default=7, verbose_name="Supprimer conversations vides après (jours)")
    
    # Optimisations
    pause_polling_onglet_inactif = models.BooleanField(default=True, verbose_name="Pause si onglet inactif")
    pause_polling_apres_heure = models.BooleanField(default=True, verbose_name="Pause nocturne active")
    heure_debut_pause = models.TimeField(default="22:00", verbose_name="Début pause nocturne")
    heure_fin_pause = models.TimeField(default="06:00", verbose_name="Fin pause nocturne")
    
    # Sécurité et limites
    max_messages_par_requete = models.IntegerField(default=50, verbose_name="Max messages par requête")
    rate_limit_secondes = models.IntegerField(default=2, verbose_name="Délai min entre envois (secondes)")

    # Activation générale
    forums_actifs = models.BooleanField(default=True, verbose_name="Forums actifs")

    # Activation par niveau
    forum_plateforme_actif = models.BooleanField(default=True, verbose_name="Forum plateforme actif")
    forum_ecole_actif = models.BooleanField(default=True, verbose_name="Forum école actif")
    forum_specialite_actif = models.BooleanField(default=True, verbose_name="Forum spécialité actif")

    # Sujet du jour
    sujet_jour_actif = models.BooleanField(default=True, verbose_name="Afficher le sujet du jour")
    sujet_jour_obligatoire = models.BooleanField(default=False, verbose_name="Sujet du jour obligatoire")

    # Limites et sécurité
    forum_max_messages_par_jour = models.IntegerField(default=100, verbose_name="Max messages par jour par utilisateur")
    forum_longueur_min_message = models.IntegerField(default=1, verbose_name="Longueur minimale du message")
    forum_longueur_max_message = models.IntegerField(default=2000, verbose_name="Longueur maximale du message")
    forum_delai_entre_messages = models.IntegerField(default=5, help_text="Secondes", verbose_name="Délai entre deux messages")

    # Modération
    forum_moderation_auto = models.BooleanField(default=False, verbose_name="Modération automatique")
    forum_signalement_seuil_blocage = models.IntegerField(default=5, verbose_name="Signalements avant blocage auto")

    # Historique
    forum_messages_par_page = models.IntegerField(default=50, verbose_name="Messages par page")
    forum_historique_conserver_jours = models.IntegerField(default=30, verbose_name="Conserver l'historique (jours)")

    # Polling forum (indépendant de la messagerie)
    forum_polling_actif = models.BooleanField(default=True, verbose_name="Polling forum actif")
    forum_intervalle_polling = models.IntegerField(default=15, verbose_name="Intervalle polling forum (secondes)")
    # Interface utilisateur
    message_polling_desactive = models.TextField(
        default="La messagerie est en mode manuel. Cliquez sur le bouton ci-dessous pour actualiser.",
        verbose_name="Message si polling désactivé"
    )
    
    # Optimisation automatique
    adaptation_auto_intervalle = models.BooleanField(default=True, verbose_name="Adapter auto l'intervalle selon charge")
    max_intervalle_polling = models.IntegerField(default=90, verbose_name="Intervalle max (secondes)")
    min_intervalle_polling = models.IntegerField(default=10, verbose_name="Intervalle min (secondes)")
    
    # Date de modification
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Paramètre messagerie"
        verbose_name_plural = "Paramètres messagerie"
    
    def __str__(self):
        return f"Paramètres messagerie (polling: {'actif' if self.polling_actif else 'inactif'})"
    
    @classmethod
    def get_config(cls):
        """Récupère la configuration (singleton)"""
        config, created = cls.objects.get_or_create(id=1)
        return config
# ==================== MODÈLES ÉPREUVES REFONDUS ====================

class RubriqueEpreuve(models.Model):
    """Rubrique principale : Baccalauréat, BEPC, Probatoire, Concours"""
    nom = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    ordre = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['ordre', 'nom']
    
    def __str__(self):
        return self.nom
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)


class CategorieEpreuve(models.Model):
    rubrique = models.ForeignKey(RubriqueEpreuve, on_delete=models.CASCADE, related_name='categories')
    nom = models.CharField(max_length=100)
    slug = models.SlugField(blank=True)
    ordre = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)
    a_des_series = models.BooleanField(default=False, help_text="Cocher si cette catégorie utilise des séries (ex: Bac)")
    class Meta:
        ordering = ['ordre', 'nom']
        unique_together = [['rubrique', 'nom']]
    
    def __str__(self):
        return f"{self.rubrique.nom} - {self.nom}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)
    @property
    def prix_pack(self):
        """Calcule le prix total de la catégorie (somme des prix des épreuves)"""
        total = sum(e.prix for e in self.epreuves.filter(statut='publie'))
        return total
    
class Epreuve(models.Model):
    SERIES_CHOICES = [
        ('', 'Toutes séries'),
        ('A', 'Série A (Littéraire)'),
        ('A1', 'Série A1'),
        ('A2', 'Série A2'),
        ('A3', 'Série A3'),
        ('A4', 'Série A4'),
        ('B', 'Série B (Économique)'),
        ('C', 'Série C (Scientifique)'),
        ('D', 'Série D (Technologique)'),
        ('E', 'Série E (STI)'),
        ('F', 'Série F'),
        ('G', 'Série G'),
        ('H', 'Série H'),
        ('TI', 'Série TI'),
    ]
    
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('publie', 'Publié'),
    ]
    
    categorie = models.ForeignKey('CategorieEpreuve', on_delete=models.SET_NULL, null=True, blank=True, related_name='epreuves')
    
    titre = models.CharField(max_length=200)
    annee = models.IntegerField(null=True, blank=True)
    serie = models.CharField(max_length=5, choices=SERIES_CHOICES, blank=True, default='')  # ← UN SEUL champ serie
    description = models.TextField(blank=True)
    fichier = models.FileField(upload_to='epreuves/fichiers/')
    apercu = models.ImageField(upload_to='epreuves/apercus/', blank=True, null=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    nb_ventes = models.IntegerField(default=0)
    est_populaire = models.BooleanField(default=False)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    date_ajout = models.DateTimeField(auto_now_add=True)
    fichier = models.FileField(upload_to='epreuves/fichiers/')
    fichier_corrige = models.FileField(upload_to='epreuves/corriges/', blank=True, null=True)  # À ajouter
    prix_corrige = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    class Meta:
        ordering = ['-annee', 'categorie__ordre', 'titre']
    
    def __str__(self):
        return f"{self.titre} ({self.annee})"

class PanierEpreuve(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='panier_epreuves')
    epreuves = models.ManyToManyField('Epreuve', blank=True)
    categories = models.ManyToManyField('CategorieEpreuve', blank=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    @property
    def total(self):
        total = sum(e.prix for e in self.epreuves.all())
        total += sum(c.prix_pack for c in self.categories.all())
        return total

class AchatEpreuve(models.Model):
    acheteur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='achats_epreuves')
    epreuves = models.ManyToManyField(Epreuve, blank=True)
    categories = models.ManyToManyField(CategorieEpreuve, blank=True)
    prix_total = models.DecimalField(max_digits=10, decimal_places=2)
    reference_paiement = models.CharField(max_length=100, unique=True, blank=True)
    type_paiement = models.CharField(max_length=20, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    statut = models.CharField(max_length=20, choices=[('en_attente','En attente'),('confirme','Confirmé'),('echoue','Échoué')], default='en_attente')
    date_achat = models.DateTimeField(auto_now_add=True)
    date_confirmation = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Achat {self.reference_paiement or self.id} - {self.acheteur.username}"

    def confirmer(self):
        from django.utils import timezone
        self.statut = 'confirme'
        self.date_confirmation = timezone.now()
        self.save()
        for e in self.epreuves.all():
            e.nb_ventes += 1
            e.save()
        for s in self.series.all():
            for e in s.epreuves_publiees:
                e.nb_ventes += 1
                e.save()
        for c in self.categories.all():
            for s in c.series.all():
                for e in s.epreuves_publiees:
                    e.nb_ventes += 1
                    e.save()

class TelechargementEpreuve(models.Model):
    achat = models.ForeignKey(AchatEpreuve, on_delete=models.CASCADE, related_name='telechargements')
    epreuve = models.ForeignKey(Epreuve, on_delete=models.CASCADE)
    date_telechargement = models.DateTimeField(auto_now_add=True)
    ip_adresse = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-date_telechargement']
# ============================================================
# MODÈLES POUR LA PAGE D'ACCUEIL DYNAMIQUE
# ============================================================
class ConfigurationPlateforme(models.Model):
    """
    Configuration centrale — tout le site public se gère d'ici.
    Singleton : toujours id=1. Utilisez get_config() pour y accéder.
    """

    # ── Identité ────────────────────────────────────────────────────
    nom_site          = models.CharField(max_length=100, default="Academia Net")
    slogan_site       = models.CharField(max_length=200, blank=True, default="La plateforme éducative de l'Afrique")
    logo              = models.ImageField(upload_to='config/logo/',    blank=True, null=True)
    favicon           = models.ImageField(upload_to='config/favicon/', blank=True, null=True)
    couleur_principale = models.CharField(max_length=7, default="#1e3a8a")
    couleur_secondaire = models.CharField(max_length=7, default="#f59e0b")
    couleur_accent     = models.CharField(max_length=7, default="#10b981")

    # ── Hero statique (fallback quand aucune diapositive) ───────────
    hero_titre         = models.CharField(max_length=200, default="La plateforme éducative de l'Afrique")
    hero_titre_accent  = models.CharField(max_length=100, default="Apprenez. Enseignez. Réussissez.")
    hero_description   = models.TextField(default="Écoles, formations, épreuves — tout au même endroit.")
    hero_bouton1_texte = models.CharField(max_length=80,  default="Commencer gratuitement")
    hero_bouton1_lien  = models.CharField(max_length=200, default="/inscription/")
    hero_bouton2_texte = models.CharField(max_length=80,  default="Explorer les formations")
    hero_bouton2_lien  = models.CharField(max_length=200, default="/formations/")
    hero_image         = models.ImageField(upload_to='config/hero/', blank=True, null=True)
    hero_video_url     = models.URLField(blank=True, default="")
    hero_afficher_stats = models.BooleanField(default=True)

    # ── Statistiques Hero ───────────────────────────────────────────
    stat1_label       = models.CharField(max_length=50, default="Écoles partenaires")
    stat1_valeur_auto = models.BooleanField(default=True)
    stat1_valeur_fixe = models.CharField(max_length=20, blank=True, default="")

    stat2_label       = models.CharField(max_length=50, default="Formations disponibles")
    stat2_valeur_auto = models.BooleanField(default=True)
    stat2_valeur_fixe = models.CharField(max_length=20, blank=True, default="")

    stat3_label       = models.CharField(max_length=50, default="Épreuves téléchargées")
    stat3_valeur_auto = models.BooleanField(default=False)
    stat3_valeur_fixe = models.CharField(max_length=20, blank=True, default="5 000+")

    stat4_label       = models.CharField(max_length=50, default="Étudiants inscrits")
    stat4_valeur_auto = models.BooleanField(default=True)
    stat4_valeur_fixe = models.CharField(max_length=20, blank=True, default="")

    # ── Visibilité des sections ─────────────────────────────────────
    section_services_visible            = models.BooleanField(default=True)
    section_formations_visible          = models.BooleanField(default=True)
    section_epreuves_visible            = models.BooleanField(default=True)
    section_ecoles_visible              = models.BooleanField(default=True)
    section_audience_visible            = models.BooleanField(default=True)
    section_temoignages_visible         = models.BooleanField(default=True)
    section_comment_ca_marche_visible   = models.BooleanField(default=True)
    section_cta_visible                 = models.BooleanField(default=True)
    section_newsletter_visible          = models.BooleanField(default=False)
    section_partenaires_visible         = models.BooleanField(default=False)

    # ── Titres des sections ─────────────────────────────────────────
    titre_section_formations       = models.CharField(max_length=100, default="Formations en vedette")
    sous_titre_section_formations  = models.CharField(max_length=200, default="Découvrez nos meilleures formations sélectionnées pour vous", blank=True)
    titre_section_epreuves         = models.CharField(max_length=100, default="Bibliothèque d'épreuves")
    sous_titre_section_epreuves    = models.CharField(max_length=200, default="Bac, BEPC, Probatoire, Concours — tout y est", blank=True)
    titre_section_ecoles           = models.CharField(max_length=100, default="Nos écoles partenaires")
    titre_section_temoignages      = models.CharField(max_length=100, default="Ils nous font confiance")
    titre_section_cta              = models.CharField(max_length=200, default="Prêt à transformer l'éducation en Afrique ?")
    sous_titre_section_cta         = models.CharField(max_length=300, default="Rejoignez la plus grande communauté éducative moderne", blank=True)

    # ── Paramètres formations ───────────────────────────────────────
    nb_formations_accueil  = models.IntegerField(default=6)
    nb_epreuves_accueil    = models.IntegerField(default=8)
    nb_ecoles_accueil      = models.IntegerField(default=6)
    formations_tri         = models.CharField(max_length=30, default='-date_publication',
        choices=[
            ('-date_publication', 'Plus récentes'),
            ('-nb_ventes',        'Plus vendues'),
            ('-note_moyenne',     'Mieux notées'),
        ]
    )
    afficher_formations_gratuites_badge = models.BooleanField(default=True)
    afficher_prix_formations            = models.BooleanField(default=True)
    afficher_note_formations            = models.BooleanField(default=True)
    afficher_nb_ventes_formations       = models.BooleanField(default=True)

    # ── Footer ──────────────────────────────────────────────────────
    footer_texte         = models.TextField(default="La plateforme qui connecte les écoles, formateurs et étudiants.", blank=True)
    footer_email_contact = models.EmailField(default="contact@academienet.cm", blank=True)
    footer_telephone     = models.CharField(max_length=30, blank=True, default="+237 6 XX XX XX XX")
    footer_adresse       = models.CharField(max_length=200, blank=True, default="Douala, Cameroun")
    footer_facebook      = models.URLField(blank=True, default="")
    footer_twitter       = models.URLField(blank=True, default="")
    footer_linkedin      = models.URLField(blank=True, default="")
    footer_youtube       = models.URLField(blank=True, default="")
    footer_instagram     = models.URLField(blank=True, default="")

    # ── Auto-publication formations ─────────────────────────────────
    auto_publication_active         = models.BooleanField(default=False)
    auto_publication_delai_minutes  = models.IntegerField(default=60)

    # ── Maintenance ─────────────────────────────────────────────────
    mode_maintenance     = models.BooleanField(default=False)
    message_maintenance  = models.TextField(default="Site en maintenance. Revenez bientôt.", blank=True)

    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration de la plateforme"
        verbose_name_plural = "Configuration de la plateforme"

    def __str__(self):
        return f"Configuration — {self.nom_site}"

    @classmethod
    def get_config(cls):
        config, _ = cls.objects.get_or_create(id=1)
        return config

class UtilisateurBloqueForum(models.Model):
    """Utilisateurs bloqués dans un forum"""
    forum = models.ForeignKey('Forum', on_delete=models.CASCADE, related_name='blocages')
    utilisateur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='blocages_forum')
    bloque_par = models.ForeignKey('Utilisateur', on_delete=models.SET_NULL, null=True, related_name='blocages_effectues')
    date_blocage = models.DateTimeField(auto_now_add=True)
    date_deblocage = models.DateTimeField(null=True, blank=True)  # ← AJOUTEZ CE CHAMP
    motif = models.TextField(blank=True, null=True)  # ← AJOUTEZ CE CHAMP
    
    class Meta:
        unique_together = ['forum', 'utilisateur']
        verbose_name = "Utilisateur bloqué"
        verbose_name_plural = "Utilisateurs bloqués"
    
    def __str__(self):
        return f"{self.utilisateur.username} bloqué dans {self.forum.nom}"

class DiapositiveHero(models.Model):
    """Diapositives du carrousel Hero sur la page d'accueil"""
    
    titre = models.CharField(max_length=200, verbose_name="Titre principal")
    sous_titre = models.CharField(max_length=200, blank=True, null=True, verbose_name="Sous-titre")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    image = models.ImageField(upload_to='hero/slides/', blank=True, null=True, verbose_name="Image")
    couleur_fond = models.CharField(max_length=20, default='#1e3a8a', verbose_name="Couleur de fond")
    
    bouton_texte = models.CharField(max_length=50, blank=True, null=True, verbose_name="Texte bouton 1")
    bouton_lien = models.CharField(max_length=200, blank=True, null=True, verbose_name="Lien bouton 1")
    
    bouton2_texte = models.CharField(max_length=50, blank=True, null=True, verbose_name="Texte bouton 2")
    bouton2_lien = models.CharField(max_length=200, blank=True, null=True, verbose_name="Lien bouton 2")
    
    ordre = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    
    date_debut = models.DateField(blank=True, null=True, verbose_name="Date de début (optionnel)")
    date_fin = models.DateField(blank=True, null=True, verbose_name="Date de fin (optionnel)")
    
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        ordering = ['ordre', '-date_creation']
        verbose_name = "Diapositive Hero"
        verbose_name_plural = "Diapositives Hero"
    
    def __str__(self):
        return self.titre


class Temoignage(models.Model):
    """Témoignages d'étudiants ou formateurs"""
    
    nom = models.CharField(max_length=100, verbose_name="Nom complet")
    role = models.CharField(max_length=100, blank=True, null=True, verbose_name="Rôle/Fonction")
    texte = models.TextField(verbose_name="Témoignage")
    note = models.IntegerField(default=5, choices=[(1, '★'), (2, '★★'), (3, '★★★'), (4, '★★★★'), (5, '★★★★★')], verbose_name="Note")
    
    avatar = models.ImageField(upload_to='temoignages/avatars/', blank=True, null=True, verbose_name="Avatar")
    
    ordre = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        ordering = ['ordre', '-date_creation']
        verbose_name = "Témoignage"
        verbose_name_plural = "Témoignages"
    
    def __str__(self):
        return f"{self.nom} - {self.note}★"


class Partenaire(models.Model):
    """Logos des partenaires (écoles, entreprises)"""
    
    nom = models.CharField(max_length=100, verbose_name="Nom du partenaire")
    logo = models.ImageField(upload_to='partenaires/logos/', verbose_name="Logo")
    url = models.URLField(blank=True, null=True, verbose_name="Lien du site")
    
    ordre = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Partenaire"
        verbose_name_plural = "Partenaires"
    
    def __str__(self):
        return self.nom


class BannierePromo(models.Model):
    """Bannière promotionnelle (affichée entre sections)"""
    
    texte = models.CharField(max_length=255, verbose_name="Texte de la bannière")
    lien = models.CharField(max_length=200, blank=True, null=True, verbose_name="Lien du bouton")
    
    couleur_fond = models.CharField(max_length=20, default='#f59e0b', verbose_name="Couleur de fond")
    couleur_texte = models.CharField(max_length=20, default='#1e3a8a', verbose_name="Couleur du texte")
    
    actif = models.BooleanField(default=True, verbose_name="Active")
    
    date_debut = models.DateField(blank=True, null=True, verbose_name="Date de début")
    date_fin = models.DateField(blank=True, null=True, verbose_name="Date de fin")
    
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        ordering = ['-actif', '-date_creation']
        verbose_name = "Bannière promotionnelle"
        verbose_name_plural = "Bannières promotionnelles"
    
    def __str__(self):
        return self.texte[:50]

# ==================== WISHLIST FORMATION ====================
class WishlistFormation(models.Model):
    """Formations sauvegardées en favoris par un utilisateur."""
    utilisateur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='wishlist')
    formation   = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='wishlist_items')
    date_ajout  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['utilisateur', 'formation']
        ordering = ['-date_ajout']
        verbose_name = "Wishlist"

    def __str__(self):
        return f"{self.utilisateur.username} ♥ {self.formation.titre}"


# ==================== MODULE DE FORMATION ====================
class ModuleFormation(models.Model):
    """Section / chapitre regroupant des fichiers."""
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='modules')
    titre     = models.CharField(max_length=200)
    ordre     = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordre']

    def __str__(self):
        return f"{self.formation.titre} — {self.titre}"


# ==================== FICHIER FORMATION (étendu) ====================
class FichierFormation(models.Model):
    TYPE_VIDEO    = 'video'
    TYPE_PDF      = 'pdf'
    TYPE_DOC      = 'document'
    TYPE_AUDIO    = 'audio'
    TYPE_AUTRE    = 'autre'

    TYPE_CHOICES = [
        (TYPE_VIDEO,  'Vidéo'),
        (TYPE_PDF,    'PDF'),
        (TYPE_DOC,    'Document (Word, etc.)'),
        (TYPE_AUDIO,  'Audio / Podcast'),
        (TYPE_AUTRE,  'Autre'),
    ]

    formation    = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='fichiers')
    module       = models.ForeignKey(ModuleFormation, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='fichiers')
    fichier      = models.FileField(upload_to='formations/fichiers/')
    titre        = models.CharField(max_length=200)
    type_fichier = models.CharField(max_length=20, choices=TYPE_CHOICES)
    taille       = models.BigIntegerField(default=0, help_text="Taille en octets")
    duree_secondes = models.PositiveIntegerField(default=0, help_text="Durée vidéo/audio en secondes")
    est_apercu   = models.BooleanField(default=False, verbose_name="Aperçu gratuit (accessible sans achat)")
    ordre        = models.PositiveIntegerField(default=0)
    date_ajout   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre']

    def __str__(self):
        return f"{self.titre} ({self.get_type_fichier_display()})"

    @property
    def duree_formatee(self):
        if not self.duree_secondes:
            return ''
        h, r = divmod(self.duree_secondes, 3600)
        m, s = divmod(r, 60)
        if h:
            return f"{h}h{m:02d}"
        return f"{m}:{s:02d}"


# ==================== PROGRESSION APPRENANT ====================
class ProgressionFormation(models.Model):
    """Suivi de progression d'un apprenant dans une formation."""
    apprenant    = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='progressions_formations')
    formation    = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='progressions')
    fichiers_vus = models.ManyToManyField(FichierFormation, blank=True)
    date_debut   = models.DateTimeField(auto_now_add=True)
    date_derniere_activite = models.DateTimeField(auto_now=True)
    terminee     = models.BooleanField(default=False)
    date_fin     = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['apprenant', 'formation']

    @property
    def pourcentage(self):
        total = self.formation.fichiers.count()
        if total == 0:
            return 0
        vus = self.fichiers_vus.count()
        return int((vus / total) * 100)

    def __str__(self):
        return f"{self.apprenant.username} — {self.formation.titre} ({self.pourcentage}%)"


# ==================== CERTIFICAT ====================
class CertificatFormation(models.Model):
    """Certificat de completion délivré après avoir fini une formation."""
    apprenant   = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='certificats')
    formation   = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='certificats')
    code_unique = models.CharField(max_length=32, unique=True, blank=True)
    date_obtenu = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['apprenant', 'formation']

    def save(self, *args, **kwargs):
        if not self.code_unique:
            self.code_unique = uuid.uuid4().hex[:16].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Certificat {self.code_unique} — {self.apprenant.username}"


class ConfigurationMessagerie(models.Model):
    """
    Configuration centralisée : messagerie privée + forums.
    Une seule ligne (id=1).
    """
    # ── Polling messagerie ──────────────────────────────────────────
    polling_actif              = models.BooleanField(default=True, verbose_name="Polling actif")
    intervalle_polling         = models.IntegerField(default=30, verbose_name="Intervalle (secondes)")
    pause_polling_onglet_inactif = models.BooleanField(default=True, verbose_name="Pause si onglet inactif")
    pause_polling_apres_heure  = models.BooleanField(default=False, verbose_name="Pause nocturne active")
    heure_debut_pause          = models.TimeField(null=True, blank=True, verbose_name="Début pause nocturne")
    heure_fin_pause            = models.TimeField(null=True, blank=True, verbose_name="Fin pause nocturne")
    adaptation_auto_intervalle = models.BooleanField(default=True, verbose_name="Adapter intervalle auto")
    min_intervalle_polling     = models.IntegerField(default=10, verbose_name="Intervalle min (s)")
    max_intervalle_polling     = models.IntegerField(default=120, verbose_name="Intervalle max (s)")
    max_messages_par_requete   = models.IntegerField(default=50)
    rate_limit_secondes        = models.IntegerField(default=1, verbose_name="Délai min entre envois (s)")
    message_polling_desactive  = models.TextField(
        default="La messagerie est en mode manuel. Actualisez pour voir les nouveaux messages.",
        verbose_name="Message si polling désactivé"
    )

    # ── Nettoyage ───────────────────────────────────────────────────
    supprimer_messages_apres_jours         = models.IntegerField(default=365)
    supprimer_conversations_vides_apres_jours = models.IntegerField(default=30)

    # ── Forums — paramètres globaux ─────────────────────────────────
    forums_actifs              = models.BooleanField(default=True, verbose_name="Forums activés")
    forum_plateforme_actif     = models.BooleanField(default=True, verbose_name="Forum général plateforme")
    forum_ecole_actif          = models.BooleanField(default=True, verbose_name="Forums d'école")
    forum_specialite_actif     = models.BooleanField(default=True, verbose_name="Forums de spécialité")

    sujet_jour_actif = models.BooleanField(default=False)
    forum_moderation_auto      = models.BooleanField(default=False, verbose_name="Modération auto (attendre validation)")
    forum_longueur_min_message = models.IntegerField(default=10, verbose_name="Longueur min message forum (caractères)")
    forum_longueur_max_message = models.IntegerField(default=5000, verbose_name="Longueur max message forum")
    forum_max_sujets_par_jour  = models.IntegerField(default=5, verbose_name="Max sujets créés par user/jour")
    forum_max_messages_par_jour = models.IntegerField(default=20, verbose_name="Max messages postés par user/jour")

    date_modification = models.DateTimeField(auto_now=True)
    forum_messages_par_page = models.IntegerField(default=20)
    
    class Meta:
        verbose_name = "Configuration messagerie & forums"

    def __str__(self):
        return "Configuration messagerie & forums"

    @classmethod
    def get_config(cls):
        config, _ = cls.objects.get_or_create(id=1)
        return config


# ==================== FORUMS ====================

class SignalementForum(models.Model):
    """Signalement d'un message ou sujet de forum."""
    MOTIF_CHOICES = [
        ('spam',       'Spam'),
        ('inapproprie','Contenu inapproprié'),
        ('hors_sujet', 'Hors sujet'),
        ('autre',      'Autre'),
    ]
    signaleur       = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='signalements_forum')
    message = models.ForeignKey('MessageForum', on_delete=models.CASCADE, null=True, blank=True)
    message         = models.ForeignKey(MessageForum, on_delete=models.CASCADE, null=True, blank=True)
    motif           = models.CharField(max_length=20, choices=MOTIF_CHOICES, default='autre')
    description     = models.TextField(blank=True)
    traite          = models.BooleanField(default=False)
    date_creation   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Signalement forum"

    def __str__(self):
        return f"Signalement {self.motif} par {self.signaleur.username}"
    
# ==================== FORUM SIMPLIFIÉ TYPE WHATSAPP ====================

class SujetDuJour(models.Model):
    """Sujet du jour pour un forum spécifique - affiché en haut du chat"""
    forum = models.ForeignKey('Forum', on_delete=models.CASCADE, related_name='sujets_jour')
    titre = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")
    date = models.DateField(verbose_name="Date")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    cree_par = models.ForeignKey('Utilisateur', on_delete=models.SET_NULL, null=True, verbose_name="Créé par")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['forum', 'date']
        ordering = ['-date']
        verbose_name = "Sujet du jour"
        verbose_name_plural = "Sujets du jour"
    
    def __str__(self):
        return f"{self.forum.nom} - {self.date} : {self.titre}"
    
# ==================== ABONNEMENT UTILISATEUR ET TRANSACTIONS ====================

class AbonnementUtilisateur(models.Model):
    """Abonnement d'un utilisateur (paiement mensuel/trimestriel)"""
    TYPE_CHOICES = [
        ('mensuel', 'Mensuel (500 FCFA)'),
        ('trimestriel', 'Trimestriel (1500 FCFA)'),
    ]
    
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('expire', 'Expiré'),
        ('annule', 'Annulé'),
        ('essai', 'Période d\'essai'),
    ]
    
    utilisateur = models.OneToOneField('Utilisateur', on_delete=models.CASCADE, related_name='abonnement_utilisateur')
    type_abonnement = models.CharField(max_length=20, choices=TYPE_CHOICES, default='mensuel')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='essai')
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin_essai = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    paiement_oblige = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Abonnement utilisateur"
        verbose_name_plural = "Abonnements utilisateurs"
    
    def est_actif(self):
        from django.utils import timezone
        
        if self.statut == 'actif' and self.date_fin and self.date_fin > timezone.now():
            return True
        
        if self.statut == 'essai' and self.date_fin_essai and self.date_fin_essai > timezone.now():
            return True
        
        return False  # ← Ce return doit être dans la méthode
    
    def jours_restants(self):
        from django.utils import timezone
        if self.statut == 'actif' and self.date_fin:
            delta = self.date_fin - timezone.now()
            return delta.days
        elif self.statut == 'essai' and self.date_fin_essai:
            delta = self.date_fin_essai - timezone.now()
            return delta.days
        return 0


class TransactionLog(models.Model):
    """Log de toutes les transactions"""
    TYPE_CHOICES = [
        ('abonnement', 'Abonnement'),
        ('formation', 'Achat formation'),
        ('epreuve', 'Achat épreuve'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('reussi', 'Réussi'),
        ('echoue', 'Échoué'),
        ('rembourse', 'Remboursé'),
    ]
    
    MOYEN_PAIEMENT_CHOICES = [
        ('orange_money', 'Orange Money'),
        ('mtn_money', 'MTN Money'),
        ('wave', 'Wave'),
        ('carte', 'Carte bancaire'),
    ]
    
    utilisateur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='transactions')
    type_transaction = models.CharField(max_length=20, choices=TYPE_CHOICES)
    montant = models.IntegerField()
    reference = models.CharField(max_length=100, unique=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    moyen_paiement = models.CharField(max_length=20, choices=MOYEN_PAIEMENT_CHOICES, blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    date_transaction = models.DateTimeField(auto_now_add=True)
    date_confirmation = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-date_transaction']
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.type_transaction} - {self.montant} FCFA - {self.statut}"
    
    

from django.db import models


class SauvegardeQCM(models.Model):
    """Sauvegarde automatique AJAX des réponses en cours."""
    etudiant        = models.ForeignKey('Utilisateur', on_delete=models.CASCADE)
    exercice        = models.ForeignKey(Exercice, on_delete=models.CASCADE)
    donnees_json    = models.JSONField(default=dict)
    date_sauvegarde = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['etudiant', 'exercice']
        verbose_name = "Sauvegarde QCM"

    def __str__(self):
        return f"Sauvegarde {self.etudiant.username} — {self.exercice.titre}"
    
# ==================== TEXTE À TROUS ====================
class TexteATrous(models.Model):
    """Un texte à trous est rattaché à un Exercice (type_exercice='texte_trous')."""
    exercice    = models.OneToOneField('Exercice', on_delete=models.CASCADE, related_name='texte_a_trous')
    texte_brut  = models.TextField(
        help_text="Utilisez {{1}}, {{2}}, etc. pour marquer les trous. "
                   "Ex: Le {{1}} est la capitale de la {{2}}."
    )

    class Meta:
        verbose_name = "Texte à trous"

    def __str__(self):
        return f"Texte à trous — {self.exercice.titre}"

    @property
    def nb_trous(self):
        return self.trous.count()


class TrouReponse(models.Model):
    """Bonne(s) réponse(s) attendue(s) pour un trou donné (numéro)."""
    texte_a_trous   = models.ForeignKey(TexteATrous, on_delete=models.CASCADE, related_name='trous')
    numero          = models.PositiveIntegerField(help_text="Correspond à {{N}} dans le texte")
    reponses_acceptees = models.TextField(
        help_text="Une réponse acceptée par ligne (insensible à la casse)"
    )
    points          = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['numero']
        unique_together = ['texte_a_trous', 'numero']
        verbose_name = "Réponse de trou"

    def __str__(self):
        return f"Trou #{self.numero} — {self.texte_a_trous.exercice.titre}"

    @property
    def liste_reponses(self):
        return [r.strip().lower() for r in self.reponses_acceptees.splitlines() if r.strip()]

    def verifier(self, reponse_soumise):
        return reponse_soumise.strip().lower() in self.liste_reponses


class ReponseTrouEtudiant(models.Model):
    """Réponse d'un étudiant à un trou spécifique."""
    soumission = models.ForeignKey('SoumissionExercice', on_delete=models.CASCADE, related_name='reponses_trous')
    trou       = models.ForeignKey(TrouReponse, on_delete=models.CASCADE)
    reponse_donnee = models.CharField(max_length=300, blank=True)
    est_correcte    = models.BooleanField(default=False)
    points_obtenus  = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Réponse trou étudiant"

    def __str__(self):
        return f"{self.soumission.etudiant.username} → Trou#{self.trou.numero}"


# ==================== RÉPONSE COURTE ====================
class QuestionReponseCourte(models.Model):
    """Question à réponse courte (texte libre, comparé à une liste de réponses acceptées)."""
    exercice    = models.ForeignKey('Exercice', on_delete=models.CASCADE, related_name='questions_courtes')
    texte       = models.TextField()
    image       = models.ImageField(upload_to='exercices/reponse_courte/', blank=True, null=True)
    reponses_acceptees = models.TextField(
        help_text="Une réponse acceptée par ligne (insensible à la casse et aux accents)"
    )
    sensible_casse = models.BooleanField(default=False, help_text="Respecter majuscules/minuscules")
    explication = models.TextField(blank=True)
    ordre       = models.PositiveIntegerField(default=0)
    points      = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Question réponse courte"

    def __str__(self):
        return f"RC{self.ordre} — {self.exercice.titre}"

    @property
    def liste_reponses(self):
        if self.sensible_casse:
            return [r.strip() for r in self.reponses_acceptees.splitlines() if r.strip()]
        return [r.strip().lower() for r in self.reponses_acceptees.splitlines() if r.strip()]

    def verifier(self, reponse_soumise):
        import unicodedata
        def normaliser(s):
            s = s.strip()
            if not self.sensible_casse:
                s = s.lower()
            return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
        cible = normaliser(reponse_soumise)
        acceptees = [normaliser(r) for r in self.liste_reponses]
        return cible in acceptees


class ReponseCourteEtudiant(models.Model):
    soumission     = models.ForeignKey('SoumissionExercice', on_delete=models.CASCADE, related_name='reponses_courtes')
    question       = models.ForeignKey(QuestionReponseCourte, on_delete=models.CASCADE)
    reponse_donnee = models.CharField(max_length=500, blank=True)
    est_correcte   = models.BooleanField(default=False)
    points_obtenus = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Réponse courte étudiant"

    def __str__(self):
        return f"{self.soumission.etudiant.username} → {self.question}"


# ==================== RÉDACTION ====================
class ConsigneRedaction(models.Model):
    """Une rédaction = un sujet + critères d'évaluation, correction manuelle."""
    exercice         = models.OneToOneField('Exercice', on_delete=models.CASCADE, related_name='redaction')
    sujet            = models.TextField()
    nb_mots_min      = models.PositiveIntegerField(default=0, help_text="0 = pas de minimum")
    nb_mots_max      = models.PositiveIntegerField(default=0, help_text="0 = pas de maximum")
    criteres_evaluation = models.TextField(
        blank=True, help_text="Un critère par ligne, ex: Orthographe (4pts), Structure (3pts)..."
    )
    document_ressource = models.FileField(upload_to='exercices/redaction/', blank=True, null=True)

    class Meta:
        verbose_name = "Consigne de rédaction"

    def __str__(self):
        return f"Rédaction — {self.exercice.titre}"

    @property
    def liste_criteres(self):
        return [c.strip() for c in self.criteres_evaluation.splitlines() if c.strip()]


class ReponseRedaction(models.Model):
    """Texte rédigé par l'étudiant — correction manuelle obligatoire."""
    soumission     = models.OneToOneField('SoumissionExercice', on_delete=models.CASCADE, related_name='redaction_reponse')
    texte_redige   = models.TextField(blank=True)
    nb_mots        = models.PositiveIntegerField(default=0)
    note_donnee    = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    commentaire_correcteur = models.TextField(blank=True)
    corrige_par    = models.ForeignKey('Utilisateur', on_delete=models.SET_NULL, null=True, blank=True,
                          related_name='redactions_corrigees')
    date_correction = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Réponse rédaction"

    def __str__(self):
        return f"Rédaction de {self.soumission.etudiant.username}"

    def save(self, *args, **kwargs):
        if self.texte_redige:
            self.nb_mots = len(self.texte_redige.split())
        super().save(*args, **kwargs)

    @property
    def est_corrigee(self):
        return self.note_donnee is not None


# ==================== DÉPÔT DE FICHIER ====================
class ConsigneDepotFichier(models.Model):
    """Exercice nécessitant le dépôt d'un fichier (PDF, image, doc, zip...)."""
    exercice          = models.OneToOneField('Exercice', on_delete=models.CASCADE, related_name='depot_fichier')
    instructions      = models.TextField()
    extensions_autorisees = models.CharField(
        max_length=200, default="pdf,doc,docx,jpg,png,zip",
        help_text="Extensions séparées par des virgules, sans le point"
    )
    taille_max_mo     = models.PositiveIntegerField(default=10)
    nb_fichiers_max   = models.PositiveIntegerField(default=1)
    document_ressource = models.FileField(upload_to='exercices/depot/ressources/', blank=True, null=True)
    grille_correction = models.TextField(blank=True, help_text="Un critère par ligne")

    class Meta:
        verbose_name = "Consigne dépôt fichier"

    def __str__(self):
        return f"Dépôt fichier — {self.exercice.titre}"

    @property
    def liste_extensions(self):
        return [e.strip().lower() for e in self.extensions_autorisees.split(',') if e.strip()]


def _depot_etudiant_upload_path(instance, filename):
    return f"exercices/depot/reponses/{instance.soumission.exercice_id}/{instance.soumission.etudiant_id}/{filename}"


class FichierDepose(models.Model):
    """Un fichier déposé par l'étudiant (peut y en avoir plusieurs)."""
    soumission     = models.ForeignKey('SoumissionExercice', on_delete=models.CASCADE, related_name='fichiers_deposes')
    fichier        = models.FileField(upload_to=_depot_etudiant_upload_path)
    nom_original   = models.CharField(max_length=255, blank=True)
    taille         = models.BigIntegerField(default=0)
    date_depot     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fichier déposé"
        ordering = ['date_depot']

    def __str__(self):
        return f"{self.nom_original} — {self.soumission.etudiant.username}"


class CorrectionDepotFichier(models.Model):
    """Note et commentaire pour un dépôt de fichier — correction manuelle."""
    soumission      = models.OneToOneField('SoumissionExercice', on_delete=models.CASCADE, related_name='correction_depot')
    note_donnee     = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    commentaire     = models.TextField(blank=True)
    fichier_annote  = models.FileField(upload_to='exercices/depot/annotations/', blank=True, null=True)
    corrige_par     = models.ForeignKey('Utilisateur', on_delete=models.SET_NULL, null=True, blank=True,
                          related_name='depots_corriges')
    date_correction = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Correction dépôt fichier"

    def __str__(self):
        return f"Correction — {self.soumission.etudiant.username}"

    @property
    def est_corrigee(self):
        return self.note_donnee is not None


# ==================== ÉTUDE DE CAS ====================
class EtudeCas(models.Model):
    """
    Étude de cas = un scénario / contexte détaillé + une série de
    sous-questions de différents types (texte libre, QCM, fichier).
    """
    exercice      = models.OneToOneField('Exercice', on_delete=models.CASCADE, related_name='etude_cas')
    contexte      = models.TextField(help_text="Présentation du cas / scénario")
    document_cas  = models.FileField(upload_to='exercices/etude_cas/', blank=True, null=True)
    image_cas     = models.ImageField(upload_to='exercices/etude_cas/images/', blank=True, null=True)

    class Meta:
        verbose_name = "Étude de cas"

    def __str__(self):
        return f"Étude de cas — {self.exercice.titre}"

    @property
    def nb_sous_questions(self):
        return self.sous_questions.count()


class SousQuestionEtudeCas(models.Model):
    TYPE_TEXTE = 'texte_libre'
    TYPE_QCM   = 'qcm'

    TYPE_CHOICES = [
        (TYPE_TEXTE, 'Texte libre (correction manuelle)'),
        (TYPE_QCM,   'QCM (correction auto)'),
    ]

    etude_cas    = models.ForeignKey(EtudeCas, on_delete=models.CASCADE, related_name='sous_questions')
    texte        = models.TextField()
    type_question = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_TEXTE)
    ordre        = models.PositiveIntegerField(default=0)
    points       = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Sous-question étude de cas"

    def __str__(self):
        return f"SQ{self.ordre} — {self.etude_cas.exercice.titre}"


class ChoixSousQuestionEtudeCas(models.Model):
    """Choix possibles si la sous-question est de type QCM."""
    sous_question = models.ForeignKey(SousQuestionEtudeCas, on_delete=models.CASCADE, related_name='choix')
    texte         = models.CharField(max_length=500)
    est_correct   = models.BooleanField(default=False)
    ordre         = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Choix sous-question"

    def __str__(self):
        return self.texte[:50]


class ReponseSousQuestionEtudeCas(models.Model):
    soumission     = models.ForeignKey('SoumissionExercice', on_delete=models.CASCADE, related_name='reponses_etude_cas')
    sous_question  = models.ForeignKey(SousQuestionEtudeCas, on_delete=models.CASCADE)
    reponse_texte  = models.TextField(blank=True)
    choix_selectionne = models.ForeignKey(ChoixSousQuestionEtudeCas, on_delete=models.SET_NULL, null=True, blank=True)
    est_correcte   = models.BooleanField(default=False)
    points_obtenus = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Réponse sous-question étude de cas"

    def __str__(self):
        return f"{self.soumission.etudiant.username} → SQ{self.sous_question.ordre}"


# =====================================================================
# website/models.py — CORRECTIONS POUR LES 4 TYPES DE LEÇON (SeanceBase)
# =====================================================================
# ==================== SÉANCE DE CORRECTION (NOUVEAU) ====================
class SeanceCorrection(models.Model):
    """
    Configuration d'une séance de type 'correction' : permet à
    l'enseignant de lier la séance qu'elle corrige, publier un corrigé
    (texte/fichier/vidéo), et débriefer les devoirs/exercices soumis.
    """
    seance              = models.OneToOneField('SeanceBase', on_delete=models.CASCADE, related_name='seance_correction')
    seance_corrigee     = models.ForeignKey('SeanceBase', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='corrections_associees',
                              help_text="La séance (devoir/exercice) que cette correction couvre")
    corrige_texte       = models.TextField(blank=True, help_text="Corrigé rédigé directement")
    corrige_fichier     = models.FileField(upload_to='seances/corrections/fichiers/', blank=True, null=True)
    corrige_video_url   = models.URLField(blank=True, help_text="Lien vidéo de correction (YouTube, etc.)")
    points_cles         = models.TextField(blank=True, help_text="Un point clé par ligne")
    publie              = models.BooleanField(default=False)
    date_publication    = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Configuration séance de correction"

    def __str__(self):
        return f"Correction — {self.seance.titre}"

    def publier(self):
        self.publie = True
        self.date_publication = timezone.now()
        self.save(update_fields=['publie', 'date_publication'])

    @property
    def liste_points_cles(self):
        return [p.strip() for p in self.points_cles.splitlines() if p.strip()]

    @property
    def a_du_contenu(self):
        return bool(self.corrige_texte or self.corrige_fichier or self.corrige_video_url)


class VueCorrectionEtudiant(models.Model):
    """Trace qu'un étudiant a consulté la correction (pour les stats)."""
    correction  = models.ForeignKey(SeanceCorrection, on_delete=models.CASCADE, related_name='vues')
    etudiant    = models.ForeignKey('Utilisateur', on_delete=models.CASCADE)
    date_vue    = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['correction', 'etudiant']
        verbose_name = "Vue correction étudiant"

    def __str__(self):
        return f"{self.etudiant.username} a vu la correction de {self.correction.seance.titre}"

class RessourceSeance(models.Model):
    """Ressource d'une séance asynchrone (fichier ou lien)"""
    TYPE_FICHIER = 'fichier'
    TYPE_LIEN = 'lien'
    
    TYPE_CHOICES = [
        (TYPE_FICHIER, 'Fichier'),
        (TYPE_LIEN, 'Lien externe'),
    ]
    
    seance = models.ForeignKey('SeanceBase', on_delete=models.CASCADE, related_name='ressources')
    type_ressource = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_FICHIER)
    fichier = models.FileField(upload_to='seances/ressources/', blank=True, null=True)
    nom_fichier = models.CharField(max_length=255, blank=True)
    taille_fichier = models.IntegerField(default=0)
    format_fichier = models.CharField(max_length=20, blank=True)
    url = models.URLField(blank=True, null=True)
    titre = models.CharField(max_length=200, blank=True)
    ordre = models.IntegerField(default=0)
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['ordre', 'date_ajout']
        verbose_name = "Ressource de séance"
    
    def __str__(self):
        return self.titre or self.nom_fichier or "Ressource"

# ============================================
# DEMANDES FORMATEUR
# ============================================

class DemandeFormateur(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('refuse', 'Refusé'),
    ]
    
    utilisateur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='demandes_formateur')
    domaine = models.CharField(max_length=255, help_text="Domaine d'expertise")
    experience = models.TextField(help_text="Description de l'expérience")
    document = models.FileField(upload_to='demandes/formateurs/', help_text="Justificatif d'expérience")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    commentaire = models.TextField(blank=True, null=True, help_text="Commentaire de l'équipe technique")
    date_demande = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    traite_par = models.ForeignKey('Utilisateur', on_delete=models.SET_NULL, null=True, blank=True, related_name='demandes_formateur_traitees')
    
    class Meta:
        ordering = ['-date_demande']
        verbose_name = "Demande de formateur"
        verbose_name_plural = "Demandes de formateurs"
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.domaine} ({self.statut})"
    
    def accepter(self, admin, commentaire=None):
        self.statut = 'valide'
        self.commentaire = commentaire
        self.date_traitement = timezone.now()
        self.traite_par = admin
        self.save()
        # Changer le rôle de l'utilisateur
        self.utilisateur.role = 'enseignant'
        self.utilisateur.save()
    
    def refuser(self, admin, commentaire):
        self.statut = 'refuse'
        self.commentaire = commentaire
        self.date_traitement = timezone.now()
        self.traite_par = admin
        self.save()


# ============================================
# PARAMÈTRES - DEMANDES FORMATEUR
# ============================================

class ParametresDemandesFormateur(models.Model):
    """Paramètres modifiables par l'équipe technique"""
    
    # Règles
    regles_texte = models.TextField(
        default="Pour devenir formateur sur Academia Net, vous devez :\n- Avoir une expérience dans le domaine d'enseignement\n- Fournir un justificatif d'expérience (attestation, diplôme, CV, etc.)\n- Valider votre email et numéro de téléphone\n- Accepter les conditions générales de la plateforme\n- Les demandes sont traitées sous 48h",
        help_text="Texte des règles affiché sur la page devenir formateur"
    )
    
    # Délai de traitement
    delai_traitement_heures = models.PositiveIntegerField(default=48, help_text="Délai de traitement en heures")
    
    # Documents acceptés
    extensions_autorisees = models.CharField(
        max_length=200,
        default="pdf,doc,docx,jpg,png,jpeg",
        help_text="Extensions séparées par des virgules"
    )
    
    # Taille max des documents (en Mo)
    taille_max_mo = models.PositiveIntegerField(default=10, help_text="Taille maximale en Mo")
    
    # Messages
    message_acceptation = models.TextField(
        default="Félicitations ! Votre demande pour devenir formateur sur Academia Net a été acceptée. Vous pouvez maintenant créer des cours, vendre des formations et gérer vos étudiants. Veuillez vous déconnecter et vous reconnecter pour activer votre rôle d'enseignant.",
        help_text="Message envoyé par email en cas d'acceptation"
    )
    
    message_refus = models.TextField(
        default="Nous vous remercions pour votre intérêt. Après examen, votre demande n'a pas été retenue. N'hésitez pas à refaire une demande ultérieurement.",
        help_text="Message envoyé par email en cas de refus"
    )
    
    # WhatsApp
    whatsapp_number = models.CharField(
        max_length=20,
        default="237691234567",
        help_text="Numéro WhatsApp pour le support (sans le +)"
    )
    
    # Activation
    demandes_actives = models.BooleanField(default=True, help_text="Activer/désactiver les demandes de formateur")
    
    class Meta:
        verbose_name = "Paramètres des demandes formateur"
        verbose_name_plural = "Paramètres des demandes formateur"
    
    def __str__(self):
        return "Paramètres des demandes formateur"
    
    @classmethod
    def get_config(cls):
        config, _ = cls.objects.get_or_create(id=1)
        return config