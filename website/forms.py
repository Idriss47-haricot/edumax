from django import forms
from django.core.exceptions import ValidationError

from website.models import Avis, Devoir, Exercice, FichierFormation, Formation, SoumissionDevoir
from django import forms

from .models import Formation, AchatFormation, ImageEcole, ParametresMessagerie, RegleVente, SignalementFormation, SujetDuJour

# Formulaire d'inscription
class InscriptionForm(forms.Form):
    nom = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    prenom = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telephone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    pays = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    def clean_password1(self):
        pwd = self.cleaned_data.get('password1')
        if pwd and len(pwd) < 8:
            raise ValidationError('Mot de passe trop court')
        return pwd
    
    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Mots de passe différents')
        return p2

# Formulaire de connexion
class ConnexionForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

# Formulaire mot de passe oublié
class MotDePasseOublieForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

# Formulaire réinitialisation
class ReinitialisationMotDePasseForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    def clean(self):
        p1 = self.cleaned_data.get('password')
        p2 = self.cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Mots de passe différents')
        return self.cleaned_data

# Formulaire école
class EcoleCreationForm(forms.Form):
    nom = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telephone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    ville = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    pays = forms.CharField(initial='Cameroun', widget=forms.TextInput(attrs={'class': 'form-control'}))
    quartier = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    numero_agrement = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    logo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    banniere = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    facebook = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    twitter = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    instagram = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    youtube = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    linkedin = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    abonnement = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'class': 'form-control'}))
    admin_ecole = forms.ChoiceField(choices=[], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Abonnement, Utilisateur
        self.fields['abonnement'].choices = [('', '---------')] + [(a.id, a.nom) for a in Abonnement.objects.all()]
        self.fields['admin_ecole'].choices = [('', '---------')] + [(u.id, u.username) for u in Utilisateur.objects.filter(role='admin_ecole')]

# Formulaire filière
class FiliereForm(forms.Form):
    nom = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    ordre = forms.IntegerField(required=False, initial=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))

# Formulaire spécialité
class SpecialiteForm(forms.Form):
    nom = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    ordre = forms.IntegerField(required=False, initial=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))

# Formulaire abonnement
class AbonnementForm(forms.Form):
    nom = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    max_etudiants = forms.IntegerField(initial=100, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    max_cours = forms.IntegerField(initial=50, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    stockage_gb = forms.IntegerField(initial=5, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    ordre = forms.IntegerField(initial=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    actif = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

# Formulaire cours
class CoursProgrammeForm(forms.Form):
    titre = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))
    objectifs = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    enseignant = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'class': 'form-control'}))
    date_debut = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    date_fin = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    actif = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Utilisateur
        self.fields['enseignant'].choices = [('', '---------')] + [(u.id, f"{u.prenom} {u.username}") for u in Utilisateur.objects.filter(role='enseignant')]

# Formulaire séance
class SeanceBaseForm(forms.Form):
    titre = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    objectifs = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    type_seance = forms.ChoiceField(choices=[('visio', 'Visioconférence'), ('asynchrone', 'Séance asynchrone'), ('integration', 'Activité intégration'), ('correction', 'Séance correction')], widget=forms.Select(attrs={'class': 'form-control'}))
    ordre = forms.IntegerField(required=False, initial=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    duree_estimee = forms.IntegerField(initial=60, widget=forms.NumberInput(attrs={'class': 'form-control'}))

# Formulaire inscription avec clé
class InscriptionAvecCleForm(forms.Form):
    cle_inscription = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    
# ==================== FORMULAIRES COMPLÉMENTAIRES ====================

# Formulaire modification école
class EcoleModificationForm(forms.Form):
    nom = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telephone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    ville = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    pays = forms.CharField(initial='Cameroun', widget=forms.TextInput(attrs={'class': 'form-control'}))
    quartier = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    numero_agrement = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    logo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    banniere = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    facebook = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    twitter = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    instagram = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    youtube = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    linkedin = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))


# Formulaire séance programmée
class SeanceProgrammeeForm(forms.Form):
    titre = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    type_seance = forms.ChoiceField(choices=[('visio', 'Visioconférence'), ('asynchrone', 'Asynchrone'), ('integration', 'Intégration'), ('correction', 'Correction')], widget=forms.Select(attrs={'class': 'form-control'}))
    jour = forms.ChoiceField(choices=[(1,'Lundi'),(2,'Mardi'),(3,'Mercredi'),(4,'Jeudi'),(5,'Vendredi'),(6,'Samedi'),(7,'Dimanche')], widget=forms.Select(attrs={'class': 'form-control'}))
    heure_debut = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}))
    heure_fin = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}))
    ordre = forms.IntegerField(required=False, initial=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    duree_estimee = forms.IntegerField(initial=30, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    note_max = forms.FloatField(initial=20, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    contenu_texte = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))
    fichier = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    lien_externe = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    lien_visio = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))


# Formulaire ressource séance
class RessourceSeanceForm(forms.Form):
    type_ressource = forms.ChoiceField(choices=[('fichier', 'Fichier'), ('lien', 'Lien externe')], widget=forms.Select(attrs={'class': 'form-control'}))
    fichier = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    url = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    titre = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

# Formulaire séance correction
class CorrectionSeanceForm(forms.Form):
    devoirs = forms.MultipleChoiceField(required=False, widget=forms.SelectMultiple(attrs={'class': 'form-control'}))
    exercices = forms.MultipleChoiceField(required=False, widget=forms.SelectMultiple(attrs={'class': 'form-control'}))
    correction_collective_texte = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10}))
    correction_collective_fichier = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Devoir, ExerciceIntegration
        self.fields['devoirs'].choices = [(d.id, d.titre) for d in Devoir.objects.all()]
        self.fields['exercices'].choices = [(e.id, e.titre) for e in ExerciceIntegration.objects.all()]

# ==================== FORMULAIRES EXERCICES ====================

class ExerciceForm(forms.ModelForm):
    class Meta:
        model = Exercice
        fields = ['titre', 'consignes', 'duree', 'type_exercice']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de l\'exercice'}),
            'consignes': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Consignes...'}),
            'duree': forms.NumberInput(attrs={'class': 'form-control', 'value': 30}),
            'type_exercice': forms.Select(attrs={'class': 'form-control'}),
        }


# ==================== FORMULAIRES DEVOIRS ====================

class DevoirForm(forms.ModelForm):
    class Meta:
        model = Devoir
        fields = ['titre', 'description', 'consignes', 'date_debut', 'date_limite', 'mode_correction', 'seance_correction']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre du devoir'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description...'}),
            'consignes': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Consignes...'}),
            'date_debut': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'date_limite': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'mode_correction': forms.Select(attrs={'class': 'form-control', 'id': 'id_mode_correction'}),
            'seance_correction': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import SeanceBase
        self.fields['seance_correction'].choices = [('', '---------')] + [(s.id, s.titre) for s in SeanceBase.objects.filter(type_seance='correction')]
        self.fields['seance_correction'].required = False


class SoumissionDevoirForm(forms.ModelForm):
    class Meta:
        model = SoumissionDevoir
        fields = ['reponse_texte', 'fichier']
        widgets = {
            'reponse_texte': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Votre réponse...'}),
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
        }


class CorrectionDevoirForm(forms.Form):
    """Formulaire pour corriger un devoir (note + feedback + fichier)"""
    note = forms.FloatField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.5}))
    feedback = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}))
    fichier_corrige = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))

# ==================== FORMATIONS ====================
class FormationForm(forms.ModelForm):
    class Meta:
        model = Formation
        fields = [
            'titre', 
            'description_courte', 
            'description_longue', 
            'resume',  # Nouveau champ pour l'accueil
            'prix', 
            'image_cover', 
            'video_presentation',
            'certifiee',      # Nouveau champ
            'mise_en_avant',  # Nouveau champ
        ]
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de la formation'}),
            'description_courte': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Brève description qui apparaît dans les cartes'}),
            'description_longue': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Description complète de la formation'}),
            'resume': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phrase accrocheuse pour la page d\'accueil'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control', 'step': '100', 'placeholder': '0'}),
            'image_cover': forms.FileInput(attrs={'class': 'form-control'}),
            'video_presentation': forms.FileInput(attrs={'class': 'form-control'}),
            'certifiee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mise_en_avant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'titre': 'Titre de la formation',
            'description_courte': 'Description courte',
            'description_longue': 'Description longue',
            'resume': 'Résumé pour l\'accueil',
            'prix': 'Prix (FCFA)',
            'image_cover': 'Image de couverture',
            'video_presentation': 'Vidéo de présentation',
            'certifiee': 'Formation certifiante',
            'mise_en_avant': 'Mettre en avant sur l\'accueil',
        }
        help_texts = {
            'resume': 'Apparaîtra sur la page d\'accueil des formations',
            'video_presentation': 'Format MP4, AVI, MKV (optionnel)',
            'image_cover': 'Format JPG, PNG (optionnel)',
            'mise_en_avant': "Cochez pour que cette formation apparaisse dans la section 'À la une'",
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class FichierFormationForm(forms.ModelForm):
    class Meta:
        model = FichierFormation
        fields = ['titre', 'fichier', 'type_fichier', 'ordre']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
            'type_fichier': forms.Select(attrs={'class': 'form-control'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class AvisForm(forms.ModelForm):
    class Meta:
        model = Avis
        fields = ['note', 'commentaire']
        widgets = {
            'note': forms.Select(attrs={'class': 'form-control'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class PaiementForm(forms.Form):
    type_paiement = forms.ChoiceField(choices=[
        ('orange', 'Orange Money'),
        ('mtn', 'MTN Mobile Money'),
        ('carte', 'Carte bancaire'),
    ], widget=forms.Select(attrs={'class': 'form-control'}))
    telephone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    coupon_code = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))


class ConditionsPublicationForm(forms.Form):
    conditions_acceptees = forms.BooleanField(required=True, label="J'accepte les conditions de publication")

class PublicationForm(forms.Form):
    conditions_acceptees = forms.BooleanField(
        required=True,
        label="J'accepte les conditions de publication",
        error_messages={'required': 'Vous devez accepter les conditions pour publier la formation.'}
    )


# Formulaire pour l'achat d'une formation
class AchatFormationForm(forms.ModelForm):
    type_paiement = forms.ChoiceField(
        choices=[('orange', 'Orange Money'), ('mtn', 'MTN Mobile Money')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    telephone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '6XXXXXXXX'})
    )
    coupon_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code promo'})
    )
    
    class Meta:
        model = AchatFormation
        fields = ['type_paiement', 'telephone']
    
    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        if telephone and not telephone.isdigit():
            raise forms.ValidationError("Le numéro de téléphone doit contenir uniquement des chiffres.")
        if telephone and len(telephone) < 9:
            raise forms.ValidationError("Le numéro de téléphone est trop court.")
        return telephone
    
class SignalementFormationForm(forms.ModelForm):
    class Meta:
        model = SignalementFormation
        fields = ['motif', 'description']
        widgets = {
            'motif': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class RegleVenteForm(forms.ModelForm):
    class Meta:
        model = RegleVente
        fields = ['rubrique', 'titre', 'contenu', 'ordre', 'actif']
        widgets = {
            'rubrique': forms.Select(attrs={'class': 'form-select'}),
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class FichierFormationForm(forms.ModelForm):
    class Meta:
        model = FichierFormation
        fields = ['titre', 'type_fichier', 'fichier']
    
    def clean_fichier(self):
        fichier = self.cleaned_data.get('fichier')
        type_fichier = self.cleaned_data.get('type_fichier')
        
        if type_fichier == 'video':
            if not fichier.name.endswith(('.mp4', '.avi', '.mkv', '.webm', '.mov')):
                raise forms.ValidationError("Format vidéo non supporté. Utilisez MP4, AVI, MKV, WEBM ou MOV.")
        elif type_fichier == 'pdf':
            if not fichier.name.endswith('.pdf'):
                raise forms.ValidationError("Le fichier doit être au format PDF.")
        elif type_fichier == 'document':
            if not fichier.name.endswith(('.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx')):
                raise forms.ValidationError("Format non supporté. Utilisez Word, Excel ou PowerPoint.")
        
        if fichier.size > 500 * 1024 * 1024:  # 500 MB max
            raise forms.ValidationError("Le fichier ne doit pas dépasser 500 Mo.")
        
        return fichier
 # ==================== FORMULAIRES FORUM ====================

class SujetDuJourForm(forms.ModelForm):
    class Meta:
        model = SujetDuJour
        fields = ['titre', 'description', 'actif']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre du sujet du jour'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description (optionnelle)'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }   
    
# forms.py

class ForumParametresForm(forms.ModelForm):
    """Formulaire pour les paramètres des forums (indépendant de la messagerie)"""
    
    class Meta:
        model = ParametresMessagerie
        fields = [
            # Activation générale
            'forums_actifs',
            'forum_plateforme_actif',
            'forum_ecole_actif',
            'forum_specialite_actif',
            
            # Polling forum
            'forum_polling_actif',
            'forum_intervalle_polling',
            
            # Pauses (utiliser les champs existants sans "forum_")
            'pause_polling_onglet_inactif',
            'pause_polling_apres_heure',
            'heure_debut_pause',
            'heure_fin_pause',
            
            # Adaptation auto (utiliser les champs existants)
            'adaptation_auto_intervalle',
            'min_intervalle_polling',
            'max_intervalle_polling',
            
            # Limites
            'forum_max_messages_par_jour',
            'forum_longueur_min_message',
            'forum_longueur_max_message',
            'forum_delai_entre_messages',
            
            # Modération
            'forum_moderation_auto',
            'forum_signalement_seuil_blocage',
            
            # Sujet du jour
            'sujet_jour_actif',
            'sujet_jour_obligatoire',
            
            # Message si polling désactivé
            'message_polling_desactive',
        ]
        widgets = {
            'heure_debut_pause': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'heure_fin_pause': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'message_polling_desactive': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'forum_intervalle_polling': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 120}),
            'forum_max_messages_par_jour': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'forum_longueur_min_message': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'forum_longueur_max_message': forms.NumberInput(attrs={'class': 'form-control', 'min': 10}),
            'min_intervalle_polling': forms.NumberInput(attrs={'class': 'form-control', 'min': 5}),
            'max_intervalle_polling': forms.NumberInput(attrs={'class': 'form-control', 'min': 10}),
        }
        labels = {
            'forums_actifs': 'Forums actifs',
            'forum_plateforme_actif': 'Forum plateforme actif',
            'forum_ecole_actif': 'Forum école actif',
            'forum_specialite_actif': 'Forum spécialité actif',
            'forum_polling_actif': 'Polling forum actif',
            'forum_intervalle_polling': 'Intervalle polling (secondes)',
            'pause_polling_onglet_inactif': 'Pause si onglet inactif',
            'pause_polling_apres_heure': 'Pause nocturne',
            'heure_debut_pause': 'Heure début pause',
            'heure_fin_pause': 'Heure fin pause',
            'adaptation_auto_intervalle': 'Adapter auto l\'intervalle',
            'min_intervalle_polling': 'Intervalle min (secondes)',
            'max_intervalle_polling': 'Intervalle max (secondes)',
            'forum_max_messages_par_jour': 'Max messages par jour',
            'forum_longueur_min_message': 'Longueur minimale',
            'forum_longueur_max_message': 'Longueur maximale',
            'forum_delai_entre_messages': 'Délai entre messages (secondes)',
            'forum_moderation_auto': 'Modération automatique',
            'forum_signalement_seuil_blocage': 'Signalements avant blocage',
            'sujet_jour_actif': 'Afficher le sujet du jour',
            'sujet_jour_obligatoire': 'Sujet du jour obligatoire',
            'message_polling_desactive': 'Message si polling désactivé',
        }
        
# ==================== FORMULAIRE PARAMÈTRES MESSAGERIE ====================

class ParametresMessagerieForm(forms.ModelForm):
    """Formulaire pour configurer la messagerie"""
    
    class Meta:
        model = ParametresMessagerie
        fields = '__all__'
        widgets = {
            'polling_actif': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'intervalle_polling': forms.Select(attrs={'class': 'form-select'}, choices=[
                (10, '10 secondes (très réactif)'),
                (20, '20 secondes (recommandé)'),
                (30, '30 secondes (équilibré)'),
                (45, '45 secondes (économie)'),
                (60, '60 secondes (1 minute)'),
                (90, '90 secondes (1.5 minute)'),
            ]),
            'pause_polling_onglet_inactif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pause_polling_apres_heure': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'adaptation_auto_intervalle': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'heure_debut_pause': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_fin_pause': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'supprimer_messages_apres_jours': forms.NumberInput(attrs={'class': 'form-control'}),
            'supprimer_conversations_vides_apres_jours': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_messages_par_requete': forms.NumberInput(attrs={'class': 'form-control'}),
            'rate_limit_secondes': forms.NumberInput(attrs={'class': 'form-control'}),
            'message_polling_desactive': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'max_intervalle_polling': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_intervalle_polling': forms.NumberInput(attrs={'class': 'form-control'}),
        }
# ==================== FORMULAIRES ÉPREUVES ====================

class AchatEpreuveForm(forms.Form):
    """Formulaire d'achat d'épreuves (panier)"""
    type_paiement = forms.ChoiceField(
        choices=[('orange', 'Orange Money'), ('mtn', 'MTN Mobile Money')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    telephone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '6XXXXXXXX'})
    )
    
    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        if telephone and not telephone.isdigit():
            raise forms.ValidationError("Le numéro de téléphone doit contenir uniquement des chiffres.")
        if telephone and len(telephone) < 9:
            raise forms.ValidationError("Le numéro de téléphone est trop court.")
        return telephone


class AjoutPanierForm(forms.Form):
    """Formulaire pour ajouter une épreuve au panier"""
    avec_corrige = forms.BooleanField(required=False, initial=False)


class AchatCategorieForm(forms.Form):
    """Formulaire pour acheter toute une catégorie"""
    type_paiement = forms.ChoiceField(
        choices=[('orange', 'Orange Money'), ('mtn', 'MTN Mobile Money')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    telephone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '6XXXXXXXX'})
    )
    
# ============================================
# FORMULAIRES - DEMANDES FORMATEUR
# ============================================

from django import forms
from .models import DemandeFormateur

class DemandeFormateurForm(forms.ModelForm):
    class Meta:
        model = DemandeFormateur
        fields = ['domaine', 'experience', 'document']
        widgets = {
            'domaine': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Développement Web, Marketing Digital, Gestion...'
            }),
            'experience': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Décrivez votre expérience, vos réalisations, vos compétences...'
            }),
            'document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.png,.jpeg'
            }),
        }