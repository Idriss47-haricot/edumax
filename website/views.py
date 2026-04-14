import time

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db import models
import uuid
import random

from .models import (
    DepotPresentation, ExerciceApplication, NoteEtudiant, ParticipantCoursProgramme, ReponseExercice, Utilisateur, Ecole, Abonnement, Filiere, Specialite, Cours, Seance, 
    InscriptionEtudiant, EnseignantEcole, 
    Quiz, Question, ReponsePossible, TentativeQuiz, ReponseEtudiant,
    Devoir, SoumissionDevoir, FichierSoumission, GroupeDevoir,
    ProgressionEtudiant, MessagePrive, Conversation, Notification, ImageEcole,
    CoursProgramme, SeanceProgrammee, PresenceSeance, SoumissionDevoir, ExerciceApplication, Quiz# ← AJOUTE PresenceSeance
)

from .forms import (
    ExerciceForm, InscriptionForm, ConnexionForm, MotDePasseOublieForm, ReinitialisationMotDePasseForm,
    EcoleCreationForm, EcoleModificationForm, FiliereForm, SeanceForm, SpecialiteForm, InscriptionAvecCleForm,
    AbonnementForm, QuizForm, QuestionForm, ReponsePossibleForm,
    DevoirForm, SoumissionDevoirForm, FichierSoumissionForm,
    CoursProgrammeForm, SeanceProgrammeeForm, Quiz, Question, ReponsePossible, Utilisateur
)

from .decorators import super_admin_required, admin_ecole_required, enseignant_required

# ==================== PAGES PUBLIQUES ====================
def accueil(request):
    ecoles = Ecole.objects.filter(actif=True).select_related('abonnement')
    return render(request, 'website/accueil.html', {'ecoles': ecoles})

def inscription(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Bienvenue {user.prenom} {user.username} !')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = InscriptionForm()
    
    return render(request, 'website/inscription.html', {'form': form})

def connexion(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            if '@' in username:
                try:
                    user_obj = Utilisateur.objects.get(email=username)
                    username = user_obj.username
                except Utilisateur.DoesNotExist:
                    pass
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bon retour {user.prenom} {user.username} !')
                return redirect('dashboard')
            else:
                messages.error(request, 'Email ou mot de passe incorrect.')
        else:
            messages.error(request, 'Email ou mot de passe incorrect.')
    else:
        form = ConnexionForm()
    
    return render(request, 'website/connexion.html', {'form': form})

@login_required
def deconnexion(request):
    logout(request)
    messages.success(request, 'Vous avez été déconnecté.')
    return redirect('accueil')

def mot_de_passe_oublie(request):
    if request.method == 'POST':
        form = MotDePasseOublieForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = Utilisateur.objects.get(email=email)
            token = str(uuid.uuid4())
            request.session['reset_token'] = token
            request.session['reset_email'] = email
            messages.success(request, 'Un lien de réinitialisation a été envoyé.')
            return redirect('reinitialisation_mot_de_passe', token=token)
    else:
        form = MotDePasseOublieForm()
    
    return render(request, 'website/mot_de_passe_oublie.html', {'form': form})

def reinitialisation_mot_de_passe(request, token):
    if request.session.get('reset_token') != token:
        messages.error(request, 'Lien invalide ou expiré.')
        return redirect('mot_de_passe_oublie')
    
    if request.method == 'POST':
        form = ReinitialisationMotDePasseForm(request.POST)
        if form.is_valid():
            email = request.session.get('reset_email')
            user = Utilisateur.objects.get(email=email)
            user.set_password(form.cleaned_data['password'])
            user.save()
            del request.session['reset_token']
            del request.session['reset_email']
            messages.success(request, 'Mot de passe réinitialisé.')
            return redirect('connexion')
    else:
        form = ReinitialisationMotDePasseForm()
    
    return render(request, 'website/reinitialisation_mot_de_passe.html', {'form': form})

# ==================== DASHBOARD GÉNÉRAL ====================
@login_required
def dashboard(request):
    user = request.user
    context = {'user': user, 'messages_non_lus': 0}
    
    if user.role == Utilisateur.SUPER_ADMIN:
        context['ecoles'] = Ecole.objects.all().select_related('abonnement')
        context['utilisateurs'] = Utilisateur.objects.all()
        context['enseignants_count'] = Utilisateur.objects.filter(role=Utilisateur.ENSEIGNANT).count()
        context['etudiants_count'] = Utilisateur.objects.filter(role=Utilisateur.ETUDIANT).count()
        context['abonnements'] = Abonnement.objects.all()
        return render(request, 'website/super_admin/dashboard.html', context)
    
    elif user.role == Utilisateur.ADMIN_ECOLE:
        ecole = user.ecole_admin
        if not ecole:
            messages.error(request, 'Vous n\'êtes pas associé à une école.')
            return redirect('accueil')
        context['ecole'] = ecole
        context['enseignants'] = Utilisateur.objects.filter(enseignant_ecoles__ecole=ecole)
        context['etudiants'] = Utilisateur.objects.filter(inscriptions__specialite__filiere__ecole=ecole).distinct()
        context['cours_count'] = Cours.objects.filter(specialite__filiere__ecole=ecole).count()
        context['filieres_count'] = Filiere.objects.filter(ecole=ecole).count()
        context['filieres'] = Filiere.objects.filter(ecole=ecole).prefetch_related('specialites')
        return render(request, 'website/admin_ecole/dashboard.html', context)
    
    elif user.role == Utilisateur.ENSEIGNANT:
            # Récupérer les cours assignés à l'enseignant (avec le bon modèle)
        cours_assignes = CoursProgramme.objects.filter(enseignant=user, actif=True).select_related('specialite__filiere__ecole')
        
        # Récupérer les écoles où l'enseignant donne des cours
        ecoles = Ecole.objects.filter(enseignants__enseignant=user)
        
        # Compter les étudiants uniques
        etudiants_ids = InscriptionEtudiant.objects.filter(
            specialite__cours_programmes__enseignant=user
        ).values_list('etudiant', flat=True).distinct()
        
        # Compter les visios à venir (avec SeanceProgrammee)
        visios_count = SeanceProgrammee.objects.filter(
            cours__in=cours_assignes,
            type_seance='visio'
        ).count()
        
        context = {
            'ecoles': ecoles,
            'cours_assignes': cours_assignes,
            'cours_count': cours_assignes.count(),
            'etudiants_count': etudiants_ids.count(),
            'visios_count': visios_count,
            'devoirs_a_corriger': 0,
            'derniers_cours': cours_assignes.order_by('-created_at')[:5]
        }
        
        # Organisation pour le menu déroulant (École → Filière → Spécialité → Cours)
        cours_data = []
        ecoles_dict = {}
        
        for cours in cours_assignes:
            ecole = cours.specialite.filiere.ecole
            filiere = cours.specialite.filiere
            specialite = cours.specialite
            
            if ecole.id not in ecoles_dict:
                ecoles_dict[ecole.id] = {
                    'nom': ecole.nom,
                    'filieres_dict': {}
                }
            
            if filiere.id not in ecoles_dict[ecole.id]['filieres_dict']:
                ecoles_dict[ecole.id]['filieres_dict'][filiere.id] = {
                    'nom': filiere.nom,
                    'specialites_dict': {}
                }
            
            if specialite.id not in ecoles_dict[ecole.id]['filieres_dict'][filiere.id]['specialites_dict']:
                ecoles_dict[ecole.id]['filieres_dict'][filiere.id]['specialites_dict'][specialite.id] = {
                    'nom': specialite.nom,
                    'cours': []
                }
            
            ecoles_dict[ecole.id]['filieres_dict'][filiere.id]['specialites_dict'][specialite.id]['cours'].append(cours)
        
        # Transformer en listes pour le template
        for ecole_id, ecole_data in ecoles_dict.items():
            ecole_item = {
                'nom': ecole_data['nom'],
                'filieres': []
            }
            for filiere_id, filiere_data in ecole_data['filieres_dict'].items():
                filiere_item = {
                    'nom': filiere_data['nom'],
                    'specialites': []
                }
                for specialite_id, specialite_data in filiere_data['specialites_dict'].items():
                    specialite_item = {
                        'nom': specialite_data['nom'],
                        'cours': specialite_data['cours']
                    }
                    filiere_item['specialites'].append(specialite_item)
                ecole_item['filieres'].append(filiere_item)
            cours_data.append(ecole_item)
        
        context['cours_data'] = cours_data
        
        return render(request, 'website/enseignant/dashboard.html', context)
    
    
    else:  # ÉTUDIANT
        inscriptions = InscriptionEtudiant.objects.filter(etudiant=user).select_related('specialite__filiere__ecole')
        context['inscriptions'] = inscriptions
        context['ecoles'] = set([ins.specialite.filiere.ecole for ins in inscriptions])
        context['prochains_cours'] = Seance.objects.filter(
            cours__specialite__inscriptions__etudiant=user,
            type_seance='visio',
            visio_date__gte=timezone.now()
        ).order_by('visio_date')[:5]
        context['quiz_realises'] = TentativeQuiz.objects.filter(etudiant=user).count()
        context['devoirs_rendus'] = SoumissionDevoir.objects.filter(etudiant=user).count()
        return render(request, 'website/etudiant/dashboard.html', context)

# ==================== MES COURS ====================

@login_required
def cours_detail_superadmin(request, cours_id):
    cours = get_object_or_404(CoursProgramme, id=cours_id)
    
    return render(request, 'website/super_admin/cours_detail.html', {
        'cours': cours,
        'seances': cours.seances_programmees.all()
    })


@login_required
def seance_ajouter(request, cours_id):
    cours = get_object_or_404(Cours, id=cours_id)
    
    if request.user.role not in [Utilisateur.ENSEIGNANT, Utilisateur.ADMIN_ECOLE, Utilisateur.SUPER_ADMIN]:
        messages.error(request, 'Droits insuffisants.')
        return redirect('cours_detail', cours_id=cours.id)
    
    if request.user.role == Utilisateur.ENSEIGNANT:
        if not EnseignantEcole.objects.filter(enseignant=request.user, ecole=cours.specialite.filiere.ecole).exists():
            messages.error(request, 'Vous n\'êtes pas autorisé.')
            return redirect('cours_detail', cours_id=cours.id)
    
    if request.method == 'POST':
        form = SeanceForm(request.POST, request.FILES)
        if form.is_valid():
            seance = form.save(commit=False)
            seance.cours = cours
            seance.save()
            messages.success(request, f'Séance "{seance.titre}" ajoutée.')
            return redirect('cours_detail', cours_id=cours.id)
    else:
        form = SeanceForm()
    
    return render(request, 'website/enseignant/seance_ajouter.html', {'form': form, 'cours': cours})

# ==================== SUPER ADMIN ====================
@login_required
@super_admin_required
def super_admin_ecole_liste(request):
    ecoles = Ecole.objects.all().select_related('abonnement', 'admin_ecole')

      # Barre de recherche
    q = request.GET.get('q', '')
    if q:
        ecoles = ecoles.filter(
            models.Q(nom__icontains=q) |
            models.Q(ville__icontains=q) |
            models.Q(pays__icontains=q) |
            models.Q(email__icontains=q)
        )
    
    return render(request, 'website/super_admin/ecoles/liste.html', {'ecoles': ecoles})

@login_required
@super_admin_required
def super_admin_ecole_creer(request):
    if request.method == 'POST':
        form = EcoleCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'École créée avec succès.')
            return redirect('super_admin_ecole_liste')
    else:
        form = EcoleCreationForm()
    return render(request, 'website/super_admin/ecoles/creer.html', {'form': form})

@login_required
@super_admin_required
def super_admin_abonnement_liste(request):
    abonnements = Abonnement.objects.all()
    return render(request, 'website/super_admin/abonnements/liste.html', {'abonnements': abonnements})

@login_required
@super_admin_required
def super_admin_abonnement_creer(request):
    if request.method == 'POST':
        form = AbonnementForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pack créé.')
            return redirect('super_admin_abonnement_liste')
    else:
        form = AbonnementForm()
    return render(request, 'website/super_admin/abonnements/creer.html', {'form': form})

@login_required
@super_admin_required
def super_admin_abonnement_modifier(request, abonnement_id):
    abonnement = get_object_or_404(Abonnement, id=abonnement_id)
    if request.method == 'POST':
        form = AbonnementForm(request.POST, instance=abonnement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pack modifié.')
            return redirect('super_admin_abonnement_liste')
    else:
        form = AbonnementForm(instance=abonnement)
    return render(request, 'website/super_admin/abonnements/modifier.html', {'form': form, 'abonnement': abonnement})

@login_required
@super_admin_required
def super_admin_abonnement_supprimer(request, abonnement_id):
    abonnement = get_object_or_404(Abonnement, id=abonnement_id)
    if abonnement.ecole_set.exists():
        messages.error(request, 'Des écoles utilisent ce pack.')
        return redirect('super_admin_abonnement_liste')
    abonnement.delete()
    messages.success(request, 'Pack supprimé.')
    return redirect('super_admin_abonnement_liste')

@login_required
@super_admin_required
def super_admin_utilisateurs(request):
    utilisateurs = Utilisateur.objects.all().order_by('-date_joined')
    q = request.GET.get('q', '')
    if q:
        utilisateurs = utilisateurs.filter(
            models.Q(username__icontains=q) |
            models.Q(email__icontains=q) |
            models.Q(prenom__icontains=q) |
            models.Q(role__icontains=q)
        )
    
    return render(request, 'website/super_admin/utilisateurs/liste.html', {'utilisateurs': utilisateurs})

@login_required
@super_admin_required
def super_admin_utilisateur_modifier(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Changer le mot de passe
        if action == 'change_password':
            new_password = request.POST.get('new_password')
            if new_password and len(new_password) >= 8:
                utilisateur.set_password(new_password)
                utilisateur.save()
                messages.success(request, 'Mot de passe modifié avec succès.')
            else:
                messages.error(request, 'Mot de passe trop court (8 caractères minimum).')
            return redirect('super_admin_utilisateur_modifier', user_id=user_id)
        
        # Modifier les informations
        else:
            utilisateur.prenom = request.POST.get('prenom', utilisateur.prenom)
            utilisateur.email = request.POST.get('email', utilisateur.email)
            utilisateur.telephone = request.POST.get('telephone', utilisateur.telephone)
            utilisateur.pays = request.POST.get('pays', utilisateur.pays)
            utilisateur.role = request.POST.get('role', utilisateur.role)
            utilisateur.is_active = request.POST.get('is_active') == 'on'
            utilisateur.save()
            messages.success(request, 'Utilisateur modifié avec succès.')
            return redirect('super_admin_utilisateurs')
    
    return render(request, 'website/super_admin/utilisateurs/modifier.html', {'utilisateur': utilisateur})

@login_required
@super_admin_required
def super_admin_utilisateur_supprimer(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    if utilisateur == request.user:
        messages.error(request, 'Vous ne pouvez pas supprimer votre compte.')
        return redirect('super_admin_utilisateurs')
    utilisateur.delete()
    messages.success(request, 'Utilisateur supprimé.')
    return redirect('super_admin_utilisateurs')

@login_required
@super_admin_required
def super_admin_changer_role(request, user_id, nouveau_role):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    roles_valides = ['super_admin', 'admin_ecole', 'enseignant', 'etudiant']
    if nouveau_role not in roles_valides:
        messages.error(request, 'Rôle invalide.')
        return redirect('super_admin_utilisateurs')
    if utilisateur == request.user:
        messages.error(request, 'Vous ne pouvez pas modifier votre propre rôle.')
        return redirect('super_admin_utilisateurs')
    utilisateur.role = nouveau_role
    if nouveau_role == 'super_admin':
        utilisateur.is_superuser = True
        utilisateur.is_staff = True
    else:
        utilisateur.is_superuser = False
        utilisateur.is_staff = False
    utilisateur.save()
    messages.success(request, f'Rôle modifié : {utilisateur.get_role_display()}')
    return redirect('super_admin_utilisateurs')

@login_required
@super_admin_required
def super_admin_utilisateur_desactiver(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    
    if utilisateur == request.user:
        messages.error(request, 'Vous ne pouvez pas désactiver votre propre compte.')
        return redirect('super_admin_utilisateurs')
    
    utilisateur.is_active = False
    utilisateur.save()
    messages.success(request, f'Le compte de {utilisateur.username} a été désactivé.')
    return redirect('super_admin_utilisateurs')

@login_required
@super_admin_required
def super_admin_utilisateur_activer(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    utilisateur.is_active = True
    utilisateur.save()
    messages.success(request, f'Le compte de {utilisateur.username} a été réactivé.')
    return redirect('super_admin_utilisateurs')

# ==================== ADMIN ÉCOLE ====================
@login_required
def admin_ecole_filiere_liste(request):
    if request.user.role != Utilisateur.SUPER_ADMIN and request.user.role != Utilisateur.ADMIN_ECOLE:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    ecole = request.user.ecole_admin if request.user.role == Utilisateur.ADMIN_ECOLE else None
    
    # Pour Super Admin, récupérer l'école depuis le paramètre GET
    if request.user.role == Utilisateur.SUPER_ADMIN:
        ecole_id = request.GET.get('ecole_id')
        if ecole_id:
            ecole = get_object_or_404(Ecole, id=ecole_id)
    
    if not ecole:
        messages.error(request, 'Aucune école sélectionnée.')
        return redirect('dashboard')
    
    filieres = Filiere.objects.filter(ecole=ecole)
    
    # Barre de recherche
    q = request.GET.get('q', '')
    if q:
        filieres = filieres.filter(nom__icontains=q)
    
    context = {
        'filieres': filieres,
        'ecole': ecole
    }
    
    return render(request, 'website/admin_ecole/filieres/liste.html', context)
@login_required
def admin_ecole_filiere_creer(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    if request.user.role != Utilisateur.ADMIN_ECOLE or request.user.ecole_admin.id != ecole.id:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = FiliereForm(request.POST)
        if form.is_valid():
            filiere = form.save(commit=False)
            filiere.ecole = ecole
            filiere.save()
            messages.success(request, 'Filière créée.')
            return redirect('admin_ecole_filiere_liste')
    else:
        form = FiliereForm()
    return render(request, 'website/dashboard/admin_ecole/filieres/creer.html', {'form': form, 'ecole': ecole})

@login_required
def admin_ecole_specialite_liste(request, filiere_id):
    filiere = get_object_or_404(Filiere, id=filiere_id)
    ecole = filiere.ecole
    
    # Vérifier les droits
    if request.user.role != Utilisateur.SUPER_ADMIN:
        if request.user.role != Utilisateur.ADMIN_ECOLE or request.user.ecole_admin.id != ecole.id:
            messages.error(request, 'Accès non autorisé.')
            return redirect('dashboard')
    
    specialites = Specialite.objects.filter(filiere=filiere)
    
    # Barre de recherche
    q = request.GET.get('q', '')
    if q:
        specialites = specialites.filter(nom__icontains=q)
    
    # Utiliser un DICTIONNAIRE correct (avec des accolades et des deux-points)
    context = {
        'specialites': specialites,
        'filiere': filiere,
        'ecole': ecole
    }
    
    return render(request, 'website/admin_ecole/specialites/liste.html', context)

@login_required
def admin_ecole_specialite_creer(request, filiere_id):
    filiere = get_object_or_404(Filiere, id=filiere_id)
    ecole = filiere.ecole
    
    if request.user.role != Utilisateur.SUPER_ADMIN:
        if request.user.role != Utilisateur.ADMIN_ECOLE or request.user.ecole_admin.id != ecole.id:
            messages.error(request, 'Accès non autorisé.')
            return redirect('dashboard')
    
    if request.method == 'POST':
        form = SpecialiteForm(request.POST)
        if form.is_valid():
            specialite = form.save(commit=False)
            specialite.filiere = filiere
            specialite.save()
            messages.success(request, f'Spécialité "{specialite.nom}" créée. Clé : {specialite.cle_inscription}')
            return redirect('admin_ecole_specialite_liste', filiere_id=filiere.id)
    else:
        form = SpecialiteForm()
    
    context = {
        'form': form,
        'filiere': filiere,
        'ecole': ecole
    }
    
    return render(request, 'website/admin_ecole/specialites/creer.html', context)
@login_required
def admin_ecole_utilisateur_desactiver(request, user_id):
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    
    # Vérifier que l'utilisateur appartient à l'école
    est_membre = EnseignantEcole.objects.filter(enseignant=utilisateur, ecole=ecole).exists()
    est_inscrit = InscriptionEtudiant.objects.filter(etudiant=utilisateur, specialite__filiere__ecole=ecole).exists()
    
    if not (est_membre or est_inscrit):
        messages.error(request, 'Cet utilisateur n\'appartient pas à votre école.')
        return redirect('admin_ecole_utilisateurs')
    
    utilisateur.is_active = False
    utilisateur.save()
    messages.success(request, f'Le compte de {utilisateur.username} a été désactivé.')
    return redirect('admin_ecole_utilisateurs')


@login_required
def admin_ecole_utilisateur_activer(request, user_id):
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    utilisateur.is_active = True
    utilisateur.save()
    messages.success(request, f'Le compte de {utilisateur.username} a été réactivé.')
    return redirect('admin_ecole_utilisateurs')

@login_required
@super_admin_required
def super_admin_ecole_desactiver(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    ecole.actif = False
    ecole.save()
    messages.success(request, f'L\'école "{ecole.nom}" a été désactivée.')
    return redirect('super_admin_ecole_liste')


@login_required
@super_admin_required
def super_admin_ecole_activer(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    ecole.actif = True
    ecole.save()
    messages.success(request, f'L\'école "{ecole.nom}" a été réactivée.')
    return redirect('super_admin_ecole_liste')
def admin_ecole_enseignants(request):
    ecole = request.user.ecole_admin
    enseignants = Utilisateur.objects.filter(enseignant_ecoles__ecole=ecole)
    return render(request, 'website/admin_ecole/enseignants.html', {'enseignants': enseignants, 'ecole': ecole})

def admin_ecole_etudiants(request):
    ecole = request.user.ecole_admin
    etudiants = Utilisateur.objects.filter(inscriptions__specialite__filiere__ecole=ecole).distinct()
    # Barre de recherche
    q = request.GET.get('q', '')
    if q:
        enseignants = enseignants.filter(
            models.Q(username__icontains=q) |
            models.Q(email__icontains=q) |
            models.Q(prenom__icontains=q)
        )
    return render(request, 'website/admin_ecole/etudiants.html', {'etudiants': etudiants, 'ecole': ecole})

@login_required
def admin_ecole_etudiants(request):
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    etudiants = Utilisateur.objects.filter(inscriptions__specialite__filiere__ecole=ecole).distinct()
    
    # Barre de recherche
    q = request.GET.get('q', '')
    if q:
        etudiants = etudiants.filter(
            models.Q(username__icontains=q) |
            models.Q(email__icontains=q) |
            models.Q(prenom__icontains=q)
        )
    
    return render(request, 'website/admin_ecole/etudiants.html', {
        'etudiants': etudiants,
        'ecole': ecole
    })
    
    
@login_required
def admin_ecole_utilisateur_desactiver(request, user_id):
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    
    # Vérifier que l'utilisateur appartient à l'école
    est_membre = EnseignantEcole.objects.filter(enseignant=utilisateur, ecole=ecole).exists()
    est_inscrit = InscriptionEtudiant.objects.filter(etudiant=utilisateur, specialite__filiere__ecole=ecole).exists()
    
    if not (est_membre or est_inscrit):
        messages.error(request, 'Cet utilisateur n\'appartient pas à votre école.')
        return redirect('admin_ecole_enseignants')
    
    utilisateur.is_active = False
    utilisateur.save()
    messages.success(request, f'Le compte de {utilisateur.username} a été désactivé.')
    
    # Rediriger vers la page précédente (enseignants ou étudiants)
    referer = request.META.get('HTTP_REFERER', 'admin_ecole_enseignants')
    return redirect(referer)

@login_required
def admin_ecole_utilisateur_activer(request, user_id):
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    
    est_membre = EnseignantEcole.objects.filter(enseignant=utilisateur, ecole=ecole).exists()
    est_inscrit = InscriptionEtudiant.objects.filter(etudiant=utilisateur, specialite__filiere__ecole=ecole).exists()
    
    if not (est_membre or est_inscrit):
        messages.error(request, 'Cet utilisateur n\'appartient pas à votre école.')
        return redirect('admin_ecole_enseignants')
    
    utilisateur.is_active = True
    utilisateur.save()
    messages.success(request, f'Le compte de {utilisateur.username} a été réactivé.')
    
    referer = request.META.get('HTTP_REFERER', 'admin_ecole_enseignants')
    return redirect(referer)


@login_required
def admin_ecole_filiere_modifier(request, filiere_id):
    filiere = get_object_or_404(Filiere, id=filiere_id)
    ecole = filiere.ecole
    
    if request.user.role != Utilisateur.SUPER_ADMIN:
        if request.user.role != Utilisateur.ADMIN_ECOLE or request.user.ecole_admin.id != ecole.id:
            messages.error(request, 'Accès non autorisé.')
            return redirect('dashboard')
    
    if request.method == 'POST':
        form = FiliereForm(request.POST, instance=filiere)
        if form.is_valid():
            form.save()
            messages.success(request, 'Filière modifiée avec succès.')
            return redirect('admin_ecole_filiere_liste')
    else:
        form = FiliereForm(instance=filiere)
    
    return render(request, 'website/admin_ecole/filieres/modifier.html', {
        'form': form,
        'filiere': filiere,
        'ecole': ecole
    })

@login_required
def admin_ecole_filiere_supprimer(request, filiere_id):
    filiere = get_object_or_404(Filiere, id=filiere_id)
    ecole = filiere.ecole
    
    if request.user.role != Utilisateur.SUPER_ADMIN:
        if request.user.role != Utilisateur.ADMIN_ECOLE or request.user.ecole_admin.id != ecole.id:
            messages.error(request, 'Accès non autorisé.')
            return redirect('dashboard')
    
    nom = filiere.nom
    filiere.delete()
    messages.success(request, f'Filière "{nom}" supprimée.')
    return redirect('admin_ecole_filiere_liste')


@login_required
def admin_ecole_specialite_modifier(request, specialite_id):
    specialite = get_object_or_404(Specialite, id=specialite_id)
    filiere = specialite.filiere
    ecole = filiere.ecole
    
    if request.user.role != Utilisateur.SUPER_ADMIN:
        if request.user.role != Utilisateur.ADMIN_ECOLE or request.user.ecole_admin.id != ecole.id:
            messages.error(request, 'Accès non autorisé.')
            return redirect('dashboard')
    
    if request.method == 'POST':
        form = SpecialiteForm(request.POST, instance=specialite)
        if form.is_valid():
            form.save()
            messages.success(request, 'Spécialité modifiée avec succès.')
            return redirect('admin_ecole_specialite_liste', filiere_id=filiere.id)
    else:
        form = SpecialiteForm(instance=specialite)
    
    return render(request, 'website/admin_ecole/specialites/modifier.html', {
        'form': form,
        'specialite': specialite,
        'filiere': filiere,
        'ecole': ecole
    })

@login_required
def admin_ecole_specialite_supprimer(request, specialite_id):
    specialite = get_object_or_404(Specialite, id=specialite_id)
    filiere = specialite.filiere
    ecole = filiere.ecole
    
    if request.user.role != Utilisateur.SUPER_ADMIN:
        if request.user.role != Utilisateur.ADMIN_ECOLE or request.user.ecole_admin.id != ecole.id:
            messages.error(request, 'Accès non autorisé.')
            return redirect('dashboard')
    
    nom = specialite.nom
    specialite.delete()
    messages.success(request, f'Spécialité "{nom}" supprimée.')
    return redirect('admin_ecole_specialite_liste', filiere_id=filiere.id)

# ==================== ÉTUDIANT ====================
@login_required
def etudiant_inscription_cle(request):
    if request.user.role != Utilisateur.ETUDIANT:
        messages.error(request, 'Seuls les étudiants peuvent s\'inscrire.')
        return redirect('dashboard')
    
    ecoles = Ecole.objects.filter(actif=True)
    
    if request.method == 'POST':
        ecole_id = request.POST.get('ecole')
        cle = request.POST.get('cle_inscription', '').upper()
        
        try:
            specialite = Specialite.objects.get(cle_inscription=cle)
            if str(specialite.filiere.ecole.id) != ecole_id:
                messages.error(request, 'Clé invalide pour cette école.')
            else:
                inscription, created = InscriptionEtudiant.objects.get_or_create(
                    etudiant=request.user, specialite=specialite
                )
                if created:
                    messages.success(request, f'Inscrit à {specialite.nom}')
                else:
                    messages.info(request, 'Déjà inscrit.')
                return redirect('dashboard')
        except Specialite.DoesNotExist:
            messages.error(request, 'Clé invalide.')
    
    return render(request, 'website/etudiant/inscription_cle.html', {'ecoles': ecoles})

# ==================== QUIZ ====================
@login_required
def quiz_creer(request, specialite_id):
    specialite = get_object_or_404(Specialite, id=specialite_id)
    if request.user.role not in [Utilisateur.ENSEIGNANT, Utilisateur.ADMIN_ECOLE, Utilisateur.SUPER_ADMIN]:
        messages.error(request, 'Droits insuffisants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.specialite = specialite
            quiz.save()
            messages.success(request, 'Quiz créé.')
            return redirect('quiz_detail', quiz_id=quiz.id)
    else:
        form = QuizForm()
    return render(request, 'website/quiz/creer.html', {'form': form, 'specialite': specialite})

@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    user = request.user
    est_inscrit = InscriptionEtudiant.objects.filter(etudiant=user, specialite=quiz.specialite).exists()
    est_enseignant = EnseignantEcole.objects.filter(enseignant=user, ecole=quiz.specialite.filiere.ecole).exists()
    est_admin = user.role in [Utilisateur.ADMIN_ECOLE, Utilisateur.SUPER_ADMIN]
    
    if not (est_inscrit or est_enseignant or est_admin):
        messages.error(request, 'Accès non autorisé.')
        return redirect('mes_cours')
    
    return render(request, 'website/quiz/detail.html', {'quiz': quiz, 'questions': quiz.questions.all(), 'est_enseignant': est_enseignant or est_admin})

@login_required
def quiz_faire(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.user.role != Utilisateur.ETUDIANT:
        messages.error(request, 'Réservé aux étudiants.')
        return redirect('quiz_detail', quiz_id=quiz.id)
    
    est_inscrit = InscriptionEtudiant.objects.filter(etudiant=request.user, specialite=quiz.specialite).exists()
    if not est_inscrit:
        messages.error(request, 'Vous n\'êtes pas inscrit.')
        return redirect('mes_cours')
    
    if request.method == 'POST':
        tentative = TentativeQuiz.objects.create(quiz=quiz, etudiant=request.user)
        points_obtenus = 0
        total_points = 0
        
        for question in quiz.questions.all():
            reponse_id = request.POST.get(f'question_{question.id}')
            total_points += question.points
            if reponse_id:
                reponse = ReponsePossible.objects.filter(id=reponse_id, question=question).first()
                est_correcte = reponse and reponse.est_correcte
                if est_correcte:
                    points_obtenus += question.points
                ReponseEtudiant.objects.create(
                    tentative=tentative, question=question,
                    reponse_id=int(reponse_id) if reponse_id else None,
                    est_correcte=est_correcte, points_obtenus=question.points if est_correcte else 0
                )
        
        note = (points_obtenus / total_points) * 20 if total_points > 0 else 0
        tentative.note = note
        tentative.date_fin = timezone.now()
        tentative.save()
        
        messages.success(request, f'Note : {note:.1f}/20')
        return redirect('quiz_resultat', quiz_id=quiz.id, tentative_id=tentative.id)
    
    questions = list(quiz.questions.all())
    if quiz.shuffle_questions:
        random.shuffle(questions)
    
    return render(request, 'website/quiz/faire.html', {'quiz': quiz, 'questions': questions})

@login_required
def quiz_resultat(request, quiz_id, tentative_id):
    tentative = get_object_or_404(TentativeQuiz, id=tentative_id, etudiant=request.user)
    return render(request, 'website/quiz/resultat.html', {'quiz': tentative.quiz, 'tentative': tentative, 'reponses': tentative.reponses.all()})


@login_required
def reponse_ajouter(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.user.role not in [Utilisateur.ENSEIGNANT, Utilisateur.ADMIN_ECOLE, Utilisateur.SUPER_ADMIN]:
        messages.error(request, 'Droits insuffisants.')
        return redirect('quiz_detail', quiz_id=question.quiz.id)
    
    if request.method == 'POST':
        form = ReponsePossibleForm(request.POST)
        if form.is_valid():
            reponse = form.save(commit=False)
            reponse.question = question
            reponse.save()
            messages.success(request, 'Réponse ajoutée.')
            return redirect('quiz_detail', quiz_id=question.quiz.id)
    else:
        form = ReponsePossibleForm()
    return render(request, 'website/quiz/reponse_ajouter.html', {'form': form, 'question': question})

# ==================== DEVOIRS ====================
@login_required
def devoir_creer(request, specialite_id):
    specialite = get_object_or_404(Specialite, id=specialite_id)
    if request.user.role not in [Utilisateur.ENSEIGNANT, Utilisateur.ADMIN_ECOLE, Utilisateur.SUPER_ADMIN]:
        messages.error(request, 'Droits insuffisants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DevoirForm(request.POST, request.FILES)
        if form.is_valid():
            devoir = form.save(commit=False)
            devoir.specialite = specialite
            devoir.save()
            messages.success(request, 'Devoir créé.')
            return redirect('devoir_detail', devoir_id=devoir.id)
    else:
        form = DevoirForm()
    return render(request, 'website/devoir/creer.html', {'form': form, 'specialite': specialite})

@login_required
def devoir_detail(request, devoir_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    user = request.user
    est_inscrit = InscriptionEtudiant.objects.filter(etudiant=user, specialite=devoir.specialite).exists()
    est_enseignant = EnseignantEcole.objects.filter(enseignant=user, ecole=devoir.specialite.filiere.ecole).exists()
    est_admin = user.role in [Utilisateur.ADMIN_ECOLE, Utilisateur.SUPER_ADMIN]
    
    if not (est_inscrit or est_enseignant or est_admin):
        messages.error(request, 'Accès non autorisé.')
        return redirect('mes_cours')
    
    soumission = None
    if user.role == Utilisateur.ETUDIANT and est_inscrit:
        soumission = SoumissionDevoir.objects.filter(devoir=devoir, etudiant=user).first()
    
    return render(request, 'website/devoir/detail.html', {'devoir': devoir, 'soumission': soumission, 'est_enseignant': est_enseignant or est_admin})

# ==================== PAGES PUBLIQUES DES ÉCOLES ====================
def ecoles_liste(request):
    ecoles = Ecole.objects.filter(actif=True).select_related('abonnement')
    q = request.GET.get('q', '')
    if q:
        ecoles = ecoles.filter(models.Q(nom__icontains=q) | models.Q(ville__icontains=q) | models.Q(pays__icontains=q))
    ecoles = ecoles.order_by('-abonnement__ordre', 'nom')
    return render(request, 'website/ecoles/liste.html', {'ecoles': ecoles, 'q': q})

def ecole_detail(request, slug):
    ecole = get_object_or_404(Ecole, slug=slug, actif=True)
    filieres = Filiere.objects.filter(ecole=ecole, public=True).prefetch_related('specialites')  # ← AJOUTER public=True
    return render(request, 'website/ecoles/detail.html', {'ecole': ecole, 'filieres': filieres})

# ==================== MESSAGERIE ====================
@login_required
def messages_liste(request):
    """Liste des conversations de l'utilisateur"""
    from .models import Conversation, MessagePrive
    
    # Récupérer les conversations où l'utilisateur est participant
    conversations = Conversation.objects.filter(
        models.Q(expediteur=request.user) | models.Q(destinataire=request.user)
    ).order_by('-date_modification')
    
    conversations_data = []
    for conv in conversations:
        if conv.expediteur == request.user:
            autre = conv.destinataire
        else:
            autre = conv.expediteur
        
        # Récupérer le dernier message
        dernier_message = conv.messages.order_by('-date_envoi').first()
        
        # Marquer les messages non lus comme lus
        MessagePrive.objects.filter(
            conversation=conv,
            destinataire=request.user,
            lu=False
        ).update(lu=True)
        
        conversations_data.append({
            'id': conv.id,
            'autre_utilisateur': autre,
            'dernier_message': dernier_message,
        })
    
    context = {
        'conversations': conversations_data,
        'messages_non_lus': 0
    }
    return render(request, 'website/messages/liste.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """Affiche une conversation spécifique"""
    from .models import Conversation, MessagePrive
    
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Vérifier que l'utilisateur est participant
    if conversation.expediteur != request.user and conversation.destinataire != request.user:
        messages.error(request, 'Accès non autorisé.')
        return redirect('messages_liste')
    
    # Marquer les messages comme lus
    MessagePrive.objects.filter(
        conversation=conversation,
        destinataire=request.user,
        lu=False
    ).update(lu=True)
    
    messages_list = MessagePrive.objects.filter(conversation=conversation).order_by('date_envoi')
    
    # Récupérer toutes les conversations pour la sidebar
    conversations = Conversation.objects.filter(
        models.Q(expediteur=request.user) | models.Q(destinataire=request.user)
    ).order_by('-date_modification')
    
    conversations_data = []
    for conv in conversations:
        if conv.expediteur == request.user:
            autre = conv.destinataire
        else:
            autre = conv.expediteur
        dernier_message = conv.messages.order_by('-date_envoi').first()
        conversations_data.append({
            'id': conv.id,
            'autre_utilisateur': autre,
            'dernier_message': dernier_message,
        })
    
    context = {
        'conversations': conversations_data,
        'conversation_active': conversation.id,
        'conversation': conversation,
        'messages': messages_list,
        'autre_utilisateur': conversation.expediteur if conversation.destinataire == request.user else conversation.destinataire,
        'messages_non_lus': 0
    }
    return render(request, 'website/messages/liste.html', context)


@login_required
def message_envoyer(request, destinataire_id=None):
    """Envoyer un nouveau message"""
    from .models import Conversation, MessagePrive, Notification
    
    if request.method == 'POST':
        destinataire_id = request.POST.get('destinataire')
        contenu = request.POST.get('contenu')
        
        if not destinataire_id or not contenu:
            messages.error(request, 'Veuillez remplir tous les champs.')
            return redirect('message_envoyer')
        
        destinataire = get_object_or_404(Utilisateur, id=destinataire_id)
        
        if destinataire == request.user:
            messages.error(request, 'Vous ne pouvez pas vous envoyer un message.')
            return redirect('message_envoyer')
        
        # Trouver ou créer la conversation
        conversation = Conversation.objects.filter(
            expediteur=request.user, destinataire=destinataire
        ).first()
        if not conversation:
            conversation = Conversation.objects.filter(
                expediteur=destinataire, destinataire=request.user
            ).first()
        if not conversation:
            conversation = Conversation.objects.create(
                expediteur=request.user, destinataire=destinataire
            )
        
        # Créer le message
        MessagePrive.objects.create(
            conversation=conversation,
            expediteur=request.user,
            destinataire=destinataire,
            contenu=contenu
        )
        
        conversation.date_modification = timezone.now()
        conversation.save()
        
        # Notification
        Notification.objects.create(
            utilisateur=destinataire,
            type_notification='nouveau_message',
            titre='Nouveau message',
            message=f"{request.user.prenom or request.user.username} vous a envoyé un message.",
            lien=f'/messages/conv/{conversation.id}/'
        )
        
        messages.success(request, 'Message envoyé avec succès.')
        return redirect('conversation_detail', conversation_id=conversation.id)
    
    # GET - Formulaire
    utilisateurs = Utilisateur.objects.exclude(id=request.user.id)
    return render(request, 'website/messages/envoyer.html', {
        'utilisateurs': utilisateurs,
        'messages_non_lus': MessagePrive.objects.filter(destinataire=request.user, lu=False).count()
    })
@login_required
@super_admin_required
def super_admin_ecole_modifier(request, ecole_id):
    """Modifier une école"""
    ecole = get_object_or_404(Ecole, id=ecole_id)
    
    if request.method == 'POST':
        form = EcoleCreationForm(request.POST, request.FILES, instance=ecole)
        if form.is_valid():
            form.save()
            messages.success(request, f'L\'école "{ecole.nom}" a été modifiée.')
            return redirect('super_admin_ecole_liste')
    else:
        form = EcoleCreationForm(instance=ecole)
    
    return render(request, 'website/super_admin/ecoles/modifier.html', {
        'form': form,
        'ecole': ecole
    })


@login_required
@super_admin_required
def super_admin_ecole_supprimer(request, ecole_id):
    """Supprimer une école"""
    ecole = get_object_or_404(Ecole, id=ecole_id)
    nom = ecole.nom
    
    if ecole.enseignants.exists() or ecole.filieres.exists():
        messages.error(request, f'Impossible de supprimer "{nom}" car elle a des données associées.')
        return redirect('super_admin_ecole_liste')
    
    ecole.delete()
    messages.success(request, f'L\'école "{nom}" a été supprimée.')
    return redirect('super_admin_ecole_liste')

@login_required
@super_admin_required
def super_admin_abonnement_liste(request):
    abonnements = Abonnement.objects.all()
    return render(request, 'website/super_admin/abonnements/liste.html', {'abonnements': abonnements})

@login_required
@super_admin_required
def super_admin_abonnement_creer(request):
    if request.method == 'POST':
        form = AbonnementForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pack créé.')
            return redirect('super_admin_abonnement_liste')
    else:
        form = AbonnementForm()
    return render(request, 'website/super_admin/abonnements/creer.html', {'form': form})

@login_required
@super_admin_required
def super_admin_abonnement_modifier(request, abonnement_id):
    abonnement = get_object_or_404(Abonnement, id=abonnement_id)
    if request.method == 'POST':
        form = AbonnementForm(request.POST, instance=abonnement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pack modifié.')
            return redirect('super_admin_abonnement_liste')
    else:
        form = AbonnementForm(instance=abonnement)
    return render(request, 'website/super_admin/abonnements/modifier.html', {'form': form, 'abonnement': abonnement})

@login_required
@super_admin_required
def super_admin_abonnement_supprimer(request, abonnement_id):
    abonnement = get_object_or_404(Abonnement, id=abonnement_id)
    if abonnement.ecole_set.exists():
        messages.error(request, 'Des écoles utilisent ce pack.')
        return redirect('super_admin_abonnement_liste')
    abonnement.delete()
    messages.success(request, 'Pack supprimé.')
    return redirect('super_admin_abonnement_liste')

@login_required
def cours_detail(request, cours_id):
    cours = get_object_or_404(CoursProgramme, id=cours_id)
    user = request.user
    
    # Vérifier l'accès selon le rôle
    est_inscrit = InscriptionEtudiant.objects.filter(etudiant=user, specialite=cours.specialite).exists()
    est_enseignant = EnseignantEcole.objects.filter(enseignant=user, ecole=cours.specialite.filiere.ecole).exists()
    est_admin = user.role in ['admin_ecole', 'super_admin']
    
    if not (est_inscrit or est_enseignant or est_admin):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    # Récupérer les séances
    seances = cours.seances_programmees.all().order_by('ordre', 'jour', 'heure_debut')
    
    # Calculer la progression pour l'étudiant
    progression = None
    seances_terminees = 0
    seances_total = seances.count()
    seances_vues = []
    
    if user.role == 'etudiant' and est_inscrit:
        seances_vues = PresenceSeance.objects.filter(
            etudiant=user,
            seance__in=seances,
            vu=True
        ).values_list('seance_id', flat=True)
        seances_terminees = len(seances_vues)
        progression = int((seances_terminees / seances_total) * 100) if seances_total > 0 else 0
    
    # Récupérer les devoirs, quiz, visios, notes
    devoirs = Devoir.objects.filter(specialite=cours.specialite)
    quizs = Quiz.objects.filter(specialite=cours.specialite)
    visios = seances.filter(type_seance='visio')
    notes = NoteEtudiant.objects.filter(etudiant=user, cours=cours) if user.role == 'etudiant' else []
    
    # Calculer la durée totale estimée
    duree_totale = sum([s.duree_estimee for s in seances]) // 60
    
    # Statut du cours
    statut = 'termine' if progression == 100 else 'en_cours'
    
    context = {
        'cours': cours,
        'seances': seances,
        'seances_vues': seances_vues,
        'seances_terminees': seances_terminees,
        'seances_total': seances_total,
        'progression': progression,
        'statut': statut,
        'duree_totale': duree_totale,
        'devoirs': devoirs,
        'quizs': quizs,
        'visios': visios,
        'notes': notes,
        'est_enseignant': est_enseignant or est_admin,
    }
    
    return render(request, 'website/cours/detail.html', context)


@login_required
def seance_ajouter(request, cours_id):
    """Ajouter une séance à un cours"""
    cours = get_object_or_404(Cours, id=cours_id)
    
    # Vérifier les droits
    if request.user.role not in [Utilisateur.ENSEIGNANT, Utilisateur.ADMIN_ECOLE, Utilisateur.SUPER_ADMIN]:
        messages.error(request, 'Vous n\'avez pas les droits pour ajouter une séance.')
        return redirect('cours_detail', cours_id=cours.id)
    
    if request.user.role == Utilisateur.ENSEIGNANT:
        if not EnseignantEcole.objects.filter(enseignant=request.user, ecole=cours.specialite.filiere.ecole).exists():
            messages.error(request, 'Vous n\'avez pas les droits pour ajouter une séance.')
            return redirect('cours_detail', cours_id=cours.id)
    
    if request.method == 'POST':
        form = SeanceForm(request.POST, request.FILES)
        if form.is_valid():
            seance = form.save(commit=False)
            seance.cours = cours
            seance.save()
            messages.success(request, f'La séance "{seance.titre}" a été ajoutée.')
            return redirect('cours_detail', cours_id=cours.id)
    else:
        form = SeanceForm()
    
    return render(request, 'website/enseignant/seance_ajouter.html', {
        'form': form,
        'cours': cours,
        'messages_non_lus': 0
    })


@login_required
def seance_detail(request, seance_id):
    """Afficher le détail d'une séance"""
    seance = get_object_or_404(SeanceProgrammee, id=seance_id)
    cours = seance.cours
    user = request.user
    
    # Vérifier l'accès
    est_inscrit = InscriptionEtudiant.objects.filter(
        etudiant=user, specialite=cours.specialite
    ).exists()
    est_enseignant = EnseignantEcole.objects.filter(
        enseignant=user, ecole=cours.specialite.filiere.ecole
    ).exists()
    est_admin = user.role in [Utilisateur.ADMIN_ECOLE, Utilisateur.SUPER_ADMIN]
    
    if not (est_inscrit or est_enseignant or est_admin):
        messages.error(request, 'Accès non autorisé.')
        return redirect('mes_cours')
    
    # Vérifier si la séance est terminée
    est_terminee = False
    if user.role == Utilisateur.ETUDIANT and est_inscrit:
        progression, _ = ProgressionEtudiant.objects.get_or_create(etudiant=user, cours=cours)
        est_terminee = progression.seance_terminees.filter(id=seance.id).exists()
    
    # ===== NOUVEAU : Pour chaque exercice de type quiz, vérifier si l'étudiant a déjà répondu =====
    for exercice in seance.exercices.all():
        if exercice.type_exercice == 'quiz':
            exercice.user_a_repondu = ReponseExercice.objects.filter(
                exercice=exercice, 
                etudiant=user
            ).exists()
    
    return render(request, 'website/cours/seance_detail.html', {
        'seance': seance,
        'cours': cours,
        'est_terminee': est_terminee,
        'est_enseignant': est_enseignant or est_admin,
        'messages_non_lus': 0
    })


@login_required
def seance_terminer(request, seance_id):
    """Marquer une séance comme terminée (pour les étudiants)"""
    seance = get_object_or_404(Seance, id=seance_id)
    cours = seance.cours
    
    if request.user.role != Utilisateur.ETUDIANT:
        messages.error(request, 'Seuls les étudiants peuvent marquer une séance comme terminée.')
        return redirect('seance_detail', seance_id=seance.id)
    
    est_inscrit = InscriptionEtudiant.objects.filter(
        etudiant=request.user, specialite=cours.specialite
    ).exists()
    
    if not est_inscrit:
        messages.error(request, 'Vous n\'êtes pas inscrit à ce cours.')
        return redirect('mes_cours')
    
    progression, _ = ProgressionEtudiant.objects.get_or_create(etudiant=request.user, cours=cours)
    progression.seance_terminees.add(seance)
    messages.success(request, f'Félicitations ! Vous avez terminé "{seance.titre}".')
    
    return redirect('cours_detail', cours_id=cours.id)

# ==================== QUIZ ====================
@login_required
def quiz_creer(request, specialite_id):
    specialite = get_object_or_404(Specialite, id=specialite_id)
    if request.user.role not in [Utilisateur.ENSEIGNANT, Utilisateur.ADMIN_ECOLE, Utilisateur.SUPER_ADMIN]:
        messages.error(request, 'Droits insuffisants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.specialite = specialite
            quiz.save()
            messages.success(request, 'Quiz créé.')
            return redirect('quiz_detail', quiz_id=quiz.id)
    else:
        form = QuizForm()
    return render(request, 'website/quiz/creer.html', {'form': form, 'specialite': specialite})


@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    user = request.user
    est_inscrit = InscriptionEtudiant.objects.filter(etudiant=user, specialite=quiz.specialite).exists()
    est_enseignant = EnseignantEcole.objects.filter(enseignant=user, ecole=quiz.specialite.filiere.ecole).exists()
    est_admin = user.role in [Utilisateur.ADMIN_ECOLE, Utilisateur.SUPER_ADMIN]
    
    if not (est_inscrit or est_enseignant or est_admin):
        messages.error(request, 'Accès non autorisé.')
        return redirect('mes_cours')
    
    return render(request, 'website/quiz/detail.html', {'quiz': quiz, 'questions': quiz.questions.all(), 'est_enseignant': est_enseignant or est_admin})


@login_required
def quiz_faire(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.user.role != Utilisateur.ETUDIANT:
        messages.error(request, 'Réservé aux étudiants.')
        return redirect('quiz_detail', quiz_id=quiz.id)
    
    est_inscrit = InscriptionEtudiant.objects.filter(etudiant=request.user, specialite=quiz.specialite).exists()
    if not est_inscrit:
        messages.error(request, 'Vous n\'êtes pas inscrit.')
        return redirect('mes_cours')
    
    if request.method == 'POST':
        tentative = TentativeQuiz.objects.create(quiz=quiz, etudiant=request.user)
        points_obtenus = 0
        total_points = 0
        
        for question in quiz.questions.all():
            reponse_id = request.POST.get(f'question_{question.id}')
            total_points += question.points
            if reponse_id:
                reponse = ReponsePossible.objects.filter(id=reponse_id, question=question).first()
                est_correcte = reponse and reponse.est_correcte
                if est_correcte:
                    points_obtenus += question.points
                ReponseEtudiant.objects.create(
                    tentative=tentative, question=question,
                    reponse_id=int(reponse_id) if reponse_id else None,
                    est_correcte=est_correcte, points_obtenus=question.points if est_correcte else 0
                )
        
        note = (points_obtenus / total_points) * 20 if total_points > 0 else 0
        tentative.note = note
        tentative.date_fin = timezone.now()
        tentative.save()
        
        messages.success(request, f'Note : {note:.1f}/20')
        return redirect('quiz_resultat', quiz_id=quiz.id, tentative_id=tentative.id)
    
    questions = list(quiz.questions.all())
    if quiz.shuffle_questions:
        random.shuffle(questions)
    
    return render(request, 'website/quiz/faire.html', {'quiz': quiz, 'questions': questions})


@login_required
def quiz_resultat(request, quiz_id, tentative_id):
    tentative = get_object_or_404(TentativeQuiz, id=tentative_id, etudiant=request.user)
    return render(request, 'website/quiz/resultat.html', {'quiz': tentative.quiz, 'tentative': tentative, 'reponses': tentative.reponses.all()})


def question_ajouter(request, exercice_id):
    """Ajouter une question à un quiz (exercice de type quiz)"""
    exercice = get_object_or_404(ExerciceApplication, id=exercice_id, type_exercice='quiz')
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = exercice
            question.save()
            messages.success(request, 'Question ajoutée avec succès.')
            return redirect('quiz_detail', exercice_id=exercice.id)
    else:
        form = QuestionForm()
    
    return render(request, 'website/quiz/question_ajouter.html', {
        'form': form,
        'exercice': exercice
    })

@login_required
def reponse_ajouter(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.user.role not in [Utilisateur.ENSEIGNANT, Utilisateur.ADMIN_ECOLE, Utilisateur.SUPER_ADMIN]:
        messages.error(request, 'Droits insuffisants.')
        return redirect('quiz_detail', quiz_id=question.quiz.id)
    
    if request.method == 'POST':
        form = ReponsePossibleForm(request.POST)
        if form.is_valid():
            reponse = form.save(commit=False)
            reponse.question = question
            reponse.save()
            messages.success(request, 'Réponse ajoutée.')
            return redirect('quiz_detail', quiz_id=question.quiz.id)
    else:
        form = ReponsePossibleForm()
    return render(request, 'website/quiz/reponse_ajouter.html', {'form': form, 'question': question})


# ==================== DEVOIRS ====================
@login_required
def devoir_creer(request, specialite_id):
    specialite = get_object_or_404(Specialite, id=specialite_id)
    if request.user.role not in [Utilisateur.ENSEIGNANT, Utilisateur.ADMIN_ECOLE, Utilisateur.SUPER_ADMIN]:
        messages.error(request, 'Droits insuffisants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DevoirForm(request.POST, request.FILES)
        if form.is_valid():
            devoir = form.save(commit=False)
            devoir.specialite = specialite
            devoir.save()
            messages.success(request, 'Devoir créé.')
            return redirect('devoir_detail', devoir_id=devoir.id)
    else:
        form = DevoirForm()
    return render(request, 'website/devoir/creer.html', {'form': form, 'specialite': specialite})


@login_required
def devoir_detail(request, devoir_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    user = request.user
    est_inscrit = InscriptionEtudiant.objects.filter(etudiant=user, specialite=devoir.specialite).exists()
    est_enseignant = EnseignantEcole.objects.filter(enseignant=user, ecole=devoir.specialite.filiere.ecole).exists()
    est_admin = user.role in [Utilisateur.ADMIN_ECOLE, Utilisateur.SUPER_ADMIN]
    
    if not (est_inscrit or est_enseignant or est_admin):
        messages.error(request, 'Accès non autorisé.')
        return redirect('mes_cours')
    
    soumission = None
    if user.role == Utilisateur.ETUDIANT and est_inscrit:
        soumission = SoumissionDevoir.objects.filter(devoir=devoir, etudiant=user).first()
    
    return render(request, 'website/devoir/detail.html', {'devoir': devoir, 'soumission': soumission, 'est_enseignant': est_enseignant or est_admin})


@login_required
def devoir_soumettre(request, devoir_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    
    if request.user.role != Utilisateur.ETUDIANT:
        messages.error(request, 'Seuls les étudiants peuvent soumettre.')
        return redirect('devoir_detail', devoir_id=devoir.id)
    
    est_inscrit = InscriptionEtudiant.objects.filter(etudiant=request.user, specialite=devoir.specialite).exists()
    if not est_inscrit:
        messages.error(request, 'Vous n\'êtes pas inscrit.')
        return redirect('mes_cours')
    
    if request.method == 'POST':
        texte_reponse = request.POST.get('texte_reponse', '')
        soumission, created = SoumissionDevoir.objects.get_or_create(
            devoir=devoir,
            etudiant=request.user,
            defaults={'texte_reponse': texte_reponse}
        )
        
        if not created:
            soumission.texte_reponse = texte_reponse
            soumission.date_soumission = timezone.now()
            soumission.save()
        
        # Gérer les fichiers
        if 'fichier' in request.FILES:
            for f in request.FILES.getlist('fichier'):
                FichierSoumission.objects.create(
                    soumission=soumission,
                    fichier=f,
                    nom_original=f.name,
                    taille=f.size
                )
        
        messages.success(request, 'Devoir soumis.')
        return redirect('devoir_detail', devoir_id=devoir.id)
    
    return render(request, 'website/devoir/soumettre.html', {'devoir': devoir})


@login_required
def devoir_corriger(request, devoir_id, soumission_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    soumission = get_object_or_404(SoumissionDevoir, id=soumission_id, devoir=devoir)
    
    if request.user.role not in [Utilisateur.ENSEIGNANT, Utilisateur.ADMIN_ECOLE, Utilisateur.SUPER_ADMIN]:
        messages.error(request, 'Droits insuffisants.')
        return redirect('devoir_detail', devoir_id=devoir.id)
    
    if request.method == 'POST':
        note = request.POST.get('note')
        feedback = request.POST.get('feedback')
        
        soumission.note = float(note) if note else None
        soumission.feedback = feedback
        soumission.save()
        
        messages.success(request, 'Correction enregistrée.')
        return redirect('devoir_detail', devoir_id=devoir.id)
    
    return render(request, 'website/devoir/corriger.html', {'devoir': devoir, 'soumission': soumission})
@login_required
def enseignant_cours_liste(request):
    """Liste des cours créés par l'enseignant"""
    if request.user.role != Utilisateur.ENSEIGNANT:
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    # Récupérer les cours de l'enseignant
    ecoles = Ecole.objects.filter(enseignants__enseignant=request.user)
    cours = []
    for ecole in ecoles:
        for c in Cours.objects.filter(specialite__filiere__ecole=ecole, actif=True):
            cours.append(c)
    
    return render(request, 'website/enseignant/cours_liste.html', {'cours': cours})

def ecoles_liste(request):
    ecoles = Ecole.objects.filter(actif=True).select_related('abonnement')
    q = request.GET.get('q', '')
    if q:
        ecoles = ecoles.filter(
            models.Q(nom__icontains=q) | 
            models.Q(ville__icontains=q) | 
            models.Q(pays__icontains=q)
        )
    ecoles = ecoles.order_by('-abonnement__ordre', 'nom')
    return render(request, 'website/ecoles/liste.html', {'ecoles': ecoles, 'q': q})

def ecole_detail(request, slug):
    ecole = get_object_or_404(Ecole, slug=slug, actif=True)
    filieres = Filiere.objects.filter(ecole=ecole).prefetch_related('specialites')
    return render(request, 'website/ecoles/detail.html', {'ecole': ecole, 'filieres': filieres})
# ==================== ADMIN ÉCOLE ====================
@login_required
def admin_ecole_modifier(request):
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Vous n\'êtes pas associé à une école.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Récupérer toutes les données
        ecole.nom = request.POST.get('nom', ecole.nom)
        ecole.description = request.POST.get('description', ecole.description)
        ecole.email = request.POST.get('email', ecole.email)
        ecole.telephone = request.POST.get('telephone', ecole.telephone)
        ecole.ville = request.POST.get('ville', ecole.ville)
        ecole.pays = request.POST.get('pays', ecole.pays)
        ecole.quartier = request.POST.get('quartier', ecole.quartier)
        ecole.numero_agrement = request.POST.get('numero_agrement', ecole.numero_agrement)
        
        # Réseaux sociaux
        ecole.facebook = request.POST.get('facebook', '')
        ecole.twitter = request.POST.get('twitter', '')
        ecole.instagram = request.POST.get('instagram', '')
        ecole.youtube = request.POST.get('youtube', '')
        ecole.linkedin = request.POST.get('linkedin', '')
        
        # Logo et bannière
        if request.FILES.get('logo'):
            ecole.logo = request.FILES['logo']
        if request.FILES.get('banniere'):
            ecole.banniere = request.FILES['banniere']
        
        ecole.save()
        messages.success(request, 'Informations de l\'école mises à jour.')
        return redirect('dashboard')
    
    return render(request, 'website/admin_ecole/ecole/modifier.html', {'ecole': ecole})

@login_required
def admin_ecole_changer_logo(request):
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    if request.method == 'POST' and request.FILES.get('logo'):
        ecole.logo = request.FILES['logo']
        ecole.save()
        messages.success(request, 'Logo modifié avec succès.')
    
    return redirect('dashboard')


@login_required
def admin_ecole_galerie(request):
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    images = ecole.galerie_images.all()
    return render(request, 'website/admin_ecole/ecole/galerie.html', {'images': images, 'ecole': ecole})


@login_required
def admin_ecole_galerie_ajouter(request):
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    if request.method == 'POST' and request.FILES.get('image'):
        ImageEcole.objects.create(
            ecole=ecole,
            image=request.FILES['image'],
            titre=request.POST.get('titre', '')
        )
        messages.success(request, 'Photo ajoutée avec succès.')
    
    return redirect('admin_ecole_galerie')


@login_required
def admin_ecole_galerie_supprimer(request, image_id):
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    from .models import ImageEcole
    image = get_object_or_404(ImageEcole, id=image_id, ecole=ecole)
    image.delete()
    messages.success(request, 'Photo supprimée.')
    return redirect('admin_ecole_galerie')


@login_required
def admin_ecole_utilisateurs(request):
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    enseignants = Utilisateur.objects.filter(enseignant_ecoles__ecole=ecole)
    etudiants = Utilisateur.objects.filter(inscriptions__specialite__filiere__ecole=ecole).distinct()
    
    return render(request, 'website/admin_ecole/utilisateurs/liste.html', {
        'ecole': ecole,
        'enseignants': enseignants,
        'etudiants': etudiants
    })


@login_required
def admin_ecole_generer_cle(request):
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    filieres = Filiere.objects.filter(ecole=ecole).prefetch_related('specialites')
    cle_generer = None
    
    if request.method == 'POST':
        role = request.POST.get('role')
        specialite_id = request.POST.get('specialite')
        
        # Générer une clé unique
        import uuid
        cle = f"{ecole.slug}_{role}_{uuid.uuid4().hex[:8]}".upper()
        
        # Stocker la clé en session ou en base (à implémenter)
        # Pour l'instant, on affiche juste
        cle_generer = cle
        
        # Envoyer par email si renseigné
        email = request.POST.get('email')
        if email:
            # À implémenter: envoi d'email
            pass
        
        messages.success(request, 'Clé générée avec succès.')
    
    return render(request, 'website/admin_ecole/utilisateurs/generer_cle.html', {
        'ecole': ecole,
        'filieres': filieres,
        'cle_generer': cle_generer
    })


@login_required
def admin_ecole_utilisateur_modifier(request, user_id):
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    
    # Vérifier que l'utilisateur appartient bien à l'école
    est_enseignant = EnseignantEcole.objects.filter(enseignant=utilisateur, ecole=ecole).exists()
    est_etudiant = InscriptionEtudiant.objects.filter(etudiant=utilisateur, specialite__filiere__ecole=ecole).exists()
    
    if not (est_enseignant or est_etudiant):
        messages.error(request, 'Cet utilisateur n\'appartient pas à votre école.')
        return redirect('admin_ecole_utilisateurs')
    
    if request.method == 'POST':
        utilisateur.prenom = request.POST.get('prenom', utilisateur.prenom)
        utilisateur.email = request.POST.get('email', utilisateur.email)
        utilisateur.telephone = request.POST.get('telephone', utilisateur.telephone)
        utilisateur.pays = request.POST.get('pays', utilisateur.pays)
        utilisateur.is_active = request.POST.get('is_active') == 'on'
        utilisateur.save()
        messages.success(request, 'Utilisateur modifié.')
        return redirect('admin_ecole_utilisateurs')
    
    return render(request, 'website/admin_ecole/utilisateurs/modifier.html', {'utilisateur': utilisateur})


@login_required
def admin_ecole_utilisateur_supprimer(request, user_id):
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    
    # Vérifier que l'utilisateur appartient à l'école
    est_enseignant = EnseignantEcole.objects.filter(enseignant=utilisateur, ecole=ecole).exists()
    est_etudiant = InscriptionEtudiant.objects.filter(etudiant=utilisateur, specialite__filiere__ecole=ecole).exists()
    
    if not (est_enseignant or est_etudiant):
        messages.error(request, 'Cet utilisateur n\'appartient pas à votre école.')
        return redirect('admin_ecole_utilisateurs')
    
    utilisateur.delete()
    messages.success(request, 'Utilisateur supprimé.')
    return redirect('admin_ecole_utilisateurs')

# ==================== SUPER ADMIN - GESTION DÉTAILLÉE DES ÉCOLES ====================
@login_required
@super_admin_required
def super_admin_ecole_detail(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    filieres = Filiere.objects.filter(ecole=ecole).prefetch_related('specialites')
    enseignants = Utilisateur.objects.filter(enseignant_ecoles__ecole=ecole)
    etudiants = Utilisateur.objects.filter(inscriptions__specialite__filiere__ecole=ecole).distinct()
    cours_count = Cours.objects.filter(specialite__filiere__ecole=ecole).count()
    
    return render(request, 'website/super_admin/ecoles/detail.html', {
        'ecole': ecole,
        'filieres': filieres,
        'enseignants': enseignants,
        'etudiants': etudiants,
        'cours_count': cours_count
    })


@login_required
@super_admin_required
def super_admin_ecole_changer_logo(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    if request.method == 'POST' and request.FILES.get('logo'):
        ecole.logo = request.FILES['logo']
        ecole.save()
        messages.success(request, 'Logo modifié.')
    return redirect('super_admin_ecole_detail', ecole_id=ecole.id)


@login_required
@super_admin_required
def super_admin_ecole_galerie(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    images = ecole.galerie_images.all()
    return render(request, 'website/super_admin/ecoles/galerie.html', {'ecole': ecole, 'images': images})


@login_required
@super_admin_required
def super_admin_ecole_galerie_ajouter(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    if request.method == 'POST' and request.FILES.get('image'):
        from .models import ImageEcole
        ImageEcole.objects.create(
            ecole=ecole,
            image=request.FILES['image'],
            titre=request.POST.get('titre', '')
        )
        messages.success(request, 'Photo ajoutée.')
    return redirect('super_admin_ecole_galerie', ecole_id=ecole.id)


@login_required
@super_admin_required
def super_admin_ecole_galerie_supprimer(request, ecole_id, image_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    from .models import ImageEcole
    image = get_object_or_404(ImageEcole, id=image_id, ecole=ecole)
    image.delete()
    messages.success(request, 'Photo supprimée.')
    return redirect('super_admin_ecole_galerie', ecole_id=ecole.id)


@login_required
@super_admin_required
def super_admin_ecole_utilisateurs(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    enseignants = Utilisateur.objects.filter(enseignant_ecoles__ecole=ecole)
    etudiants = Utilisateur.objects.filter(inscriptions__specialite__filiere__ecole=ecole).distinct()
    
    return render(request, 'website/super_admin/ecoles/utilisateurs.html', {
        'ecole': ecole,
        'enseignants': enseignants,
        'etudiants': etudiants
    })


@login_required
@super_admin_required
def super_admin_ecole_utilisateur_modifier(request, ecole_id, user_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    
    if request.method == 'POST':
        utilisateur.prenom = request.POST.get('prenom', utilisateur.prenom)
        utilisateur.email = request.POST.get('email', utilisateur.email)
        utilisateur.telephone = request.POST.get('telephone', utilisateur.telephone)
        utilisateur.pays = request.POST.get('pays', utilisateur.pays)
        utilisateur.is_active = request.POST.get('is_active') == 'on'
        utilisateur.save()
        messages.success(request, 'Utilisateur modifié.')
        return redirect('super_admin_ecole_utilisateurs', ecole_id=ecole.id)
    
    return render(request, 'website/super_admin/utilisateurs/modifier.html', {'utilisateur': utilisateur, 'ecole': ecole})


@login_required
@super_admin_required
def super_admin_ecole_utilisateur_supprimer(request, ecole_id, user_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    utilisateur.delete()
    messages.success(request, 'Utilisateur supprimé.')
    return redirect('super_admin_ecole_utilisateurs', ecole_id=ecole.id)


@login_required
@super_admin_required
def super_admin_ecole_generer_cle(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    filieres = Filiere.objects.filter(ecole=ecole).prefetch_related('specialites')
    cle_generer = None
    
    if request.method == 'POST':
        import uuid
        role = request.POST.get('role')
        specialite_id = request.POST.get('specialite')
        cle = f"{ecole.slug}_{role}_{uuid.uuid4().hex[:8]}".upper()
        cle_generer = cle
        messages.success(request, 'Clé générée.')
    
    return render(request, 'website/super_admin/ecoles/generer_cle.html', {
        'ecole': ecole,
        'filieres': filieres,
        'cle_generer': cle_generer
    })


@login_required
@super_admin_required
def super_admin_ecole_cours(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    cours = Cours.objects.filter(specialite__filiere__ecole=ecole, actif=True)
    return render(request, 'website/super_admin/ecoles/cours.html', {'ecole': ecole, 'cours': cours})

@login_required
@super_admin_required
def super_admin_ecole_supprimer(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    nom = ecole.nom
    
    # Vérifier si l'école a des données associées
    if ecole.filieres.exists():
        messages.error(request, f'Impossible de supprimer "{nom}" car elle contient des filières.')
        return redirect('super_admin_ecole_liste')
    
    ecole.delete()
    messages.success(request, f'L\'école "{nom}" a été supprimée.')
    return redirect('super_admin_ecole_liste')

@login_required
@super_admin_required
def super_admin_filiere_creer(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    
    if request.method == 'POST':
        form = FiliereForm(request.POST)
        if form.is_valid():
            filiere = form.save(commit=False)
            filiere.ecole = ecole
            filiere.save()
            messages.success(request, f'Filière "{filiere.nom}" créée.')
            return redirect('super_admin_ecole_detail', ecole_id=ecole.id)
    else:
        form = FiliereForm()
    
    return render(request, 'website/super_admin/ecoles/filiere_creer.html', {'form': form, 'ecole': ecole})

@login_required
@super_admin_required
def super_admin_specialite_creer(request, filiere_id):
    filiere = get_object_or_404(Filiere, id=filiere_id)
    ecole = filiere.ecole
    
    if request.method == 'POST':
        form = SpecialiteForm(request.POST)
        if form.is_valid():
            specialite = form.save(commit=False)
            specialite.filiere = filiere
            specialite.save()
            messages.success(request, f'Spécialité "{specialite.nom}" créée.')
            return redirect('super_admin_ecole_detail', ecole_id=ecole.id)
    else:
        form = SpecialiteForm()
    
    return render(request, 'website/super_admin/ecoles/specialite_creer.html', {
        'form': form,
        'filiere': filiere,
        'ecole': ecole
    })
@login_required
@super_admin_required
def super_admin_utilisateur_ajouter(request, ecole_id=None):
    ecole_selected = None
    if ecole_id:
        ecole_selected = get_object_or_404(Ecole, id=ecole_id)
    
    ecoles = Ecole.objects.filter(actif=True)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        prenom = request.POST.get('prenom')
        telephone = request.POST.get('telephone')
        pays = request.POST.get('pays')
        password = request.POST.get('password')
        role = request.POST.get('role')
        ecole_id_post = request.POST.get('ecole')
        is_active = request.POST.get('is_active') == 'on'
        
        if Utilisateur.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur existe déjà.')
        elif Utilisateur.objects.filter(email=email).exists():
            messages.error(request, 'Cet email est déjà utilisé.')
        else:
            user = Utilisateur.objects.create_user(
                username=username,
                email=email,
                password=password,
                prenom=prenom,
                telephone=telephone,
                pays=pays,
                role=role,
                is_active=is_active
            )
            
            if ecole_id_post and role in ['admin_ecole', 'enseignant', 'etudiant']:
                ecole = get_object_or_404(Ecole, id=ecole_id_post)
                if role == 'admin_ecole':
                    ecole.admin_ecole = user
                    ecole.save()
                elif role == 'enseignant':
                    EnseignantEcole.objects.get_or_create(enseignant=user, ecole=ecole)
            
            messages.success(request, f'Utilisateur "{username}" créé.')
            
            if ecole_id:
                return redirect('super_admin_ecole_utilisateurs', ecole_id=ecole_id)
            else:
                return redirect('super_admin_utilisateurs')
    
    return render(request, 'website/super_admin/utilisateurs/ajouter.html', {
        'ecoles': ecoles,
        'ecole_selected': ecole_selected
    })

# ==================== COURS ====================
@login_required
def cours_creer(request, specialite_id):
    specialite = get_object_or_404(Specialite, id=specialite_id)
    
    # Vérifier les droits (enseignant, admin ecole, super admin)
    user = request.user
    est_autorise = False
    
    if user.role == 'super_admin':
        est_autorise = True
    elif user.role == 'admin_ecole':
        if user.ecole_admin == specialite.filiere.ecole:
            est_autorise = True
    elif user.role == 'enseignant':
        if EnseignantEcole.objects.filter(enseignant=user, ecole=specialite.filiere.ecole).exists():
            est_autorise = True
    
    if not est_autorise:
        messages.error(request, 'Vous n\'avez pas les droits pour créer un cours dans cette spécialité.')
        return redirect('specialite_detail', specialite_id=specialite.id)
    
    if request.method == 'POST':
        form = CoursProgrammeForm(request.POST)
        if form.is_valid():
            cours = form.save(commit=False)
            cours.specialite = specialite
            cours.created_by = user
            cours.save()
            messages.success(request, f'Le cours "{cours.titre}" a été créé avec succès.')
            return redirect('specialite_detail', specialite_id=specialite.id)
    else:
        form = CoursProgrammeForm(initial={'date_debut': timezone.now().date()})
    
    return render(request, 'website/cours/creer.html', {
        'form': form,
        'specialite': specialite
    })


@login_required
def cours_detail(request, cours_id):
    cours = get_object_or_404(CoursProgramme, id=cours_id)
    
    # Vérifier l'accès
    user = request.user
    est_participant = ParticipantCoursProgramme.objects.filter(cours=cours, etudiant=user).exists()
    est_enseignant = EnseignantEcole.objects.filter(enseignant=user, ecole=cours.specialite.filiere.ecole).exists()
    est_admin = user.role in ['admin_ecole', 'super_admin']
    
    if not (est_participant or est_enseignant or est_admin):
        messages.error(request, 'Vous n\'avez pas accès à ce cours.')
        return redirect('mes_cours')
    
    seances = cours.seances_programmees.all().order_by('ordre', 'jour', 'heure_debut')
    participants = cours.participants.all()
    
    return render(request, 'website/cours/detail.html', {
        'cours': cours,
        'seances': seances,
        'participants': participants,
        'est_enseignant': est_enseignant or est_admin
    })
    
  
@login_required
def specialite_detail(request, specialite_id):
    specialite = get_object_or_404(Specialite, id=specialite_id)
    ecole = specialite.filiere.ecole
    filiere = specialite.filiere
    
    cours_list = CoursProgramme.objects.filter(specialite=specialite, actif=True).order_by('date_debut')
    
    return render(request, 'website/specialite/detail.html', {
        'specialite': specialite,
        'ecole': ecole,
        'filiere': filiere,
        'cours_list': cours_list
    })
    
    
@login_required
def cours_supprimer(request, cours_id):
    cours = get_object_or_404(CoursProgramme, id=cours_id)
    specialite = cours.specialite
    
    # Vérifier les droits
    user = request.user
    est_autorise = False
    
    if user.role == 'super_admin':
        est_autorise = True
    elif user.role == 'admin_ecole':
        if user.ecole_admin == specialite.filiere.ecole:
            est_autorise = True
    elif user.role == 'enseignant':
        if EnseignantEcole.objects.filter(enseignant=user, ecole=specialite.filiere.ecole).exists():
            est_autorise = True
    
    if not est_autorise:
        messages.error(request, 'Vous n\'avez pas les droits pour supprimer ce cours.')
        return redirect('specialite_detail', specialite_id=specialite.id)
    
    titre = cours.titre
    cours.delete()
    messages.success(request, f'Le cours "{titre}" a été supprimé.')
    return redirect('specialite_detail', specialite_id=specialite.id)

@login_required
def specialite_detail(request, specialite_id):
    specialite = get_object_or_404(Specialite, id=specialite_id)
    ecole = specialite.filiere.ecole
    filiere = specialite.filiere
    
    cours_list = CoursProgramme.objects.filter(specialite=specialite, actif=True).order_by('date_debut')
    
    return render(request, 'website/specialite/detail.html', {
        'specialite': specialite,
        'ecole': ecole,
        'filiere': filiere,
        'cours_list': cours_list
    })
    
@login_required
def admin_ecole_specialites_liste(request):
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    specialites = Specialite.objects.filter(filiere__ecole=ecole).select_related('filiere')
    
    return render(request, 'website/admin_ecole/specialites_liste.html', {
        'specialites': specialites,
        'ecole': ecole
    })
    
# ==================== SÉANCES (ENSEIGNANT) ====================

@login_required
def mes_cours_enseignant(request):
    user = request.user
    
    if user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    # Récupérer les écoles où l'enseignant donne des cours
    ecoles = Ecole.objects.filter(enseignants__enseignant=user).distinct()
    
    # Organiser les cours par école et par filière
    data = []
    for ecole in ecoles:
        ecole_data = {
            'ecole': ecole,
            'filieres': []
        }
        
        # Récupérer les filières de cette école où l'enseignant a des cours
        filieres = Filiere.objects.filter(
            ecole=ecole,
            specialites__cours_programmes__enseignant=user
        ).distinct()
        
        for filiere in filieres:
            filiere_data = {
                'filiere': filiere,
                'cours': CoursProgramme.objects.filter(
                    specialite__filiere=filiere,
                    enseignant=user,
                    actif=True
                ).order_by('date_debut')
            }
            ecole_data['filieres'].append(filiere_data)
        
        data.append(ecole_data)
    
    return render(request, 'website/enseignant/mes_cours_assignes.html', {
        'data': data
    })

@login_required
def cours_detail_enseignant(request, cours_id):
    cours = get_object_or_404(CoursProgramme, id=cours_id)
    user = request.user
    
    if cours.enseignant != user and user.role not in ['admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas accès à ce cours.')
        return redirect('dashboard')
    
    # Récupérer les séances
    seances = cours.seances_programmees.all().order_by('ordre', 'jour', 'heure_debut')
    
    # Récupérer les quiz (via les séances)
    quizs = Quiz.objects.filter(seance__in=seances)
    
    # Récupérer les devoirs
    devoirs = Devoir.objects.filter(seance__in=seances)
    
    # Récupérer les exercices
    exercices = ExerciceApplication.objects.filter(seance__in=seances)
    
    context = {
        'cours': cours,
        'seances': seances,
        'quizs': quizs,
        'devoirs': devoirs,
        'exercices': exercices,
        'est_enseignant': True,
    }
    
    return render(request, 'website/enseignant/cours_detail.html', context)


@login_required
def seance_ajouter(request, cours_id):
    """Ajouter une séance à un cours"""
    cours = get_object_or_404(CoursProgramme, id=cours_id, enseignant=request.user)
    
    if request.method == 'POST':
        form = SeanceProgrammeeForm(request.POST, request.FILES)
        if form.is_valid():
            seance = form.save(commit=False)
            seance.cours = cours
            seance.save()
            messages.success(request, f'Séance "{seance.titre}" ajoutée avec succès.')
            return redirect('cours_detail_enseignant', cours_id=cours.id)
    else:
        form = SeanceProgrammeeForm()
    
    return render(request, 'website/enseignant/seance_ajouter.html', {
        'form': form,
        'cours': cours
    })



@login_required
def seance_supprimer(request, seance_id):
    """Supprimer une séance"""
    seance = get_object_or_404(SeanceProgrammee, id=seance_id)
    cours = seance.cours
    
    if cours.enseignant != request.user and request.user.role not in ['admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits pour supprimer cette séance.')
        return redirect('dashboard')
    
    titre = seance.titre
    seance.delete()
    messages.success(request, f'Séance "{titre}" supprimée.')
    return redirect('cours_detail_enseignant', cours_id=cours.id)

@login_required
def mes_cours_enseignant(request):
    """Affiche les cours assignés à l'enseignant"""
    user = request.user
    
    if user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    # Récupérer les cours où l'enseignant est responsable
    cours_list = CoursProgramme.objects.filter(enseignant=user, actif=True).order_by('date_debut')
    
    return render(request, 'website/enseignant/mes_cours_assignes.html', {
        'cours_list': cours_list
    })
    
@login_required
def seance_marquer_vue(request, seance_id):
    seance = get_object_or_404(SeanceProgrammee, id=seance_id)
    
    if request.user.role != 'etudiant':
        messages.error(request, 'Seuls les étudiants peuvent marquer une séance comme vue.')
        return redirect('cours_detail', cours_id=seance.cours.id)
    
    presence, created = PresenceSeance.objects.get_or_create(
        seance=seance,
        etudiant=request.user,
        defaults={'vu': True, 'date_vu': timezone.now()}
    )
    
    if not created:
        presence.vu = True
        presence.date_vu = timezone.now()
        presence.save()
    
    messages.success(request, f'Séance "{seance.titre}" marquée comme vue.')
    return redirect('cours_detail', cours_id=seance.cours.id)

@login_required
def etudiant_mes_cours(request):
    """Vue structurée pour l'étudiant : École → Filière → Spécialité → Cours"""
    user = request.user
    
    if user.role != 'etudiant':
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('dashboard')
    
    # Récupérer toutes les inscriptions de l'étudiant
    inscriptions = InscriptionEtudiant.objects.filter(etudiant=user).select_related('specialite__filiere__ecole')
    
    # Structure: École → Filière → Spécialité → Cours
    data = []
    ecoles_dict = {}
    
    for inscription in inscriptions:
        specialite = inscription.specialite
        filiere = specialite.filiere
        ecole = filiere.ecole
        
        # Chercher ou créer l'école
        if ecole.id not in ecoles_dict:
            ecoles_dict[ecole.id] = {
                'id': ecole.id,
                'nom': ecole.nom,
                'logo': ecole.logo,
                'filieres_dict': {}
            }
        
        # Chercher ou créer la filière dans l'école
        if filiere.id not in ecoles_dict[ecole.id]['filieres_dict']:
            ecoles_dict[ecole.id]['filieres_dict'][filiere.id] = {
                'id': filiere.id,
                'nom': filiere.nom,
                'specialites_dict': {}
            }
        
        # Chercher ou créer la spécialité dans la filière
        if specialite.id not in ecoles_dict[ecole.id]['filieres_dict'][filiere.id]['specialites_dict']:
            # Récupérer la progression pour cette spécialité
            cours_list = CoursProgramme.objects.filter(specialite=specialite, actif=True).order_by('date_debut')
            
            # Calculer la progression globale de la spécialité
            total_seances = 0
            seances_vues = 0
            for cours in cours_list:
                for seance in cours.seances_programmees.all():
                    total_seances += 1
                    if PresenceSeance.objects.filter(seance=seance, etudiant=user, vu=True).exists():
                        seances_vues += 1
            
            progression = int((seances_vues / total_seances) * 100) if total_seances > 0 else 0
            
            ecoles_dict[ecole.id]['filieres_dict'][filiere.id]['specialites_dict'][specialite.id] = {
                'id': specialite.id,
                'nom': specialite.nom,
                'description': specialite.description,
                'progression': progression,
                'cours': list(cours_list)
            }
    
    # Transformer en liste pour le template
    for ecole_id, ecole_data in ecoles_dict.items():
        ecole_item = {
            'id': ecole_data['id'],
            'nom': ecole_data['nom'],
            'logo': ecole_data['logo'],
            'filieres': []
        }
        for filiere_id, filiere_data in ecole_data['filieres_dict'].items():
            filiere_item = {
                'id': filiere_data['id'],
                'nom': filiere_data['nom'],
                'specialites': list(filiere_data['specialites_dict'].values())
            }
            ecole_item['filieres'].append(filiere_item)
        data.append(ecole_item)
    
    return render(request, 'website/etudiant/mes_cours.html', {'data': data})

@login_required
def etudiant_specialite_detail(request, specialite_id):
    specialite = get_object_or_404(Specialite, id=specialite_id)
    user = request.user
    
    # Vérifier que l'étudiant est inscrit
    if not InscriptionEtudiant.objects.filter(etudiant=user, specialite=specialite).exists():
        messages.error(request, 'Vous n\'êtes pas inscrit à cette spécialité.')
        return redirect('etudiant_mes_cours')
    
    cours_list = CoursProgramme.objects.filter(specialite=specialite, actif=True).order_by('date_debut')
    
    # Calculer la progression globale
    total_seances = 0
    seances_vues = 0
    for cours in cours_list:
        for seance in cours.seances_programmees.all():
            total_seances += 1
            if PresenceSeance.objects.filter(seance=seance, etudiant=user, vu=True).exists():
                seances_vues += 1
    progression = int((seances_vues / total_seances) * 100) if total_seances > 0 else 0
    
    return render(request, 'website/etudiant/specialite_detail.html', {
        'specialite': specialite,
        'cours_list': cours_list,
        'progression': progression
    })


@login_required
def etudiant_cours_detail(request, cours_id):
    cours = get_object_or_404(CoursProgramme, id=cours_id)
    user = request.user
    
    # Vérifier que l'étudiant est inscrit à la spécialité
    if not InscriptionEtudiant.objects.filter(etudiant=user, specialite=cours.specialite).exists():
        messages.error(request, 'Vous n\'êtes pas inscrit à ce cours.')
        return redirect('etudiant_mes_cours')
    
    seances = cours.seances_programmees.all().order_by('ordre', 'jour', 'heure_debut')
    
    # Séances déjà vues
    seances_vues = PresenceSeance.objects.filter(
        etudiant=user,
        seance__in=seances,
        vu=True
    ).values_list('seance_id', flat=True)
    
    # Progression
    total_seances = seances.count()
    seances_terminees = len(seances_vues)
    progression = int((seances_terminees / total_seances) * 100) if total_seances > 0 else 0
    
    return render(request, 'website/etudiant/cours_detail.html', {
        'cours': cours,
        'seances': seances,
        'seances_vues': seances_vues,
        'seances_terminees': seances_terminees,
        'seances_total': total_seances,
        'progression': progression
    })
    
@login_required
def enseignant_devoirs_a_corriger(request):
    user = request.user
    
    if user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    # Récupérer les écoles où l'enseignant donne des cours
    ecoles = Ecole.objects.filter(enseignants__enseignant=user)
    
    # Récupérer les soumissions de devoirs pour les cours de l'enseignant
    soumissions = SoumissionDevoir.objects.filter(
        devoir__specialite__cours_programmes__enseignant=user,
        note__isnull=True  # Non encore corrigés
    ).select_related('devoir', 'etudiant', 'devoir__specialite').distinct()
    
    return render(request, 'website/enseignant/devoirs_a_corriger.html', {
        'soumissions': soumissions
    })
@login_required
def enseignant_corriger_devoir(request, soumission_id):
    soumission = get_object_or_404(SoumissionDevoir, id=soumission_id)
    
    # Vérifier que l'enseignant est bien responsable du cours
    user = request.user
    if user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    # Vérifier que l'enseignant donne bien ce cours
    cours_existe = CoursProgramme.objects.filter(
        specialite=soumission.devoir.specialite,
        enseignant=user
    ).exists()
    
    if not cours_existe and user.role != 'super_admin':
        messages.error(request, 'Vous n\'êtes pas autorisé à corriger ce devoir.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        note = request.POST.get('note')
        feedback = request.POST.get('feedback')
        
        soumission.note = float(note) if note else None
        soumission.feedback = feedback
        soumission.save()
        
        messages.success(request, f'Correction enregistrée pour {soumission.etudiant.username}')
        return redirect('enseignant_devoirs_a_corriger')
    
    return render(request, 'website/enseignant/corriger_devoir.html', {
        'soumission': soumission
    })

@login_required
def forum_liste(request):
    return render(request, 'website/forum/liste.html', {'message': 'Forum en construction'})


@login_required
def enseignant_mes_cours(request):
    user = request.user
    
    if user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    # Essayer avec les deux modèles
    cours_list = CoursProgramme.objects.filter(enseignant=user, actif=True)
    
    # Si aucun, essayer avec l'ancien modèle
    if cours_list.count() == 0:
        from .models import Cours
        cours_list = Cours.objects.filter(enseignant=user, actif=True)
    
    # Structure: École → Filière → Spécialité → Cours
    data = []
    ecoles_dict = {}
    
    for cours in cours_list:
        # Adapter selon le modèle
        if hasattr(cours, 'specialite'):
            specialite = cours.specialite
        else:
            continue
            
        filiere = specialite.filiere
        ecole = filiere.ecole
        
        if ecole.id not in ecoles_dict:
            ecoles_dict[ecole.id] = {
                'id': ecole.id,
                'nom': ecole.nom,
                'logo': ecole.logo,
                'filieres_dict': {}
            }
        
        if filiere.id not in ecoles_dict[ecole.id]['filieres_dict']:
            ecoles_dict[ecole.id]['filieres_dict'][filiere.id] = {
                'id': filiere.id,
                'nom': filiere.nom,
                'specialites_dict': {}
            }
        
        if specialite.id not in ecoles_dict[ecole.id]['filieres_dict'][filiere.id]['specialites_dict']:
            ecoles_dict[ecole.id]['filieres_dict'][filiere.id]['specialites_dict'][specialite.id] = {
                'id': specialite.id,
                'nom': specialite.nom,
                'cours': []
            }
        
        ecoles_dict[ecole.id]['filieres_dict'][filiere.id]['specialites_dict'][specialite.id]['cours'].append(cours)
    
    # Transformer en liste pour le template
    for ecole_id, ecole_data in ecoles_dict.items():
        ecole_item = {
            'id': ecole_data['id'],
            'nom': ecole_data['nom'],
            'logo': ecole_data['logo'],
            'filieres': []
        }
        for filiere_id, filiere_data in ecole_data['filieres_dict'].items():
            filiere_item = {
                'id': filiere_data['id'],
                'nom': filiere_data['nom'],
                'specialites': []
            }
            for specialite_id, specialite_data in filiere_data['specialites_dict'].items():
                specialite_item = {
                    'id': specialite_data['id'],
                    'nom': specialite_data['nom'],
                    'cours': specialite_data['cours']
                }
                filiere_item['specialites'].append(specialite_item)
            ecole_item['filieres'].append(filiere_item)
        data.append(ecole_item)
    
    return render(request, 'website/enseignant/mes_cours.html', {'data': data})
@login_required
def enseignant_devoirs_a_corriger(request):
    user = request.user
    
    if user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    # Récupérer les soumissions des devoirs pour les cours de l'enseignant
    soumissions = SoumissionDevoir.objects.filter(
        devoir__specialite__cours_programmes__enseignant=user,
        note__isnull=True
    ).select_related('devoir', 'etudiant', 'devoir__specialite').distinct()
    
    return render(request, 'website/enseignant/devoirs_a_corriger.html', {
        'soumissions': soumissions
    })
    
@login_required
def enseignant_corriger_devoir(request, soumission_id):
    soumission = get_object_or_404(SoumissionDevoir, id=soumission_id)
    user = request.user
    
    if user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        note = request.POST.get('note')
        feedback = request.POST.get('feedback')
        
        soumission.note = float(note) if note else None
        soumission.feedback = feedback
        soumission.save()
        
        messages.success(request, f'Correction enregistrée pour {soumission.etudiant.username}')
        return redirect('enseignant_devoirs_a_corriger')
    
    return render(request, 'website/enseignant/corriger_devoir.html', {
        'soumission': soumission
    })
@login_required
def deposer_presentation(request, seance_id):
    seance = get_object_or_404(SeanceProgrammee, id=seance_id)
    
    if request.user.role != 'etudiant':
        messages.error(request, 'Seuls les étudiants peuvent déposer une présentation.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        fichier = request.FILES.get('fichier')
        lien_video = request.POST.get('lien_video')
        
        depot, created = DepotPresentation.objects.get_or_create(
            seance=seance,
            etudiant=request.user,
            defaults={'fichier': fichier, 'lien_video': lien_video}
        )
        
        if not created:
            depot.fichier = fichier
            depot.lien_video = lien_video
            depot.save()
        
        messages.success(request, 'Présentation déposée avec succès.')
        return redirect('cours_detail_etudiant', cours_id=seance.cours.id)

@login_required
def cours_detail_superadmin(request, cours_id):
    cours = get_object_or_404(CoursProgramme, id=cours_id)
    seances = cours.seances_programmees.all().order_by('ordre', 'jour', 'heure_debut')
    
    return render(request, 'website/cours/detail.html', {
        'cours': cours,
        'seances': seances,
        'est_enseignant': True
    })
@login_required
def enseignant_presentations(request, seance_id):
    seance = get_object_or_404(SeanceProgrammee, id=seance_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    depots = DepotPresentation.objects.filter(seance=seance).select_related('etudiant')
    
    return render(request, 'website/enseignant/presentations.html', {
        'seance': seance,
        'depots': depots
    })
@login_required
def cours_modifier(request, cours_id):
    cours = get_object_or_404(CoursProgramme, id=cours_id)
    user = request.user
    
    # Vérifier les droits
    est_autorise = False
    if user.role == 'super_admin':
        est_autorise = True
    elif user.role == 'admin_ecole':
        if user.ecole_admin == cours.specialite.filiere.ecole:
            est_autorise = True
    elif user.role == 'enseignant':
        if cours.enseignant == user:
            est_autorise = True
    
    if not est_autorise:
        messages.error(request, 'Vous n\'avez pas les droits pour modifier ce cours.')
        return redirect('cours_detail', cours_id=cours.id)
    
    if request.method == 'POST':
        form = CoursProgrammeForm(request.POST, instance=cours)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cours modifié avec succès.')
            return redirect('cours_detail', cours_id=cours.id)
    else:
        form = CoursProgrammeForm(instance=cours)
    
    return render(request, 'website/cours/modifier.html', {
        'form': form,
        'cours': cours
    })
# ==================== GESTION DES EXERCICES ====================
@login_required
def exercice_ajouter(request, seance_id):
    seance = get_object_or_404(SeanceProgrammee, id=seance_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ExerciceForm(request.POST)
        if form.is_valid():
            exercice = form.save(commit=False)
            exercice.seance = seance
            exercice.save()
            messages.success(request, f'Exercice "{exercice.titre}" ajouté.')
            return redirect('seance_detail', seance_id=seance.id)
    else:
        form = ExerciceForm()
    
    return render(request, 'website/enseignant/exercice_ajouter.html', {
        'form': form,
        'seance': seance
    })


@login_required
def exercice_demarrer(request, exercice_id):
    exercice = get_object_or_404(ExerciceApplication, id=exercice_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    exercice.demarre = True
    exercice.date_demarrage = timezone.now()
    exercice.date_fermeture = timezone.now() + timedelta(minutes=exercice.duree)
    exercice.save()
    
    messages.success(request, f'Exercice "{exercice.titre}" démarré. Disponible jusqu\'à {exercice.date_fermeture.strftime("%H:%M")}')
    return redirect('seance_detail', seance_id=exercice.seance.id)


@login_required
def exercice_terminer(request, exercice_id):
    exercice = get_object_or_404(ExerciceApplication, id=exercice_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    exercice.demarre = False
    exercice.date_fermeture = timezone.now()
    exercice.save()
    
    messages.success(request, f'Exercice "{exercice.titre}" terminé.')
    return redirect('seance_detail', seance_id=exercice.seance.id)


@login_required
def exercice_faire(request, exercice_id):
    exercice = get_object_or_404(ExerciceApplication, id=exercice_id)
    
    if request.user.role != 'etudiant':
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('dashboard')
    
    # Vérifier que l'exercice est démarré
    if not exercice.demarre:
        messages.error(request, 'Cet exercice n\'est pas encore disponible.')
        return redirect('seance_detail', seance_id=exercice.seance.id)
    
    # Vérifier que l'exercice n'est pas fermé
    if exercice.date_fermeture and timezone.now() > exercice.date_fermeture:
        messages.error(request, 'Le temps imparti pour cet exercice est écoulé.')
        return redirect('seance_detail', seance_id=exercice.seance.id)
    
    # Vérifier les tentatives
    tentatives = ReponseExercice.objects.filter(exercice=exercice, etudiant=request.user).count()
    if tentatives >= exercice.tentative_max:
        messages.error(request, f'Vous avez atteint le nombre maximum de tentatives ({exercice.tentative_max}).')
        return redirect('seance_detail', seance_id=exercice.seance.id)
    
    if request.method == 'POST':
        reponse_json = {}
        # Récupérer les réponses du formulaire
        for key, value in request.POST.items():
            if key.startswith('q_'):
                reponse_json[key] = value
        
        reponse = ReponseExercice.objects.create(
            exercice=exercice,
            etudiant=request.user,
            reponse_json=reponse_json,
            tentative_numero=tentatives + 1
        )
        
        # Correction automatique si activée
        if exercice.correction_auto and exercice.questions_json:
            score = 0
            total = len(exercice.questions_json)
            # Logique de correction (à adapter selon format)
            reponse.note = score
            reponse.save()
        
        messages.success(request, 'Exercice soumis avec succès.')
        return redirect('exercice_resultat', reponse_id=reponse.id)
    
    return render(request, 'website/etudiant/exercice_faire.html', {
        'exercice': exercice,
        'tentatives_restantes': exercice.tentative_max - tentatives
    })


@login_required
def exercice_resultat(request, reponse_id):
    reponse = get_object_or_404(ReponseExercice, id=reponse_id, etudiant=request.user)
    
    return render(request, 'website/etudiant/exercice_resultat.html', {
        'reponse': reponse
    })


# ==================== GESTION DES DEVOIRS ====================
@login_required
def devoir_ajouter(request, seance_id):
    seance = get_object_or_404(SeanceProgrammee, id=seance_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DevoirForm(request.POST)
        if form.is_valid():
            devoir = form.save(commit=False)
            devoir.seance = seance
            devoir.save()
            messages.success(request, f'Devoir "{devoir.titre}" ajouté.')
            return redirect('seance_detail', seance_id=seance.id)
    else:
        form = DevoirForm()
    
    return render(request, 'website/enseignant/devoir_ajouter.html', {
        'form': form,
        'seance': seance
    })


@login_required
def devoir_soumettre(request, devoir_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    
    if request.user.role != 'etudiant':
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('dashboard')
    
    # Vérifier que le devoir est ouvert
    if not devoir.est_ouvert:
        if devoir.est_ferme:
            messages.error(request, 'La date limite de soumission est dépassée.')
        else:
            messages.error(request, 'Ce devoir n\'est pas encore disponible.')
        return redirect('seance_detail', seance_id=devoir.seance.id)
    
    # Vérifier si l'étudiant a déjà soumis
    soumission = SoumissionDevoir.objects.filter(devoir=devoir, etudiant=request.user).first()
    
    if request.method == 'POST':
        form = SoumissionDevoirForm(request.POST, request.FILES, instance=soumission)
        if form.is_valid():
            soumission = form.save(commit=False)
            soumission.devoir = devoir
            soumission.etudiant = request.user
            soumission.save()
            
            # Gérer les fichiers
            for f in request.FILES.getlist('fichiers'):
                FichierSoumission.objects.create(
                    soumission=soumission,
                    fichier=f,
                    nom_original=f.name,
                    taille=f.size
                )
            
            messages.success(request, 'Devoir soumis avec succès.')
            return redirect('seance_detail', seance_id=devoir.seance.id)
    else:
        form = SoumissionDevoirForm(instance=soumission)
    
    return render(request, 'website/etudiant/devoir_soumettre.html', {
        'devoir': devoir,
        'form': form,
        'soumission': soumission
    })


# ==================== BIGBLUEBUTTON (VISIO) ====================
import hashlib
import requests
from datetime import timedelta

@login_required
def creer_visio(request, seance_id):
    seance = get_object_or_404(SeanceProgrammee, id=seance_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    # Configuration BigBlueButton
    BBB_URL = "https://bigbluebutton.edumax.com/bigbluebutton/"
    BBB_SECRET = "ton_secret_bbb"
    
    meeting_id = f"edumax_{seance.id}_{int(time.time())}"
    name = f"EduMax - {seance.titre}"
    
    # Créer la réunion via API
    params = {
        'meetingID': meeting_id,
        'name': name,
        'attendeePW': 'user123',
        'moderatorPW': 'admin123',
        'record': 'true',
        'autoStartRecording': 'true',
        'allowStartStopRecording': 'false',
        'duration': seance.duree_estimee,
    }
    
    # Générer la checksum
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    checksum = hashlib.sha1(f"create{query_string}{BBB_SECRET}".encode()).hexdigest()
    
    # Appel API
    url = f"{BBB_URL}api/create?{query_string}&checksum={checksum}"
    response = requests.get(url)
    
    if response.status_code == 200:
        # Extraire le lien de la réunion
        join_params = {
            'meetingID': meeting_id,
            'password': 'admin123',
            'fullName': f"{request.user.prenom} {request.user.username}",
            'role': 'MODERATOR'
        }
        join_query = '&'.join([f"{k}={v}" for k, v in join_params.items()])
        join_checksum = hashlib.sha1(f"join{join_query}{BBB_SECRET}".encode()).hexdigest()
        lien_visio = f"{BBB_URL}api/join?{join_query}&checksum={join_checksum}"
        
        seance.lien_visio = lien_visio
        seance.meeting_id = meeting_id
        seance.save()
        
        messages.success(request, 'Salle de visio créée avec succès.')
        return redirect(lien_visio)
    else:
        messages.error(request, 'Erreur lors de la création de la salle de visio.')
        return redirect('seance_detail', seance_id=seance.id)


@login_required
def rejoindre_visio(request, seance_id):
    seance = get_object_or_404(SeanceProgrammee, id=seance_id)
    
    if not seance.lien_visio:
        messages.error(request, 'La visio n\'est pas encore disponible.')
        return redirect('seance_detail', seance_id=seance.id)
    
    # Récupérer l'enregistrement si disponible
    if seance.enregistrement_url:
        # Vérifier si l'enregistrement est encore valide (15 jours)
        if seance.enregistrement_disponible_jusqua and timezone.now() < seance.enregistrement_disponible_jusqua:
            messages.info(request, f'Un enregistrement est disponible. Il expirera le {seance.enregistrement_disponible_jusqua.strftime("%d/%m/%Y")}')
    
    return redirect(seance.lien_visio)
    
@login_required
def cours_modifier(request, cours_id):
    cours = get_object_or_404(CoursProgramme, id=cours_id)
    user = request.user
    
    # Vérifier les droits
    est_autorise = False
    if user.role == 'super_admin':
        est_autorise = True
    elif user.role == 'admin_ecole':
        if user.ecole_admin == cours.specialite.filiere.ecole:
            est_autorise = True
    elif user.role == 'enseignant':
        if cours.enseignant == user:
            est_autorise = True
    
    if not est_autorise:
        messages.error(request, 'Vous n\'avez pas les droits pour modifier ce cours.')
        return redirect('specialite_detail', specialite_id=cours.specialite.id)
    
    if request.method == 'POST':
        form = CoursProgrammeForm(request.POST, instance=cours)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cours modifié avec succès.')
            return redirect('specialite_detail', specialite_id=cours.specialite.id)
    else:
        form = CoursProgrammeForm(instance=cours)
    
    return render(request, 'website/cours/modifier.html', {
        'form': form,
        'cours': cours
    })


@login_required
def cours_supprimer(request, cours_id):
    cours = get_object_or_404(CoursProgramme, id=cours_id)
    user = request.user
    
    # Vérifier les droits
    est_autorise = False
    if user.role == 'super_admin':
        est_autorise = True
    elif user.role == 'admin_ecole':
        if user.ecole_admin == cours.specialite.filiere.ecole:
            est_autorise = True
    elif user.role == 'enseignant':
        if cours.enseignant == user:
            est_autorise = True
    
    if not est_autorise:
        messages.error(request, 'Vous n\'avez pas les droits pour supprimer ce cours.')
        return redirect('specialite_detail', specialite_id=cours.specialite.id)
    
    titre = cours.titre
    cours.delete()
    messages.success(request, f'Le cours "{titre}" a été supprimé.')
    return redirect('specialite_detail', specialite_id=cours.specialite.id) 

# ==================== EXERCICES ====================
@login_required
def exercice_ajouter(request, seance_id):
    seance = get_object_or_404(SeanceProgrammee, id=seance_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ExerciceForm(request.POST)
        if form.is_valid():
            exercice = form.save(commit=False)
            exercice.seance = seance
            exercice.save()
            messages.success(request, f'Exercice "{exercice.titre}" ajouté.')
            return redirect('seance_detail', seance_id=seance.id)
    else:
        form = ExerciceForm()
    
    return render(request, 'website/enseignant/exercice_ajouter.html', {
        'form': form,
        'seance': seance
    })


@login_required
def exercice_demarrer(request, exercice_id):
    exercice = get_object_or_404(ExerciceApplication, id=exercice_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    from django.utils import timezone
    from datetime import timedelta
    
    exercice.demarre = True
    exercice.date_demarrage = timezone.now()
    exercice.date_fermeture = timezone.now() + timedelta(minutes=exercice.duree)
    exercice.save()
    
    messages.success(request, f'Exercice "{exercice.titre}" démarré. Disponible jusqu\'à {exercice.date_fermeture.strftime("%H:%M")}')
    return redirect('seance_detail', seance_id=exercice.seance.id)


@login_required
def exercice_terminer(request, exercice_id):
    exercice = get_object_or_404(ExerciceApplication, id=exercice_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    exercice.demarre = False
    exercice.date_fermeture = timezone.now()
    exercice.save()
    
    messages.success(request, f'Exercice "{exercice.titre}" terminé.')
    return redirect('seance_detail', seance_id=exercice.seance.id)


@login_required
def exercice_faire(request, exercice_id):
    exercice = get_object_or_404(ExerciceApplication, id=exercice_id)
    
    if request.user.role != 'etudiant':
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('dashboard')
    
    if not exercice.demarre:
        messages.error(request, 'Cet exercice n\'est pas encore disponible.')
        return redirect('seance_detail', seance_id=exercice.seance.id)
    
    if exercice.date_fermeture and timezone.now() > exercice.date_fermeture:
        messages.error(request, 'Le temps imparti est écoulé.')
        return redirect('seance_detail', seance_id=exercice.seance.id)
    
    if request.method == 'POST':
        reponse_json = {}
        for key, value in request.POST.items():
            if key.startswith('q_'):
                reponse_json[key] = value
        
        reponse = ReponseExercice.objects.create(
            exercice=exercice,
            etudiant=request.user,
            reponse_json=reponse_json
        )
        messages.success(request, 'Exercice soumis avec succès.')
        return redirect('exercice_resultat', reponse_id=reponse.id)
    
    return render(request, 'website/etudiant/exercice_faire.html', {
        'exercice': exercice
    })


@login_required
def exercice_resultat(request, reponse_id):
    reponse = get_object_or_404(ReponseExercice, id=reponse_id, etudiant=request.user)
    return render(request, 'website/etudiant/exercice_resultat.html', {'reponse': reponse})

# ==================== DEVOIRS ====================
@login_required
def devoir_ajouter(request, seance_id):
    seance = get_object_or_404(SeanceProgrammee, id=seance_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DevoirForm(request.POST)
        if form.is_valid():
            devoir = form.save(commit=False)
            devoir.seance = seance
            devoir.save()
            messages.success(request, f'Devoir "{devoir.titre}" ajouté.')
            return redirect('seance_detail', seance_id=seance.id)
    else:
        form = DevoirForm()
    
    return render(request, 'website/enseignant/devoir_ajouter.html', {
        'form': form,
        'seance': seance
    })


@login_required
def devoir_soumettre(request, devoir_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    
    if request.user.role != 'etudiant':
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('dashboard')
    
    if not devoir.actif:
        messages.error(request, 'Ce devoir n\'est pas disponible.')
        return redirect('seance_detail', seance_id=devoir.seance.id)
    
    if timezone.now() > devoir.date_limite:
        messages.error(request, 'La date limite de soumission est dépassée.')
        return redirect('seance_detail', seance_id=devoir.seance.id)
    
    soumission, created = SoumissionDevoir.objects.get_or_create(
        devoir=devoir,
        etudiant=request.user
    )
    
    if request.method == 'POST':
        soumission.texte_reponse = request.POST.get('texte_reponse', '')
        if request.FILES.get('fichier'):
            soumission.fichier = request.FILES['fichier']
        soumission.save()
        messages.success(request, 'Devoir soumis avec succès.')
        return redirect('seance_detail', seance_id=devoir.seance.id)
    
    return render(request, 'website/etudiant/devoir_soumettre.html', {
        'devoir': devoir,
        'soumission': soumission
    })


@login_required
def devoir_corriger(request, soumission_id):
    soumission = get_object_or_404(SoumissionDevoir, id=soumission_id)
    devoir = soumission.devoir
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        soumission.note = request.POST.get('note')
        soumission.feedback = request.POST.get('feedback')
        soumission.save()
        messages.success(request, f'Note enregistrée pour {soumission.etudiant.username}')
        return redirect('devoir_soumissions', devoir_id=devoir.id)
    
    return render(request, 'website/enseignant/devoir_corriger.html', {
        'soumission': soumission,
        'devoir': devoir
    })


@login_required
def devoir_soumissions(request, devoir_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    soumissions = SoumissionDevoir.objects.filter(devoir=devoir).select_related('etudiant')
    
    return render(request, 'website/enseignant/devoir_soumissions.html', {
        'devoir': devoir,
        'soumissions': soumissions
    })

@login_required
def seance_modifier(request, seance_id):
    seance = get_object_or_404(SeanceProgrammee, id=seance_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SeanceProgrammeeForm(request.POST, request.FILES, instance=seance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Séance modifiée avec succès.')
            return redirect('cours_detail_enseignant', cours_id=seance.cours.id)
    else:
        form = SeanceProgrammeeForm(instance=seance)
    
    return render(request, 'website/enseignant/seance_modifier.html', {
        'form': form,
        'seance': seance
    })

@login_required
def seance_supprimer(request, seance_id):
    seance = get_object_or_404(SeanceProgrammee, id=seance_id)
    cours_id = seance.cours.id
    seance.delete()
    messages.success(request, 'Séance supprimée')
    return redirect('cours_detail_enseignant', cours_id=cours_id)

@login_required
def exercice_modifier(request, exercice_id):
    exercice = get_object_or_404(ExerciceApplication, id=exercice_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ExerciceForm(request.POST, instance=exercice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exercice modifié')
            return redirect('seance_detail', seance_id=exercice.seance.id)
    else:
        form = ExerciceForm(instance=exercice)
    
    return render(request, 'website/enseignant/exercice_modifier.html', {
        'form': form,
        'exercice': exercice
    })


@login_required
def exercice_supprimer(request, exercice_id):
    exercice = get_object_or_404(ExerciceApplication, id=exercice_id)
    seance_id = exercice.seance.id
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    exercice.delete()
    messages.success(request, 'Exercice supprimé')
    return redirect('seance_detail', seance_id=seance_id)


@login_required
def devoir_modifier(request, devoir_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DevoirForm(request.POST, instance=devoir)
        if form.is_valid():
            form.save()
            messages.success(request, 'Devoir modifié')
            return redirect('seance_detail', seance_id=devoir.seance.id)
    else:
        form = DevoirForm(instance=devoir)
    
    return render(request, 'website/enseignant/devoir_modifier.html', {
        'form': form,
        'devoir': devoir
    })


@login_required
def devoir_supprimer(request, devoir_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    seance_id = devoir.seance.id
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    devoir.delete()
    messages.success(request, 'Devoir supprimé')
    return redirect('seance_detail', seance_id=seance_id)

# ==================== QUIZ ====================

@login_required
def quiz_creer(request, seance_id):
    """Créer un quiz dans une séance"""
    seance = get_object_or_404(SeanceProgrammee, id=seance_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.seance = seance
            quiz.save()
            messages.success(request, f'Quiz "{quiz.titre}" créé.')
            return redirect('quiz_detail', quiz_id=quiz.id)
    else:
        form = QuizForm()
    
    return render(request, 'website/enseignant/quiz_creer.html', {
        'form': form,
        'seance': seance
    })


@login_required
def quiz_detail(request, quiz_id):
    """Voir le détail d'un quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = Question.objects.filter(quiz=quiz).order_by('ordre')
    
    return render(request, 'website/enseignant/quiz_detail.html', {
        'quiz': quiz,
        'questions': questions
    })




@login_required
def reponse_ajouter(request, question_id):
    """Ajouter une réponse possible à une question"""
    question = get_object_or_404(Question, id=question_id)
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ReponsePossibleForm(request.POST)
        if form.is_valid():
            reponse = form.save(commit=False)
            reponse.question = question
            reponse.save()
            messages.success(request, 'Réponse ajoutée.')
            return redirect('quiz_detail', quiz_id=question.quiz.id)
    else:
        form = ReponsePossibleForm()
    
    return render(request, 'website/enseignant/reponse_ajouter.html', {
        'form': form,
        'question': question
    })
@login_required
def quiz_detail(request, exercice_id):
    exercice = get_object_or_404(ExerciceApplication, id=exercice_id, type_exercice='quiz')
    return render(request, 'website/quiz/detail.html', {'exercice': exercice})

@login_required
def repondre_quiz(request, exercice_id):
    exercice = get_object_or_404(ExerciceApplication, id=exercice_id, type_exercice='quiz')
    
    if request.user.role != 'etudiant':
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('dashboard')
    
    # Vérifier si l'étudiant a déjà répondu
    reponse_existante = ReponseExercice.objects.filter(exercice=exercice, etudiant=request.user).first()
    if reponse_existante:
        messages.warning(request, 'Vous avez déjà répondu à ce quiz.')
        return redirect('seance_detail', seance_id=exercice.seance.id)
    
    if request.method == 'POST':
        reponses = {}
        for question in exercice.questions.all():
            reponse_id = request.POST.get(f'question_{question.id}')
            if reponse_id:
                reponses[question.id] = int(reponse_id)
        
        # Sauvegarder les réponses
        reponse = ReponseExercice.objects.create(
            exercice=exercice,
            etudiant=request.user,
            reponse_json=reponses
        )
        messages.success(request, 'Quiz soumis avec succès. En attente de publication des résultats.')
        return redirect('seance_detail', seance_id=exercice.seance.id)
    
    return render(request, 'website/etudiant/repondre_quiz.html', {
        'exercice': exercice
    })
    
@login_required
def publier_resultats_quiz(request, exercice_id):
    exercice = get_object_or_404(ExerciceApplication, id=exercice_id, type_exercice='quiz')
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('dashboard')
    
    # Récupérer toutes les réponses des étudiants
    reponses = ReponseExercice.objects.filter(exercice=exercice)
    
    # Calculer les notes
    for reponse in reponses:
        score = 0
        total_points = 0
        reponses_data = reponse.reponse_json
        
        for question in exercice.questions.all():
            points = question.points
            total_points += points
            
            reponse_id = reponses_data.get(str(question.id))
            if reponse_id:
                bonne_reponse = question.reponses.filter(est_correcte=True, id=reponse_id).exists()
                if bonne_reponse:
                    score += points
        
        note = (score / total_points) * 20 if total_points > 0 else 0
        reponse.note = round(note, 2)
        reponse.save()
    
    # Marquer comme publié
    exercice.resultats_publies = True
    exercice.save()
    
    messages.success(request, f'Les résultats du quiz "{exercice.titre}" ont été publiés.')
    return redirect('quiz_resultats', exercice_id=exercice.id)


@login_required
def quiz_resultats(request, exercice_id):
    exercice = get_object_or_404(ExerciceApplication, id=exercice_id, type_exercice='quiz')
    
    if request.user.role == 'enseignant':
        reponses = ReponseExercice.objects.filter(exercice=exercice).select_related('etudiant')
        return render(request, 'website/enseignant/quiz_resultats.html', {
            'exercice': exercice,
            'reponses': reponses
        })
    else:
        # Étudiant
        reponse = ReponseExercice.objects.filter(exercice=exercice, etudiant=request.user).first()
        return render(request, 'website/etudiant/quiz_resultats.html', {
            'exercice': exercice,
            'reponse': reponse
        })
        
        
import hashlib
import requests
import time
from django.conf import settings

def creer_salle_visio(seance_id, titre, enseignant_nom, duree=120):
    """Crée une salle BigBlueButton et retourne le lien modérateur"""
    
    meeting_id = f"edumax_{seance_id}_{int(time.time())}"
    
    params = {
        'meetingID': meeting_id,
        'name': titre[:80],
        'attendeePW': 'user123',
        'moderatorPW': 'admin123',
        'record': 'true',
        'autoStartRecording': 'true',
        'allowStartStopRecording': 'false',
        'duration': duree,
    }
    
    # Générer la checksum
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    checksum = hashlib.sha1(f"create{query_string}{settings.BBB_SECRET}".encode()).hexdigest()
    
    # Appel API
    url = f"{settings.BBB_URL}api/create?{query_string}&checksum={checksum}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and 'returncode="SUCCESS"' in response.text:
            # Générer le lien pour le modérateur (enseignant)
            join_params = {
                'meetingID': meeting_id,
                'password': 'admin123',
                'fullName': enseignant_nom[:50],
                'role': 'MODERATOR'
            }
            join_query = '&'.join([f"{k}={v}" for k, v in join_params.items()])
            join_checksum = hashlib.sha1(f"join{join_query}{settings.BBB_SECRET}".encode()).hexdigest()
            lien_modo = f"{settings.BBB_URL}api/join?{join_query}&checksum={join_checksum}"
            
            return lien_modo
        else:
            return None
    except:
        return None

@login_required
def demarrer_visio(request, seance_id):
    seance = get_object_or_404(SeanceProgrammee, id=seance_id, type_seance='visio')
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('seance_detail', seance_id=seance.id)
    
    # Vérifier si un lien existe déjà
    if seance.lien_visio:
        return redirect(seance.lien_visio)
    
    enseignant_nom = f"{request.user.prenom} {request.user.username}"
    lien = creer_salle_visio(seance.id, seance.titre, enseignant_nom, seance.duree_estimee or 120)
    
    if lien:
        seance.lien_visio = lien
        seance.save()
        messages.success(request, 'Salle de visio créée avec succès.')
        return redirect(lien)
    else:
        messages.error(request, 'Erreur lors de la création de la salle. Veuillez réessayer.')
        return redirect('seance_detail', seance_id=seance.id)