import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, FileExtensionValidator
from django.utils.text import slugify
from django.utils import timezone

# ==================== MODÈLE UTILISATEUR ====================
class Utilisateur(AbstractUser):
    # Types d'utilisateurs
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
    
    # Champs supplémentaires
    prenom = models.CharField(max_length=100, verbose_name='Prénom')
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Numéro de téléphone')
    pays = models.CharField(max_length=100, blank=True, null=True, verbose_name='Pays')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True, verbose_name='Rôle')
    email_valide = models.BooleanField(default=False, verbose_name='Email validé')
    date_inscription = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    
    def __str__(self):
        return f"{self.prenom} {self.username} - {self.get_role_display()}"


# ==================== MODÈLE ABONNEMENT ====================
class Abonnement(models.Model):
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom du pack")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    # Limites
    max_etudiants = models.IntegerField(default=100, verbose_name="Nombre max d'étudiants")
    max_cours = models.IntegerField(default=50, verbose_name="Nombre max de cours")
    stockage_gb = models.IntegerField(default=5, verbose_name="Stockage (GB)")
    ordre = models.IntegerField(default=0, verbose_name="Ordre d'affichage (plus grand = en haut)")
    
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-ordre', '-date_creation']
    
    def __str__(self):
        return f"{self.nom} - {self.max_etudiants} étudiants max"


# ==================== MODÈLE ÉCOLE ====================
class Ecole(models.Model):
    nom = models.CharField(max_length=200, unique=True, verbose_name="Nom de l'école")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Identifiant URL")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name="Logo")
    description = models.TextField(verbose_name="Description")
    
    # Contact et localisation
    email = models.EmailField(verbose_name="Email de contact")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    ville = models.CharField(max_length=100, verbose_name="Ville")
    pays = models.CharField(max_length=100, default="Cameroun", verbose_name="Pays")
    quartier = models.CharField(max_length=200, blank=True, null=True, verbose_name="Quartier")
    
    # Agrément
    numero_agrement = models.CharField(max_length=100, blank=True, null=True, verbose_name="Numéro d'agrément")
    agrement_valide = models.BooleanField(default=False, verbose_name="Agrément validé")
    
    # Abonnement
    abonnement = models.ForeignKey(Abonnement, on_delete=models.SET_NULL, null=True, verbose_name="Pack d'abonnement")
    
    # Gestion
    actif = models.BooleanField(default=True, verbose_name="École active")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    # Réseaux sociaux
    facebook = models.URLField(blank=True, null=True, verbose_name="Facebook")
    twitter = models.URLField(blank=True, null=True, verbose_name="Twitter")
    instagram = models.URLField(blank=True, null=True, verbose_name="Instagram")
    youtube = models.URLField(blank=True, null=True, verbose_name="YouTube")
    linkedin = models.URLField(blank=True, null=True, verbose_name="LinkedIn")

    # Images
    banniere = models.ImageField(upload_to='ecoles/bannieres/', blank=True, null=True, verbose_name="Bannière")
    
    # Admin de l'école (l'utilisateur qui gère cette école)
    admin_ecole = models.OneToOneField(
        Utilisateur, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='ecole_admin',
        verbose_name="Administrateur de l'école"
    )
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nom


# ==================== MODÈLE ENSEIGNANT (relation) ====================
class EnseignantEcole(models.Model):
    enseignant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='enseignant_ecoles')
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, related_name='enseignants')
    date_affectation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['enseignant', 'ecole']
    
    def __str__(self):
        return f"{self.enseignant.prenom} {self.enseignant.username} - {self.ecole.nom}"


# ==================== MODÈLE FILIÈRE ====================
class Filiere(models.Model):
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, related_name='filieres')
    nom = models.CharField(max_length=100, verbose_name="Nom de la filière")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    ordre = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    public = models.BooleanField(default=True, verbose_name="Afficher sur la page publique")
    
    class Meta:
        unique_together = ['ecole', 'nom']
        ordering = ['ordre', 'nom']
    
    def __str__(self):
        return f"{self.ecole.nom} - {self.nom}"


# ==================== MODÈLE SPÉCIALITÉ (contient le niveau) ====================
class Specialite(models.Model):
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='specialites')
    nom = models.CharField(max_length=100, verbose_name="Nom de la spécialité (ex: Réseaux Niveau 1)")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    # Clé d'inscription unique pour cette spécialité
    cle_inscription = models.CharField(max_length=50, unique=True, blank=True, verbose_name="Clé d'inscription")
    
    ordre = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    
    class Meta:
        unique_together = ['filiere', 'nom']
        ordering = ['ordre', 'nom']
    
    def save(self, *args, **kwargs):
        if not self.cle_inscription:
            # Générer une clé unique
            self.cle_inscription = f"{slugify(self.filiere.ecole.nom)}_{slugify(self.filiere.nom)}_{slugify(self.nom)}_{uuid.uuid4().hex[:8]}".upper()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.filiere.nom} - {self.nom}"


# ==================== MODÈLE INSCRIPTION ÉTUDIANT (avec clé) ====================
class InscriptionEtudiant(models.Model):
    etudiant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='inscriptions')
    specialite = models.ForeignKey(Specialite, on_delete=models.CASCADE, related_name='inscriptions')
    date_inscription = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['etudiant', 'specialite']
    
    def __str__(self):
        return f"{self.etudiant.prenom} {self.etudiant.username} - {self.specialite.nom}"


# ==================== MODÈLE COURS ====================
class Cours(models.Model):
    """Un cours regroupant plusieurs séances"""
    specialite = models.ForeignKey('Specialite', on_delete=models.CASCADE, related_name='cours')
    titre = models.CharField(max_length=200, verbose_name="Titre du cours")
    description = models.TextField(verbose_name="Description")
    image = models.ImageField(upload_to='cours/images/', blank=True, null=True, verbose_name="Image du cours")
    ordre = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    actif = models.BooleanField(default=True, verbose_name="Cours actif")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['ordre', 'date_creation']
    
    def __str__(self):
        return f"{self.titre} - {self.specialite.nom}"



# ==================== MODÈLE FORUM ====================
class SujetForum(models.Model):
    FORUM_ECOLE = 'ecole'
    FORUM_SPECIALITE = 'specialite'
    
    TYPE_CHOICES = [
        (FORUM_ECOLE, 'Forum École'),
        (FORUM_SPECIALITE, 'Forum Spécialité'),
        
    ]
    
    
    type_forum = models.CharField(max_length=20, choices=TYPE_CHOICES)
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, null=True, blank=True, related_name='sujets_forum')
    specialite = models.ForeignKey(Specialite, on_delete=models.CASCADE, null=True, blank=True, related_name='sujets_forum')
    
    titre = models.CharField(max_length=200, verbose_name="Titre du sujet")
    contenu = models.TextField(verbose_name="Contenu")
    auteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='sujets_forum')
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.titre} - {self.auteur.username}"


class MessageForum(models.Model):
    sujet = models.ForeignKey(SujetForum, on_delete=models.CASCADE, related_name='messages')
    contenu = models.TextField(verbose_name="Message")
    auteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='messages_forum')
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date_creation']
    
    def __str__(self):
        return f"{self.auteur.username} - {self.date_creation.strftime('%d/%m/%Y %H:%M')}"


# ==================== MODÈLE CHAT PRIVÉ ====================
class Conversation(models.Model):
    participants = models.ManyToManyField(Utilisateur, related_name='conversations')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_modification']
    
    def __str__(self):
        participants_noms = ", ".join([p.username for p in self.participants.all()])
        return f"Conversation entre {participants_noms}"


class MessagePrive(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    expediteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='messages_envoyes')
    contenu = models.TextField(verbose_name="Message")
    lu = models.BooleanField(default=False, verbose_name="Lu")
    date_envoi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date_envoi']
    
    def __str__(self):
        return f"{self.expediteur.username}: {self.contenu[:50]}"


# ==================== MODÈLE NOTIFICATION ====================
class Notification(models.Model):
    TYPE_RAPPEL_COURS = 'rappel_cours'
    TYPE_NOUVEAU_COURS = 'nouveau_cours'
    TYPE_NOUVEAU_MESSAGE = 'nouveau_message'
    TYPE_REPONSE_FORUM = 'reponse_forum'
    
    TYPE_CHOICES = [
        (TYPE_RAPPEL_COURS, 'Rappel de cours'),
        (TYPE_NOUVEAU_COURS, 'Nouveau cours'),
        (TYPE_NOUVEAU_MESSAGE, 'Nouveau message'),
        (TYPE_REPONSE_FORUM, 'Réponse sur le forum'),
    ]
    
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications')
    type_notification = models.CharField(max_length=50, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=200, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    lien = models.CharField(max_length=500, blank=True, null=True, verbose_name="Lien")
    lu = models.BooleanField(default=False, verbose_name="Lue")
    email_envoye = models.BooleanField(default=False, verbose_name="Email envoyé")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_creation']
  # ==================== QUIZ ====================
class Quiz(models.Model):
    seance = models.ForeignKey('SeanceProgrammee', on_delete=models.CASCADE, related_name='quizs_de_la_seance')
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date_limite = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resultats_publies = models.BooleanField(default=False)
    date_publication = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.titre

# ==================== MODÈLE SÉANCE ====================
class Seance(models.Model):
    TYPE_CHOICES = [
        ('fichier', 'Fichier (Document)'),
        ('visio', 'Visio-conférence'),
        ('quiz', 'Quiz'),
        ('devoir', 'Devoir'),
    ]
    
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='seances')
    titre = models.CharField(max_length=200, verbose_name="Titre de la séance")
    description = models.TextField(blank=True, null=True)
    type_seance = models.CharField(max_length=20, choices=TYPE_CHOICES)
    jour = models.CharField(max_length=20, blank=True, null=True)
    heure = models.TimeField(blank=True, null=True)
    fichier = models.FileField(upload_to='cours/fichiers/', blank=True, null=True)
    lien_video = models.URLField(blank=True, null=True)
    lien_visio = models.URLField(blank=True, null=True)
    visio_date = models.DateTimeField(blank=True, null=True)
    visio_enregistrement = models.FileField(upload_to='cours/enregistrements/', blank=True, null=True)
    quiz = models.ForeignKey('Quiz', on_delete=models.SET_NULL, blank=True, null=True, related_name='seances_quiz')
    #devoir = models.ForeignKey('Devoir', on_delete=models.SET_NULL, blank=True, null=True, related_name='seances_associees')
    ordre = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['ordre', 'visio_date', 'heure']
    
    def __str__(self):
        return f"{self.titre} ({self.get_type_seance_display()})"


# ==================== MODÈLE QUESTION ====================
class Question(models.Model):
    TYPE_CHOICES = [
        ('qcm', 'Choix multiples'),
        ('vrai_faux', 'Vrai/Faux'),
        ('reponse_courte', 'Réponse courte'),
        ('numerique', 'Numérique'),
        ('appariement', 'Appariement'),
        ('redaction', 'Rédaction'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    type_question = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type de question")
    enonce = models.TextField(verbose_name="Énoncé de la question")
    points = models.FloatField(default=1, verbose_name="Points")
    ordre = models.IntegerField(default=0, verbose_name="Ordre")
    
    # Pour les questions avec feedback spécifique
    feedback_general = models.TextField(blank=True, null=True, verbose_name="Feedback général")
    
    # Pour les questions avec variables aléatoires (calculées)
    template = models.JSONField(blank=True, null=True, verbose_name="Template pour questions aléatoires")
    
    class Meta:
        ordering = ['ordre']
    
    def __str__(self):
        return f"{self.quiz.titre} - {self.enonce[:50]}"


# ==================== MODÈLE RÉPONSE POSSIBLE ====================
class ReponsePossible(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='reponses')
    texte = models.TextField(verbose_name="Texte de la réponse")
    est_correcte = models.BooleanField(default=False, verbose_name="Est correcte")
    feedback = models.TextField(blank=True, null=True, verbose_name="Feedback spécifique")
    ordre = models.IntegerField(default=0, verbose_name="Ordre")
    
    class Meta:
        ordering = ['ordre']
    
    def __str__(self):
        return f"{self.texte[:50]} - {'Correct' if self.est_correcte else 'Incorrect'}"


# ==================== MODÈLE TENTATIVE QUIZ ====================
class TentativeQuiz(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='tentatives')
    etudiant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='tentatives_quiz')
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(blank=True, null=True)
    note = models.FloatField(blank=True, null=True, verbose_name="Note obtenue")
    tentative_numero = models.IntegerField(default=1, verbose_name="Numéro de tentative")
    
    class Meta:
        unique_together = ['quiz', 'etudiant', 'tentative_numero']
    
    def __str__(self):
        return f"{self.etudiant.username} - {self.quiz.titre} - Tentative {self.tentative_numero}"


# ==================== MODÈLE RÉPONSE ÉTUDIANT ====================
class ReponseEtudiant(models.Model):
    tentative = models.ForeignKey(TentativeQuiz, on_delete=models.CASCADE, related_name='reponses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    reponse_texte = models.TextField(blank=True, null=True, verbose_name="Réponse texte")
    reponse_id = models.IntegerField(blank=True, null=True, verbose_name="ID de la réponse choisie")
    est_correcte = models.BooleanField(default=False, verbose_name="Est correcte")
    points_obtenus = models.FloatField(default=0, verbose_name="Points obtenus")
    feedback = models.TextField(blank=True, null=True, verbose_name="Feedback personnalisé")
    
    def __str__(self):
        return f"{self.tentative.etudiant.username} - {self.question.enonce[:50]}"


# ==================== MODÈLE GROUPE DEVOIR ====================
class GroupeDevoir(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom du groupe")
    membres = models.ManyToManyField(Utilisateur, related_name='groupes_devoir')
    date_creation = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.devoir.titre} - {self.nom}"



# ==================== MODÈLE PROGRESSION ÉTUDIANT ====================
class ProgressionEtudiant(models.Model):
    """Suivi de la progression de l'étudiant dans un cours"""
    etudiant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='progressions')
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='progressions')
    seance_terminees = models.ManyToManyField(Seance, blank=True, related_name='terminee_par')
    date_debut = models.DateTimeField(auto_now_add=True)
    date_derniere_activite = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['etudiant', 'cours']
    
    def __str__(self):
        return f"{self.etudiant.username} - {self.cours.titre}"
    
    @property
    def progression(self):
        total = self.cours.seances.count()
        if total == 0:
            return 0
        terminees = self.seance_terminees.count()
        return int((terminees / total) * 100)
      
class ImageEcole(models.Model):
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, related_name='galerie_images')
    image = models.ImageField(upload_to='ecoles/galerie/')
    titre = models.CharField(max_length=200, blank=True, null=True)
    ordre = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['ordre']    
        
class ImageEcole(models.Model):
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, related_name='galerie_images')
    image = models.ImageField(upload_to='ecoles/galerie/')
    titre = models.CharField(max_length=200, blank=True, null=True)
    ordre = models.IntegerField(default=0)
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['ordre', '-date_ajout']
    
    def __str__(self):
        return f"{self.ecole.nom} - {self.titre or 'Image'}" 

# ==================== NOUVEAUX MODÈLES POUR LES COURS (ÉVITE LES CONFLITS) ====================

class CoursProgramme(models.Model):
    specialite = models.ForeignKey('Specialite', on_delete=models.CASCADE, related_name='cours_programmes')
    titre = models.CharField(max_length=200, verbose_name="Titre du cours")
    description = models.TextField(verbose_name="Description")
    objectifs = models.TextField(blank=True, null=True, verbose_name="Objectifs pédagogiques")  # ← NOUVEAU
    enseignant = models.ForeignKey('Utilisateur', on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='cours_assignes', limit_choices_to={'role': 'enseignant'},
                                   verbose_name="Enseignant responsable")
    actif = models.BooleanField(default=True, verbose_name="Cours actif")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(blank=True, null=True, verbose_name="Date de fin")
    created_by = models.ForeignKey('Utilisateur', on_delete=models.SET_NULL, null=True, 
                                   related_name='cours_crees', verbose_name="Créé par")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
    ]
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_cours', verbose_name="Statut du cours")  # ← NOUVEAU
    
    MODE_RECURRENT = 'recurrent'
    MODE_PERSONNALISE = 'personnalise'
    MODE_CHOICES = [
        (MODE_RECURRENT, 'Hebdomadaire récurrent'),
        (MODE_PERSONNALISE, 'Personnalisé par semaine'),
    ]
    mode_programmation = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_RECURRENT)
    
    class Meta:
        ordering = ['date_debut', 'titre']
    
    def __str__(self):
        return f"{self.titre} - {self.specialite.nom}"


class SeanceProgrammee(models.Model):
    """Séance hebdomadaire programmée"""
    
    # Types de séances
    TYPE_VISIO = 'visio'
    TYPE_FICHIER = 'fichier'
    TYPE_VIDEO = 'video'
    TYPE_QUIZ = 'quiz'
    TYPE_DISCUSSION = 'discussion'
    TYPE_QCM = 'qcm'
    TYPE_CODE = 'code'
    TYPE_ETUDE_CAS = 'etude_cas'
    TYPE_DEVOIR = 'devoir'
    TYPE_PROJET = 'projet'
    TYPE_REDAC = 'redaction'
    TYPE_PRES = 'presentation'
    TYPE_RECHERCHE = 'recherche'
    TYPE_CORRECTION_DEVOIR = 'correction_devoir'
    TYPE_CORRECTION_PROJET = 'correction_projet'
    TYPE_CORRECTION_QUIZ = 'correction_quiz'
    TYPE_SOUTENANCE = 'soutenance'
    TYPE_EVAL_PAIR = 'eval_pair'
    TYPE_FEEDBACK = 'feedback'
    TYPE_RATTRAPAGE = 'rattrapage'
    TYPE_CORRECTION = 'correction'
    TYPE_PRESENTATION = 'presentation'
    
    TYPE_CHOICES = [
    ('visio', 'Visioconférence (BigBlueButton)'),
    ('asynchrone', 'Séance asynchrone (Vidéo + Document)'),
    ('integration', 'Activité d\'intégration (Projet long)'),
    ('correction', 'Séance de correction'),
    ('presentation', 'Présentation / Soutenance'),
]
    
    cours = models.ForeignKey(CoursProgramme, on_delete=models.CASCADE, related_name='seances_programmees')
    titre = models.CharField(max_length=200, verbose_name="Titre de la séance")
    description = models.TextField(blank=True, verbose_name="Description")
    type_seance = models.CharField(max_length=30, choices=TYPE_CHOICES, verbose_name="Type de séance")
    
    objectifs = models.TextField(blank=True, null=True, verbose_name="Objectifs pédagogiques")
    JOURS = [(1,'Lundi'),(2,'Mardi'),(3,'Mercredi'),(4,'Jeudi'),(5,'Vendredi'),(6,'Samedi'),(7,'Dimanche')]
    jour = models.IntegerField(choices=JOURS, verbose_name="Jour")
    heure_debut = models.TimeField(verbose_name="Heure de début")
    heure_fin = models.TimeField(verbose_name="Heure de fin")
    ordre = models.IntegerField(default=0, verbose_name="Ordre")
    
    duree_estimee = models.IntegerField(default=30, help_text="Durée estimée en minutes")
    note_max = models.FloatField(default=20, help_text="Note maximale")
    lien_visio = models.URLField(blank=True, null=True, verbose_name="Lien BigBlueButton")
    enregistrement_url = models.URLField(blank=True, null=True, verbose_name="URL de l'enregistrement")
    enregistrement_disponible_jusqua = models.DateTimeField(blank=True, null=True)
    contenu_texte = models.TextField(blank=True, verbose_name="Contenu texte")
    fichier = models.FileField(upload_to='seances/fichiers/', blank=True, null=True)
    lien_externe = models.URLField(blank=True, null=True)
    
    
    quiz_associe = models.ForeignKey('Quiz', on_delete=models.SET_NULL, null=True, blank=True)
    objectifs = models.TextField(blank=True, null=True, verbose_name="Objectifs pédagogiques") 
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['ordre', 'jour', 'heure_debut']
    
    def __str__(self):
        return f"{self.titre} - {self.get_type_seance_display()}"


class ParticipantCoursProgramme(models.Model):
    """Participants au cours"""
    cours = models.ForeignKey(CoursProgramme, on_delete=models.CASCADE, related_name='participants')
    etudiant = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='cours_programmes_participes')
    bloque = models.BooleanField(default=False, verbose_name="Bloqué")
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['cours', 'etudiant']
    
    def __str__(self):
        return f"{self.etudiant.username} - {self.cours.titre}"
    
class PresenceSeance(models.Model):
    seance = models.ForeignKey('SeanceProgrammee', on_delete=models.CASCADE, related_name='presences')
    etudiant = models.ForeignKey('Utilisateur', on_delete=models.CASCADE)
    present = models.BooleanField(default=False)
    vu = models.BooleanField(default=False, verbose_name="Séance vue")  # ← NOUVEAU
    date_vu = models.DateTimeField(null=True, blank=True)  # ← NOUVEAU
    temps_connecte = models.IntegerField(default=0)
    note = models.FloatField(null=True, blank=True)
    
    class Meta:
        unique_together = ['seance', 'etudiant']

class DepotPresentation(models.Model):
    seance = models.ForeignKey('SeanceProgrammee', on_delete=models.CASCADE, related_name='depots')
    etudiant = models.ForeignKey('Utilisateur', on_delete=models.CASCADE)
    fichier = models.FileField(upload_to='presentations/', verbose_name="Fichier (PPT, PDF)")
    lien_video = models.URLField(blank=True, null=True, verbose_name="Lien vidéo")
    date_depot = models.DateTimeField(auto_now_add=True)
    note = models.FloatField(blank=True, null=True)
    feedback = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['seance', 'etudiant']


class NoteEtudiant(models.Model):
    etudiant = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='notes')
    cours = models.ForeignKey('CoursProgramme', on_delete=models.CASCADE, related_name='notes')
    seance = models.ForeignKey('SeanceProgrammee', on_delete=models.CASCADE, null=True, blank=True, related_name='notes')
    note = models.FloatField(verbose_name="Note")
    note_max = models.FloatField(default=20, verbose_name="Note maximale")
    commentaire = models.TextField(blank=True, null=True, verbose_name="Commentaire")
    date_attribution = models.DateTimeField(auto_now_add=True)
    enseignant = models.ForeignKey('Utilisateur', on_delete=models.SET_NULL, null=True, related_name='notes_donnees')
    
    class Meta:
        unique_together = ['etudiant', 'cours', 'seance']

# ==================== DEVOIRS (AMÉLIORÉ) ====================
class Devoir(models.Model):
    TYPE_CHOICES = [
        ('document', 'Dépôt de document'),
        ('projet', 'Projet'),
        ('code', 'Code'),
        ('presentation', 'Présentation'),
    ]
    
    seance = models.ForeignKey('SeanceProgrammee', on_delete=models.CASCADE, related_name='devoirs')
    titre = models.CharField(max_length=200)
    description = models.TextField()
    type_devoir = models.CharField(max_length=20, choices=TYPE_CHOICES)
    consignes = models.TextField()
    
    date_debut = models.DateTimeField()
    date_limite = models.DateTimeField()
    note_max = models.FloatField(default=20)
    
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ExerciceApplication(models.Model):
    TYPE_CHOICES = [
        ('quiz', 'Quiz (QCM)'),
        ('pratique', 'Exercice pratique'),
        ('etude_cas', 'Étude de cas'),
        ('redaction', 'Rédaction courte'),
        ('code', 'Exercice de code'),
    ]
    
    seance = models.ForeignKey('SeanceProgrammee', on_delete=models.CASCADE, related_name='exercices')
    titre = models.CharField(max_length=200)
    description = models.TextField()
    type_exercice = models.CharField(max_length=20, choices=TYPE_CHOICES)
    duree = models.IntegerField(help_text="Durée en minutes")
    consignes = models.TextField()
    questions_json = models.JSONField(blank=True, null=True)
    demarre = models.BooleanField(default=False)
    date_demarrage = models.DateTimeField(blank=True, null=True)
    date_fermeture = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resultats_publies = models.BooleanField(default=False)

class ReponseExercice(models.Model):
    exercice = models.ForeignKey(ExerciceApplication, on_delete=models.CASCADE, related_name='reponses')
    etudiant = models.ForeignKey('Utilisateur', on_delete=models.CASCADE)
    reponse_json = models.JSONField(default=dict)
    note = models.FloatField(blank=True, null=True)
    feedback = models.TextField(blank=True)
    date_soumission = models.DateTimeField(auto_now_add=True)


class Devoir(models.Model):
    TYPE_CHOICES = [
        ('document', 'Dépôt de document'),
        ('projet', 'Projet'),
        ('code', 'Code'),
        ('presentation', 'Présentation'),
    ]
    
    seance = models.ForeignKey('SeanceProgrammee', on_delete=models.CASCADE, related_name='devoirs')
    titre = models.CharField(max_length=200)
    description = models.TextField()
    type_devoir = models.CharField(max_length=20, choices=TYPE_CHOICES)
    consignes = models.TextField()
    date_debut = models.DateTimeField()
    date_limite = models.DateTimeField()
    note_max = models.FloatField(default=20)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SoumissionDevoir(models.Model):
    devoir = models.ForeignKey(Devoir, on_delete=models.CASCADE, related_name='soumissions')
    etudiant = models.ForeignKey('Utilisateur', on_delete=models.CASCADE)
    texte_reponse = models.TextField(blank=True, null=True)
    fichier = models.FileField(upload_to='devoirs/soumissions/', blank=True, null=True)
    date_soumission = models.DateTimeField(auto_now_add=True)
    note = models.FloatField(blank=True, null=True)
    feedback = models.TextField(blank=True)


class FichierSoumission(models.Model):
    soumission = models.ForeignKey(SoumissionDevoir, on_delete=models.CASCADE, related_name='fichiers')
    fichier = models.FileField(upload_to='devoirs/soumissions/')
    nom_original = models.CharField(max_length=255)
    taille = models.IntegerField()
    date_upload = models.DateTimeField(auto_now_add=True)
