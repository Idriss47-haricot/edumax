import time
import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .models import (
    Utilisateur, Ecole, Abonnement, Filiere, Specialite, 
    Cours, Seance, CoursProgramme, SeanceProgrammee, ParticipantCoursProgramme,
    Quiz, Question, ReponsePossible, TentativeQuiz, ReponseEtudiant,
    Devoir, SoumissionDevoir, FichierSoumission, GroupeDevoir,
    ProgressionEtudiant, MessagePrive, Conversation, Notification, ImageEcole,
    ExerciceApplication, ReponseExercice  # ← AJOUTE CES LIGNES
)




# ==================== FORMULAIRE D'INSCRIPTION ====================
class InscriptionForm(forms.ModelForm):
    nom = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre nom'}),
        label='Nom'
    )
    prenom = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre prénom'}),
        label='Prénom'
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemple@email.com'}),
        label='Adresse email'
    )
    telephone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 6XXXXXXXX'}),
        label='Numéro de téléphone'
    )
    pays = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre pays'}),
        label='Pays'
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'}),
        label='Mot de passe'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmer le mot de passe'}),
        label='Confirmer le mot de passe'
    )
    
    class Meta:
        model = Utilisateur
        fields = ['nom', 'prenom', 'email', 'telephone', 'pays', 'password1', 'password2']
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            if len(password) < 8:
                raise ValidationError('Le mot de passe doit contenir au moins 8 caractères.')
            if not re.search(r'[A-Z]', password):
                raise ValidationError('Le mot de passe doit contenir au moins une majuscule.')
            if not re.search(r'[a-z]', password):
                raise ValidationError('Le mot de passe doit contenir au moins une minuscule.')
            if not re.search(r'[0-9]', password):
                raise ValidationError('Le mot de passe doit contenir au moins un chiffre.')
        return password
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Utilisateur.objects.filter(email=email).exists():
            raise ValidationError('Cette adresse email est déjà utilisée.')
        return email
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Les mots de passe ne correspondent pas.')
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email'].split('@')[0] + '_' + str(int(time.time()))
        user.prenom = self.cleaned_data['prenom']
        user.telephone = self.cleaned_data.get('telephone', '')
        user.pays = self.cleaned_data.get('pays', '')
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


# ==================== FORMULAIRE DE CONNEXION ====================
class ConnexionForm(AuthenticationForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email ou nom d\'utilisateur'}), label='Email ou nom d\'utilisateur')
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'}), label='Mot de passe')


# ==================== FORMULAIRE MOT DE PASSE OUBLIÉ ====================
class MotDePasseOublieForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Votre adresse email'}), label='Adresse email')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not Utilisateur.objects.filter(email=email).exists():
            raise ValidationError('Aucun compte trouvé avec cette adresse email.')
        return email


# ==================== FORMULAIRE RÉINITIALISATION ====================
class ReinitialisationMotDePasseForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nouveau mot de passe'}), label='Nouveau mot de passe')
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmer le mot de passe'}), label='Confirmer le mot de passe')
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise ValidationError('Les mots de passe ne correspondent pas.')
        if password:
            if len(password) < 8:
                raise ValidationError('Le mot de passe doit contenir au moins 8 caractères.')
            if not re.search(r'[A-Z]', password):
                raise ValidationError('Le mot de passe doit contenir au moins une majuscule.')
            if not re.search(r'[a-z]', password):
                raise ValidationError('Le mot de passe doit contenir au moins une minuscule.')
            if not re.search(r'[0-9]', password):
                raise ValidationError('Le mot de passe doit contenir au moins un chiffre.')
        return cleaned_data


# ==================== FORMULAIRE ÉCOLE ====================
class EcoleCreationForm(forms.ModelForm):
    logo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}), label='Logo')
    
    class Meta:
        model = Ecole
        fields = ['nom', 'description', 'email', 'telephone', 'ville', 'pays', 'quartier', 'numero_agrement', 'abonnement', 'admin_ecole']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'pays': forms.TextInput(attrs={'class': 'form-control'}),
            'quartier': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_agrement': forms.TextInput(attrs={'class': 'form-control'}),
            'abonnement': forms.Select(attrs={'class': 'form-control'}),
            'admin_ecole': forms.Select(attrs={'class': 'form-control'}),
        }


# ==================== FORMULAIRE FILIÈRE ====================
class FiliereForm(forms.ModelForm):
    class Meta:
        model = Filiere
        fields = ['nom', 'description', 'ordre']  # ← SUPPRIME 'public'
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
        }


# ==================== FORMULAIRE SPÉCIALITÉ ====================
class SpecialiteForm(forms.ModelForm):
    class Meta:
        model = Specialite
        fields = ['nom', 'description', 'ordre']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
        }


# ==================== FORMULAIRE INSCRIPTION AVEC CLÉ ====================
class InscriptionAvecCleForm(forms.Form):
    cle_inscription = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez votre clé d\'inscription'}), label='Clé d\'inscription')
    
    def clean_cle_inscription(self):
        cle = self.cleaned_data.get('cle_inscription').upper()
        try:
            specialite = Specialite.objects.get(cle_inscription=cle)
        except Specialite.DoesNotExist:
            raise ValidationError('Clé d\'inscription invalide.')
        return specialite


# ==================== FORMULAIRE ABONNEMENT ====================
class AbonnementForm(forms.ModelForm):
    class Meta:
        model = Abonnement
        fields = ['nom', 'description', 'max_etudiants', 'max_cours', 'stockage_gb', 'ordre', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'max_etudiants': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_cours': forms.NumberInput(attrs={'class': 'form-control'}),
            'stockage_gb': forms.NumberInput(attrs={'class': 'form-control'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ==================== FORMULAIRE COURS ====================
class CoursProgrammeForm(forms.ModelForm):
    class Meta:
        model = CoursProgramme
        fields = ['titre', 'description', 'objectifs', 'enseignant', 'date_debut', 'date_fin', 'actif', 'mode_programmation', 'statut']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'objectifs': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'enseignant': forms.Select(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mode_programmation': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
        }


# ==================== FORMULAIRE MODIFICATION ÉCOLE ====================
class EcoleModificationForm(forms.ModelForm):
    logo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}), label='Logo')
    
    class Meta:
        model = Ecole
        fields = ['nom', 'description', 'email', 'telephone', 'ville', 'pays', 'quartier', 'numero_agrement']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'pays': forms.TextInput(attrs={'class': 'form-control'}),
            'quartier': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_agrement': forms.TextInput(attrs={'class': 'form-control'}),
        }


# ==================== FORMULAIRE SÉANCE ====================
class SeanceForm(forms.ModelForm):
    class Meta:
        model = Seance
        fields = ['titre', 'description', 'type_seance', 'jour', 'heure', 'fichier', 'lien_video', 'lien_visio', 'visio_date', 'ordre']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'type_seance': forms.Select(attrs={'class': 'form-control', 'id': 'type_seance'}),
            'jour': forms.Select(attrs={'class': 'form-control', 'choices': [('', 'Choisir un jour'), ('Lundi', 'Lundi'), ('Mardi', 'Mardi'), ('Mercredi', 'Mercredi'), ('Jeudi', 'Jeudi'), ('Vendredi', 'Vendredi'), ('Samedi', 'Samedi'), ('Dimanche', 'Dimanche')]}),
            'heure': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
            'lien_video': forms.URLInput(attrs={'class': 'form-control'}),
            'lien_visio': forms.URLInput(attrs={'class': 'form-control'}),
            'visio_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        type_seance = cleaned_data.get('type_seance')
        if type_seance == 'fichier':
            if not cleaned_data.get('fichier') and not cleaned_data.get('lien_video'):
                raise ValidationError('Veuillez fournir un fichier ou un lien vidéo.')
        elif type_seance == 'visio':
            if not cleaned_data.get('lien_visio'):
                raise ValidationError('Veuillez fournir un lien de visio-conférence.')
            if not cleaned_data.get('visio_date'):
                raise ValidationError('Veuillez fournir une date et heure pour la visio.')
        return cleaned_data
    # ==================== FORMULAIRES QUIZ ====================
class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['titre', 'description', 'date_limite']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_limite': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['type_question', 'enonce', 'points', 'ordre', 'feedback_general']
        widgets = {
            'type_question': forms.Select(attrs={'class': 'form-control'}),
            'enonce': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
            'feedback_general': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ReponsePossibleForm(forms.ModelForm):
    class Meta:
        model = ReponsePossible
        fields = ['texte', 'est_correcte', 'ordre']
        widgets = {
            'texte': forms.TextInput(attrs={'class': 'form-control'}),
            'est_correcte': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['type_question', 'enonce', 'points', 'ordre', 'feedback_general']
        widgets = {
            'type_question': forms.Select(attrs={'class': 'form-control', 'id': 'type_question'}),
            'enonce': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
            'feedback_general': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ReponsePossibleForm(forms.ModelForm):
    class Meta:
        model = ReponsePossible
        fields = ['texte', 'est_correcte', 'feedback', 'ordre']
        widgets = {
            'texte': forms.TextInput(attrs={'class': 'form-control'}),
            'est_correcte': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
        }



class FichierSoumissionForm(forms.ModelForm):
    class Meta:
        model = FichierSoumission
        fields = ['fichier']
        widgets = {
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
        }

class EcoleCreationForm(forms.ModelForm):
    logo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}), label='Logo')
    banniere = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}), label='Bannière')
    facebook = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}), label='Facebook')
    twitter = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}), label='Twitter')
    instagram = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}), label='Instagram')
    youtube = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}), label='YouTube')
    
    class Meta:
        model = Ecole
        fields = ['nom', 'description', 'email', 'telephone', 'ville', 'pays', 'quartier', 
                  'numero_agrement', 'abonnement', 'admin_ecole', 'logo', 'banniere',
                  'facebook', 'twitter', 'instagram', 'youtube']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'pays': forms.TextInput(attrs={'class': 'form-control'}),
            'quartier': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_agrement': forms.TextInput(attrs={'class': 'form-control'}),
            'abonnement': forms.Select(attrs={'class': 'form-control'}),
            'admin_ecole': forms.Select(attrs={'class': 'form-control'}),
        }

class SeanceProgrammeeForm(forms.ModelForm):
    class Meta:
        model = SeanceProgrammee
        fields = ['titre', 'description', 'objectifs', 'type_seance', 'jour', 'heure_debut', 
                  'heure_fin', 'ordre', 'duree_estimee', 'note_max', 'contenu_texte', 
                  'fichier', 'lien_externe', 'lien_visio']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'type_seance': forms.Select(attrs={'class': 'form-control'}),
            'jour': forms.Select(attrs={'class': 'form-control'}),
            'objectifs': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'heure_debut': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
            'duree_estimee': forms.NumberInput(attrs={'class': 'form-control'}),
            'note_max': forms.NumberInput(attrs={'class': 'form-control'}),
            'contenu_texte': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
            'lien_externe': forms.URLInput(attrs={'class': 'form-control'}),
            'objectifs': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
# ==================== EXERCICES ====================
class ExerciceForm(forms.ModelForm):
    class Meta:
        model = ExerciceApplication
        fields = ['titre', 'description', 'type_exercice', 'duree', 'consignes', 'questions_json']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'type_exercice': forms.Select(attrs={'class': 'form-control'}),
            'duree': forms.NumberInput(attrs={'class': 'form-control'}),
            'consignes': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'questions_json': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Format JSON pour les quiz'}),
        }


# ==================== DEVOIRS ====================
class DevoirForm(forms.ModelForm):
    class Meta:
        model = Devoir
        fields = ['titre', 'description', 'type_devoir', 'consignes', 'date_debut', 'date_limite', 'note_max', 'actif']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'type_devoir': forms.Select(attrs={'class': 'form-control'}),
            'consignes': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'date_debut': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'date_limite': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'note_max': forms.NumberInput(attrs={'class': 'form-control'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SoumissionDevoirForm(forms.ModelForm):
    class Meta:
        model = SoumissionDevoir
        fields = ['texte_reponse']
        widgets = {
            'texte_reponse': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }