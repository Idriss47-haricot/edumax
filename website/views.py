import json
import time
import uuid
import random
import hashlib
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
import requests
from datetime import timedelta
from django.template.loader import render_to_string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db import models
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.db.models import Q, Avg, Count, F,  Avg, Count
from decimal import Decimal 
from .services.paiement_service import get_paiement_service
from django.core.paginator import Paginator
from django.core.mail import send_mail
import json, re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from .models import DemandeFormateur, ParametresDemandesFormateur

from .models import (
    Answer, CentreInteret, ConfigurationPlateforme, Devoir, Exercice, Question, RegleVente, ReponseEtudiant,
    SignalementFormation, SoumissionDevoir, SoumissionExercice,  Utilisateur, Ecole, Abonnement, Filiere, Specialite, 
    InscriptionEtudiant, EnseignantEcole,Formation, FichierFormation, Avis, AchatFormation,
    ConditionVente, Coupon, AcceptationConditionsPublication,CoursProgramme, SeanceProgrammee, ParticipantCoursProgramme,
    SeanceBase, SeanceVisio, RessourceSeance,Cours, Seance,  # Anciens modèles (compatibilité)
    ProgressionEtudiant, ProgressionEtudiantSeance, PresenceSeance,MessagePrive, Conversation, Notification, NotificationVisio,
    MessageForum,DepotPresentation,ImageEcole, ValidationAutomatiqueLog, Utilisateur, Abonnement, TransactionLog, AbonnementUtilisateur,
    RubriqueEpreuve, CategorieEpreuve,  Epreuve, PanierEpreuve, AchatEpreuve, TelechargementEpreuve, RessourceSeance,
)

from .forms import (
    AchatFormationForm, CorrectionDevoirForm, DemandeFormateurForm, DevoirForm,  ExerciceForm, InscriptionForm, ConnexionForm, MotDePasseOublieForm, PublicationForm, 
    RegleVenteForm, ReinitialisationMotDePasseForm,
    EcoleCreationForm, EcoleModificationForm, FiliereForm, SignalementFormationForm, SoumissionDevoirForm, SpecialiteForm, InscriptionAvecCleForm,
    AbonnementForm, CoursProgrammeForm, SeanceProgrammeeForm,
    SeanceBaseForm, RessourceSeanceForm, CorrectionSeanceForm,FormationForm, FichierFormationForm, AvisForm, PaiementForm, ConditionsPublicationForm, 
    AchatEpreuveForm, AjoutPanierForm, AchatCategorieForm,
)

from .decorators import role_required, super_admin_required, admin_ecole_required, enseignant_required

# ==================== PAGES PUBLIQUES ====================

def accueil(request):
    """
    Page d'accueil principale — toutes les données viennent de la base,
    tout le contenu est modifiable depuis le panneau super_admin.
    """
    from django.db import models as db_models
    from django.utils import timezone
    from django.db.models import Count, Avg
    from .models import (
        ConfigurationPlateforme, DiapositiveHero, Temoignage,
        Partenaire, BannierePromo, Ecole, Formation, Epreuve,
        RubriqueEpreuve, CentreInteret, Utilisateur, TelechargementEpreuve
    )

    # ── Configuration centrale ──────────────────────────────────────────
    config = ConfigurationPlateforme.get_config()

    # ── Diaporama Hero ──────────────────────────────────────────────────
    today = timezone.now().date()
    slides = DiapositiveHero.objects.filter(actif=True).filter(
        db_models.Q(date_debut__lte=today) | db_models.Q(date_debut__isnull=True)
    ).filter(
        db_models.Q(date_fin__gte=today) | db_models.Q(date_fin__isnull=True)
    ).order_by('ordre')

    # ── Statistiques dynamiques ─────────────────────────────────────────
    stats = {}
    
    # Stat 1 - Écoles
    if config.stat1_valeur_auto:
        stats['stat1'] = Ecole.objects.filter(actif=True).count()
    else:
        stats['stat1'] = config.stat1_valeur_fixe or "50+"
    stats['stat1_label'] = config.stat1_label

    # Stat 2 - Formations
    if config.stat2_valeur_auto:
        stats['stat2'] = Formation.objects.filter(statut='publie').count()
    else:
        stats['stat2'] = config.stat2_valeur_fixe or "200+"
    stats['stat2_label'] = config.stat2_label

    # Stat 3 - Téléchargements
    if config.stat3_valeur_auto:
        stats['stat3'] = TelechargementEpreuve.objects.count()
    else:
        stats['stat3'] = config.stat3_valeur_fixe or "5 000+"
    stats['stat3_label'] = config.stat3_label

    # Stat 4 - Étudiants
    if config.stat4_valeur_auto:
        stats['stat4'] = Utilisateur.objects.filter(role='etudiant', is_active=True).count()
    else:
        stats['stat4'] = config.stat4_valeur_fixe or "10 000+"
    stats['stat4_label'] = config.stat4_label

    # ── Formations en vedette ───────────────────────────────────────────
    formations_qs = Formation.objects.filter(statut='publie').select_related('createur')
    tri = config.formations_tri or '-date_publication'
    formations_vedette = formations_qs.order_by(tri)[:config.nb_formations_accueil]

    # Formations gratuites
    formations_gratuites = formations_qs.filter(prix=0).order_by('-date_publication')[:4]

    # ── Centres d'intérêt les plus populaires ──────────────────────────
    centres_populaires = CentreInteret.objects.filter(actif=True).annotate(
        nb=Count('formations')
    ).filter(nb__gt=0).order_by('-nb')[:8]

    # ── Épreuves populaires ─────────────────────────────────────────────
    epreuves_vedette = Epreuve.objects.filter(
        statut='publie'
    ).order_by('-nb_ventes', '-date_ajout')[:config.nb_epreuves_accueil]

    # Rubriques pour navigation rapide épreuves
    rubriques = RubriqueEpreuve.objects.filter(actif=True).prefetch_related(
        'categories'
    ).order_by('ordre')

    # ── Écoles partenaires ──────────────────────────────────────────────
    ecoles = Ecole.objects.filter(actif=True).select_related(
        'abonnement'
    ).order_by('?')[:config.nb_ecoles_accueil]

    # ── Témoignages ─────────────────────────────────────────────────────
    temoignages = Temoignage.objects.filter(actif=True).order_by('ordre')

    # ── Partenaires ─────────────────────────────────────────────────────
    partenaires = Partenaire.objects.filter(actif=True).order_by('ordre')

    # ── Bannière promo ──────────────────────────────────────────────────
    banniere_promo = BannierePromo.objects.filter(
        actif=True
    ).filter(
        db_models.Q(date_debut__lte=today) | db_models.Q(date_debut__isnull=True)
    ).filter(
        db_models.Q(date_fin__gte=today) | db_models.Q(date_fin__isnull=True)
    ).first()

    # ── Formateurs mis en avant ─────────────────────────────────────────
    formateurs_vedette = Utilisateur.objects.filter(
        role='enseignant',
        is_active=True,
        formations_crees__statut='publie'
    ).annotate(
        nb_formations=Count('formations_crees')
    ).order_by('-nb_formations')[:4]

    context = {
        'config': config,
        'slides': slides,
        'stats': stats,
        'formations_vedette': formations_vedette,
        'formations_gratuites': formations_gratuites,
        'centres_populaires': centres_populaires,
        'epreuves_vedette': epreuves_vedette,
        'rubriques': rubriques,
        'ecoles': ecoles,
        'temoignages': temoignages,
        'partenaires': partenaires,
        'banniere_promo': banniere_promo,
        'formateurs_vedette': formateurs_vedette,
    }
    return render(request, 'website/accueil.html', context)

def inscription(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            import time
            username = form.cleaned_data['email'].split('@')[0] + '_' + str(int(time.time()))
            user = Utilisateur.objects.create_user(
                username=username,
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                prenom=form.cleaned_data['prenom'],
                telephone=form.cleaned_data.get('telephone', ''),
                pays=form.cleaned_data.get('pays', ''),
                role='etudiant'
            )
            login(request, user)
            # ← JAMAIS redirect dashboard ici, toujours choix_abonnement
            return redirect('choix_abonnement')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = InscriptionForm()
    
    return render(request, 'website/inscription.html', {'form': form})

def connexion(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ConnexionForm(request.POST)  
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
        ecole = getattr(user, 'ecole_admin', None)
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
        context['quiz_realises'] = 0
        context['devoirs_rendus'] = 0
        return render(request, 'website/etudiant/dashboard.html', context)


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
            from .models import Ecole, Abonnement, Utilisateur
            from django.utils.text import slugify
            
            # Récupérer l'abonnement et l'admin école
            abonnement = None
            if form.cleaned_data.get('abonnement'):
                abonnement = Abonnement.objects.get(id=form.cleaned_data['abonnement'])
            
            admin_ecole = None
            if form.cleaned_data.get('admin_ecole'):
                admin_ecole = Utilisateur.objects.get(id=form.cleaned_data['admin_ecole'])
            
            # Créer l'école manuellement
            ecole = Ecole.objects.create(
                nom=form.cleaned_data['nom'],
                description=form.cleaned_data['description'],
                email=form.cleaned_data['email'],
                telephone=form.cleaned_data['telephone'],
                ville=form.cleaned_data['ville'],
                pays=form.cleaned_data['pays'],
                quartier=form.cleaned_data.get('quartier', ''),
                numero_agrement=form.cleaned_data.get('numero_agrement', ''),
                abonnement=abonnement,
                admin_ecole=admin_ecole,
                slug=slugify(form.cleaned_data['nom'])
            )
            
            # Gérer le logo et la bannière
            if 'logo' in request.FILES:
                ecole.logo = request.FILES['logo']
            if 'banniere' in request.FILES:
                ecole.banniere = request.FILES['banniere']
            ecole.save()
            
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
    
    from .forms import UtilisateurForm  # Créez ce formulaire si nécessaire
    
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    
    if request.method == 'POST':
        # Gestion du changement de mot de passe
        nouveau_mdp = request.POST.get('nouveau_mot_de_passe')
        if nouveau_mdp and len(nouveau_mdp) >= 6:
            utilisateur.set_password(nouveau_mdp)
            utilisateur.save()
            messages.success(request, f"Mot de passe de {utilisateur.username} modifié avec succès.")
        
        # Gestion de la désactivation du paiement
        desactiver_paiement = request.POST.get('desactiver_paiement') == 'on'
        if desactiver_paiement != utilisateur.paiement_desactive:
            utilisateur.paiement_desactive = desactiver_paiement
            utilisateur.save()
            
            # Mettre à jour l'abonnement
            try:
                abonnement = Abonnement.objects.get(utilisateur=utilisateur)
                abonnement.paiement_oblige = not desactiver_paiement
                abonnement.save()
            except Abonnement.DoesNotExist:
                pass
            
            if desactiver_paiement:
                messages.success(request, f"L'obligation de paiement a été désactivée pour {utilisateur.username}.")
            else:
                messages.success(request, f"L'obligation de paiement a été réactivée pour {utilisateur.username}.")
        
        # Autres champs...
        # ... votre code existant pour modifier les autres champs
        
        return redirect('super_admin_utilisateurs')
    
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
            from .models import Filiere
            filiere = Filiere.objects.create(
                ecole=ecole,
                nom=form.cleaned_data['nom'],
                description=form.cleaned_data.get('description', ''),
                ordre=form.cleaned_data.get('ordre', 0)
            )
            messages.success(request, 'Filière créée.')
            return redirect('admin_ecole_filiere_liste')
    else:
        form = FiliereForm()
    return render(request, 'website/admin_ecole/filieres/creer.html', {'form': form, 'ecole': ecole})

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
            from .models import Specialite
            specialite = Specialite.objects.create(
                filiere=filiere,
                nom=form.cleaned_data['nom'],
                description=form.cleaned_data.get('description', ''),
                ordre=form.cleaned_data.get('ordre', 0)
            )
            messages.success(request, f'Spécialité "{specialite.nom}" créée.')
            return redirect('admin_ecole_specialite_liste', filiere_id=filiere.id)
    else:
        form = SpecialiteForm()
    
    return render(request, 'website/admin_ecole/specialites/creer.html', {'form': form, 'filiere': filiere, 'ecole': ecole})


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
        form = FiliereForm(request.POST)
        if form.is_valid():
            filiere.nom = form.cleaned_data['nom']
            filiere.description = form.cleaned_data.get('description', '')
            filiere.ordre = form.cleaned_data.get('ordre', 0)
            filiere.save()
            messages.success(request, 'Filière modifiée.')
            return redirect('admin_ecole_filiere_liste')
    else:
        form = FiliereForm(initial={
            'nom': filiere.nom,
            'description': filiere.description,
            'ordre': filiere.ordre,
        })
    
    return render(request, 'website/admin_ecole/filieres/modifier.html', {'form': form, 'filiere': filiere, 'ecole': ecole})

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
        form = SpecialiteForm(request.POST)
        if form.is_valid():
            specialite.nom = form.cleaned_data['nom']
            specialite.description = form.cleaned_data.get('description', '')
            specialite.ordre = form.cleaned_data.get('ordre', 0)
            specialite.save()
            messages.success(request, 'Spécialité modifiée.')
            return redirect('admin_ecole_specialite_liste', filiere_id=filiere.id)
    else:
        form = SpecialiteForm(initial={
            'nom': specialite.nom,
            'description': specialite.description,
            'ordre': specialite.ordre,
        })
    
    return render(request, 'website/admin_ecole/specialites/modifier.html', {'form': form, 'specialite': specialite, 'filiere': filiere, 'ecole': ecole})

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


# ==================== MESSAGERIE ====================
@login_required
def messages_liste(request, conversation_id=None):
    """Page principale de messagerie"""
    from .models import Conversation, MessagePrive
    from django.db.models import Q
    
    conversation = None
    messages_list = []
    autre_utilisateur = None

    # Récupérer toutes les conversations
    conversations = Conversation.objects.filter(
        participants=request.user
    ).exclude(
        supprimes_par=request.user
    ).order_by('-date_modification')
    
    conversations_data = []
    for conv in conversations:
        autre = conv.participants.exclude(id=request.user.id).first()
        dernier_message = conv.messages.order_by('-date_envoi').first()
        non_lus = conv.messages.filter(lu=False).exclude(expediteur=request.user).count()
        
        if autre:
            conversations_data.append({
                'id': conv.id,
                'autre': autre,
                'dernier_msg': dernier_message,
                'non_lus': non_lus,
            })
    
    # Si une conversation spécifique est demandée
    if conversation_id:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Vérifier l'accès
        if request.user not in conversation.participants.all():
            return redirect('messages_liste')
        
        # Marquer les messages comme lus
        MessagePrive.objects.filter(
            conversation=conversation, 
            lu=False
        ).exclude(expediteur=request.user).update(lu=True)
        
        messages_list = MessagePrive.objects.filter(conversation=conversation).order_by('date_envoi')
        autre_utilisateur = conversation.participants.exclude(id=request.user.id).first()
    
    context = {
        'conversations': conversations_data,
        'conversation': conversation,
        'messages': messages_list,
        'autre_utilisateur': autre_utilisateur,
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
    ecole = get_object_or_404(Ecole, id=ecole_id)
    
    if request.method == 'POST':
        form = EcoleCreationForm(request.POST, request.FILES)
        if form.is_valid():
            from .models import Abonnement, Utilisateur
            
            ecole.nom = form.cleaned_data['nom']
            ecole.description = form.cleaned_data['description']
            ecole.email = form.cleaned_data['email']
            ecole.telephone = form.cleaned_data['telephone']
            ecole.ville = form.cleaned_data['ville']
            ecole.pays = form.cleaned_data['pays']
            ecole.quartier = form.cleaned_data.get('quartier', '')
            ecole.numero_agrement = form.cleaned_data.get('numero_agrement', '')
            
            if form.cleaned_data.get('abonnement'):
                ecole.abonnement = Abonnement.objects.get(id=form.cleaned_data['abonnement'])
            if form.cleaned_data.get('admin_ecole'):
                ecole.admin_ecole = Utilisateur.objects.get(id=form.cleaned_data['admin_ecole'])
            
            if 'logo' in request.FILES:
                ecole.logo = request.FILES['logo']
            if 'banniere' in request.FILES:
                ecole.banniere = request.FILES['banniere']
            
            ecole.save()
            messages.success(request, 'École modifiée avec succès.')
            return redirect('super_admin_ecole_liste')
    else:
        form = EcoleCreationForm(initial={
            'nom': ecole.nom,
            'description': ecole.description,
            'email': ecole.email,
            'telephone': ecole.telephone,
            'ville': ecole.ville,
            'pays': ecole.pays,
            'quartier': ecole.quartier,
            'numero_agrement': ecole.numero_agrement,
            'abonnement': ecole.abonnement.id if ecole.abonnement else '',
            'admin_ecole': ecole.admin_ecole.id if ecole.admin_ecole else '',
        })
    
    return render(request, 'website/super_admin/ecoles/modifier.html', {'form': form, 'ecole': ecole})


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
            from .models import Abonnement
            # Créer l'abonnement manuellement
            abonnement = Abonnement.objects.create(
                nom=form.cleaned_data['nom'],
                description=form.cleaned_data.get('description', ''),
                max_etudiants=form.cleaned_data['max_etudiants'],
                max_cours=form.cleaned_data['max_cours'],
                stockage_gb=form.cleaned_data['stockage_gb'],
                ordre=form.cleaned_data['ordre'],
                actif=form.cleaned_data.get('actif', True)
            )
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
        form = AbonnementForm(request.POST)
        if form.is_valid():
            abonnement.nom = form.cleaned_data['nom']
            abonnement.description = form.cleaned_data.get('description', '')
            abonnement.max_etudiants = form.cleaned_data['max_etudiants']
            abonnement.max_cours = form.cleaned_data['max_cours']
            abonnement.stockage_gb = form.cleaned_data['stockage_gb']
            abonnement.ordre = form.cleaned_data['ordre']
            abonnement.actif = form.cleaned_data.get('actif', True)
            abonnement.save()
            messages.success(request, 'Pack modifié.')
            return redirect('super_admin_abonnement_liste')
    else:
        form = AbonnementForm(initial={
            'nom': abonnement.nom,
            'description': abonnement.description,
            'max_etudiants': abonnement.max_etudiants,
            'max_cours': abonnement.max_cours,
            'stockage_gb': abonnement.stockage_gb,
            'ordre': abonnement.ordre,
            'actif': abonnement.actif,
        })
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
        'est_enseignant': est_enseignant or est_admin,
    }
    
    return render(request, 'website/cours/detail.html', context)



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

@login_required
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
            from .models import Filiere
            filiere = Filiere.objects.create(
                ecole=ecole,
                nom=form.cleaned_data['nom'],
                description=form.cleaned_data.get('description', ''),
                ordre=form.cleaned_data.get('ordre', 0)
            )
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
            from .models import Specialite
            specialite = Specialite.objects.create(
                filiere=filiere,
                nom=form.cleaned_data['nom'],
                description=form.cleaned_data.get('description', ''),
                ordre=form.cleaned_data.get('ordre', 0)
            )
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
        messages.error(request, 'Vous n\'avez pas les droits.')
        return redirect('specialite_detail', specialite_id=specialite.id)
    
    if request.method == 'POST':
        form = CoursProgrammeForm(request.POST)
        if form.is_valid():
            from .models import CoursProgramme, Utilisateur
            enseignant = None
            if form.cleaned_data.get('enseignant'):
                enseignant = Utilisateur.objects.get(id=form.cleaned_data['enseignant'])
            
            cours = CoursProgramme.objects.create(
                specialite=specialite,
                titre=form.cleaned_data['titre'],
                description=form.cleaned_data['description'],
                objectifs=form.cleaned_data.get('objectifs', ''),
                enseignant=enseignant,
                date_debut=form.cleaned_data['date_debut'],
                date_fin=form.cleaned_data.get('date_fin'),
                actif=form.cleaned_data.get('actif', True),
                mode_programmation=form.cleaned_data.get('mode_programmation', 'recurrent'),
                statut=form.cleaned_data.get('statut', 'en_cours'),
                created_by=user
            )
            messages.success(request, f'Cours "{cours.titre}" créé.')
            return redirect('specialite_detail', specialite_id=specialite.id)
    else:
        form = CoursProgrammeForm(initial={'date_debut': timezone.now().date()})
    
    return render(request, 'website/cours/creer.html', {'form': form, 'specialite': specialite})


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
def cours_detail_enseignant(request, cours_id):
    """Détail d'un cours pour un enseignant"""
    cours = get_object_or_404(CoursProgramme, id=cours_id)
    
    if cours.enseignant != request.user and request.user.role not in ['admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'êtes pas responsable de ce cours.')
        return redirect('dashboard')
    
    from .models import SeanceBase
    seances = SeanceBase.objects.filter(cours=cours).order_by('ordre', 'date_creation')
    
    # SEUL CHANGEMENT : remplacer TentativeQCM par SoumissionExercice
    from .models import SoumissionExercice
    soumissions_en_attente = SoumissionExercice.objects.filter(
        exercice__seance__cours=cours,
        note__isnull=True,
        status='termine'
    ).count()
    
    return render(request, 'website/enseignant/cours_detail.html', {
        'cours': cours,
        'seances': seances,
        'soumissions_en_attente': soumissions_en_attente,
        'est_enseignant': True,
    })
    
    
@login_required
def seance_modifier(request, seance_id):
    seance = get_object_or_404(SeanceBase, id=seance_id)
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SeanceBaseForm(request.POST)
        if form.is_valid():
            seance.titre = form.cleaned_data['titre']
            seance.description = form.cleaned_data.get('description', '')
            seance.objectifs = form.cleaned_data.get('objectifs', '')
            seance.type_seance = form.cleaned_data['type_seance']
            seance.ordre = form.cleaned_data.get('ordre', 0)
            seance.duree_estimee = form.cleaned_data.get('duree_estimee', 60)
            seance.save()
            messages.success(request, 'Séance modifiée.')
            return redirect('seance_detail', seance_id=seance.id)
    else:
        form = SeanceBaseForm(initial={
            'titre': seance.titre,
            'description': seance.description,
            'objectifs': seance.objectifs,
            'type_seance': seance.type_seance,
            'ordre': seance.ordre,
            'duree_estimee': seance.duree_estimee,
        })
    
    return render(request, 'website/seance/modifier.html', {'form': form, 'seance': seance})

@login_required
def seance_supprimer(request, seance_id):
    """Supprimer une séance"""
    seance = get_object_or_404(SeanceBase, id=seance_id)
    cours_id = seance.cours.id
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits pour supprimer cette séance.')
        return redirect('dashboard')
    
    titre = seance.titre
    seance.delete()
    messages.success(request, f'La séance "{titre}" a été supprimée.')
    
    return redirect('cours_detail_superadmin', cours_id=cours_id)

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
    user = request.user
    
    if user.role != 'etudiant':
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('dashboard')
    
    inscriptions = InscriptionEtudiant.objects.filter(etudiant=user).select_related('specialite__filiere__ecole')
    
    data = []
    ecoles_dict = {}
    
    for inscription in inscriptions:
        specialite = inscription.specialite
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
            cours_list = CoursProgramme.objects.filter(specialite=specialite, actif=True).order_by('date_debut')
            
            total_seances = 0
            seances_vues = 0
            
            for cours in cours_list:
                # Utilisation correcte de la relation 'seances'
                for seance in cours.seances.all():
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
    
    if not InscriptionEtudiant.objects.filter(etudiant=user, specialite=specialite).exists():
        messages.error(request, 'Vous n\'êtes pas inscrit à cette spécialité.')
        return redirect('etudiant_mes_cours')
    
    cours_list = CoursProgramme.objects.filter(specialite=specialite, actif=True).order_by('date_debut')
    
    total_seances = 0
    seances_vues = 0
    
    for cours in cours_list:
        # Correction : utilise 'seances' au lieu de 'seances_programmees'
        for seance in cours.seances.all():
            total_seances += 1
            if PresenceSeance.objects.filter(seance=seance, etudiant=user, vu=True).exists():
                seances_vues += 1
    
    progression = int((seances_vues / total_seances) * 100) if total_seances > 0 else 0
    
    return render(request, 'website/etudiant/specialite_detail.html', {
        'specialite': specialite,
        'cours_list': cours_list,
        'progression': progression,
    })

@login_required
def etudiant_cours_detail(request, cours_id):
    cours = get_object_or_404(CoursProgramme, id=cours_id)
    user = request.user
    
    if not InscriptionEtudiant.objects.filter(etudiant=user, specialite=cours.specialite).exists():
        messages.error(request, 'Vous n\'êtes pas inscrit à ce cours.')
        return redirect('etudiant_mes_cours')
    
    # Correction : utilise 'seances' au lieu de 'seances_programmees'
    seances = cours.seances.all().order_by('ordre', 'date_creation')
    
    seances_vues = PresenceSeance.objects.filter(
        seance__in=seances,
        etudiant=user,
        vu=True
    ).values_list('seance_id', flat=True)
    
    total_seances = seances.count()
    seances_terminees = len(seances_vues)
    progression = int((seances_terminees / total_seances) * 100) if total_seances > 0 else 0
    
    return render(request, 'website/etudiant/cours_detail.html', {
        'cours': cours,
        'seances': seances,
        'seances_vues': seances_vues,
        'seances_terminees': seances_terminees,
        'seances_total': total_seances,
        'progression': progression,
    })
    
    
@login_required
def forum_liste(request):
    """Liste des forums accessibles à l'utilisateur"""
    from .models import Forum, MessageForum, ConfigurationMessagerie
    
    # Récupérer la configuration
    config = ConfigurationMessagerie.get_config()
    
    # Récupérer tous les forums actifs
    tous_forums = Forum.objects.filter(actif=True).order_by('type_forum', 'ordre', 'nom')
    
    # Séparer les forums par type
    forums_plateforme = []
    forums_ecoles = []
    forums_specialites = []
    
    for forum in tous_forums:
        accessible = False
        
        # Super admin voit tout
        if request.user.role == 'super_admin':
            accessible = True
        
        # Forum plateforme - accessible à tous les utilisateurs connectés
        elif forum.type_forum == 'plateforme':
            accessible = True
        
        # Forum école
        elif forum.type_forum == 'ecole' and forum.ecole:
            if request.user.role == 'admin_ecole':
                if hasattr(request.user, 'ecole_admin') and request.user.ecole_admin == forum.ecole:
                    accessible = True
            
            elif request.user.role == 'enseignant':
                if hasattr(request.user, 'enseignant_ecoles') and forum.ecole in request.user.enseignant_ecoles.all():
                    accessible = True
            
            elif request.user.role == 'etudiant':
                if hasattr(request.user, 'inscriptions'):
                    for inscription in request.user.inscriptions.all():
                        if inscription.specialite and inscription.specialite.filiere:
                            if inscription.specialite.filiere.ecole == forum.ecole:
                                accessible = True
                                break
        
        # Forum spécialité
        elif forum.type_forum == 'specialite' and forum.specialite:
            if request.user.role == 'etudiant':
                if hasattr(request.user, 'inscriptions'):
                    for inscription in request.user.inscriptions.all():
                        if inscription.specialite == forum.specialite:
                            accessible = True
                            break
            
            elif request.user.role == 'enseignant':
                if hasattr(request.user, 'cours_crees'):
                    for cours in request.user.cours_crees.all():
                        if cours.specialite == forum.specialite:
                            accessible = True
                            break
        
        if accessible:
            # Compter les messages non lus
            try:
                forum.non_lus = MessageForum.objects.filter(
                    forum=forum, est_cache=False
                ).exclude(auteur=request.user).count()
            except:
                forum.non_lus = 0
            
            forum.total_messages = forum.messages.filter(est_cache=False).count()
            
            # Ajouter à la bonne liste
            if forum.type_forum == 'plateforme':
                forums_plateforme.append(forum)
            elif forum.type_forum == 'ecole':
                forums_ecoles.append(forum)
            elif forum.type_forum == 'specialite':
                forums_specialites.append(forum)
    
    # Compter les totaux
    total_messages = sum(f.total_messages for f in forums_plateforme + forums_ecoles + forums_specialites)
    total_sujets = len(forums_plateforme + forums_ecoles + forums_specialites)
    total_membres = request.user.__class__.objects.filter(is_active=True).count()
    
    context = {
        'config': config,
        'forums_plateforme': forums_plateforme,
        'forums_ecoles': forums_ecoles,
        'forums_specialites': forums_specialites,
        'total_messages': total_messages,
        'total_sujets': total_sujets,
        'total_membres': total_membres,
    }
    
    return render(request, 'website/forum/liste.html', context)

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
    """Détail d'un cours pour super admin / admin ecole / enseignant"""
    cours = get_object_or_404(CoursProgramme, id=cours_id)
    
    # Récupérer les séances (peu importe le statut pour les admins)
    from .models import SeanceBase
    seances = SeanceBase.objects.filter(cours=cours).order_by('ordre', 'date_creation')
    
    print(f"DEBUG - Cours: {cours.titre}, Séances trouvées: {seances.count()}")  # Debug
    
    return render(request, 'website/cours/detail.html', {
        'cours': cours,
        'seances': seances,
        'est_enseignant': True,
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

# ==================== BIGBLUEBUTTON (VISIO) ====================
import hashlib
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
    name = f"Edumax - {seance.titre}"
    
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
        messages.error(request, 'Vous n\'avez pas les droits.')
        return redirect('specialite_detail', specialite_id=cours.specialite.id)
    
    if request.method == 'POST':
        form = CoursProgrammeForm(request.POST)
        if form.is_valid():
            from .models import Utilisateur
            enseignant = None
            if form.cleaned_data.get('enseignant'):
                enseignant = Utilisateur.objects.get(id=form.cleaned_data['enseignant'])
            
            cours.titre = form.cleaned_data['titre']
            cours.description = form.cleaned_data['description']
            cours.objectifs = form.cleaned_data.get('objectifs', '')
            cours.enseignant = enseignant
            cours.date_debut = form.cleaned_data['date_debut']
            cours.date_fin = form.cleaned_data.get('date_fin')
            cours.actif = form.cleaned_data.get('actif', True)
            cours.mode_programmation = form.cleaned_data.get('mode_programmation', 'recurrent')
            cours.statut = form.cleaned_data.get('statut', 'en_cours')
            cours.save()
            messages.success(request, 'Cours modifié.')
            return redirect('specialite_detail', specialite_id=cours.specialite.id)
    else:
        form = CoursProgrammeForm(initial={
            'titre': cours.titre,
            'description': cours.description,
            'objectifs': cours.objectifs,
            'enseignant': cours.enseignant.id if cours.enseignant else '',
            'date_debut': cours.date_debut,
            'date_fin': cours.date_fin,
            'actif': cours.actif,
            'mode_programmation': cours.mode_programmation,
            'statut': cours.statut,
        })
    
    return render(request, 'website/cours/modifier.html', {'form': form, 'cours': cours})


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

   
import hashlib
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
    from .models import SeanceBase, SeanceVisio
    import hashlib
    import time
    from django.conf import settings
    
    seance = get_object_or_404(SeanceBase, id=seance_id, type_seance='visio')
    
    if request.user.role != 'enseignant':
        messages.error(request, 'Accès réservé aux enseignants.')
        return redirect('seance_detail', seance_id=seance.id)
    
    # Récupérer ou créer l'objet SeanceVisio
    visio, created = SeanceVisio.objects.get_or_create(seance=seance)
    
    if visio.lien_enseignant:
        return redirect(visio.lien_enseignant)
    
    meeting_id = f"edumax_{seance.id}_{int(time.time())}"
    
    params = {
        'meetingID': meeting_id,
        'name': seance.titre[:80],
        'attendeePW': 'user123',
        'moderatorPW': 'admin123',
        'record': 'true',
        'autoStartRecording': 'true',
        'allowStartStopRecording': 'false',
        'duration': seance.duree_estimee or 120,
    }
    
    # Utiliser des valeurs par défaut si settings n'a pas BBB_URL
    BBB_URL = getattr(settings, 'BBB_URL', 'https://test.bigbluebutton.org/bigbluebutton/')
    BBB_SECRET = getattr(settings, 'BBB_SECRET', '8cd8ef52e8e101574e400365b55e11a6')
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    checksum = hashlib.sha1(f"create{query_string}{BBB_SECRET}".encode()).hexdigest()
    url = f"{BBB_URL}api/create?{query_string}&checksum={checksum}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and 'returncode="SUCCESS"' in response.text:
            # Lien pour l'enseignant (modérateur)
            join_params_mod = {
                'meetingID': meeting_id,
                'password': 'admin123',
                'fullName': f"{request.user.prenom} {request.user.username}",
                'role': 'MODERATOR'
            }
            join_query_mod = '&'.join([f"{k}={v}" for k, v in join_params_mod.items()])
            join_checksum_mod = hashlib.sha1(f"join{join_query_mod}{BBB_SECRET}".encode()).hexdigest()
            lien_enseignant = f"{BBB_URL}api/join?{join_query_mod}&checksum={join_checksum_mod}"
            
            # Lien pour l'étudiant (participant)
            join_params_etud = {
                'meetingID': meeting_id,
                'password': 'user123',
                'fullName': 'Étudiant',
                'role': 'VIEWER'
            }
            join_query_etud = '&'.join([f"{k}={v}" for k, v in join_params_etud.items()])
            join_checksum_etud = hashlib.sha1(f"join{join_query_etud}{BBB_SECRET}".encode()).hexdigest()
            lien_etudiant = f"{BBB_URL}api/join?{join_query_etud}&checksum={join_checksum_etud}"
            
            visio.meeting_id = meeting_id
            visio.lien_enseignant = lien_enseignant
            visio.lien_etudiant = lien_etudiant
            visio.save()
            
            messages.success(request, 'Salle de visio créée avec succès.')
            return redirect(lien_enseignant)
        else:
            # Mode mock pour développement
            visio.meeting_id = meeting_id
            visio.lien_enseignant = f"/visio/mock/enseignant/{seance.id}"
            visio.lien_etudiant = f"/visio/mock/etudiant/{seance.id}"
            visio.save()
            messages.warning(request, 'Mode démo: salle de visio simulée.')
            return redirect(visio.lien_enseignant)
    except Exception as e:
        print(f"Erreur BBB: {e}")
        # Mode mock
        visio.meeting_id = meeting_id
        visio.lien_enseignant = f"/visio/mock/enseignant/{seance.id}"
        visio.lien_etudiant = f"/visio/mock/etudiant/{seance.id}"
        visio.save()
        messages.warning(request, 'Mode démo: salle de visio simulée.')
        return redirect(visio.lien_enseignant)
        
# ==================== CRÉATION D'UNE SÉANCE ====================
@login_required
def seance_ajouter(request, cours_id):
    cours = get_object_or_404(CoursProgramme, id=cours_id)
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SeanceBaseForm(request.POST)
        if form.is_valid():
            from .models import SeanceBase, SeanceVisio
            import uuid
            
            seance = SeanceBase.objects.create(
                cours=cours,
                titre=form.cleaned_data['titre'],
                description=form.cleaned_data.get('description', ''),
                objectifs=form.cleaned_data.get('objectifs', ''),
                type_seance=form.cleaned_data['type_seance'],
                ordre=form.cleaned_data.get('ordre', 0),
                duree_estimee=form.cleaned_data.get('duree_estimee', 60),
                created_by=request.user
            )
            
            # ========== CRÉER LA VISIO SI TYPE VISIO ==========
            if seance.type_seance == 'visio':
                meeting_id = f"edumax_{seance.id}_{uuid.uuid4().hex[:8]}"
                SeanceVisio.objects.create(
                    seance=seance,
                    meeting_id=meeting_id,
                    lien_enseignant=f"/visio/mock/enseignant/{seance.id}",
                    lien_etudiant=f"/visio/mock/etudiant/{seance.id}"
                )
                messages.info(request, 'Salle de visio créée (mode mock).')
            
            messages.success(request, f'Séance "{seance.titre}" créée.')
            
            # Redirection selon le type
            if seance.type_seance == 'visio':
                return redirect('seance_visio_config', seance_id=seance.id)
            elif seance.type_seance == 'asynchrone':
                return redirect('seance_asynchrone_config', seance_id=seance.id)
            elif seance.type_seance == 'integration':
                return redirect('seance_integration_config', seance_id=seance.id)
            elif seance.type_seance == 'correction':
                return redirect('seance_correction_config', seance_id=seance.id)
            
            return redirect('cours_detail_superadmin', cours_id=cours.id)
    else:
        form = SeanceBaseForm()
    
    return render(request, 'website/seance/ajouter.html', {'form': form, 'cours': cours})

# ==================== DÉTAIL D'UNE SÉANCE ====================
@login_required
def seance_detail(request, seance_id):
    """Afficher le détail d'une séance selon son type — VERSION COMPLÈTE."""
    from .models import SeanceBase, InscriptionEtudiant, ProgressionEtudiantSeance

    seance = get_object_or_404(SeanceBase, id=seance_id)
    user = request.user
    est_enseignant = user.role in ['enseignant', 'admin_ecole', 'super_admin']
    est_inscrit = InscriptionEtudiant.objects.filter(
        etudiant=user, specialite=seance.cours.specialite
    ).exists() if user.role == 'etudiant' else False

    if not (est_enseignant or est_inscrit):
        messages.error(request, 'Vous n\'avez pas accès à cette séance.')
        return redirect('dashboard')

    # Marquer comme vu pour les étudiants
    if user.role == 'etudiant':
        progression, _ = ProgressionEtudiantSeance.objects.get_or_create(
            seance=seance, etudiant=user
        )
        if not progression.vu:
            progression.vu = True
            progression.date_vu = timezone.now()
            progression.save(update_fields=['vu', 'date_vu'])

    context = {
        'seance':         seance,
        'cours':          seance.cours,
        'est_enseignant': est_enseignant,
    }

    # ── TYPE VISIO ──────────────────────────────────────────────────
    if seance.type_seance == SeanceBase.TYPE_VISIO:
        visio = getattr(seance, 'visio', None)
        context['visio'] = visio
        if visio and visio.enregistrement_url and visio.enregistrement_valide():
            context['enregistrement_disponible'] = True
            context['enregistrement_expire_le']  = visio.enregistrement_disponible_jusqua

    # ── TYPE ASYNCHRONE ─────────────────────────────────────────────
    elif seance.type_seance == SeanceBase.TYPE_ASYNCHRONE:
        context['ressources'] = seance.ressources.all().order_by('ordre')

    # ── TYPE INTÉGRATION (RÉACTIVÉ) ─────────────────────────────────
    elif seance.type_seance == SeanceBase.TYPE_INTEGRATION:
        from .models import SoumissionExercice

        exercices = seance.exercices.all().order_by('id')
        context['exercices_integration'] = exercices

        if user.role == 'etudiant':
            # Pour chaque exercice, indiquer si l'étudiant a déjà soumis
            soumissions = {
                s.exercice_id: s for s in SoumissionExercice.objects.filter(
                    etudiant=user, exercice__in=exercices
                ).order_by('-date_debut')
            }
            for ex in exercices:
                ex.ma_soumission = soumissions.get(ex.id)
                ex.peut_passer   = ex.peut_etre_passe_par(user)
        else:
            # Enseignant : nombre de soumissions reçues par exercice
            for ex in exercices:
                ex.nb_soumissions = SoumissionExercice.objects.filter(
                    exercice=ex, status='termine'
                ).count()

    # ── TYPE CORRECTION (NOUVELLEMENT IMPLÉMENTÉ) ───────────────────
    elif seance.type_seance == SeanceBase.TYPE_CORRECTION:
        from .models import VueCorrectionEtudiant

        correction = getattr(seance, 'correction', None)
        context['correction'] = correction

        if correction:
            if user.role == 'etudiant' and correction.publie:
                # Tracer la consultation
                VueCorrectionEtudiant.objects.get_or_create(
                    correction=correction, etudiant=user
                )
            if est_enseignant:
                context['nb_vues_correction'] = correction.vues.count()

            # Soumissions de la séance corrigée (si liée à un exercice)
            if correction.seance_corrigee:
                from .models import SoumissionExercice
                exercices_corriges = correction.seance_corrigee.exercices.all()
                context['exercices_corriges'] = exercices_corriges
                if est_enseignant:
                    context['soumissions_a_revoir'] = SoumissionExercice.objects.filter(
                        exercice__in=exercices_corriges, status='termine'
                    ).select_related('etudiant').order_by('-date_soumission')[:20]

    return render(request, 'website/seance/detail.html', context)

# ==================== PUBLIER UNE SÉANCE ====================
@login_required
def seance_publier(request, seance_id):
    """Publier une séance (la rendre visible aux étudiants)"""
    seance = get_object_or_404(SeanceBase, id=seance_id)
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits.')
        return redirect('dashboard')
    
    if seance.statut == SeanceBase.STATUT_BROUILLON:
        seance.publier()
        messages.success(request, f'La séance "{seance.titre}" a été publiée et est maintenant visible par les étudiants.')
    else:
        messages.warning(request, 'Cette séance est déjà publiée.')
    
    return redirect('seance_detail', seance_id=seance.id)

# ==================== GESTION VISIOCONFÉRENCE ====================
@login_required
def seance_visio_config(request, seance_id):
    """Configurer une séance de visioconférence"""
    seance = get_object_or_404(SeanceBase, id=seance_id, type_seance=SeanceBase.TYPE_VISIO)
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits.')
        return redirect('dashboard')
    
    visio = getattr(seance, 'visio', None)
    
    return render(request, 'website/seance/visio_config.html', {
        'seance': seance,
        'visio': visio,
    })


@login_required
def seance_visio_demarrer(request, seance_id):
    seance = get_object_or_404(SeanceBase, id=seance_id, type_seance=SeanceBase.TYPE_VISIO)
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits pour démarrer la visio.')
        return redirect('dashboard')
    
    visio = getattr(seance, 'visio', None)
    
    if not visio:
        messages.error(request, 'Erreur: aucune configuration de visio trouvée.')
        return redirect('seance_detail', seance_id=seance.id)
    
    # Démarrer la réunion
    visio.est_active = True
    visio.date_debut = timezone.now()
    visio.save()
    
    messages.success(request, 'La visioconférence a été démarrée.')
    
    # Rediriger l'enseignant vers son lien
    if visio.lien_enseignant:
        return redirect(visio.lien_enseignant)
    
    return redirect('seance_detail', seance_id=seance.id)

@login_required
def seance_visio_rejoindre(request, seance_id):
    seance = get_object_or_404(SeanceBase, id=seance_id, type_seance=SeanceBase.TYPE_VISIO)
    
    if request.user.role != 'etudiant':
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('dashboard')
    
    if not InscriptionEtudiant.objects.filter(etudiant=request.user, specialite=seance.cours.specialite).exists():
        messages.error(request, 'Vous n\'êtes pas inscrit à ce cours.')
        return redirect('dashboard')
    
    visio = getattr(seance, 'visio', None)
    
    if not visio or not visio.est_active:
        messages.error(request, 'La visioconférence n\'est pas encore démarrée.')
        return redirect('seance_detail', seance_id=seance.id)
    
    if visio.lien_etudiant:
        return redirect(visio.lien_etudiant)
    
    messages.error(request, 'Erreur: lien de participation non disponible.')
    return redirect('seance_detail', seance_id=seance.id)


@login_required
def seance_visio_terminer(request, seance_id):
    """Terminer la visioconférence (enseignant) — fonctionne maintenant."""
    from .models import SeanceBase

    seance = get_object_or_404(SeanceBase, id=seance_id, type_seance=SeanceBase.TYPE_VISIO)

    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits.')
        return redirect('dashboard')

    visio = getattr(seance, 'visio', None)

    if visio:
        visio.terminer()
        messages.success(request, 'La visioconférence a été terminée.')
    else:
        messages.error(request, 'Aucune configuration de visio trouvée.')

    return redirect('seance_detail', seance_id=seance.id)


# ==================== SÉANCE ASYNCHRONE ====================
@login_required
def seance_asynchrone_config(request, seance_id):
    """Configurer une séance asynchrone (ajout de ressources)"""
    seance = get_object_or_404(SeanceBase, id=seance_id, type_seance=SeanceBase.TYPE_ASYNCHRONE)
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits.')
        return redirect('dashboard')
    
    ressources = seance.ressources.all().order_by('ordre')
    
    if request.method == 'POST':
        form = RessourceSeanceForm(request.POST, request.FILES)
        if form.is_valid():
            ressource = form.save(commit=False)
            ressource.seance = seance
            
            if ressource.type_ressource == 'fichier':
                ressource.nom_fichier = request.FILES['fichier'].name
                ressource.taille_fichier = request.FILES['fichier'].size
                ressource.format_fichier = request.FILES['fichier'].name.split('.')[-1].lower()
            
            ressource.save()
            messages.success(request, 'Ressource ajoutée avec succès.')
            return redirect('seance_asynchrone_config', seance_id=seance.id)
    else:
        form = RessourceSeanceForm()
    
    return render(request, 'website/seance/asynchrone_config.html', {
        'seance': seance,
        'ressources': ressources,
        'form': form,
    })


@login_required
def seance_asynchrone_ressource_supprimer(request, ressource_id):
    """Supprimer une ressource d'une séance asynchrone"""
    ressource = get_object_or_404(RessourceSeance, id=ressource_id)
    seance_id = ressource.seance.id
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits.')
        return redirect('dashboard')
    
    ressource.delete()
    messages.success(request, 'Ressource supprimée.')
    return redirect('seance_asynchrone_config', seance_id=seance_id)

# ==================== ACTIVITÉ D'INTÉGRATION ====================
@login_required
def seance_integration_config(request, seance_id):
    """Configurer une activité d'intégration (gestion des exercices) — corrigée."""
    from .models import SeanceBase, SoumissionExercice

    seance = get_object_or_404(SeanceBase, id=seance_id, type_seance=SeanceBase.TYPE_INTEGRATION)

    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits.')
        return redirect('dashboard')

    exercices = seance.exercices.all().order_by('id')
    for ex in exercices:
        ex.nb_questions_total = ex.nb_questions if hasattr(ex, 'nb_questions') else 0
        ex.nb_soumissions     = SoumissionExercice.objects.filter(exercice=ex, status='termine').count()

    return render(request, 'website/seance/integration_config.html', {
        'seance':    seance,
        'exercices': exercices,
    })


# ==================== VUES POUR EXERCICES ====================
@login_required
def exercice_ajouter(request, seance_id):
    from .models import SeanceBase, Exercice

    seance = get_object_or_404(SeanceBase, id=seance_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    if request.method == 'POST':
        titre         = request.POST.get('titre', '').strip()
        consignes     = request.POST.get('consignes', '').strip()
        type_exercice = request.POST.get('type_exercice', 'qcm')
        duree         = int(request.POST.get('duree', 30))
        points        = int(request.POST.get('points', 10))
        context_type  = request.POST.get('context_type', 'session')
        nb_tentatives = int(request.POST.get('nb_tentatives_max', 1))

        if not titre or not consignes:
            messages.error(request, 'Titre et consignes sont obligatoires.')
            return redirect('exercice_ajouter', seance_id=seance_id)

        exercice = Exercice.objects.create(
            seance=seance,
            titre=titre,
            consignes=consignes,
            type_exercice=type_exercice,
            duree=duree,
            points=points,
            context_type=context_type,
            nb_tentatives_max=nb_tentatives,
            melanger_questions='melanger_questions' in request.POST,
            melanger_reponses='melanger_reponses' in request.POST,
            afficher_note_immediate='afficher_note_immediate' in request.POST,
            afficher_correction_immediate='afficher_correction_immediate' in request.POST,
            multi_reponse='multi_reponse' in request.POST,
        )
        messages.success(request, f'Exercice "{titre}" créé.')

        # Rediriger vers la config selon le type
        if type_exercice in ['qcm', 'vrai_faux']:
            return redirect('qcm_configurer', exercice_id=exercice.id)
        return redirect('seance_detail', seance_id=seance.id)

    context = {
        'seance':         seance,
        'type_choices':   Exercice.TYPE_CHOICES,
        'context_choices': Exercice.CONTEXT_CHOICES,
    }
    return render(request, 'website/exercice/ajouter.html', context)

@login_required
def exercice_configurer(request, exercice_id):
    from .models import Exercice

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    if exercice.type_exercice in ['qcm', 'vrai_faux']:
        return redirect('qcm_configurer', exercice_id=exercice_id)

    # Pour les autres types (rédaction, dépôt fichier, etc.)
    context = {'exercice': exercice}
    return render(request, 'website/exercice/configurer.html', context)


@login_required
def exercice_lancer(request, exercice_id):
    exercice = get_object_or_404(Exercice, id=exercice_id)
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    exercice.est_lance = True
    exercice.save()
    messages.success(request, f'Exercice "{exercice.titre}" lancé.')
    return redirect('seance_detail', seance_id=exercice.seance.id)


@login_required
def exercice_publier_resultats(request, exercice_id):
    exercice = get_object_or_404(Exercice, id=exercice_id)
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    exercice.resultats_publies = True
    exercice.save()
    messages.success(request, 'Résultats publiés.')
    return redirect('seance_detail', seance_id=exercice.seance.id)


@login_required
def exercice_publier_correction(request, exercice_id):
    exercice = get_object_or_404(exercice, id=exercice_id)
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    exercice.correction_publiee = True
    exercice.save()
    messages.success(request, 'Correction publiée.')
    return redirect('seance_detail', seance_id=exercice.seance.id)


@login_required
def exercice_modifier(request, exercice_id):
    exercice = get_object_or_404(Exercice, id=exercice_id)
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ExerciceForm(request.POST, instance=exercice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exercice modifié.')
            return redirect('seance_detail', seance_id=exercice.seance.id)
    else:
        form = ExerciceForm(instance=exercice)
    
    return render(request, 'website/exercice/modifier.html', {'form': form, 'exercice': exercice})


@login_required
def exercice_supprimer(request, exercice_id):
    exercice = get_object_or_404(Exercice, id=exercice_id)
    seance_id = exercice.seance.id
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    exercice.delete()
    messages.success(request, 'Exercice supprimé.')
    return redirect('seance_detail', seance_id=seance_id)


@login_required
def exercice_resultat(request, exercice_id):
    from .models import Exercice, SoumissionExercice, ReponseEtudiant

    exercice = get_object_or_404(Exercice, id=exercice_id)

    soumission = SoumissionExercice.objects.filter(
        exercice=exercice,
        etudiant=request.user,
        status='termine'
    ).order_by('-date_soumission').first()

    if not soumission:
        messages.warning(request, 'Vous n\'avez pas encore soumis cet exercice.')
        return redirect('exercice_passer', exercice_id=exercice_id)

    reponses = ReponseEtudiant.objects.filter(
        soumission=soumission
    ).select_related('question', 'reponse_choisie').prefetch_related(
        'question__reponses', 'reponses_choisies'
    ).order_by('question__ordre')

    context = {
        'exercice':   exercice,
        'soumission': soumission,
        'reponses':   reponses,
        'afficher_correction': exercice.correction_publiee or exercice.afficher_correction_immediate,
        'afficher_note':       exercice.resultats_publies  or exercice.afficher_note_immediate,
    }
    return render(request, 'website/exercice/qcm/resultat.html', context)


# ==================== VUES POUR DEVOIRS ====================
@login_required
def devoir_configurer(request, devoir_id):
    """Configurer un devoir (type d'exercice, consignes, etc.)"""
    from .models import Devoir, Exercice
    
    devoir = get_object_or_404(Devoir, id=devoir_id)
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Mettre à jour le devoir
        devoir.titre = request.POST.get('titre', devoir.titre)
        devoir.description = request.POST.get('description', devoir.description)
        devoir.consignes = request.POST.get('consignes', devoir.consignes)
        devoir.type_exercice = request.POST.get('type_exercice', devoir.type_exercice)
        devoir.save()
        
        # Créer l'exercice correspondant
        exercice = Exercice.objects.create(
            seance=devoir.seance,
            titre=devoir.titre,
            consignes=devoir.consignes,
            type_exercice=devoir.type_exercice,
            points=10,
            duree=60,
            est_publie=devoir.est_publie,
            context_type='homework',  # Devoir
        )
        
        messages.success(request, f'Devoir "{devoir.titre}" configuré. Vous pouvez maintenant ajouter le contenu.')
        
        # Rediriger vers la configuration du type d'exercice correspondant
        if devoir.type_exercice == 'qcm':
            return redirect('qcm_configurer', exercice_id=exercice.id)
        elif devoir.type_exercice == 'vrai_faux':
            return redirect('vrai_faux_configurer', exercice_id=exercice.id)
        elif devoir.type_exercice == 'texte_trous':
            return redirect('texte_trous_configurer', exercice_id=exercice.id)
        elif devoir.type_exercice == 'reponse_courte':
            return redirect('reponse_courte_configurer', exercice_id=exercice.id)
        elif devoir.type_exercice == 'redaction':
            return redirect('redaction_configurer', exercice_id=exercice.id)
        elif devoir.type_exercice == 'depot_fichier':
            return redirect('depot_fichier_configurer', exercice_id=exercice.id)
        elif devoir.type_exercice == 'etude_cas':
            return redirect('etude_cas_configurer', exercice_id=exercice.id)
        else:
            messages.warning(request, 'Configuration pour ce type de devoir en cours de développement.')
            return redirect('seance_detail', seance_id=devoir.seance.id)
    
    # Récupérer les types d'exercice depuis le modèle Devoir
    type_choices = Devoir.TYPE_CHOICES
    
    context = {
        'devoir': devoir,
        'type_choices': type_choices,
    }
    return render(request, 'website/devoir/configurer.html', context)

@login_required
def devoir_ajouter(request, seance_id):
    seance = get_object_or_404(SeanceBase, id=seance_id)
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DevoirForm(request.POST)
        if form.is_valid():
            devoir = form.save(commit=False)
            devoir.seance = seance
            devoir.save()
            messages.success(request, f'Devoir "{devoir.titre}" créé.')
            return redirect('seance_detail', seance_id=seance.id)
    else:
        form = DevoirForm()
    
    return render(request, 'website/devoir/ajouter.html', {'form': form, 'seance': seance})


@login_required
def devoir_modifier(request, devoir_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DevoirForm(request.POST, instance=devoir)
        if form.is_valid():
            form.save()
            messages.success(request, 'Devoir modifié.')
            return redirect('seance_detail', seance_id=devoir.seance.id)
    else:
        form = DevoirForm(instance=devoir)
    
    return render(request, 'website/devoir/modifier.html', {'form': form, 'devoir': devoir})


@login_required
def devoir_supprimer(request, devoir_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    seance_id = devoir.seance.id
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    devoir.delete()
    messages.success(request, 'Devoir supprimé.')
    return redirect('seance_detail', seance_id=seance_id)


@login_required
def devoir_publier(request, devoir_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    devoir.est_publie = True
    devoir.save()
    messages.success(request, 'Devoir publié.')
    return redirect('seance_detail', seance_id=devoir.seance.id)

@login_required
def devoir_voir_correction(request, devoir_id):
    """Voir la correction d'un devoir (étudiant)"""
    from .models import Devoir, SoumissionDevoir
    
    devoir = get_object_or_404(Devoir, id=devoir_id)
    
    if request.user.role != 'etudiant':
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('dashboard')
    
    soumission = SoumissionDevoir.objects.filter(
        devoir=devoir, 
        etudiant=request.user
    ).first()
    
    if not soumission:
        messages.warning(request, 'Vous n\'avez pas encore soumis ce devoir.')
        return redirect('devoir_soumettre', devoir_id=devoir_id)
    
    if not devoir.correction_publiee:
        messages.warning(request, 'La correction n\'est pas encore disponible.')
        return redirect('seance_detail', seance_id=devoir.seance.id)
    
    context = {
        'devoir': devoir,
        'soumission': soumission,
    }
    return render(request, 'website/devoir/voir_correction.html', context)

@login_required
def devoir_publier_correction(request, devoir_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    
    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    devoir.correction_publiee = True
    devoir.save()
    messages.success(request, 'Correction publiée.')
    return redirect('seance_detail', seance_id=devoir.seance.id)


@login_required
def devoir_soumettre(request, devoir_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    
    if request.user.role != 'etudiant':
        messages.error(request, 'Accès réservé aux étudiants.')
        return redirect('dashboard')
    
    if not devoir.est_publie:
        messages.error(request, 'Ce devoir n\'est pas encore disponible.')
        return redirect('seance_detail', seance_id=devoir.seance.id)
    
    if timezone.now() > devoir.date_limite:
        messages.error(request, 'La date limite est dépassée.')
        return redirect('seance_detail', seance_id=devoir.seance.id)
    
    soumission, created = SoumissionDevoir.objects.get_or_create(devoir=devoir, etudiant=request.user)
    
    if request.method == 'POST':
        form = SoumissionDevoirForm(request.POST, request.FILES, instance=soumission)
        if form.is_valid():
            form.save()
            messages.success(request, 'Devoir soumis avec succès.')
            return redirect('seance_detail', seance_id=devoir.seance.id)
    else:
        form = SoumissionDevoirForm(instance=soumission)
    
    return render(request, 'website/devoir/soumettre.html', {'form': form, 'devoir': devoir, 'soumission': soumission})

from django.db.models import Q, Avg
from decimal import Decimal
from .models import Formation, FichierFormation, Avis, AchatFormation, ConditionVente, Coupon, AcceptationConditionsPublication
from .forms import FormationForm, FichierFormationForm, AvisForm, PaiementForm, ConditionsPublicationForm
from .services.paiement_service import get_paiement_service
import uuid

@login_required
def formations_liste(request):
    """
    Catalogue complet des formations avec :
    - Recherche texte
    - Filtres : catégorie, prix, niveau, langue, note, certifiée
    - Tri dynamique
    - Pagination
    - Wishlist IDs pour l'utilisateur connecté
    """
    from .models import (
        Formation, CentreInteret, Utilisateur, WishlistFormation
    )

    # ── Base queryset ──────────────────────────────────────────────
    qs = Formation.objects.filter(statut='publie').select_related(
        'createur', 'ecole'
    ).prefetch_related('centres_interet')

    # ── Recherche ──────────────────────────────────────────────────
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(titre__icontains=q) |
            Q(description_courte__icontains=q) |
            Q(description_longue__icontains=q) |
            Q(resume__icontains=q) |
            Q(centres_interet__nom__icontains=q)
        ).distinct()

    # ── Filtre centre d'intérêt ────────────────────────────────────
    centres_selectionnes = request.GET.getlist('centre')
    if centres_selectionnes:
        for slug in centres_selectionnes:
            qs = qs.filter(centres_interet__slug=slug)

    centre_actif = centres_selectionnes[0] if len(centres_selectionnes) == 1 else ''

    # ── Filtre prix ────────────────────────────────────────────────
    prix_type = request.GET.get('prix_type', '')
    prix_min  = request.GET.get('prix_min', '')
    prix_max  = request.GET.get('prix_max', '')

    if prix_type == 'gratuit':
        qs = qs.filter(prix=0)
    elif prix_type == 'payant':
        qs = qs.filter(prix__gt=0)
    elif prix_type == 'range':
        if prix_min:
            qs = qs.filter(prix__gte=prix_min)
        if prix_max:
            qs = qs.filter(prix__lte=prix_max)

    # ── Filtre niveau ──────────────────────────────────────────────
    niveaux_selectionnes = request.GET.getlist('niveau')
    if niveaux_selectionnes:
        qs = qs.filter(niveau__in=niveaux_selectionnes)

    # ── Filtre langue ──────────────────────────────────────────────
    langues_selectionnees = request.GET.getlist('langue')
    if langues_selectionnees:
        qs = qs.filter(langue__in=langues_selectionnees)

    # ── Filtre note minimum ────────────────────────────────────────
    note_min = request.GET.get('note_min', '')
    if note_min:
        qs = qs.filter(note_moyenne__gte=note_min)

    # ── Filtre certifiée ───────────────────────────────────────────
    certifiee = request.GET.get('certifiee', '')
    if certifiee:
        qs = qs.filter(certifiee=True)

    # ── Filtre formateur ───────────────────────────────────────────
    formateur_id = request.GET.get('formateur', '')
    if formateur_id:
        qs = qs.filter(createur_id=formateur_id)

    # ── Tri ────────────────────────────────────────────────────────
    tri_map = {
        '-date_publication': '-date_publication',
        '-nb_ventes':        '-nb_ventes',
        '-note_moyenne':     '-note_moyenne',
        'prix':              'prix',
        '-prix':             '-prix',
    }
    tri = request.GET.get('tri', '-date_publication')
    qs = qs.order_by(tri_map.get(tri, '-date_publication'))

    # ── Pagination ─────────────────────────────────────────────────
    paginator = Paginator(qs, 12)
    formations = paginator.get_page(request.GET.get('page'))

    # ── Données sidebar ────────────────────────────────────────────
    tous_centres = list(
        CentreInteret.objects.filter(actif=True).annotate(
            nb=Count('formations', filter=Q(formations__statut='publie'))
        ).filter(nb__gt=0).order_by('-nb', 'nom')
    )

    centres_populaires = tous_centres[:8]

    formateurs_sidebar = Utilisateur.objects.filter(
        role='enseignant',
        formations_crees__statut='publie'
    ).annotate(nb_formations=Count('formations_crees')).order_by('-nb_formations')[:5]

    # ── Wishlist IDs (utilisateur connecté) ───────────────────────
    wishlist_ids = set()
    if request.user.is_authenticated:
        wishlist_ids = set(
            WishlistFormation.objects.filter(utilisateur=request.user)
            .values_list('formation_id', flat=True)
        )

    # ── Stats hero ──────────────────────────────────────────────────
    from .models import Utilisateur as Util
    stats = {
        'nb_formations':  Formation.objects.filter(statut='publie').count(),
        'nb_formateurs':  Util.objects.filter(role='enseignant', formations_crees__statut='publie').distinct().count(),
        'nb_etudiants':   Util.objects.filter(role='etudiant').count(),
    }

    # ── Tags filtres actifs ────────────────────────────────────────
    filtres_tags = _build_filtres_tags(request, tous_centres)
    filtres_actifs_count = len(filtres_tags)

    context = {
        # Formations
        'formations':            formations,
        'q':                     q,
        # Filtres sidebar
        'tous_centres':          tous_centres,
        'centres_selectionnes':  centres_selectionnes,
        'centre_actif':          centre_actif,
        'centres_populaires':    centres_populaires,
        'prix_options':          PRIX_OPTIONS,
        'prix_type':             prix_type,
        'prix_min':              prix_min,
        'prix_max':              prix_max,
        'niveaux':               NIVEAUX,
        'niveaux_selectionnes':  niveaux_selectionnes,
        'langues':               LANGUES,
        'langues_selectionnees': langues_selectionnees,
        'note_min':              note_min,
        'certifiee':             certifiee,
        # Tri
        'tri':                   tri,
        # Sidebar formateurs
        'formateurs_sidebar':    formateurs_sidebar,
        # Wishlist
        'wishlist_ids':          wishlist_ids,
        # Stats
        'stats':                 stats,
        # Tags actifs
        'filtres_tags':          filtres_tags,
        'filtres_actifs_count':  filtres_actifs_count,
    }
    return render(request, 'website/formations/liste.html', context)

@login_required
def formation_detail(request, slug):
    """
    Page de détail complète d'une formation :
    - Vidéo de présentation
    - Curriculum (modules + fichiers)
    - Répartition des notes (barres)
    - Formations similaires
    - Coupon
    """
    from .models import (
        Formation, AchatFormation, Avis,
        WishlistFormation, ProgressionFormation
    )
    from django.db.models import Count as DjCount

    formation = get_object_or_404(Formation, slug=slug, statut='publie')

    # Incrémenter le compteur de vues (sans recharger l'objet)
    formation.incrementer_vues()

    # ── Accès & achat ──────────────────────────────────────────────
    a_deja_achete    = False
    peut_laisser_avis = False
    avis_utilisateur = None
    en_wishlist      = False
    progression      = None

    if request.user.is_authenticated:
        achat = AchatFormation.objects.filter(
            formation=formation, acheteur=request.user, statut='confirme'
        ).first()
        a_deja_achete = achat is not None

        peut_laisser_avis = (
            a_deja_achete and
            not Avis.objects.filter(formation=formation, utilisateur=request.user).exists()
        )
        avis_utilisateur = Avis.objects.filter(
            formation=formation, utilisateur=request.user
        ).first()

        en_wishlist = WishlistFormation.objects.filter(
            utilisateur=request.user, formation=formation
        ).exists()

        if a_deja_achete:
            progression, _ = ProgressionFormation.objects.get_or_create(
                apprenant=request.user, formation=formation
            )

    # ── Fichiers ───────────────────────────────────────────────────
    fichiers = formation.fichiers.select_related('module').order_by('module__ordre', 'ordre')

    # ── Avis & répartition ─────────────────────────────────────────
    avis_list = Avis.objects.filter(formation=formation).select_related(
        'utilisateur'
    ).order_by('-date_creation')[:20]

    # Répartition par note (5→1) → pourcentage pour les barres
    repartition_notes = {}
    total_avis = formation.nb_avis or 1
    for n in range(1, 6):
        nb = Avis.objects.filter(formation=formation, note=n).count()
        repartition_notes[n] = int((nb / total_avis) * 100)

    # ── Formations similaires ──────────────────────────────────────
    centres_ids = formation.centres_interet.values_list('id', flat=True)
    formations_similaires = Formation.objects.filter(
        statut='publie',
        centres_interet__in=centres_ids
    ).exclude(pk=formation.pk).annotate(
        pertinence=DjCount('centres_interet')
    ).order_by('-pertinence', '-note_moyenne')[:6]

    context = {
        'formation':           formation,
        'fichiers':            fichiers,
        'a_deja_achete':       a_deja_achete,
        'peut_laisser_avis':   peut_laisser_avis,
        'avis_utilisateur':    avis_utilisateur,
        'avis_list':           avis_list,
        'repartition_notes':   repartition_notes,
        'formations_similaires': formations_similaires,
        'en_wishlist':         en_wishlist,
        'progression':         progression,
    }
    return render(request, 'website/formations/formation_detail.html', context)

@login_required
def formations_accueil(request):
    """Page d'accueil des formations - Style Coursera"""
    formations = Formation.objects.filter(statut='publie')
    
    # Récupérer TOUS les centres d'intérêt actifs
    tous_centres = CentreInteret.objects.filter(actif=True).order_by('ordre', 'nom')
    
    # Compter le nombre de formations par centre (pour badge)
    centres_avec_nb = []
    for centre in tous_centres:
        nb = centre.formations.filter(statut='publie').count()
        if nb > 0:
            centres_avec_nb.append({
                'id': centre.id,
                'nom': centre.nom,
                'slug': centre.slug,
                'nb_formations': nb
            })
    
    # Pour l'affichage "populaire": utiliser cette même liste ou limiter à 12
    centres_populaires = centres_avec_nb[:12]
    
    # Dernières formations
    dernieres = formations.order_by('-date_publication')[:8]
    
    # Formations gratuites
    gratuites = formations.filter(prix=0).order_by('-date_publication')[:4]
    
    context = {
        'centres_populaires': centres_populaires,
        'tous_centres': tous_centres,
        'dernieres_formations': dernieres,
        'formations_gratuites': gratuites,
    }
    return render(request, 'website/formations/accueil.html', context)

@login_required
def formation_creer(request):
    """Création d'une formation par un enseignant/formateur."""
    from .models import Formation, CentreInteret, ValidationAutomatiqueLog

    if request.method == 'POST':
        titre              = request.POST.get('titre', '').strip()
        description_courte = request.POST.get('description_courte', '').strip()
        description_longue = request.POST.get('description_longue', '').strip()
        resume             = request.POST.get('resume', '').strip()
        prix_raw           = request.POST.get('prix', '0')
        prix_original_raw  = request.POST.get('prix_original', '')
        niveau             = request.POST.get('niveau', 'tous_niveaux')
        langue             = request.POST.get('langue', 'fr')
        duree              = request.POST.get('duree', '').strip()
        objectifs          = request.POST.get('objectifs', '').strip()
        prerequis          = request.POST.get('prerequis', '').strip()
        public_cible       = request.POST.get('public_cible', '').strip()

        if not titre or not description_courte:
            messages.error(request, "Le titre et la description courte sont obligatoires.")
            return redirect('formation_creer')

        try:
            prix = float(prix_raw)
        except (ValueError, TypeError):
            prix = 0.0

        try:
            prix_original = float(prix_original_raw) if prix_original_raw else None
        except (ValueError, TypeError):
            prix_original = None

        formation = Formation(
            createur=request.user,
            titre=titre,
            description_courte=description_courte,
            description_longue=description_longue,
            resume=resume,
            prix=prix,
            prix_original=prix_original,
            niveau=niveau,
            langue=langue,
            duree=duree,
            objectifs=objectifs,
            prerequis=prerequis,
            public_cible=public_cible,
        )

        if 'image_cover' in request.FILES:
            formation.image_cover = request.FILES['image_cover']
        if 'video_presentation' in request.FILES:
            formation.video_presentation = request.FILES['video_presentation']

        # Validation auto ou manuelle
        if getattr(request.user, 'validation_automatique', False):
            formation.statut = 'publie'
            formation.validation_auto = True
            formation.date_publication = timezone.now()
            formation.save()
            ValidationAutomatiqueLog.objects.create(
                utilisateur=request.user,
                formation=formation,
                ip_adresse=_get_client_ip(request)
            )
            messages.success(request, "✅ Formation publiée automatiquement.")
        else:
            formation.statut = 'en_attente'
            formation.save()
            messages.success(request, "✅ Formation soumise à validation. Réponse sous 72h.")

        # Centres d'intérêt
        centres_noms = request.POST.getlist('centres_interet')
        for nom in centres_noms:
            nom = nom.strip()
            if nom:
                centre, _ = CentreInteret.objects.get_or_create(
                    nom__iexact=nom,
                    defaults={'nom': nom, 'slug': slugify(nom)}
                )
                formation.centres_interet.add(centre)

        return redirect('formation_ajouter_fichiers', slug=formation.slug)

    context = {
        'niveaux': NIVEAUX,
        'langues': LANGUES,
    }
    return render(request, 'website/formations/creer.html', context)
    
@login_required
def formations_par_centre(request, slug):
    centre = get_object_or_404(CentreInteret, slug=slug, actif=True)
    formations = centre.formations.filter(statut='publie').order_by('-date_publication')
    
    context = {
        'centre': centre,
        'formations': formations,
        'total': formations.count(),
    }
    return render(request, 'website/formations/par_centre.html', context)

@login_required
@role_required('super_admin')
def centres_interet_liste(request):
    centres = CentreInteret.objects.all().order_by('ordre', 'nom')
    return render(request, 'website/super_admin/formations/centres.html', {'centres': centres})

@login_required
@role_required('super_admin')
def centre_ajouter(request):
    if request.method == 'POST':
        CentreInteret.objects.create(
            nom=request.POST.get('nom'),
            description=request.POST.get('description', ''),
            ordre=request.POST.get('ordre', 0),
            actif=request.POST.get('actif') == 'on'
        )
        messages.success(request, "Centre d'intérêt ajouté")
        return redirect('super_admin_gerer_formations')
    # ...

@login_required
@role_required('super_admin')
def centre_modifier(request, id):
    centre = get_object_or_404(CentreInteret, id=id)
    if request.method == 'POST':
        centre.nom = request.POST.get('nom')
        centre.description = request.POST.get('description', '')
        centre.ordre = request.POST.get('ordre', 0)
        centre.actif = request.POST.get('actif') == 'on'
        centre.save()
        messages.success(request, "Centre modifié")
        return redirect('super_admin_gerer_formations')
    # ...

@login_required
@role_required('super_admin')
def centre_supprimer(request, id):
    centre = get_object_or_404(CentreInteret, id=id)
    centre.delete()
    messages.success(request, "Centre supprimé")
    return redirect('super_admin_gerer_formations')

@require_http_methods(["GET"])
def rechercher_centres_interet(request):
    """Recherche des centres d'intérêt via l'API DBpedia"""
    import requests
    from django.core.cache import cache
    
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse([], safe=False)
    
    cache_key = f"dbpedia_{query.lower()}"
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached, safe=False)
    
    try:
        url = "http://lookup.dbpedia.org/api/search/KeywordSearch"
        params = {'QueryString': query, 'MaxHits': 10, 'Format': 'json'}
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data.get('results', []):
                results.append({
                    'nom': item.get('label', ''),
                    'description': item.get('comment', '')[:100],
                    'uri': item.get('uri', '')
                })
            cache.set(cache_key, results, 60 * 60 * 24)
            return JsonResponse(results, safe=False)
    except Exception as e:
        print(f"Erreur DBpedia: {e}")
    
    return JsonResponse([], safe=False)

@require_http_methods(["POST"])
def creer_centre_interet_api(request):
    """API pour proposer un nouveau centre d'intérêt"""
    data = json.loads(request.body)
    nom = data.get('nom', '').strip()
    
    if nom:
        centre, created = CentreInteret.objects.get_or_create(
            nom=nom.capitalize(),
            defaults={
                'statut': 'en_attente',
                'propose_par': request.user if request.user.is_authenticated else None,
                'actif': False
            }
        )
        if created:
            return JsonResponse({'id': centre.id, 'nom': centre.nom, 'created': True, 'message': 'Proposition envoyée'})
        else:
            return JsonResponse({'id': centre.id, 'nom': centre.nom, 'created': False, 'message': 'Existe déjà'})
    
    return JsonResponse({'error': 'Nom requis'}, status=400)

@login_required
@role_required('super_admin')
def gerer_propositions_centres(request):
    """Gérer les centres d'intérêt proposés"""
    propositions = CentreInteret.objects.filter(statut='en_attente').order_by('-date_proposition')
    approuves = CentreInteret.objects.filter(statut='approuve').order_by('nom')
    rejetes = CentreInteret.objects.filter(statut='rejete').order_by('-date_proposition')[:50]
    
    context = {
        'propositions': propositions,
        'approuves': approuves,
        'rejetes': rejetes,
    }
    return render(request, 'website/super_admin/centres_interet.html', context)

@login_required
@role_required('super_admin')
def approuver_centre(request, centre_id):
    centre = get_object_or_404(CentreInteret, id=centre_id)
    centre.statut = 'approuve'
    centre.actif = True
    centre.date_validation = timezone.now()
    centre.valide_par = request.user
    centre.save()
    messages.success(request, f"Centre '{centre.nom}' approuvé.")
    return redirect('gerer_propositions_centres')

@login_required
@role_required('super_admin')
def rejeter_centre(request, centre_id):
    centre = get_object_or_404(CentreInteret, id=centre_id)
    motif = request.POST.get('motif', 'Contenu inapproprié')
    centre.statut = 'rejete'
    centre.actif = False
    centre.motif_rejet = motif
    centre.save()
    messages.warning(request, f"Centre '{centre.nom}' rejeté.")
    return redirect('gerer_propositions_centres')

@login_required
def formation_ajouter_fichiers(request, slug):
    from .models import Formation, FichierFormation, ModuleFormation

    formation = get_object_or_404(Formation, slug=slug, createur=request.user)

    if request.method == 'POST':
        action = request.POST.get('action', 'ajouter_fichier')

        if action == 'ajouter_module':
            titre_module = request.POST.get('titre_module', '').strip()
            if titre_module:
                ordre = formation.modules.count()
                ModuleFormation.objects.create(formation=formation, titre=titre_module, ordre=ordre)
                messages.success(request, f"Module « {titre_module} » créé.")
            return redirect('formation_ajouter_fichiers', slug=formation.slug)

        if action == 'supprimer_fichier':
            fichier_id = request.POST.get('fichier_id')
            FichierFormation.objects.filter(id=fichier_id, formation=formation).delete()
            messages.success(request, "Fichier supprimé.")
            return redirect('formation_ajouter_fichiers', slug=formation.slug)

        if action == 'supprimer_module':
            module_id = request.POST.get('module_id')
            ModuleFormation.objects.filter(id=module_id, formation=formation).delete()
            messages.success(request, "Module supprimé.")
            return redirect('formation_ajouter_fichiers', slug=formation.slug)

        # Ajouter un fichier
        titre        = request.POST.get('titre', '').strip()
        type_fichier = request.POST.get('type_fichier')
        module_id    = request.POST.get('module_id') or None
        est_apercu   = 'est_apercu' in request.POST
        fichier      = request.FILES.get('fichier')

        if titre and type_fichier and fichier:
            module_obj = None
            if module_id:
                module_obj = ModuleFormation.objects.filter(id=module_id, formation=formation).first()

            FichierFormation.objects.create(
                formation=formation,
                module=module_obj,
                titre=titre,
                type_fichier=type_fichier,
                fichier=fichier,
                taille=fichier.size,
                est_apercu=est_apercu,
                ordre=formation.fichiers.count()
            )
            # Mettre à jour nb_modules
            formation.nb_modules = formation.modules.count() or formation.fichiers.count()
            formation.save(update_fields=['nb_modules'])
            messages.success(request, f"Fichier « {titre} » ajouté.")
        else:
            messages.error(request, "Titre, type et fichier sont obligatoires.")

        return redirect('formation_ajouter_fichiers', slug=formation.slug)

    modules  = formation.modules.prefetch_related('fichiers').order_by('ordre')
    fichiers = formation.fichiers.filter(module=None).order_by('ordre')

    context = {
        'formation':    formation,
        'modules':      modules,
        'fichiers':     fichiers,
        'type_choices': FichierFormation.TYPE_CHOICES,
    }
    return render(request, 'website/formations/ajouter_fichiers.html', context)

@login_required
def formation_publier_confirmation(request, slug):
    formation = get_object_or_404(Formation, slug=slug, createur=request.user)
    
    if request.method == 'POST':
        form = PublicationForm(request.POST)
        if form.is_valid():
            # Passer en attente de validation (pas publié directement)
            formation.statut = 'en_attente'
            formation.save()
            messages.success(request, "Votre formation a été soumise à validation. Vous recevrez une réponse sous 72h.")
            return redirect('mes_formations')
    else:
        form = PublicationForm()
    
    return render(request, 'website/formations/publier_confirmation.html', {
        'formation': formation,
        'form': form
    })

from website.services.paiement_service import calculer_commission
@login_required
def formation_acheter(request, slug):
    from .models import Formation, AchatFormation, ConditionVente, Coupon

    formation = get_object_or_404(Formation, slug=slug, statut='publie')

    # Déjà acheté ?
    if AchatFormation.objects.filter(
        formation=formation, acheteur=request.user, statut='confirme'
    ).exists():
        messages.warning(request, 'Vous avez déjà accès à cette formation.')
        return redirect('formation_detail', slug=formation.slug)

    # Formation gratuite → accès direct
    if formation.prix == 0:
        achat, created = AchatFormation.objects.get_or_create(
            formation=formation,
            acheteur=request.user,
            defaults={
                'prix_original': 0,
                'prix_net': 0,
                'commission': 0,
                'revenu_createur': 0,
                'statut': 'confirme',
                'reference_paiement': f"GRATUIT-{formation.id}-{request.user.id}",
                'date_confirmation': timezone.now(),
            }
        )
        if created:
            formation.nb_ventes += 1
            formation.save(update_fields=['nb_ventes'])
        messages.success(request, '🎉 Accès accordé ! Bonne formation.')
        return redirect('mes_formations')

    # Commission
    condition = ConditionVente.objects.filter(actif=True).first()
    commission_pct = float(condition.commission_pourcentage) if condition else 10.0
    prix = float(formation.prix)

    # Coupon appliqué ?
    coupon_code   = request.GET.get('coupon', '').strip().upper()
    coupon_obj    = None
    reduction     = 0.0
    if coupon_code:
        coupon_obj = Coupon.objects.filter(code=coupon_code, actif=True).first()
        if coupon_obj and coupon_obj.est_valide():
            if coupon_obj.reduction_pourcentage:
                reduction = prix * float(coupon_obj.reduction_pourcentage) / 100
            elif coupon_obj.reduction_fixe:
                reduction = float(coupon_obj.reduction_fixe)
            reduction = min(reduction, prix)

    prix_net         = max(0.0, prix - reduction)
    commission       = (prix_net * commission_pct) / 100
    revenu_createur  = prix_net - commission

    if request.method == 'POST':
        type_paiement = request.POST.get('type_paiement', '')
        telephone     = request.POST.get('telephone', '').strip()
        conditions_ok = 'conditions' in request.POST

        if not type_paiement or not telephone:
            messages.error(request, "Veuillez choisir un mode de paiement et entrer votre numéro.")
            return redirect('formation_acheter', slug=slug)

        if not conditions_ok:
            messages.error(request, "Vous devez accepter les conditions de vente.")
            return redirect('formation_acheter', slug=slug)

        import uuid as _uuid
        ref = f"PAY-{_uuid.uuid4().hex[:12].upper()}"

        achat = AchatFormation.objects.create(
            formation=formation,
            acheteur=request.user,
            coupon=coupon_obj,
            prix_original=prix,
            reduction=reduction,
            prix_net=prix_net,
            commission=commission,
            revenu_createur=revenu_createur,
            statut='en_attente',
            type_paiement=type_paiement,
            telephone=telephone,
            reference_paiement=ref,
            conditions_acceptees=True,
            date_acceptation_conditions=timezone.now(),
            ip_acceptation=_get_client_ip(request),
        )

        # Incrémenter l'utilisation du coupon
        if coupon_obj:
            coupon_obj.utilisations_count += 1
            coupon_obj.save(update_fields=['utilisations_count'])

        messages.success(request, f"Paiement initié (réf: {ref}). Vous recevrez une confirmation.")
        return redirect('formation_confirmation', slug=slug, achat_id=achat.id)

    context = {
        'formation':         formation,
        'prix':              prix,
        'reduction':         reduction,
        'prix_net':          prix_net,
        'commission_pct':    commission_pct,
        'commission':        commission,
        'revenu_createur':   revenu_createur,
        'coupon_code':       coupon_code,
        'coupon_obj':        coupon_obj,
    }
    return render(request, 'website/formations/paiement.html', context)


@login_required
def formation_confirmation(request, slug, achat_id):
    from .models import AchatFormation
    achat = get_object_or_404(AchatFormation, id=achat_id, acheteur=request.user)
    return render(request, 'website/formations/confirmation.html', {'achat': achat})

@login_required
def formation_laisser_avis(request, slug):
    from .models import Formation, AchatFormation, Avis

    formation = get_object_or_404(Formation, slug=slug)

    if not AchatFormation.objects.filter(
        formation=formation, acheteur=request.user, statut='confirme'
    ).exists():
        messages.error(request, "Vous devez avoir acheté la formation pour laisser un avis.")
        return redirect('formation_detail', slug=slug)

    if Avis.objects.filter(formation=formation, utilisateur=request.user).exists():
        messages.warning(request, "Vous avez déjà laissé un avis pour cette formation.")
        return redirect('formation_detail', slug=slug)

    if request.method == 'POST':
        note        = int(request.POST.get('note', 5))
        commentaire = request.POST.get('commentaire', '').strip()

        if not (1 <= note <= 5):
            messages.error(request, "Note invalide (1 à 5).")
            return redirect('formation_laisser_avis', slug=slug)

        Avis.objects.create(
            formation=formation,
            utilisateur=request.user,
            note=note,
            commentaire=commentaire
        )
        formation.mettre_a_jour_note()
        messages.success(request, "Merci pour votre avis ! 🙏")
        return redirect('formation_detail', slug=slug)

    return render(request, 'website/formations/laisser_avis.html', {'formation': formation})

@login_required
def mes_formations(request):
    from .models import Formation, AchatFormation, RegleVente, WishlistFormation

    formations_crees = Formation.objects.filter(
        createur=request.user
    ).annotate(nb_acheteurs=Count('achats')).order_by('-date_creation')

    formations_achetees = Formation.objects.filter(
        achats__acheteur=request.user, achats__statut='confirme'
    ).select_related('createur').order_by('-achats__date_achat')

    wishlist = WishlistFormation.objects.filter(
        utilisateur=request.user
    ).select_related('formation').order_by('-date_ajout')

    regles = RegleVente.objects.filter(actif=True).order_by('rubrique', 'ordre')

    # Stats créateur
    total_ventes  = sum(f.nb_ventes   for f in formations_crees)
    total_revenus = sum(f.revenu_total for f in formations_crees)

    context = {
        'formations_crees':   formations_crees,
        'formations_achetees': formations_achetees,
        'wishlist':            wishlist,
        'regles':              regles,
        'total_ventes':        total_ventes,
        'total_revenus':       total_revenus,
    }
    return render(request, 'website/formations/mes_formations.html', context)

@login_required
@super_admin_required
def formation_configurer_conditions(request):
    condition, created = ConditionVente.objects.get_or_create(actif=True)
    
    if request.method == 'POST':
        condition.commission_pourcentage = request.POST.get('commission_pourcentage')
        condition.frais_fixes = request.POST.get('frais_fixes', 0)
        condition.save()
        messages.success(request, 'Conditions de vente mises à jour.')
        return redirect('formation_configurer_conditions')
    
    return render(request, 'website/super_admin/formations/conditions.html', {'condition': condition})


@login_required
@super_admin_required
def formation_gerer_coupons(request):
    coupons = Coupon.objects.all().order_by('-validite_debut')
    
    if request.method == 'POST':
        code = request.POST.get('code')
        reduction_pourcentage = request.POST.get('reduction_pourcentage', 0)
        reduction_fixe = request.POST.get('reduction_fixe', 0)
        validite_debut = request.POST.get('validite_debut')
        validite_fin = request.POST.get('validite_fin')
        utilisations_max = request.POST.get('utilisations_max', 1)
        
        Coupon.objects.create(
            code=code.upper(),
            reduction_pourcentage=reduction_pourcentage,
            reduction_fixe=reduction_fixe,
            validite_debut=validite_debut,
            validite_fin=validite_fin,
            utilisations_max=utilisations_max
        )
        messages.success(request, 'Code promo créé.')
        return redirect('formation_gerer_coupons')
    
    return render(request, 'website/super_admin/formations/coupons.html', {'coupons': coupons})


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@login_required
def signaler_formation(request, slug):
    from .models import Formation, SignalementFormation

    formation = get_object_or_404(Formation, slug=slug)

    if SignalementFormation.objects.filter(formation=formation, utilisateur=request.user).exists():
        messages.warning(request, "Vous avez déjà signalé cette formation.")
        return redirect('formation_detail', slug=slug)

    if request.method == 'POST':
        motif       = request.POST.get('motif', 'autre')
        description = request.POST.get('description', '').strip()
        SignalementFormation.objects.create(
            formation=formation,
            utilisateur=request.user,
            motif=motif,
            description=description
        )
        messages.success(request, "Formation signalée. Merci pour votre vigilance.")
        return redirect('formation_detail', slug=slug)

    return render(request, 'website/formations/signaler.html', {
        'formation': formation,
        'motifs':    SignalementFormation.MOTIFS,
    })

@login_required
@role_required('super_admin')
def formations_en_attente(request):
    formations = Formation.objects.filter(statut='en_attente').order_by('-date_creation')
    return render(request, 'website/super_admin/formations/en_attente.html', {'formations': formations})

@login_required
@role_required('super_admin')
def valider_formation(request, formation_id):
    formation = get_object_or_404(Formation, id=formation_id)
    if formation.statut == 'en_attente':
        formation.statut = 'publie'
        formation.valide_par = request.user
        formation.date_validation = timezone.now()
        formation.save()
        messages.success(request, f"Formation '{formation.titre}' validée.")
    else:
        messages.error(request, "Cette formation n'est pas en attente.")
    return redirect('super_admin_gerer_formations')  # Changement ici

@login_required
@role_required('super_admin')
def certifier_utilisateur(request, user_id):
    user = get_object_or_404(Utilisateur, id=user_id)
    user.certifie = True
    user.date_certification = timezone.now()
    user.save()
    messages.success(request, f"L'utilisateur {user.username} est maintenant certifié.")
    return redirect('super_admin_utilisateurs')

@login_required
@role_required('super_admin')
def regles_liste(request):
    regles = RegleVente.objects.all().order_by('rubrique', 'ordre')
    return render(request, 'website/super_admin/formations/regles.html', {'regles': regles})

@login_required
@role_required('super_admin')
def regle_ajouter(request):
    if request.method == 'POST':
        form = RegleVenteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Règle ajoutée.")
            return redirect('regles_liste')
    else:
        form = RegleVenteForm()
    return render(request, 'website/super_admin/formations/regle_form.html', {'form': form, 'titre': 'Ajouter une règle'})

@login_required
@role_required('super_admin')
def regle_modifier(request, pk):
    regle = get_object_or_404(RegleVente, pk=pk)
    if request.method == 'POST':
        form = RegleVenteForm(request.POST, instance=regle)
        if form.is_valid():
            form.save()
            messages.success(request, "Règle modifiée.")
            return redirect('regles_liste')
    else:
        form = RegleVenteForm(instance=regle)
    return render(request, 'website/super_admin/formations/regle_form.html', {'form': form, 'titre': 'Modifier une règle'})

@login_required
@role_required('super_admin')
def regle_supprimer(request, pk):
    regle = get_object_or_404(RegleVente, pk=pk)
    regle.delete()
    messages.success(request, "Règle supprimée.")
    return redirect('regles_liste')

@login_required
def super_admin_gerer_formations(request):
    from .models import Formation, Utilisateur, ValidationAutomatiqueLog
    from django.core.paginator import Paginator
    from django.db.models import Q
    from django.utils import timezone

    if request.user.role != 'super_admin':
        return redirect('accueil')

    statut = request.GET.get('statut', 'en_attente')
    q = request.GET.get('q', '').strip()

    qs = Formation.objects.select_related('createur').order_by('-date_creation')
    if statut:
        qs = qs.filter(statut=statut)
    if q:
        qs = qs.filter(Q(titre__icontains=q) | Q(createur__username__icontains=q))

    # Traitement POST
    if request.method == 'POST':
        formation_id = request.POST.get('formation_id')
        action = request.POST.get('action')
        raison = request.POST.get('raison', '').strip()

        formation = get_object_or_404(Formation, id=formation_id)

        if action == 'valider':
            formation.statut = 'publie'
            formation.valide_par = request.user
            formation.date_validation = timezone.now()
            formation.save()
            messages.success(request, f"« {formation.titre} » publiée.")

        elif action == 'refuser':
            formation.statut = 'refuse'
            formation.save()
            messages.warning(request, f"« {formation.titre} » refusée.")

        elif action == 'suspendre':
            formation.statut = 'suspendu'
            formation.save()
            messages.warning(request, f"« {formation.titre} » suspendue.")

        elif action == 'mettre_en_avant':
            formation.mise_en_avant = not formation.mise_en_avant
            formation.save()
            messages.success(request, "Mise en avant modifiée.")

        elif action == 'certifier':
            formation.certifiee = not formation.certifiee
            formation.save()
            messages.success(request, "Certification modifiée.")

        return redirect(f"{request.path}?statut={statut}")

    # Pagination
    paginator = Paginator(qs, 20)
    formations = paginator.get_page(request.GET.get('page'))

    # Compteurs par statut
    counts = {
        'en_attente': Formation.objects.filter(statut='en_attente').count(),
        'publie': Formation.objects.filter(statut='publie').count(),
        'refuse': Formation.objects.filter(statut='refuse').count(),
        'suspendu': Formation.objects.filter(statut='suspendu').count(),
        'brouillon': Formation.objects.filter(statut='brouillon').count(),
    }

    # ========== DONNÉES POUR LE TEMPLATE ==========
    # Formations en attente (pour la section validations manuelles)
    formations_en_attente_list = Formation.objects.filter(statut='en_attente').order_by('-date_creation').select_related('createur')
    
    # Tous les utilisateurs enseignants (pour la section validations automatiques)
    tous_utilisateurs = Utilisateur.objects.filter(role='enseignant').order_by('-date_joined')
    
    # Logs des publications automatiques
    logs_auto_validation = ValidationAutomatiqueLog.objects.all().order_by('-date_log')[:50]

    context = {
        'formations': formations,
        'statut': statut,
        'q': q,
        'counts': counts,
        'formations_en_attente_list': formations_en_attente_list,
        'formations_en_attente': formations_en_attente_list.count(),
        'tous_utilisateurs': tous_utilisateurs,
        'logs_auto_validation': logs_auto_validation,
    }
    return render(request, 'website/super_admin/gerer_formations.html', context)

@login_required
@role_required('super_admin')
def refuser_formation(request, formation_id):
    formation = get_object_or_404(Formation, id=formation_id)
    motif = request.POST.get('motif_refus', '')
    formation.statut = 'refuse'
    formation.save()
    messages.warning(request, f"Formation '{formation.titre}' refusée.")
    return redirect('super_admin_gerer_formations')  # Changement ici

# Supprimer une formation
@login_required
@role_required('super_admin')
def supprimer_formation(request, formation_id):
    formation = get_object_or_404(Formation, id=formation_id)
    formation.delete()
    messages.success(request, "Formation supprimée.")
    return redirect('super_admin_gerer_formations')

# Décertifier un utilisateur
@login_required
@role_required('super_admin')
def decertifier_utilisateur(request, user_id):
    user = get_object_or_404(Utilisateur, id=user_id)
    user.certifie = False
    user.date_certification = None
    user.save()
    messages.success(request, f"Certification retirée à {user.username}.")
    return redirect('super_admin_gerer_formations')

# Traiter un signalement
@login_required
@role_required('super_admin')
def traiter_signalement(request, signalement_id):
    signalement = get_object_or_404(SignalementFormation, id=signalement_id)
    action = request.GET.get('action')
    
    if action == 'supprimer':
        signalement.formation.delete()
        message = "Formation supprimée."
    elif action == 'suspendre':
        signalement.formation.statut = 'suspendu'
        signalement.formation.save()
        message = "Formation suspendue."
    else:
        message = "Signalement ignoré."
    
    signalement.traite = True
    signalement.commentaire_traitement = message
    signalement.save()
    messages.success(request, message)
    return redirect('super_admin_gerer_formations')

@login_required
def demander_remboursement(request, achat_id):
    achat = get_object_or_404(AchatFormation, id=achat_id, acheteur=request.user)
    if achat.date_achat >= timezone.now() - timedelta(days=14):
        achat.statut = 'rembourse'
        achat.save()
        messages.success(request, "Votre demande de remboursement a été enregistrée.")
    else:
        messages.error(request, "Délai de remboursement expiré (14 jours).")
    return redirect('mes_formations')

@login_required
def formation_supprimer_fichier(request, slug, fichier_id):
    """Supprimer un fichier d'une formation"""
    formation = get_object_or_404(Formation, slug=slug)
    
    # Vérifier que l'utilisateur est le créateur de la formation
    if formation.createur != request.user and not request.user.is_superuser:
        messages.error(request, "Vous n'êtes pas autorisé à supprimer ce fichier.")
        return redirect('formation_detail', slug=formation.slug)
    
    fichier = get_object_or_404(FichierFormation, id=fichier_id, formation=formation)
    fichier.delete()
    messages.success(request, f"Fichier '{fichier.titre}' supprimé avec succès.")
    
    return redirect('formation_ajouter_fichiers', slug=formation.slug)

@login_required
@role_required('super_admin')
def certifier_formation(request, formation_id):
    formation = get_object_or_404(Formation, id=formation_id)
    formation.certifiee = not formation.certifiee
    formation.save()
    status = "certifiée" if formation.certifiee else "décertifiée"
    messages.success(request, f"Formation {status}.")
    return redirect('super_admin_gerer_formations')

@login_required
@role_required('super_admin')
def configurer_auto_publication(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        config, _ = ConfigurationPlateforme.objects.get_or_create(id=1)
        config.auto_publication_active = data.get('active', False)
        config.save()
        return JsonResponse({'success': True})

# Cron/Management command pour publication auto
def verifier_publications_auto():
    config = ConfigurationPlateforme.objects.first()
    if config and config.auto_publication_active:
        seuil = timezone.now() - timedelta(minutes=config.auto_publication_delai_minutes)
        formations = Formation.objects.filter(
            statut='en_attente', 
            date_creation__lte=seuil
        )
        for f in formations:
            f.statut = 'publie'
            f.save()
            
@login_required
def formation_supprimer(request, formation_id):
    formation = get_object_or_404(Formation, id=formation_id, createur=request.user)
    formation.delete()
    messages.success(request, "Formation supprimée avec succès.")
    return redirect('mes_formations')

def profil_public(request, user_id):
    user = get_object_or_404(Utilisateur, id=user_id)
    formations = Formation.objects.filter(createur=user, statut='publie')
    context = {
        'profil': user,
        'formations': formations,
        'total_ventes': AchatFormation.objects.filter(formation__createur=user, statut='confirme').count(),
    }
    return render(request, 'website/profil_public.html', context)

@login_required
@role_required('super_admin')
def activer_auto_validation(request, user_id):
    user = get_object_or_404(Utilisateur, id=user_id)
    user.validation_automatique = True
    user.date_activation_auto = timezone.now()
    user.save()
    messages.success(request, f"Validation automatique activée pour {user.username}. Ses formations seront publiées sans validation manuelle.")
    return redirect('super_admin_gerer_formations')

@login_required
@role_required('super_admin')
def desactiver_auto_validation(request, user_id):
    user = get_object_or_404(Utilisateur, id=user_id)
    user.validation_automatique = False
    user.date_activation_auto = None
    user.save()
    messages.success(request, f"Validation automatique désactivée pour {user.username}. Ses formations devront être validées manuellement.")
    return redirect('super_admin_gerer_formations')

# ==================== PARAMÈTRES MESSAGERIE (SUPER ADMIN) ====================

@login_required
@super_admin_required
def parametres_messagerie(request):
    """Page de configuration de la messagerie (polling intelligent)"""
    from .models import ParametresMessagerie
    from .forms import ParametresMessagerieForm
    
    config = ParametresMessagerie.get_config()
    
    # Statistiques pour le tableau de bord
    maintenant = timezone.now()
    debut_jour = maintenant.replace(hour=0, minute=0, second=0, microsecond=0)
    
    from .models import MessagePrive
    
    stats = {
        'messages_aujourdhui': MessagePrive.objects.filter(date_envoi__gte=debut_jour).count(),
        'messages_total': MessagePrive.objects.count(),
        'conversations_total': Conversation.objects.count(),
        'conversations_vides': Conversation.objects.filter(messages__isnull=True).count(),
        'utilisateurs_actifs': request.session.get('utilisateurs_actifs_messagerie', 0),
        'intervalle_actuel': config.intervalle_polling if config.polling_actif else 'Désactivé',
        'charge_estimee': 'faible',  # À calculer
    }
    
    if request.method == 'POST':
        form = ParametresMessagerieForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Paramètres de messagerie mis à jour.')
            
            # Journaliser le changement
            from .models import Notification
            Notification.objects.create(
                utilisateur=request.user,
                titre='Modification messagerie',
                message=f"Intervalle polling modifié à {config.intervalle_polling}s | Actif: {config.polling_actif}"
            )
            
            return redirect('parametres_messagerie')
    else:
        form = ParametresMessagerieForm(instance=config)
    
    return render(request, 'website/super_admin/parametres_messagerie.html', {
        'form': form,
        'config': config,
        'stats': stats,
    })

# ==================== MESSAGERIE PRIVÉE ====================

# ==================== VUES ÉPREUVES ====================

def epreuves_accueil(request):
    """Page d'accueil des épreuves : rubriques principales"""
    rubriques = RubriqueEpreuve.objects.filter(actif=True)
    epreuves_populaires = Epreuve.objects.filter(
        statut='publie', 
        est_populaire=True
    )[:8]
    
    # Calcul des prix des packs par catégorie
    rubriques_data = []
    for rubrique in rubriques:
        categories_data = []
        for cat in rubrique.categories.filter(actif=True):
            categories_data.append({
                'categorie': cat,
                'prix_pack': cat.prix_pack,
                'nb_epreuves': cat.epreuves.filter(statut='publie').count(),
            })
        rubriques_data.append({
            'rubrique': rubrique,
            'categories': categories_data,
        })
    
    context = {
        'rubriques_data': rubriques_data,
        'epreuves_populaires': epreuves_populaires,
    }
    return render(request, 'website/epreuves/accueil.html', context)

@login_required
def epreuves_rubrique(request, slug):
    """Affiche toutes les épreuves d'une rubrique avec filtres"""
    from django.db import models
    
    rubrique = get_object_or_404(RubriqueEpreuve, slug=slug, actif=True)
    
    # Base de la requête
    epreuves = Epreuve.objects.filter(
        categorie__rubrique=rubrique,
        statut='publie'
    ).select_related('categorie')
    
    # Filtres
    serie = request.GET.get('serie', '')
    annee = request.GET.get('annee', '')
    categorie_id = request.GET.get('categorie', '')
    
    if serie:
        epreuves = epreuves.filter(serie=serie)
    if annee:
        epreuves = epreuves.filter(annee=annee)
    if categorie_id:
        epreuves = epreuves.filter(categorie_id=categorie_id)
    
    # Regrouper par année
    annees = epreuves.values_list('annee', flat=True).distinct().order_by('-annee')
    
    # Groupement par année
    epreuves_par_annee = {}
    for an in annees:
        if an:
            epreuves_par_annee[an] = epreuves.filter(annee=an).order_by('categorie__ordre', 'titre')
    
    # Catégories pour filtres
    categories = rubrique.categories.filter(actif=True)
    
    # Séries disponibles (depuis les choix du modèle)
    series_disponibles = [code for code, label in Epreuve.SERIES_CHOICES if code]
    
    context = {
        'rubrique': rubrique,
        'epreuves_par_annee': epreuves_par_annee,
        'categories': categories,
        'series_disponibles': series_disponibles,
        'serie_active': serie,
        'annee_active': annee,
        'categorie_active': categorie_id,
    }
    return render(request, 'website/epreuves/rubrique.html', context)

def epreuves_categorie_ajax(request, categorie_id):
    """AJAX pour charger plus d'épreuves d'une catégorie"""
    categorie = get_object_or_404(CategorieEpreuve, id=categorie_id)
    epreuves = categorie.epreuves.filter(statut='publie').order_by('-annee', 'titre')
    
    html = render_to_string('website/epreuves/partials/epreuves_grid.html', 
                           {'epreuves': epreuves[:20]})
    return JsonResponse({'html': html, 'total': epreuves.count()})


def epreuve_detail(request, epreuve_id):
    epreuve = get_object_or_404(Epreuve, id=epreuve_id, statut='publie')
    return render(request, 'website/epreuves/detail.html', {'epreuve': epreuve})


# ==================== VUES ADMIN ÉPREUVES ====================

from django.contrib.admin.views.decorators import staff_member_required
from django.utils.text import slugify
from .models import RubriqueEpreuve, CategorieEpreuve, Epreuve



# ========== GESTION DES RUBRIQUES ==========

@staff_member_required
def admin_rubrique_ajouter(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        ordre = request.POST.get('ordre', 0)
        if nom:
            rubrique = RubriqueEpreuve.objects.create(
                nom=nom,
                ordre=ordre,
                slug=slugify(nom)
            )
            messages.success(request, f'Rubrique "{nom}" créée avec succès.')
            return redirect('admin_epreuves_dashboard')
    return redirect('admin_epreuves_dashboard')


@staff_member_required
def admin_rubrique_modifier(request, rubrique_id):
    rubrique = get_object_or_404(RubriqueEpreuve, id=rubrique_id)
    if request.method == 'POST':
        rubrique.nom = request.POST.get('nom', rubrique.nom)
        rubrique.ordre = request.POST.get('ordre', rubrique.ordre)
        rubrique.actif = request.POST.get('actif') == 'on'
        rubrique.slug = slugify(rubrique.nom)
        rubrique.save()
        messages.success(request, f'Rubrique "{rubrique.nom}" modifiée.')
        return redirect('admin_epreuves_dashboard')
    return redirect('admin_epreuves_dashboard')


@staff_member_required
def admin_rubrique_supprimer(request, rubrique_id):
    rubrique = get_object_or_404(RubriqueEpreuve, id=rubrique_id)
    nom = rubrique.nom
    rubrique.delete()
    messages.success(request, f'Rubrique "{nom}" supprimée.')
    return redirect('admin_epreuves_dashboard')


# ========== GESTION DES CATÉGORIES ==========

@staff_member_required
def admin_categorie_ajouter(request):
    if request.method == 'POST':
        rubrique_id = request.POST.get('rubrique')
        nom = request.POST.get('nom')
        ordre = request.POST.get('ordre', 0)
        
        CategorieEpreuve.objects.create(
            rubrique_id=rubrique_id,
            nom=nom,
            ordre=ordre,
        )
        messages.success(request, "Catégorie ajoutée avec succès")
        return redirect('admin_epreuves_dashboard')
    
    return redirect('admin_epreuves_dashboard')


@staff_member_required
def admin_categorie_modifier(request):
    """Modifier une catégorie"""
    if request.method == 'POST':
        categorie_id = request.POST.get('categorie_id')
        categorie = get_object_or_404(CategorieEpreuve, id=categorie_id)
        
        categorie.rubrique_id = request.POST.get('rubrique')
        categorie.nom = request.POST.get('nom')
        categorie.ordre = request.POST.get('ordre', 0)
        categorie.actif = request.POST.get('actif') == 'on'
        categorie.save()
        
        messages.success(request, f"Catégorie '{categorie.nom}' modifiée avec succès")
        return redirect('admin_epreuves_dashboard')
    
    return redirect('admin_epreuves_dashboard')


@staff_member_required
def admin_categorie_supprimer(request, categorie_id):
    categorie = get_object_or_404(CategorieEpreuve, id=categorie_id)
    nom = categorie.nom
    
    if categorie.epreuves.exists():
        messages.error(request, f"Impossible de supprimer '{nom}' : elle contient encore des épreuves.")
    else:
        categorie.delete()
        messages.success(request, f"Catégorie '{nom}' supprimée avec succès")
    
    return redirect('admin_epreuves_dashboard')


# ========== GESTION DES ÉPREUVES ==========
@staff_member_required
def admin_epreuve_ajouter(request):
    """Ajouter une nouvelle épreuve"""
    if request.method == 'POST':
        try:
            categorie_id = request.POST.get('categorie')
            titre = request.POST.get('titre')
            annee = request.POST.get('annee')
            serie = request.POST.get('serie', '')
            description = request.POST.get('description', '')
            prix = request.POST.get('prix', 0)
            est_populaire = request.POST.get('est_populaire') == 'on'
            statut = request.POST.get('statut', 'brouillon')
            
            # Validation
            if not categorie_id:
                messages.error(request, "Veuillez sélectionner une catégorie")
                return redirect('admin_epreuves_dashboard')
            
            if not titre:
                messages.error(request, "Veuillez saisir un titre")
                return redirect('admin_epreuves_dashboard')
            
            if 'fichier' not in request.FILES:
                messages.error(request, "Veuillez télécharger le fichier de l'épreuve")
                return redirect('admin_epreuves_dashboard')
            
            # Récupérer la catégorie
            categorie = get_object_or_404(CategorieEpreuve, id=categorie_id)
            
            # Créer l'épreuve
            epreuve = Epreuve.objects.create(
                categorie=categorie,
                titre=titre,
                annee=annee if annee else None,
                serie=serie,
                description=description,
                prix=prix,
                est_populaire=est_populaire,
                statut=statut,
                fichier=request.FILES['fichier']  # Champ fichier obligatoire
            )
            
            # Gérer l'aperçu si présent
            if 'apercu' in request.FILES:
                epreuve.apercu = request.FILES['apercu']
                epreuve.save()
            
            messages.success(request, f'Épreuve "{titre}" créée avec succès.')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création : {str(e)}")
        
        return redirect('admin_epreuves_dashboard')
    
    # GET - Rediriger vers le dashboard
    return redirect('admin_epreuves_dashboard')

@staff_member_required
def admin_epreuve_modifier(request, epreuve_id):
    epreuve = get_object_or_404(Epreuve, id=epreuve_id)
    
    if request.method == 'POST':
        epreuve.categorie_id = request.POST.get('categorie', epreuve.categorie_id)
        epreuve.titre = request.POST.get('titre', epreuve.titre)
        epreuve.annee = request.POST.get('annee') or None
        epreuve.serie = request.POST.get('serie', epreuve.serie)
        epreuve.description = request.POST.get('description', '')
        epreuve.prix = request.POST.get('prix', epreuve.prix)
        epreuve.est_populaire = request.POST.get('est_populaire') == 'on'
        epreuve.statut = request.POST.get('statut', epreuve.statut)
        
        # Gérer les fichiers
        if 'fichier' in request.FILES:
            epreuve.fichier = request.FILES['fichier']
        if 'apercu' in request.FILES:
            epreuve.apercu = request.FILES['apercu']
        
        epreuve.save()
        messages.success(request, f'Épreuve "{epreuve.titre}" modifiée.')
        return redirect('admin_epreuves_dashboard')
    
    categories = CategorieEpreuve.objects.filter(actif=True)
    series_choices = [{'code': code, 'label': label} for code, label in Epreuve.SERIES_CHOICES if code]
    
    context = {
        'epreuve': epreuve,
        'categories': categories,
        'series_choices': series_choices,
    }
    return render(request, 'website/super_admin/epreuves/epreuve_modifier.html', context)
@staff_member_required
def admin_epreuve_supprimer(request, epreuve_id):
    epreuve = get_object_or_404(Epreuve, id=epreuve_id)
    titre = epreuve.titre
    epreuve.delete()
    messages.success(request, f'Épreuve "{titre}" supprimée.')
    return redirect('admin_epreuves_dashboard')


@staff_member_required
def admin_epreuves_dashboard(request):
    """Dashboard de gestion des épreuves pour super admin"""
    rubriques = RubriqueEpreuve.objects.all().order_by('ordre')
    categories = CategorieEpreuve.objects.all().order_by('rubrique__ordre', 'ordre')
    epreuves = Epreuve.objects.all().order_by('-date_ajout')
    
    # Récupérer toutes les séries uniques existantes dans les épreuves
    series_existantes = Epreuve.objects.filter(
        statut='publie'
    ).exclude(
        serie=''
    ).values_list('serie', flat=True).distinct().order_by('serie')
    
    # Calcul des ventes totales
    ventes_total = sum(e.nb_ventes for e in epreuves)
    
    stats = {
        'total_rubriques': rubriques.count(),
        'total_categories': categories.count(),
        'total_epreuves': epreuves.count(),
        'epreuves_publiees': epreuves.filter(statut='publie').count(),
        'epreuves_brouillon': epreuves.filter(statut='brouillon').count(),
        'ventes_total': ventes_total,
        'total_series': series_existantes.count(),  # Ajout du compteur
    }
    
    # Liste des choix de séries depuis le modèle (si vous avez SERIES_CHOICES)
    series_choices = []
    if hasattr(Epreuve, 'SERIES_CHOICES'):
        series_choices = [{'code': code, 'nom': nom} for code, nom in Epreuve.SERIES_CHOICES if code]
    
    context = {
        'rubriques': rubriques,
        'categories': categories,
        'epreuves': epreuves,
        'stats': stats,
        'series_existantes': series_existantes,  # Séries déjà utilisées
        'series_choices': series_choices,  # Toutes les séries disponibles
    }
    return render(request, 'website/super_admin/epreuves/dashboard.html', context)


# ========== RECHERCHE ==========
def epreuves_recherche(request):
    from django.db import models
    
    query = request.GET.get('q', '').strip()
    
    categories_trouvees = []
    epreuves_trouvees = []
    
    if query:
        # Rechercher les catégories
        categories_trouvees = CategorieEpreuve.objects.filter(
            models.Q(nom__icontains=query) |
            models.Q(rubrique__nom__icontains=query)
        ).filter(actif=True).select_related('rubrique').distinct()
        
        # Rechercher les épreuves
        epreuves_trouvees = Epreuve.objects.filter(
            models.Q(titre__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(annee__icontains=query) |
            models.Q(serie__icontains=query) |
            models.Q(categorie__nom__icontains=query) |
            models.Q(categorie__rubrique__nom__icontains=query)
        ).filter(statut='publie').select_related('categorie', 'categorie__rubrique').distinct()
    
    # Préparer les données des catégories pour le template
    categories_data = []
    for categorie in categories_trouvees:
        # Compter les épreuves publiées de cette catégorie
        nb_epreuves = categorie.epreuves.filter(statut='publie').count()
        # Calculer le prix total du pack
        prix_pack = sum(e.prix for e in categorie.epreuves.filter(statut='publie'))
        
        categories_data.append({
            'id': categorie.id,
            'nom': categorie.nom,
            'slug': categorie.slug,
            'rubrique_nom': categorie.rubrique.nom,
            'rubrique_slug': categorie.rubrique.slug,
            'a_des_series': categorie.a_des_series,
            'nb_epreuves': nb_epreuves,
            'prix_pack': prix_pack,
        })
    
    context = {
        'query': query,
        'categories_data': categories_data,
        'epreuves_trouvees': epreuves_trouvees,
        'total_categories': len(categories_data),
        'total_epreuves': epreuves_trouvees.count(),
    }
    return render(request, 'website/epreuves/recherche.html', context)
# ========== GESTION DES SÉRIES ==========

@staff_member_required
def admin_serie_ajouter(request):
    """Ajouter une série (catégorie d'épreuve)"""
    if request.method == 'POST':
        categorie_id = request.POST.get('categorie')
        nom = request.POST.get('nom')
        code = request.POST.get('code', '')
        ordre = request.POST.get('ordre', 0)
        
        try:
            # Récupérer la catégorie parente
            categorie = CategorieEpreuve.objects.get(id=categorie_id)
            messages.success(request, f"Série '{nom}' ajoutée avec succès")
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
        
        return redirect('admin_epreuves_dashboard')
    
    categories = CategorieEpreuve.objects.filter(actif=True)
    return render(request, 'website/super_admin/epreuves/serie_ajouter.html', {
        'categories': categories
    })


@staff_member_required
def admin_serie_modifier(request, id):
    """Modifier une série"""
    if request.method == 'POST':
        messages.success(request, "Série modifiée avec succès")
        return redirect('admin_epreuves_dashboard')
    
    return redirect('admin_epreuves_dashboard')


@staff_member_required
def admin_serie_supprimer(request, id):
    """Supprimer une série"""
    if request.method == 'POST':
        messages.success(request, "Série supprimée avec succès")
        return redirect('admin_epreuves_dashboard')
    
    return redirect('admin_epreuves_dashboard')


# ========== PANIER ÉPREUVES ==========

@login_required
def ajouter_au_panier(request):
    """Ajouter une épreuve ou une catégorie au panier"""
    if request.method == 'POST':
        panier, created = PanierEpreuve.objects.get_or_create(utilisateur=request.user)
        
        epreuve_id = request.POST.get('epreuve_id')
        categorie_id = request.POST.get('categorie_id')
        
        if epreuve_id:
            epreuve = get_object_or_404(Epreuve, id=epreuve_id)
            panier.epreuves.add(epreuve)
            messages.success(request, f"'{epreuve.titre}' ajouté au panier")
        
        elif categorie_id:
            categorie = get_object_or_404(CategorieEpreuve, id=categorie_id)
            panier.categories.add(categorie)
            messages.success(request, f"Pack '{categorie.nom}' ajouté au panier")
        
        return redirect(request.META.get('HTTP_REFERER', 'epreuves_accueil'))
    
    return redirect('epreuves_accueil')


@login_required
def voir_panier(request):
    """Afficher le panier"""
    panier, created = PanierEpreuve.objects.get_or_create(utilisateur=request.user)
    
    context = {
        'panier': panier,
        'total': panier.total,
    }
    return render(request, 'website/epreuves/panier.html', context)


def epreuves_panier(request):
    """Afficher le panier d'épreuves"""
    if not request.user.is_authenticated:
        return redirect('connexion')
    
    panier, created = PanierEpreuve.objects.get_or_create(utilisateur=request.user)
    context = {
        'panier': panier,
        'total': panier.total,
        'categories': CategorieEpreuve.objects.filter(actif=True),
    }
    return render(request, 'website/epreuves/panier.html', context)


@login_required
def ajouter_categorie_panier(request):
    """Ajouter une catégorie au panier (version DB)"""
    categorie_id = request.POST.get('categorie_id') or request.GET.get('categorie_id')
    
    if not categorie_id:
        messages.error(request, "Impossible d'ajouter : ID de catégorie manquant.")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'ID de catégorie manquant'})
        return redirect(request.META.get('HTTP_REFERER', 'epreuves_accueil'))

    try:
        categorie = get_object_or_404(CategorieEpreuve, id=categorie_id)
        
        # Utiliser le modèle PanierEpreuve au lieu de la session
        panier, created = PanierEpreuve.objects.get_or_create(utilisateur=request.user)
        
        # Vérifier si la catégorie est déjà dans le panier
        if panier.categories.filter(id=categorie.id).exists():
            message = f"Le pack '{categorie.nom}' est déjà dans votre panier."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': message})
            messages.info(request, message)
        else:
            panier.categories.add(categorie)
            message = f"Le pack '{categorie.nom}' a été ajouté au panier."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': message})
            messages.success(request, message)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': message, 'cart_count': panier.categories.count() + panier.epreuves.count()})
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': str(e)})
        messages.error(request, f"Erreur : {str(e)}")
    
    return redirect(request.META.get('HTTP_REFERER', 'epreuves_accueil'))


@login_required
def retirer_du_panier(request):
    if request.method == 'POST':
        panier = get_object_or_404(PanierEpreuve, utilisateur=request.user)
        
        epreuve_id = request.POST.get('epreuve_id')
        categorie_id = request.POST.get('categorie_id')
        
        if epreuve_id:
            epreuve = get_object_or_404(Epreuve, id=epreuve_id)
            panier.epreuves.remove(epreuve)
        elif categorie_id:
            categorie = get_object_or_404(CategorieEpreuve, id=categorie_id)
            panier.categories.remove(categorie)
        
        messages.success(request, "Article retiré du panier")
    return redirect('epreuves_panier')


@login_required
def vider_panier(request):
    if request.method == 'POST':
        panier = get_object_or_404(PanierEpreuve, utilisateur=request.user)
        panier.epreuves.clear()
        panier.categories.clear()
        messages.success(request, "Panier vidé")
    return redirect('epreuves_panier')


@login_required
def finaliser_achat(request):
    """Finaliser l'achat du panier"""
    panier = get_object_or_404(PanierEpreuve, utilisateur=request.user)
    
    if request.method == 'POST':
        type_paiement = request.POST.get('type_paiement')
        telephone = request.POST.get('telephone')
        
        # Générer une référence unique
        import uuid
        reference = str(uuid.uuid4())[:8].upper()
        
        # Créer l'achat
        achat = AchatEpreuve.objects.create(
            acheteur=request.user,
            prix_total=panier.total,
            reference_paiement=reference,
            type_paiement=type_paiement,
            telephone=telephone,
            statut='en_attente'
        )
        
        # Copier les épreuves et catégories
        achat.epreuves.set(panier.epreuves.all())
        achat.categories.set(panier.categories.all())
        
        # Vider le panier
        panier.epreuves.clear()
        panier.categories.clear()
        
        # Ici : appeler l'API de paiement (Orange Money / MTN)
        messages.success(request, f"Commande créée ! Référence : {reference}")
        
        return redirect('confirmation_achat', achat_id=achat.id)
    
    return redirect('epreuves_panier')


@login_required
def confirmation_achat(request, achat_id):
    """Page de confirmation après paiement"""
    achat = get_object_or_404(AchatEpreuve, id=achat_id, acheteur=request.user)
    
    # Si le statut est encore 'en_attente', on vérifie le paiement (simulation)
    if achat.statut == 'en_attente':
        achat.confirmer()
    
    context = {
        'achat': achat,
    }
    return render(request, 'website/epreuves/confirmation.html', context)


@login_required
def mes_epreuves(request):
    """Liste des épreuves achetées"""
    achats = AchatEpreuve.objects.filter(acheteur=request.user, statut='confirme')
    
    epreuves_achetees = []
    for achat in achats:
        for epreuve in achat.epreuves.all():
            epreuves_achetees.append({
                'epreuve': epreuve,
                'date_achat': achat.date_achat,
                'reference': achat.reference_paiement
            })
        for categorie in achat.categories.all():
            for epreuve in categorie.epreuves.filter(statut='publie'):
                epreuves_achetees.append({
                    'epreuve': epreuve,
                    'date_achat': achat.date_achat,
                    'reference': achat.reference_paiement
                })
    
    # Supprimer les doublons
    vues = set()
    epreuves_uniques = []
    for e in epreuves_achetees:
        if e['epreuve'].id not in vues:
            vues.add(e['epreuve'].id)
            epreuves_uniques.append(e)
    
    context = {
        'epreuves': epreuves_uniques,
    }
    return render(request, 'website/epreuves/mes_epreuves.html', context)

@login_required
def telecharger_epreuve(request, epreuve_id):
    """Télécharger une épreuve achetée"""
    from django.db import models
    
    epreuve = get_object_or_404(Epreuve, id=epreuve_id)
    
    # Vérifier si l'utilisateur a acheté cette épreuve
    a_achete = AchatEpreuve.objects.filter(
        acheteur=request.user,
        statut='confirme'
    ).filter(
        models.Q(epreuves=epreuve) | models.Q(categories__epreuves=epreuve)
    ).exists()
    
    if not a_achete:
        messages.error(request, "Vous n'avez pas acheté cette épreuve")
        return redirect('epreuves_accueil')
    
    # Incrémenter le compteur de téléchargement
    TelechargementEpreuve.objects.create(
        achat=None,
        epreuve=epreuve,
        ip_adresse=get_client_ip(request)
    )
    
    return redirect(epreuve.fichier_sujet.url if hasattr(epreuve, 'fichier_sujet') and epreuve.fichier_sujet else epreuve.fichier.url)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def api_panier_count(request):
    """Retourne le nombre d'articles dans le panier"""
    panier, created = PanierEpreuve.objects.get_or_create(utilisateur=request.user)
    count = panier.epreuves.count() + panier.categories.count()
    return JsonResponse({'count': count})


@login_required
def gerer_series_epreuves(request):
    """Voir et modifier la liste des séries disponibles"""
    if not request.user.is_superuser:
        messages.error(request, "Accès non autorisé")
        return redirect('dashboard')
    
    # Séries actuelles (depuis le modèle Epreuve)
    series_actuelles = [c[0] for c in Epreuve.SERIES_CHOICES if c[0]]
    
    if request.method == 'POST':
        messages.success(request, "Configuration des séries mise à jour")
        return redirect('admin_epreuves_dashboard')
    
    context = {
        'series_actuelles': series_actuelles,
        'toutes_series': Epreuve.SERIES_CHOICES,
    }
    return render(request, 'website/super_admin/epreuves/gerer_series.html', context)

@login_required
def ajouter_serie_epreuve(request):
    """Ajouter une nouvelle série"""
    if request.method == 'POST' and request.user.is_superuser:
        code = request.POST.get('code', '').upper()
        nom = request.POST.get('nom', '')
        if code and nom:
            messages.success(request, f"Série '{code} - {nom}' ajoutée")
        else:
            messages.error(request, "Code et nom requis")
    return redirect('admin_epreuves_dashboard')

@login_required
@role_required('super_admin')
def super_admin_configuration(request):
    """
    REMPLACE la fonction existante du même nom dans views.py.
    Vue de configuration centrale — sauvegarde TOUS les champs du modèle.
    Compatible avec le modèle ConfigurationPlateforme (document 9/12).
    """
    from .models import (
        ConfigurationPlateforme, DiapositiveHero, Temoignage,
        BannierePromo, Ecole, Formation, Epreuve, Utilisateur
    )

    if request.user.role != 'super_admin':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    config = ConfigurationPlateforme.get_config()

    if request.method == 'POST':

        # ── Champs texte simples ──────────────────────────────────
        champs_texte = [
            # Identité
            'nom_site', 'slogan_site',
            # Couleurs
            'couleur_principale', 'couleur_secondaire', 'couleur_accent',
            # Hero
            'hero_titre', 'hero_titre_accent', 'hero_description',
            'hero_bouton1_texte', 'hero_bouton1_lien',
            'hero_bouton2_texte', 'hero_bouton2_lien',
            'hero_video_url',
            # Stats labels
            'stat1_label', 'stat1_valeur_fixe',
            'stat2_label', 'stat2_valeur_fixe',
            'stat3_label', 'stat3_valeur_fixe',
            'stat4_label', 'stat4_valeur_fixe',
            # Titres sections
            'titre_section_formations', 'sous_titre_section_formations',
            'titre_section_epreuves',   'sous_titre_section_epreuves',
            'titre_section_ecoles',     'titre_section_temoignages',
            'titre_section_cta',        'sous_titre_section_cta',
            # Formations
            'formations_tri',
            # Footer
            'footer_texte', 'footer_email_contact', 'footer_telephone',
            'footer_adresse', 'footer_facebook', 'footer_twitter',
            'footer_linkedin', 'footer_youtube', 'footer_instagram',
            # Maintenance
            'message_maintenance',
        ]
        for champ in champs_texte:
            valeur = request.POST.get(champ, '').strip()
            if valeur or champ not in ['couleur_principale', 'couleur_secondaire', 'couleur_accent']:
                setattr(config, champ, valeur)

        # ── Champs entiers ────────────────────────────────────────
        champs_entiers = [
            'nb_formations_accueil', 'nb_epreuves_accueil',
            'nb_ecoles_accueil', 'auto_publication_delai_minutes',
        ]
        for champ in champs_entiers:
            try:
                valeur = int(request.POST.get(champ, getattr(config, champ)))
                setattr(config, champ, valeur)
            except (ValueError, TypeError):
                pass

        # ── Booléens (checkbox = présente → True, absente → False) ──
        champs_bool = [
            'hero_afficher_stats',
            'stat1_valeur_auto', 'stat2_valeur_auto',
            'stat3_valeur_auto', 'stat4_valeur_auto',
            'section_services_visible',
            'section_formations_visible',
            'section_epreuves_visible',
            'section_ecoles_visible',
            'section_audience_visible',
            'section_temoignages_visible',
            'section_comment_ca_marche_visible',
            'section_cta_visible',
            'section_newsletter_visible',
            'section_partenaires_visible',
            'afficher_formations_gratuites_badge',
            'afficher_prix_formations',
            'afficher_note_formations',
            'afficher_nb_ventes_formations',
            'auto_publication_active',
            'mode_maintenance',
        ]
        for champ in champs_bool:
            setattr(config, champ, champ in request.POST)

        # ── Fichiers images ───────────────────────────────────────
        for champ_fichier in ['logo', 'favicon', 'hero_image']:
            if champ_fichier in request.FILES and request.FILES[champ_fichier]:
                setattr(config, champ_fichier, request.FILES[champ_fichier])

        config.save()
        messages.success(
            request,
            '✅ Configuration enregistrée ! Les modifications sont visibles sur le site.'
        )
        return redirect('super_admin_configuration')

    # ── GET : préparer le contexte ────────────────────────────────
    stats = {
        'nb_ecoles':       Ecole.objects.filter(actif=True).count(),
        'nb_formations':   Formation.objects.filter(statut='publie').count(),
        'nb_epreuves':     Epreuve.objects.filter(statut='publie').count(),
        'nb_utilisateurs': Utilisateur.objects.count(),
    }

    context = {
        'config':        config,
        'slides':        DiapositiveHero.objects.order_by('ordre'),
        'temoignages':   Temoignage.objects.order_by('ordre'),
        'banniere_promo': BannierePromo.objects.filter(actif=True).first(),
        'stats':         stats,
    }
    return render(request, 'website/super_admin/configuration.html', context)

@login_required
@role_required('super_admin')
def export_transactions_csv(request):
    """Exporter les transactions en CSV"""
    import csv
    from django.http import HttpResponse
    from .models import TransactionLog
    
    transactions = TransactionLog.objects.all().select_related('utilisateur')
    
    # Appliquer les mêmes filtres que dans logs_transactions
    statut = request.GET.get('statut')
    type_transaction = request.GET.get('type_transaction')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    utilisateur_id = request.GET.get('utilisateur_id')
    
    if statut and statut != '':
        transactions = transactions.filter(statut=statut)
    
    if type_transaction and type_transaction != '':
        transactions = transactions.filter(type_transaction=type_transaction)
    
    if utilisateur_id and utilisateur_id != '':
        transactions = transactions.filter(utilisateur_id=utilisateur_id)
    
    if date_debut:
        try:
            transactions = transactions.filter(date_transaction__gte=date_debut)
        except:
            pass
    
    if date_fin:
        try:
            transactions = transactions.filter(date_transaction__lte=date_fin + ' 23:59:59')
        except:
            pass
    
    # Créer la réponse CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="transactions_{}.csv"'.format(
        timezone.now().strftime('%Y%m%d_%H%M%S')
    )
    
    # Écrire l'en-tête avec BOM pour UTF-8
    response.write('\ufeff')
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Utilisateur', 'Email', 'Type', 'Montant (FCFA)', 
        'Statut', 'Moyen paiement', 'Téléphone', 'Date', 'Référence', 'Détails'
    ])
    
    for t in transactions:
        writer.writerow([
            t.id,
            t.utilisateur.username,
            t.utilisateur.email,
            t.get_type_transaction_display(),
            t.montant,
            t.get_statut_display(),
            t.get_moyen_paiement_display() if t.moyen_paiement else '',
            t.telephone or '',
            t.date_transaction.strftime('%d/%m/%Y %H:%M:%S'),
            t.reference,
            t.details or '',
        ])
    
    return response

# ==================== ABONNEMENT ET PAIEMENT ====================
@login_required
def initier_paiement(request):
    """Initier un paiement (simulation avec Orange Money/MTN Money)"""
    if request.method != 'POST':
        return redirect('choix_abonnement')
    
    type_abonnement = request.POST.get('type_abonnement')
    moyen_paiement = request.POST.get('moyen_paiement')
    telephone = request.POST.get('telephone', '').strip()
    
    if type_abonnement not in ['mensuel', 'trimestriel']:
        messages.error(request, "Type d'abonnement invalide.")
        return redirect('choix_abonnement')
    
    montant = 500 if type_abonnement == 'mensuel' else 1500
    
    # Générer une référence unique
    reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"
    
    # Créer la transaction
    transaction = TransactionLog.objects.create(
        utilisateur=request.user,
        type_transaction='abonnement',
        montant=montant,
        reference=reference,
        statut='en_attente',
        moyen_paiement=moyen_paiement,
        telephone=telephone,
        details=f"Abonnement {type_abonnement} - {montant} FCFA"
    )
    
    # SIMULATION : Ici vous intégrerez l'API réelle Orange Money/MTN Money
    # Pour l'instant, simulation avec confirmation automatique
    context = {
        'transaction': transaction,
        'telephone': telephone,
        'montant': montant,
        'type_abonnement': type_abonnement,
        'reference': reference,
    }
    
    return render(request, 'website/paiement/simulation.html', context)

@login_required
def confirmer_paiement(request, reference):
    from .models import AbonnementUtilisateur

    transaction = get_object_or_404(TransactionLog, reference=reference, utilisateur=request.user)

    if transaction.statut != 'en_attente':
        messages.warning(request, "Cette transaction a déjà été traitée.")
        return redirect('dashboard')

    transaction.statut = 'reussi'
    transaction.date_confirmation = timezone.now()
    transaction.save()

    type_abonnement = 'mensuel' if transaction.montant == 500 else 'trimestriel'
    duree_jours = 30 if type_abonnement == 'mensuel' else 90

    abonnement, _ = AbonnementUtilisateur.objects.get_or_create(utilisateur=request.user)
    abonnement.type_abonnement = type_abonnement
    abonnement.statut = 'actif'
    abonnement.date_debut = timezone.now()
    abonnement.date_fin = timezone.now() + timezone.timedelta(days=duree_jours)
    abonnement.save()

    messages.success(request, f"Paiement confirmé ! Abonnement actif jusqu'au {abonnement.date_fin.strftime('%d/%m/%Y')}.")
    return redirect('dashboard')


@login_required
def paiement_callback(request):
    """Webhook/callback pour confirmer les paiements (API externe)"""
    # À implémenter avec les vraies API
    pass


@login_required
def verifier_abonnement(request):
    """API pour vérifier le statut de l'abonnement (AJAX)"""
    try:
        abonnement = AbonnementUtilisateur.objects.get(utilisateur=request.user)
        data = {
            'est_actif': abonnement.est_actif(),
            'statut': abonnement.statut,
            'jours_restants': abonnement.jours_restants(),
            'date_fin': abonnement.date_fin.strftime('%d/%m/%Y') if abonnement.date_fin else None,
        }
    except Abonnement.DoesNotExist:
        data = {
            'est_actif': False,
            'statut': 'aucun',
            'jours_restants': 0,
            'date_fin': None,
        }
    return JsonResponse(data)
 
 
# ==================== LOGS DES TRANSACTIONS (SUPER ADMIN) ====================

@login_required
@role_required('super_admin')
def logs_transactions(request):
    """Liste des transactions avec filtres"""
    
    transactions = TransactionLog.objects.all().select_related('utilisateur')
    
    # Filtres
    statut = request.GET.get('statut')
    type_transaction = request.GET.get('type_transaction')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    utilisateur_id = request.GET.get('utilisateur_id')
    
    if statut and statut != '':
        transactions = transactions.filter(statut=statut)
    
    if type_transaction and type_transaction != '':
        transactions = transactions.filter(type_transaction=type_transaction)
    
    if utilisateur_id and utilisateur_id != '':
        transactions = transactions.filter(utilisateur_id=utilisateur_id)
    
    if date_debut:
        try:
            transactions = transactions.filter(date_transaction__gte=date_debut)
        except:
            pass
    
    if date_fin:
        try:
            transactions = transactions.filter(date_transaction__lte=date_fin + ' 23:59:59')
        except:
            pass
    
    # Pagination
    paginator = Paginator(transactions, 50)
    page = request.GET.get('page', 1)
    transactions_page = paginator.get_page(page)
    
    # Stats
    stats = {
        'total_encaisses': transactions.filter(statut='reussi').aggregate(total=models.Sum('montant'))['total'] or 0,
        'total_transactions': transactions.count(),
        'transactions_reussies': transactions.filter(statut='reussi').count(),
        'transactions_echouees': transactions.filter(statut='echoue').count(),
    }
    
    # Liste des utilisateurs pour le filtre
    utilisateurs = Utilisateur.objects.all().order_by('username')
    
    context = {
        'transactions': transactions_page,
        'stats': stats,
        'utilisateurs': utilisateurs,
        'filtres': {
            'statut': statut,
            'type_transaction': type_transaction,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'utilisateur_id': utilisateur_id,
        }
    }
    return render(request, 'website/super_admin/logs_transactions.html', context)


@login_required
@role_required('super_admin')
def supprimer_transaction(request, transaction_id):
    """Supprimer un log de transaction"""
    transaction = get_object_or_404(TransactionLog, id=transaction_id)
    transaction.delete()
    messages.success(request, "Transaction supprimée avec succès.")
    return redirect('logs_transactions')

@login_required
@role_required('super_admin')
def reinitialiser_mot_de_passe(request, user_id):
    """Envoyer un email de réinitialisation de mot de passe"""
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    
    # Générer un token (utiliser django.contrib.auth.tokens)
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    
    token = default_token_generator.make_token(utilisateur)
    uid = urlsafe_base64_encode(force_bytes(utilisateur.pk))
    reset_url = request.build_absolute_uri(f'/reinitialisation/{uid}/{token}/')
    
    # Envoyer l'email
    subject = "Réinitialisation de votre mot de passe"
    message = render_to_string('website/emails/reinitialisation_mdp.html', {
        'utilisateur': utilisateur,
        'reset_url': reset_url,
    })
    
    try:
        send_mail(subject, message, 'noreply@academia.net', [utilisateur.email], html_message=message)
        messages.success(request, f"Email de réinitialisation envoyé à {utilisateur.email}")
    except Exception as e:
        messages.error(request, f"Erreur lors de l'envoi de l'email: {str(e)}")
    
    return redirect('super_admin_utilisateurs')

@login_required
def choix_abonnement(request):
    from .models import AbonnementUtilisateur
    from django.utils import timezone

    if request.user.role == 'super_admin':
        return redirect('dashboard')

    if getattr(request.user, 'paiement_desactive', False):
        return redirect('dashboard')

    # Chercher un abonnement EXISTANT sans en créer
    abonnement = AbonnementUtilisateur.objects.filter(
        utilisateur=request.user
    ).first()

    # Si abonnement payant encore actif → pas besoin d'être ici
    if abonnement and abonnement.statut == 'actif':
        if abonnement.date_fin and abonnement.date_fin > timezone.now():
            messages.info(request, "Vous avez déjà un abonnement actif.")
            return redirect('dashboard')

    # Calculer jours d'essai restants (0 si pas encore d'abonnement)
    jours_essai = 0
    essai_expire = False
    essai_en_cours = False

    if abonnement and abonnement.statut == 'essai' and abonnement.date_fin_essai:
        delta = abonnement.date_fin_essai - timezone.now()
        jours_essai = max(delta.days, 0)
        essai_expire = (jours_essai == 0)
        essai_en_cours = (jours_essai > 0)

    # Nouvel inscrit : pas encore d'abonnement du tout
    premier_passage = (abonnement is None)

    context = {
        'abonnement': abonnement,
        'jours_essai': jours_essai,
        'essai_expire': essai_expire,
        'essai_en_cours': essai_en_cours,
        'premier_passage': premier_passage,
        'prix_mensuel': 500,
        'prix_trimestriel': 1500,
    }
    return render(request, 'website/paiement/choix_abonnement.html', context)
 

@login_required
def demarrer_essai(request):
    from .models import AbonnementUtilisateur
    from django.utils import timezone

    if request.method != 'POST':
        return redirect('choix_abonnement')

    # Bloquer si déjà un essai ou abonnement existant
    existant = AbonnementUtilisateur.objects.filter(
        utilisateur=request.user
    ).first()

    if existant:
        # Déjà utilisé un essai ou a un abonnement → on refuse
        if existant.statut in ('actif',):
            messages.warning(request, "Vous avez déjà un abonnement actif.")
            return redirect('dashboard')
        if existant.statut == 'essai':
            messages.warning(request, "Vous avez déjà utilisé votre essai gratuit.")
            return redirect('choix_abonnement')

    # Première fois : créer l'essai
    AbonnementUtilisateur.objects.create(
        utilisateur=request.user,
        statut='essai',
        date_fin_essai=timezone.now() + timezone.timedelta(days=15),
        paiement_oblige=True
    )
    messages.success(request, "Votre essai gratuit de 15 jours a démarré !")
    return redirect('dashboard')

@login_required
def abandonner_inscription(request):
    """
    L'utilisateur clique sur 'Quitter' depuis choix_abonnement.
    Son compte est supprimé car il n'a pas finalisé son inscription.
    """
    from .models import AbonnementUtilisateur

    user = request.user

    # Seulement si l'utilisateur n'a AUCUN abonnement
    # (il n'a pas encore fait de choix)
    a_abonnement = AbonnementUtilisateur.objects.filter(
        utilisateur=user
    ).exists()

    if not a_abonnement:
        logout(request)
        user.delete()
        messages.info(request, "Votre compte a été supprimé. Vous pouvez vous réinscrire à tout moment.")
        return redirect('accueil')

    # S'il a déjà un abonnement (essai ou payant), on déconnecte juste
    logout(request)
    return redirect('accueil')

# ─────────────────────────────────────────────
# CRUD Diapositives Hero
# ─────────────────────────────────────────────
@login_required
@role_required('super_admin')
def super_admin_slide_create(request):
    from .models import DiapositiveHero
    if request.method == 'POST':
        slide = DiapositiveHero()
        slide.titre = request.POST.get('titre', '')
        slide.sous_titre = request.POST.get('sous_titre', '')
        slide.description = request.POST.get('description', '')
        slide.couleur_fond = request.POST.get('couleur_fond', '#1e3a8a')
        slide.bouton_texte = request.POST.get('bouton_texte', '')
        slide.bouton_lien = request.POST.get('bouton_lien', '')
        slide.bouton2_texte = request.POST.get('bouton2_texte', '')
        slide.bouton2_lien = request.POST.get('bouton2_lien', '')
        slide.ordre = int(request.POST.get('ordre', 0))
        slide.actif = 'actif' in request.POST
        if 'image' in request.FILES:
            slide.image = request.FILES['image']
        slide.save()
        messages.success(request, 'Diapositive créée.')
        return redirect('super_admin_configuration')
 
    return render(request, 'website/super_admin/slide_form.html', {'action': 'Créer'})
 
 
@login_required
@role_required('super_admin')
def super_admin_slide_edit(request, slide_id):
    from .models import DiapositiveHero
    slide = get_object_or_404(DiapositiveHero, id=slide_id)
    if request.method == 'POST':
        slide.titre = request.POST.get('titre', '')
        slide.sous_titre = request.POST.get('sous_titre', '')
        slide.description = request.POST.get('description', '')
        slide.couleur_fond = request.POST.get('couleur_fond', '#1e3a8a')
        slide.bouton_texte = request.POST.get('bouton_texte', '')
        slide.bouton_lien = request.POST.get('bouton_lien', '')
        slide.bouton2_texte = request.POST.get('bouton2_texte', '')
        slide.bouton2_lien = request.POST.get('bouton2_lien', '')
        slide.ordre = int(request.POST.get('ordre', 0))
        slide.actif = 'actif' in request.POST
        if 'image' in request.FILES:
            slide.image = request.FILES['image']
        slide.save()
        messages.success(request, 'Diapositive mise à jour.')
        return redirect('super_admin_configuration')
 
    return render(request, 'website/super_admin/slide_form.html', {'slide': slide, 'action': 'Modifier'})
 
 
@login_required
@role_required('super_admin')
def super_admin_slide_delete(request, slide_id):
    from .models import DiapositiveHero
    slide = get_object_or_404(DiapositiveHero, id=slide_id)
    slide.delete()
    messages.success(request, 'Diapositive supprimée.')
    return redirect('super_admin_configuration')
 
# ─────────────────────────────────────────────
# CRUD Témoignages
# ─────────────────────────────────────────────
@login_required
@role_required('super_admin')
def super_admin_temoignage_create(request):
    from .models import Temoignage
    if request.method == 'POST':
        t = Temoignage()
        t.nom = request.POST.get('nom', '')
        t.role = request.POST.get('role', '')
        t.texte = request.POST.get('texte', '')
        t.note = int(request.POST.get('note', 5))
        t.ordre = int(request.POST.get('ordre', 0))
        t.actif = 'actif' in request.POST
        if 'avatar' in request.FILES:
            t.avatar = request.FILES['avatar']
        t.save()
        messages.success(request, 'Témoignage ajouté.')
        return redirect('super_admin_configuration')
    return render(request, 'website/super_admin/temoignage_form.html', {'action': 'Ajouter'})
 
 
@login_required
@role_required('super_admin')
def super_admin_temoignage_edit(request, t_id):
    from .models import Temoignage
    t = get_object_or_404(Temoignage, id=t_id)
    if request.method == 'POST':
        t.nom = request.POST.get('nom', '')
        t.role = request.POST.get('role', '')
        t.texte = request.POST.get('texte', '')
        t.note = int(request.POST.get('note', 5))
        t.ordre = int(request.POST.get('ordre', 0))
        t.actif = 'actif' in request.POST
        if 'avatar' in request.FILES:
            t.avatar = request.FILES['avatar']
        t.save()
        messages.success(request, 'Témoignage modifié.')
        return redirect('super_admin_configuration')
    return render(request, 'website/super_admin/temoignage_form.html', {'temoignage': t, 'action': 'Modifier'})
 
 
@login_required
@role_required('super_admin')
def super_admin_temoignage_delete(request, t_id):
    from .models import Temoignage
    get_object_or_404(Temoignage, id=t_id).delete()
    messages.success(request, 'Témoignage supprimé.')
    return redirect('super_admin_configuration')
# ─────────────────────────────────────────────
# CRUD Bannière promo
# ─────────────────────────────────────────────
@login_required
@role_required('super_admin')
def super_admin_banniere_create(request):
    from .models import BannierePromo
    if request.method == 'POST':
        b = BannierePromo()
        b.texte = request.POST.get('texte', '')
        b.lien = request.POST.get('lien', '')
        b.couleur_fond = request.POST.get('couleur_fond', '#f59e0b')
        b.couleur_texte = request.POST.get('couleur_texte', '#1e3a8a')
        b.actif = 'actif' in request.POST
        b.save()
        # Désactiver les autres si celle-ci est active
        if b.actif:
            BannierePromo.objects.exclude(id=b.id).update(actif=False)
        messages.success(request, 'Bannière créée.')
        return redirect('super_admin_configuration')
    return render(request, 'website/super_admin/banniere_form.html', {'action': 'Créer'})
 
@login_required
@role_required('super_admin')
def super_admin_banniere_edit(request, b_id):
    from .models import BannierePromo
    b = get_object_or_404(BannierePromo, id=b_id)
    if request.method == 'POST':
        b.texte = request.POST.get('texte', '')
        b.lien = request.POST.get('lien', '')
        b.couleur_fond = request.POST.get('couleur_fond', '#f59e0b')
        b.couleur_texte = request.POST.get('couleur_texte', '#1e3a8a')
        b.actif = 'actif' in request.POST
        b.save()
        if b.actif:
            BannierePromo.objects.exclude(id=b.id).update(actif=False)
        messages.success(request, 'Bannière modifiée.')
        return redirect('super_admin_configuration')
    return render(request, 'website/super_admin/banniere_form.html', {'banniere': b, 'action': 'Modifier'})


# ─────────────────────────────────────────────────────────────────────
# HELPER — OPTIONS POUR LES FILTRES (réutilisable)
# ─────────────────────────────────────────────────────────────────────
PRIX_OPTIONS = [
    ('',        'Tous les prix'),
    ('gratuit', 'Gratuit'),
    ('range',   'Fourchette de prix'),
    ('payant',  'Payant uniquement'),
]

NIVEAUX = [
    ('debutant',      'Débutant'),
    ('intermediaire', 'Intermédiaire'),
    ('avance',        'Avancé'),
    ('expert',        'Expert'),
    ('tous_niveaux',  'Tous niveaux'),
]

LANGUES = [
    ('fr', 'Français'),
    ('en', 'Anglais'),
    ('ar', 'Arabe'),
    ('es', 'Espagnol'),
    ('pt', 'Portugais'),
]


def _build_filtres_tags(request, tous_centres):
    """Construit la liste des tags de filtres actifs pour l'affichage."""
    tags = []
    base_url = request.path

    def url_sans(param, val=None):
        params = request.GET.copy()
        if val:
            items = params.getlist(param)
            if val in items:
                items.remove(val)
            params.setlist(param, items)
        else:
            params.pop(param, None)
        params.pop('page', None)
        return f"{base_url}?{params.urlencode()}" if params else base_url

    # Recherche
    q = request.GET.get('q', '')
    if q:
        tags.append({'label': f'Recherche : "{q}"', 'url_remove': url_sans('q')})

    # Centres
    for slug in request.GET.getlist('centre'):
        centre = next((c for c in tous_centres if c.slug == slug), None)
        if centre:
            tags.append({'label': centre.nom, 'url_remove': url_sans('centre', slug)})

    # Prix
    prix_type = request.GET.get('prix_type', '')
    if prix_type == 'gratuit':
        tags.append({'label': 'Gratuit', 'url_remove': url_sans('prix_type')})
    elif prix_type == 'range':
        pmin = request.GET.get('prix_min', '0')
        pmax = request.GET.get('prix_max', '100000')
        tags.append({'label': f'{pmin}–{pmax} FCFA', 'url_remove': url_sans('prix_type')})

    # Niveaux
    for val in request.GET.getlist('niveau'):
        label = dict(NIVEAUX).get(val, val)
        tags.append({'label': label, 'url_remove': url_sans('niveau', val)})

    # Langues
    for val in request.GET.getlist('langue'):
        label = dict(LANGUES).get(val, val)
        tags.append({'label': label, 'url_remove': url_sans('langue', val)})

    # Note min
    note_min = request.GET.get('note_min', '')
    if note_min:
        tags.append({'label': f'Note ≥ {note_min}★', 'url_remove': url_sans('note_min')})

    # Certifiée
    if request.GET.get('certifiee'):
        tags.append({'label': 'Certifiée', 'url_remove': url_sans('certifiee')})

    return tags

@login_required
def formation_modifier(request, slug):
    """Modifier une formation existante (propriétaire uniquement)."""
    from .models import Formation, CentreInteret

    formation = get_object_or_404(Formation, slug=slug)
    if formation.createur != request.user and not request.user.role == 'super_admin':
        messages.error(request, "Vous n'êtes pas autorisé à modifier cette formation.")
        return redirect('mes_formations')

    if request.method == 'POST':
        formation.titre              = request.POST.get('titre', formation.titre).strip()
        formation.description_courte = request.POST.get('description_courte', '').strip()
        formation.description_longue = request.POST.get('description_longue', '').strip()
        formation.resume             = request.POST.get('resume', '').strip()
        formation.objectifs          = request.POST.get('objectifs', '').strip()
        formation.prerequis          = request.POST.get('prerequis', '').strip()
        formation.public_cible       = request.POST.get('public_cible', '').strip()
        formation.niveau             = request.POST.get('niveau', formation.niveau)
        formation.langue             = request.POST.get('langue', formation.langue)
        formation.duree              = request.POST.get('duree', '').strip()

        try:
            formation.prix = float(request.POST.get('prix', 0))
        except (ValueError, TypeError):
            pass

        try:
            po = request.POST.get('prix_original', '')
            formation.prix_original = float(po) if po else None
        except (ValueError, TypeError):
            pass

        if 'image_cover' in request.FILES:
            formation.image_cover = request.FILES['image_cover']
        if 'video_presentation' in request.FILES:
            formation.video_presentation = request.FILES['video_presentation']

        # Repassage en attente si publiée (re-validation)
        if formation.statut == 'publie':
            formation.statut = 'en_attente'
            messages.info(request, "Votre formation repassera en validation après modification.")

        formation.save()

        # Mettre à jour les centres d'intérêt
        formation.centres_interet.clear()
        for nom in request.POST.getlist('centres_interet'):
            nom = nom.strip()
            if nom:
                centre, _ = CentreInteret.objects.get_or_create(
                    nom__iexact=nom, defaults={'nom': nom, 'slug': slugify(nom)}
                )
                formation.centres_interet.add(centre)

        messages.success(request, "Formation modifiée avec succès.")
        return redirect('formation_ajouter_fichiers', slug=formation.slug)

    context = {
        'formation': formation,
        'niveaux':   NIVEAUX,
        'langues':   LANGUES,
        'centres_selectionnes': list(formation.centres_interet.values_list('nom', flat=True)),
    }
    return render(request, 'website/formations/modifier.html', context)

@login_required
def formation_wishlist_toggle(request, formation_id):
    from .models import Formation, WishlistFormation

    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    formation = get_object_or_404(Formation, id=formation_id)
    obj, created = WishlistFormation.objects.get_or_create(
        utilisateur=request.user, formation=formation
    )
    if not created:
        obj.delete()
        return JsonResponse({'added': False, 'message': 'Retiré des favoris'})
    return JsonResponse({'added': True, 'message': 'Ajouté aux favoris'})


def formation_verifier_coupon(request):
    from .models import Coupon

    code = request.GET.get('code', '').strip().upper()
    if not code:
        return JsonResponse({'valide': False, 'message': 'Code vide'})

    coupon = Coupon.objects.filter(code=code, actif=True).first()
    if not coupon:
        return JsonResponse({'valide': False, 'message': 'Code introuvable'})

    if not coupon.est_valide():
        return JsonResponse({'valide': False, 'message': 'Code expiré ou limite atteinte'})

    if coupon.reduction_pourcentage:
        desc = f"-{coupon.reduction_pourcentage}% sur le prix"
    else:
        desc = f"-{coupon.reduction_fixe} FCFA"

    return JsonResponse({'valide': True, 'description': desc})


@login_required
def formation_marquer_fichier_vu(request, fichier_id):
    from .models import FichierFormation, AchatFormation, ProgressionFormation, CertificatFormation

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    fichier = get_object_or_404(FichierFormation, id=fichier_id)

    # Vérifier l'accès
    a_acces = AchatFormation.objects.filter(
        formation=fichier.formation, acheteur=request.user, statut='confirme'
    ).exists() or fichier.formation.prix == 0

    if not a_acces:
        return JsonResponse({'error': 'Accès refusé'}, status=403)

    progression, _ = ProgressionFormation.objects.get_or_create(
        apprenant=request.user, formation=fichier.formation
    )
    progression.fichiers_vus.add(fichier)

    pct = progression.pourcentage

    # Délivrer certificat si 100%
    certificat = None
    if pct == 100 and fichier.formation.certifiee:
        cert, created = CertificatFormation.objects.get_or_create(
            apprenant=request.user, formation=fichier.formation
        )
        if created:
            certificat = cert.code_unique

        if not progression.terminee:
            progression.terminee = True
            progression.date_fin = timezone.now()
            progression.save(update_fields=['terminee', 'date_fin'])

    return JsonResponse({
        'pourcentage': pct,
        'certificat':  certificat,
    })

def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

# =====================================================================
# website/views.py — VUES MESSAGERIE & FORUMS (complet)
# =====================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.core.paginator import Paginator

def _format_time(dt, now):
    """Formater la date d'un message de façon lisible."""
    diff = now - dt
    if diff.days >= 7:
        return dt.strftime('%d/%m/%Y')
    elif diff.days >= 1:
        return dt.strftime('%a %d/%m')
    elif diff.seconds >= 3600:
        return dt.strftime('%H:%M')
    elif diff.seconds >= 60:
        return f"{diff.seconds // 60} min"
    else:
        return "À l'instant"

@login_required
def forum_detail(request, forum_id):
    """
    Page de chat d'un forum - style WhatsApp
    - Affiche le sujet du jour en haut
    - Affiche les messages (paginés)
    - Formulaire pour poster
    """
    from .models import Forum, MessageForum, UtilisateurBloqueForum, ConfigurationMessagerie
    from django.core.paginator import Paginator
    
    config = ConfigurationMessagerie.get_config()
    
    # Vérifier si les forums sont actifs
    if not config.forums_actifs:
        return render(request, 'website/forum/desactive.html', {'config': config})
    
    # Récupérer le forum
    forum = get_object_or_404(Forum, id=forum_id, actif=True)
    
    # Vérifier l'accès
    if not forum.peut_voir(request.user):
        messages.error(request, "Vous n'avez pas accès à ce forum.")
        return redirect('forum_liste')
    
    # Vérifier si l'utilisateur est bloqué
    est_bloque = UtilisateurBloqueForum.objects.filter(
        utilisateur=request.user, forum=forum, date_deblocage__isnull=True
    ).exists()
    
    # Récupérer le sujet du jour
    sujet_jour = None
    if config.sujet_jour_actif:
        sujet_jour = forum.get_sujet_jour()
    
    # Récupérer les messages (paginés)
    messages_qs = forum.messages.filter(est_cache=False).select_related('auteur').order_by('date_creation')
    paginator = Paginator(messages_qs, config.forum_messages_par_page)
    messages_page = paginator.get_page(request.GET.get('page', 1))
    
    # Inverser l'ordre pour afficher du plus ancien au plus récent
    messages_list = list(reversed(messages_page))
    
    # Dernier message ID pour le polling
    dernier_message_id = messages_qs.last().id if messages_qs.last() else 0
    
    context = {
        'forum': forum,
        'sujet_jour': sujet_jour,
        'forum_messages': messages_list,  # ← Renommer pour éviter conflit avec Django messages
        'messages_page': messages_page,
        'est_bloque': est_bloque,
        'peut_poster': forum.peut_poster(request.user) and not est_bloque,
        'dernier_message_id': dernier_message_id,
        'config': config,
    }
    return render(request, 'website/forum/detail.html', context)
    
@login_required
def forum_signaler(request, type_contenu, contenu_id):
    """Signaler un message de forum."""
    from .models import MessageForum, SignalementForum
    
    if request.method == 'POST':
        kwargs = {
            'signaleur': request.user, 
            'motif': request.POST.get('motif', 'autre'), 
            'description': request.POST.get('description', '')
        }
        
        # On ne signale plus que des messages (plus de sujets)
        if type_contenu == 'message':
            kwargs['message'] = get_object_or_404(MessageForum, id=contenu_id)
        else:
            # Si quelqu'un essaie de signaler un sujet (ancien système)
            messages.warning(request, "Le signalement des sujets n'est plus disponible. Veuillez signaler le message directement.")
            return redirect(request.META.get('HTTP_REFERER', 'forum_liste'))
        
        # Vérifier si déjà signalé
        existe = SignalementForum.objects.filter(
            signaleur=request.user, 
            message=kwargs['message']
        ).exists()
        
        if not existe:
            SignalementForum.objects.create(**kwargs)
            messages.success(request, "Signalement envoyé. Merci !")
        else:
            messages.warning(request, "Vous avez déjà signalé ce message.")
    
    return redirect(request.META.get('HTTP_REFERER', 'forum_liste'))

@login_required
@role_required('super_admin')
def super_admin_forums_parametres(request):
    """Paramètres des forums (indépendants de la messagerie)"""
    from .models import ParametresMessagerie
    from .forms import ForumParametresForm
    
    config = ParametresMessagerie.get_config()
    
    if request.method == 'POST':
        form = ForumParametresForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Paramètres des forums enregistrés.")
            return redirect('super_admin_forums_parametres')
    else:
        form = ForumParametresForm(instance=config)
    
    return render(request, 'website/super_admin/forums_parametres.html', {
        'form': form,
        'config': config
    })
    
# ── Configuration messagerie (super admin) ─────────────────────────

@login_required
def configurer_messagerie(request):
    """Configuration messagerie + forums pour le super admin."""
    from .models import ConfigurationMessagerie

    if request.user.role != 'super_admin':
        return redirect('accueil')

    config = ConfigurationMessagerie.get_config()

    if request.method == 'POST':
        # Polling
        for champ in ['intervalle_polling', 'max_messages_par_requete', 'rate_limit_secondes',
                       'min_intervalle_polling', 'max_intervalle_polling',
                       'supprimer_messages_apres_jours', 'supprimer_conversations_vides_apres_jours',
                       'forum_longueur_min_message', 'forum_longueur_max_message',
                       'forum_max_sujets_par_jour', 'forum_max_messages_par_jour']:
            try:
                setattr(config, champ, int(request.POST.get(champ, getattr(config, champ))))
            except (ValueError, TypeError):
                pass

        for champ in ['polling_actif', 'pause_polling_onglet_inactif', 'pause_polling_apres_heure',
                       'adaptation_auto_intervalle', 'forums_actifs', 'forum_plateforme_actif',
                       'forum_ecole_actif', 'forum_specialite_actif', 'forum_moderation_auto']:
            setattr(config, champ, champ in request.POST)

        config.message_polling_desactive = request.POST.get('message_polling_desactive', config.message_polling_desactive)

        h_debut = request.POST.get('heure_debut_pause')
        h_fin   = request.POST.get('heure_fin_pause')
        if h_debut:
            config.heure_debut_pause = h_debut
        if h_fin:
            config.heure_fin_pause = h_fin

        config.save()
        messages.success(request, "Configuration enregistrée.")
        return redirect('configurer_messagerie')

    return render(request, 'website/super_admin/parametres_messagerie.html', {'config': config})


# ── Helpers ────────────────────────────────────────────────────────

def _get_messagerie_config():
    from .models import ConfigurationMessagerie
    return ConfigurationMessagerie.get_config()

def _count_messages_forum(forum):
    from .models import MessageForum
    return MessageForum.objects.filter(forum=forum, est_cache=False).count()

def _get_dernier_message_forum(forum):
    return MessageForum.objects.filter(
        forum=forum, est_cache=False
    ).select_related('auteur').order_by('-date_creation').first()


@login_required
@role_required('super_admin')
def super_admin_parametres(request):
    """Page centrale des paramètres du site"""
    return render(request, 'website/super_admin/parametres_site.html')


# ==================== FORUM SIMPLIFIÉ ====================
@login_required
def forum_envoyer_message(request, forum_id):
    """
    Envoyer un message dans le forum (AJAX)
    """
    from .models import Forum, MessageForum, UtilisateurBloqueForum, ConfigurationMessagerie
    from django.views.decorators.csrf import csrf_exempt
    from django.utils import timezone
    import json
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    config = ConfigurationMessagerie.get_config()
    
    # Récupérer le forum
    forum = get_object_or_404(Forum, id=forum_id, actif=True)
    
    # Vérifier les permissions
    if not forum.peut_poster(request.user):
        return JsonResponse({'error': 'Vous ne pouvez pas poster dans ce forum'}, status=403)
    
    # Vérifier si bloqué
    if UtilisateurBloqueForum.objects.filter(utilisateur=request.user, forum=forum, date_deblocage__isnull=True).exists():
        return JsonResponse({'error': 'Vous êtes bloqué de ce forum'}, status=403)
    
    # Récupérer le contenu
    try:
        data = json.loads(request.body)
        contenu = data.get('contenu', '').strip()
    except:
        contenu = request.POST.get('contenu', '').strip()
    
    # Validation avec valeurs par défaut sécurisées
    min_length = getattr(config, 'forum_longueur_min_message', 1)
    max_length = getattr(config, 'forum_longueur_max_message', 2000)
    max_par_jour = getattr(config, 'forum_max_messages_par_jour', 100)
    
    if not contenu:
        return JsonResponse({'error': 'Le message ne peut pas être vide'}, status=400)
    
    if len(contenu) < min_length:
        return JsonResponse({'error': f'Message trop court (minimum {min_length} caractères)'}, status=400)
    
    if len(contenu) > max_length:
        return JsonResponse({'error': f'Message trop long (maximum {max_length} caractères)'}, status=400)
    
    # Vérifier limite quotidienne
    aujourdhui = timezone.now().date()
    messages_aujourdhui = MessageForum.objects.filter(
        auteur=request.user, forum=forum, date_creation__date=aujourdhui
    ).count()
    
    if messages_aujourdhui >= max_par_jour:
        return JsonResponse({'error': f'Limite quotidienne atteinte ({max_par_jour} messages/jour)'}, status=400)
    
    # Créer le message
    message = MessageForum.objects.create(
        forum=forum,
        auteur=request.user,
        contenu=contenu
    )
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'contenu': message.contenu,
            'date_creation': message.date_creation.strftime('%H:%M'),
            'date_full': message.date_creation.strftime('%d/%m/%Y %H:%M'),
            'auteur': {
                'id': message.auteur.id,
                'username': message.auteur.username,
                'prenom': getattr(message.auteur, 'prenom', ''),
                'nom': getattr(message.auteur, 'nom', ''),
                'avatar': None
            }
        }
    })

@login_required
def forum_charger_nouveaux_messages(request, forum_id):
    """
    Charge les nouveaux messages depuis un ID donné (pour polling)
    """
    from .models import Forum
    
    dernier_id = request.GET.get('dernier_id', 0)
    
    try:
        dernier_id = int(dernier_id)
    except ValueError:
        dernier_id = 0
    
    forum = get_object_or_404(Forum, id=forum_id, actif=True)
    
    # Vérifier l'accès
    if not forum.peut_voir(request.user):
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    
    # Récupérer les nouveaux messages
    nouveaux_messages = forum.get_messages_depuis(dernier_id)
    
    messages_data = []
    for msg in nouveaux_messages:
        messages_data.append({
            'id': msg.id,
            'contenu': msg.contenu,
            'date_creation': msg.date_creation.strftime('%H:%M'),
            'date_full': msg.date_creation.strftime('%d/%m/%Y %H:%M'),
            'auteur': {
                'id': msg.auteur.id,
                'username': msg.auteur.username,
                'prenom': getattr(msg.auteur, 'prenom', ''),
                'nom': getattr(msg.auteur, 'nom', ''),
                'avatar': None
            }
        })
    
    return JsonResponse({
        'success': True,
        'messages': messages_data,
        'dernier_id': nouveaux_messages.last().id if nouveaux_messages else dernier_id
    })


@login_required
def forum_signalement(request, message_id):
    """
    Signaler un message (AJAX)
    """
    from .models import MessageForum, ConfigurationMessagerie
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    message = get_object_or_404(MessageForum, id=message_id)
    config = ConfigurationMessagerie.get_config()
    
    # Ajouter le signalement
    message.ajouter_signalement(request.user)
    
    # Vérifier seuil de blocage automatique
    if message.nb_signalements >= config.forum_signalement_seuil_blocage:
        message.masquer(request.user, f"Blocage automatique après {message.nb_signalements} signalements")
    
    return JsonResponse({
        'success': True,
        'nb_signalements': message.nb_signalements,
        'message': 'Message signalé. Merci pour votre vigilance.'
    })


@login_required
@role_required('super_admin')
def forum_masquer_message(request, message_id):
    """
    Masquer un message (Super Admin uniquement)
    """
    from .models import MessageForum
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    data = json.loads(request.body)
    motif = data.get('motif', '')
    
    message = get_object_or_404(MessageForum, id=message_id)
    message.masquer(request.user, motif)
    
    return JsonResponse({'success': True, 'message': 'Message masqué'})


@login_required
@role_required('super_admin')
def forum_bloquer_utilisateur(request, forum_id, user_id):
    """
    Bloquer un utilisateur d'un forum
    """
    from .models import Forum, Utilisateur, UtilisateurBloqueForum
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    forum = get_object_or_404(Forum, id=forum_id)
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    data = json.loads(request.body)
    motif = data.get('motif', '')
    
    blocage, created = UtilisateurBloqueForum.objects.get_or_create(
        utilisateur=utilisateur,
        forum=forum,
        defaults={'bloque_par': request.user, 'motif': motif}
    )
    
    if not created and blocage.date_deblocage:
        # Réactiver un ancien blocage
        blocage.date_deblocage = None
        blocage.motif = motif
        blocage.bloque_par = request.user
        blocage.save()
    
    return JsonResponse({'success': True, 'message': f"{utilisateur.username} bloqué du forum"})


@login_required
@role_required('super_admin')
def forum_debloquer_utilisateur(request, forum_id, user_id):
    """
    Débloquer un utilisateur d'un forum
    """
    from .models import Forum, Utilisateur, UtilisateurBloqueForum
    from django.utils import timezone
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    forum = get_object_or_404(Forum, id=forum_id)
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    
    blocage = get_object_or_404(UtilisateurBloqueForum, utilisateur=utilisateur, forum=forum)
    blocage.date_deblocage = timezone.now()
    blocage.save()
    
    return JsonResponse({'success': True, 'message': f"{utilisateur.username} débloqué du forum"})


@login_required
@role_required('super_admin')
def admin_sujet_jour(request, forum_id):
    """
    Gérer le sujet du jour pour un forum
    """
    from .models import Forum, SujetDuJour
    from .forms import SujetDuJourForm
    
    forum = get_object_or_404(Forum, id=forum_id)
    
    # Récupérer le sujet du jour actuel
    aujourdhui = timezone.now().date()
    sujet_jour = SujetDuJour.objects.filter(forum=forum, date=aujourdhui).first()
    
    if request.method == 'POST':
        form = SujetDuJourForm(request.POST, instance=sujet_jour)
        if form.is_valid():
            sujet = form.save(commit=False)
            sujet.forum = forum
            sujet.date = aujourdhui
            sujet.cree_par = request.user
            sujet.save()
            messages.success(request, "Sujet du jour mis à jour")
            return redirect('forum_detail', forum_id=forum_id)
    else:
        form = SujetDuJourForm(instance=sujet_jour)
    
    return render(request, 'website/super_admin/sujet_jour.html', {
        'form': form,
        'forum': forum,
        'sujet_jour': sujet_jour
    })
    
# ==================== SUPER ADMIN - PARAMÈTRES FORUMS CENTRAL ====================

@login_required
@role_required('super_admin')
def super_admin_forums_parametres(request):
    """
    Page centrale d'administration des forums :
    - Paramètres généraux (polling, limites)
    - Gestion des utilisateurs bloqués
    - Signalements en attente
    - Modération
    - Création et gestion des forums
    """
    from .models import (ParametresMessagerie, UtilisateurBloqueForum, MessageForum, 
                         SignalementForum, Utilisateur, Forum, Ecole, Specialite)
    from django.db import models
    
    config = ParametresMessagerie.get_config()
    
    # Traitement POST
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # === PARAMÈTRES GÉNÉRAUX ===
        if action == 'parametres':
            config.forums_actifs = 'forums_actifs' in request.POST
            config.forum_polling_actif = 'forum_polling_actif' in request.POST
            config.sujet_jour_actif = 'sujet_jour_actif' in request.POST
            
            try:
                config.forum_intervalle_polling = int(request.POST.get('forum_intervalle_polling', 15))
                config.forum_max_messages_par_jour = int(request.POST.get('forum_max_messages_par_jour', 100))
                config.forum_longueur_min_message = int(request.POST.get('forum_longueur_min_message', 1))
                config.forum_longueur_max_message = int(request.POST.get('forum_longueur_max_message', 2000))
                config.min_intervalle_polling = int(request.POST.get('min_intervalle_polling', 10))
                config.max_intervalle_polling = int(request.POST.get('max_intervalle_polling', 60))
            except ValueError:
                pass
            
            config.pause_polling_onglet_inactif = 'pause_polling_onglet_inactif' in request.POST
            config.pause_polling_apres_heure = 'pause_polling_apres_heure' in request.POST
            config.adaptation_auto_intervalle = 'adaptation_auto_intervalle' in request.POST
            
            try:
                heure_debut = request.POST.get('heure_debut_pause')
                heure_fin = request.POST.get('heure_fin_pause')
                if heure_debut:
                    from datetime import datetime
                    config.heure_debut_pause = datetime.strptime(heure_debut, '%H:%M').time()
                if heure_fin:
                    config.heure_fin_pause = datetime.strptime(heure_fin, '%H:%M').time()
            except:
                pass
            
            config.save()
            messages.success(request, "Paramètres des forums enregistrés.")
        
        # === CRÉER UN FORUM ===
        elif action == 'creer_forum':
            type_forum = request.POST.get('type_forum')
            nom = request.POST.get('nom', '').strip()
            description = request.POST.get('description', '')
            icone = request.POST.get('icone', 'fas fa-comments')
            couleur = request.POST.get('couleur', '#1e3a8a')
            ordre = int(request.POST.get('ordre', 0))
            moderation = 'moderation' in request.POST
            
            if not nom:
                messages.error(request, "Le nom du forum est obligatoire")
            else:
                forum = Forum.objects.create(
                    type_forum=type_forum,
                    nom=nom,
                    description=description,
                    icone=icone,
                    couleur=couleur,
                    ordre=ordre,
                    moderation=moderation,
                    cree_par=request.user
                )
                
                if type_forum == 'ecole':
                    ecole_id = request.POST.get('ecole_id')
                    if ecole_id:
                        forum.ecole_id = ecole_id
                        forum.save()
                elif type_forum == 'specialite':
                    specialite_id = request.POST.get('specialite_id')
                    if specialite_id:
                        forum.specialite_id = specialite_id
                        forum.save()
                
                messages.success(request, f"Forum '{nom}' créé avec succès")
        
        # === MODIFIER UN FORUM ===
        elif action == 'modifier_forum':
            forum_id = request.POST.get('forum_id')
            forum = get_object_or_404(Forum, id=forum_id)
            forum.nom = request.POST.get('nom')
            forum.description = request.POST.get('description', '')
            forum.icone = request.POST.get('icone', 'fas fa-comments')
            forum.couleur = request.POST.get('couleur', '#1e3a8a')
            forum.moderation = 'moderation' in request.POST
            forum.save()
            messages.success(request, f"Forum '{forum.nom}' modifié")
        
        # === ACTIVER/DÉSACTIVER UN FORUM ===
        elif action == 'toggle_forum':
            forum_id = request.POST.get('forum_id')
            forum = get_object_or_404(Forum, id=forum_id)
            forum.actif = not forum.actif
            forum.save()
            status = "activé" if forum.actif else "désactivé"
            messages.success(request, f"Forum '{forum.nom}' {status}")
        
        # === SUPPRIMER UN FORUM ===
        elif action == 'supprimer_forum':
            forum_id = request.POST.get('forum_id')
            forum = get_object_or_404(Forum, id=forum_id)
            nom = forum.nom
            forum.delete()
            messages.success(request, f"Forum '{nom}' supprimé")
        
        # === AJOUTER UN PARTICIPANT ===
        elif action == 'ajouter_participant':
            forum_id = request.POST.get('forum_id')
            utilisateur_id = request.POST.get('utilisateur_id')
            forum = get_object_or_404(Forum, id=forum_id)
            utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
            # Ici la logique d'ajout selon le type de forum
            messages.success(request, f"{utilisateur.username} a été ajouté au forum")
        
        # === RETIRER UN PARTICIPANT ===
        elif action == 'supprimer_participant':
            forum_id = request.POST.get('forum_id')
            utilisateur_id = request.POST.get('utilisateur_id')
            forum = get_object_or_404(Forum, id=forum_id)
            utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
            messages.success(request, f"{utilisateur.username} a été retiré du forum")
        
        # === BLOQUER UN UTILISATEUR ===
        elif action == 'bloquer':
            utilisateur_id = request.POST.get('utilisateur_id')
            forum_id = request.POST.get('forum_id')
            motif = request.POST.get('motif', '')
            
            if utilisateur_id and forum_id:
                utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
                forum = get_object_or_404(Forum, id=forum_id)
                
                blocage, created = UtilisateurBloqueForum.objects.get_or_create(
                    utilisateur=utilisateur,
                    forum=forum,
                    defaults={'bloque_par': request.user, 'motif': motif}
                )
                if not created and blocage.date_deblocage:
                    blocage.date_deblocage = None
                    blocage.motif = motif
                    blocage.bloque_par = request.user
                    blocage.save()
                messages.success(request, f"{utilisateur.username} bloqué du forum {forum.nom}")
        
        # === DÉBLOQUER UN UTILISATEUR ===
        elif action == 'debloquer':
            blocage_id = request.POST.get('blocage_id')
            blocage = get_object_or_404(UtilisateurBloqueForum, id=blocage_id)
            blocage.date_deblocage = timezone.now()
            blocage.save()
            messages.success(request, f"{blocage.utilisateur.username} débloqué")
        
        # === MASQUER UN MESSAGE ===
        elif action == 'masquer_message':
            message_id = request.POST.get('message_id')
            message = get_object_or_404(MessageForum, id=message_id)
            message.est_cache = True
            message.moderateur = request.user
            message.motif_cache = request.POST.get('motif', '')
            message.date_moderation = timezone.now()
            message.save()
            messages.success(request, "Message masqué")
        
        # === TRAITER UN SIGNALEMENT ===
        elif action == 'traiter_signalement':
            signalement_id = request.POST.get('signalement_id')
            signalement = get_object_or_404(SignalementForum, id=signalement_id)
            signalement.traite = True
            signalement.date_traitement = timezone.now()
            signalement.traite_par = request.user
            signalement.save()
            messages.success(request, "Signalement traité")
        
        return redirect('super_admin_forums_parametres')
    
    # === GET : Récupérer toutes les données ===
    
    # Tous les forums
    tous_forums = Forum.objects.all().order_by('type_forum', 'actif', 'ordre', 'nom')
    
    for forum in tous_forums:
        if forum.type_forum == 'plateforme':
            # Exclure le super admin de la liste des participants
            forum.participants_list = Utilisateur.objects.filter(is_active=True).exclude(role='super_admin')[:50]
        elif forum.type_forum == 'ecole' and forum.ecole:
            forum.participants_list = Utilisateur.objects.filter(
                models.Q(ecole_admin=forum.ecole) |
                models.Q(inscriptions__specialite__filiere__ecole=forum.ecole)
            ).exclude(role='super_admin').distinct()
        elif forum.type_forum == 'specialite' and forum.specialite:
            forum.participants_list = Utilisateur.objects.filter(
                models.Q(inscriptions__specialite=forum.specialite)
            ).exclude(role='super_admin').distinct()
        else:
            forum.participants_list = []
        
        # Utilisateurs bloqués de ce forum
        forum.bloques_list = UtilisateurBloqueForum.objects.filter(
            forum=forum, 
            date_deblocage__isnull=True
        ).select_related('utilisateur')
    
    # Utilisateurs bloqués (tous)
    bloques = UtilisateurBloqueForum.objects.filter(date_deblocage__isnull=True).select_related('utilisateur', 'forum', 'bloque_par')
    
    # Signalements en attente
    signalements = SignalementForum.objects.filter(traite=False).select_related('signaleur', 'message', 'message__auteur')
    
    # Messages masqués récents
    messages_masques = MessageForum.objects.filter(est_cache=True).order_by('-date_moderation')[:50]
    
    # Utilisateurs (pour le blocage)
    utilisateurs = Utilisateur.objects.filter(is_active=True).order_by('username')[:100]
    
    # Écoles et spécialités (pour la création)
    ecoles = Ecole.objects.filter(actif=True).order_by('nom')
    specialites = Specialite.objects.select_related('filiere__ecole').order_by('filiere__ecole__nom', 'filiere__nom', 'nom')
    
    context = {
        'config': config,
        'tous_forums': tous_forums,
        'bloques': bloques,
        'signalements': signalements,
        'messages_masques': messages_masques,
        'utilisateurs': utilisateurs,
        'ecoles': ecoles,
        'specialites': specialites,
    }
    return render(request, 'website/super_admin/forums_parametres.html', context)


# ==================== ADMIN ÉCOLE - GESTION DES FORUMS ====================

@login_required
def admin_ecole_forums(request):
    """Admin école - Gestion des forums de son école"""
    from .models import Forum, Specialite, UtilisateurBloqueForum, SignalementForum, Utilisateur
    if request.user.role not in ['admin_ecole', 'super_admin']:
        messages.error(request, "Accès non autorisé")
        return redirect('dashboard')
    
    ecole = request.user.ecole_admin
    if not ecole and request.user.role != 'super_admin':
        messages.error(request, "Aucune école associée")
        return redirect('dashboard')
    # Initialiser les variables à vide
    forums_ecole = []
    forums_specialites = []
    tous_forums = []

    # Ensuite seulement si ecole existe
    if ecole:
        forums_ecole = Forum.objects.filter(ecole=ecole, type_forum='ecole').order_by('ordre', 'nom')
        forums_specialites = Forum.objects.filter(specialite__filiere__ecole=ecole, type_forum='specialite').order_by('specialite__nom')
        tous_forums = list(forums_ecole) + list(forums_specialites)
        from .models import Forum, Specialite, UtilisateurBloqueForum, SignalementForum, Utilisateur
    
    # Traitement POST
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'creer_forum':
            type_forum = request.POST.get('type_forum')
            nom = request.POST.get('nom', '').strip()
            description = request.POST.get('description', '')
            icone = request.POST.get('icone', 'fas fa-comments')
            couleur = request.POST.get('couleur', '#1e3a8a')
            ordre = int(request.POST.get('ordre', 0))
            moderation = 'moderation' in request.POST
            
            forum = Forum.objects.create(
                type_forum=type_forum,
                nom=nom,
                description=description,
                icone=icone,
                couleur=couleur,
                ordre=ordre,
                moderation=moderation,
                cree_par=request.user
            )
            
            if type_forum == 'ecole':
                forum.ecole = ecole
            elif type_forum == 'specialite':
                specialite_id = request.POST.get('specialite_id')
                if specialite_id:
                    forum.specialite_id = specialite_id
            forum.save()
            messages.success(request, f"Forum '{nom}' créé")
        
        elif action == 'modifier_forum':
            forum = get_object_or_404(Forum, id=request.POST.get('forum_id'))
            if forum.ecole != ecole and (forum.specialite and forum.specialite.filiere.ecole != ecole):
                messages.error(request, "Action non autorisée")
            else:
                forum.nom = request.POST.get('nom')
                forum.description = request.POST.get('description', '')
                forum.icone = request.POST.get('icone', 'fas fa-comments')
                forum.couleur = request.POST.get('couleur', '#1e3a8a')
                forum.moderation = 'moderation' in request.POST
                forum.save()
                messages.success(request, "Forum modifié")
        
        elif action == 'bloquer':
            # Même code que super admin
            pass
        
        elif action == 'debloquer':
            # Même code que super admin
            pass
        
        elif action == 'traiter_signalement':
            # Même code que super admin
            pass
        
        elif action == 'masquer_message':
            # Même code que super admin
            pass
        
        elif action == 'toggle_forum':
            forum = get_object_or_404(Forum, id=request.POST.get('forum_id'))
            forum.actif = not forum.actif
            forum.save()
            messages.success(request, f"Forum {'activé' if forum.actif else 'désactivé'}")

        elif action == 'modifier_forum':
            forum = get_object_or_404(Forum, id=request.POST.get('forum_id'))
            forum.nom = request.POST.get('nom')
            forum.description = request.POST.get('description', '')
            forum.icone = request.POST.get('icone', 'fas fa-comments')
            forum.couleur = request.POST.get('couleur', '#1e3a8a')
            forum.moderation = 'moderation' in request.POST
            forum.save()
            messages.success(request, "Forum modifié")

        elif action == 'supprimer_forum':
            forum = get_object_or_404(Forum, id=request.POST.get('forum_id'))
            forum.delete()
            messages.success(request, "Forum supprimé")

        elif action == 'ajouter_participant':
            # À implémenter selon votre logique
            messages.success(request, "Participant ajouté")

        elif action == 'supprimer_participant':
            # À implémenter selon votre logique
            messages.success(request, "Participant retiré")
                
            return redirect('admin_ecole_forums')
            # Après avoir récupéré les forums
    
    for forum in forums_ecole:
        forum.participants = Utilisateur.objects.filter(
            models.Q(ecole_admin=ecole) |
            models.Q(inscriptions__specialite__filiere__ecole=ecole)
        ).distinct()

    for forum in forums_specialites:
        forum.participants = Utilisateur.objects.filter(
            models.Q(inscriptions__specialite=forum.specialite)
        ).distinct()
    # GET - Récupérer les données
    forums_ecole = Forum.objects.filter(ecole=ecole, type_forum='ecole')
    forums_specialites = Forum.objects.filter(specialite__filiere__ecole=ecole, type_forum='specialite', actif=True)
    specialites = Specialite.objects.filter(filiere__ecole=ecole)
    
    tous_forums = list(forums_ecole) + list(forums_specialites)
    forums_ids = [f.id for f in tous_forums]
    
    bloques = UtilisateurBloqueForum.objects.filter(forum_id__in=forums_ids, date_deblocage__isnull=True)
    signalements = SignalementForum.objects.filter(message__forum_id__in=forums_ids, traite=False).select_related('signaleur', 'message', 'message__auteur')
    utilisateurs = Utilisateur.objects.filter(
        inscriptions__specialite__filiere__ecole=ecole
    ).distinct()
    
    context = {
        'ecole': ecole,
        'forums_ecole': forums_ecole,
        'forums_specialites': forums_specialites,
        'specialites': specialites,
        'tous_forums': tous_forums,
        'bloques': bloques,
        'signalements': signalements,
        'utilisateurs': utilisateurs,
    }
    return render(request, 'website/admin_ecole/forums.html', context)

@login_required
def forum_sujet_detail(request, sujet_id):
    """Redirige vers le forum correspondant (plus de sujets)"""
    from .models import SujetForum
    try:
        sujet = SujetForum.objects.get(id=sujet_id)
        return redirect('forum_detail', forum_id=sujet.forum.id)
    except:
        return redirect('forum_liste')

def redirection_sujet(request, sujet_id):
    """Redirige les anciens liens vers le forum"""
    from .models import MessageForum
    try:
        message = MessageForum.objects.get(id=sujet_id)
        return redirect('forum_detail', forum_id=message.forum.id)
    except:
        return redirect('forum_liste')

# Dans models.py, classe Formation
def publier(self):
    """Publier la formation"""
    self.statut = 'publie'
    self.date_publication = timezone.now()
    self.save()
    
@login_required
def api_messages_non_lus(request):
    """Retourne le nombre de messages non lus pour le polling"""
    from .models import MessagePrive
    
    non_lus = MessagePrive.objects.filter(
        conversation__participants=request.user,
        lu=False
    ).exclude(expediteur=request.user).count()
    
    return JsonResponse({
        'nouveaux_messages': non_lus,
        'utilisateurs_actifs': 0,
        'charge_serveur': 0
    })

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@login_required
@require_http_methods(["POST"])
def messagerie_api(request):
    """API AJAX pour la messagerie"""
    from .models import Conversation, MessagePrive, Utilisateur
    from django.db.models import Q
    from django.utils import timezone
    import json
    
    try:
        action = request.POST.get('action')
        
        # ========== 1. ENVOYER UN MESSAGE ==========
        if action == 'send':
            conv_id = request.POST.get('conv_id')
            contenu = request.POST.get('contenu', '').strip()
            
            if not contenu:
                return JsonResponse({'success': False, 'error': 'Message vide'})
            
            if not conv_id or conv_id == 'null':
                return JsonResponse({'success': False, 'error': 'Conversation invalide'})
            
            conversation = Conversation.objects.get(id=int(conv_id))
            
            # Vérifier l'accès
            if request.user not in conversation.participants.all():
                return JsonResponse({'success': False, 'error': 'Non autorisé'})
            
            # Créer le message
            message = MessagePrive.objects.create(
                conversation=conversation,
                expediteur=request.user,
                contenu=contenu
            )
            
            # Mettre à jour la conversation
            conversation.date_modification = timezone.now()
            conversation.save()
            
            return JsonResponse({
                'success': True,
                'message_id': message.id,
                'message': {
                    'id': message.id,
                    'contenu': message.contenu,
                    'date_envoi': message.date_envoi.strftime('%H:%M'),
                    'expediteur_id': message.expediteur.id,
                }
            })
        
        # ========== 2. CHARGER UNE CONVERSATION ==========
        elif action == 'load':
            conv_id = request.POST.get('conv_id')
            conversation = Conversation.objects.get(id=int(conv_id))
            
            if request.user not in conversation.participants.all():
                return JsonResponse({'error': 'Non autorisé'}, status=403)
            
            # Marquer comme lus
            MessagePrive.objects.filter(
                conversation=conversation, 
                lu=False
            ).exclude(expediteur=request.user).update(lu=True)
            
            messages = MessagePrive.objects.filter(conversation=conversation).order_by('date_envoi')
            autre = conversation.participants.exclude(id=request.user.id).first()
            
            # Avatar
            avatar_url = None
            if autre and hasattr(autre, 'photo') and autre.photo:
                avatar_url = autre.photo.url
            
            return JsonResponse({
                'messages': [
                    {
                        'id': m.id,
                        'contenu': m.contenu,
                        'date_envoi': m.date_envoi.strftime('%H:%M'),
                        'expediteur_id': m.expediteur.id,
                    } for m in messages
                ],
                'autre_participant': {
                    'id': autre.id,
                    'nom': autre.get_full_name() or autre.username,
                    'avatar': avatar_url,
                    'role': getattr(autre, 'role', '')
                } if autre else None
            })
        
        # ========== 3. NOUVELLE CONVERSATION ==========
        elif action == 'new_conv':
            user_id = request.POST.get('user_id')
            destinataire = Utilisateur.objects.get(id=int(user_id))
            
            if destinataire == request.user:
                return JsonResponse({'error': 'Vous ne pouvez pas discuter avec vous-même'}, status=400)
            
            # Vérifier si conversation existe déjà
            conversation = Conversation.objects.filter(
                participants=request.user
            ).filter(
                participants=destinataire
            ).first()
            
            if not conversation:
                conversation = Conversation.objects.create()
                conversation.participants.add(request.user, destinataire)
                conversation.save()
            
            return JsonResponse({'conversation_id': conversation.id})
        
        # ========== 4. RECHERCHE UTILISATEURS ==========
        elif action == 'search_users':
            search = request.POST.get('search', '').strip()
            
            if len(search) < 2:
                return JsonResponse({'utilisateurs': []})
            
            utilisateurs = Utilisateur.objects.filter(
                Q(username__icontains=search) | 
                Q(email__icontains=search) | 
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(prenom__icontains=search)
            ).exclude(id=request.user.id)[:10]
            
            utilisateurs_data = []
            for u in utilisateurs:
                nom = u.get_full_name() or u.username
                avatar_url = u.photo.url if hasattr(u, 'photo') and u.photo else None
                
                utilisateurs_data.append({
                    'id': u.id,
                    'nom': nom,
                    'email': u.email,
                    'avatar': avatar_url,
                    'role': getattr(u, 'role', '')
                })
            
            return JsonResponse({'utilisateurs': utilisateurs_data})
        
        # ========== 5. SUPPRIMER UN MESSAGE ==========
        elif action == 'delete_message':
            message_id = request.POST.get('message_id')
            message = MessagePrive.objects.get(id=int(message_id))
            
            if message.expediteur != request.user:
                return JsonResponse({'success': False, 'error': 'Non autorisé'})
            
            message.delete()
            return JsonResponse({'success': True})
        
        # ========== 6. SUPPRIMER CONVERSATION ==========
        elif action == 'delete':
            conv_id = request.POST.get('conv_id')
            conversation = Conversation.objects.get(id=int(conv_id))
            conversation.delete()
            return JsonResponse({'success': True})
        
        # ========== 7. POLLING ==========
        elif action == 'poll':
            conv_id = request.POST.get('conv_id')
            last_message_id = request.POST.get('last_message_id')
            
            conversation = Conversation.objects.get(id=int(conv_id))
            
            query = MessagePrive.objects.filter(conversation=conversation)
            if last_message_id and last_message_id != 'null':
                query = query.filter(id__gt=int(last_message_id))
            
            has_new = query.exists()
            return JsonResponse({'has_new_messages': has_new})
        
        # ========== 8. MARQUER COMME LU ==========
        elif action == 'mark_read':
            conv_id = request.POST.get('conv_id')
            conversation = Conversation.objects.get(id=int(conv_id))
            autre = conversation.participants.exclude(id=request.user.id).first()
            
            MessagePrive.objects.filter(
                conversation=conversation,
                expediteur=autre,
                lu=False
            ).update(lu=True)
            
            return JsonResponse({'success': True})
        
        else:
            return JsonResponse({'error': f'Action inconnue: {action}'}, status=400)
            
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation introuvable'}, status=404)
    except Utilisateur.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur introuvable'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
    
def get_autre_participant(self, user):
    """Retourne l'autre participant de la conversation"""
    if self.initateur == user:
        return self.destinataire
    return self.initateur

@login_required
@role_required('super_admin')
def forum_sujet_jour(request, forum_id):
    from .models import SujetDuJour, Forum
    
    forum = get_object_or_404(Forum, id=forum_id)
    
    if request.method == 'POST':
        sujet, created = SujetDuJour.objects.get_or_create(
            forum=forum,
            date=timezone.now().date()
        )
        sujet.titre = request.POST.get('titre')
        sujet.description = request.POST.get('description')
        sujet.save()
        messages.success(request, "Sujet du jour mis à jour")
        return redirect('forum_detail', forum_id=forum.id)
    
    return render(request, 'website/forum/sujet_jour.html', {'forum': forum})

from django.shortcuts import redirect
from django.contrib import messages

def login_required_inscription(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Vous devez créer un compte ou vous connecter pour accéder à cette page.")
            return redirect('inscription')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
def mon_abonnement(request):
    from .models import AbonnementUtilisateur, TransactionLog
    from django.utils import timezone

    # Récupérer ou créer l'abonnement
    abonnement, _ = AbonnementUtilisateur.objects.get_or_create(
        utilisateur=request.user,
        defaults={
            'statut': 'essai',
            'date_fin_essai': timezone.now() + timezone.timedelta(days=15),
            'paiement_oblige': True,
        }
    )

    # Historique des transactions réussies
    historique = TransactionLog.objects.filter(
        utilisateur=request.user,
        statut='reussi',
        type_transaction='abonnement'
    ).order_by('-date_transaction')

    # Calcul jours restants
    jours_restants = 0
    date_fin_affichee = None

    if abonnement.statut == 'actif' and abonnement.date_fin:
        delta = abonnement.date_fin - timezone.now()
        jours_restants = max(delta.days, 0)
        date_fin_affichee = abonnement.date_fin
    elif abonnement.statut == 'essai' and abonnement.date_fin_essai:
        delta = abonnement.date_fin_essai - timezone.now()
        jours_restants = max(delta.days, 0)
        date_fin_affichee = abonnement.date_fin_essai

    # Peut renouveler à l'avance si abonnement actif avec moins de 7 jours
    peut_renouveler_anticipe = (
        abonnement.statut == 'actif' and jours_restants <= 7
    )

    context = {
        'abonnement': abonnement,
        'historique': historique,
        'jours_restants': jours_restants,
        'date_fin_affichee': date_fin_affichee,
        'peut_renouveler_anticipe': peut_renouveler_anticipe,
        'prix_mensuel': 500,
        'prix_trimestriel': 1500,
    }
    return render(request, 'website/paiement/mon_abonnement.html', context)

# =====================================================================
# website/views.py — VUES QCM COMPLÈTES
# Remplacez les fonctions existantes et ajoutez les nouvelles
# =====================================================================
# ─────────────────────────────────────────────────────────────────────
# RÔLES AUTORISÉS
# ─────────────────────────────────────────────────────────────────────
ROLES_ENSEIGNANT = ['enseignant', 'admin_ecole', 'super_admin']
ROLES_ETUDIANT   = ['etudiant']


def _check_enseignant(request):
    return request.user.role in ROLES_ENSEIGNANT


def _check_acces_exercice(request, exercice):
    """Vérifie que l'enseignant a accès à cet exercice."""
    if request.user.role == 'super_admin':
        return True
    if exercice.seance and hasattr(exercice.seance, 'cours_programme'):
        cours = exercice.seance.cours_programme
        return cours.enseignant == request.user
    return True  # permissif si pas de cours attaché

# ─────────────────────────────────────────────────────────────────────
# 2. CONFIGURER UN QCM (enseignant — ajouter questions/réponses)
# ─────────────────────────────────────────────────────────────────────
@login_required
def qcm_configurer(request, exercice_id):
    from .models import Exercice, Question, Answer

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    questions = exercice.questions.prefetch_related('reponses').order_by('ordre')

    context = {
        'exercice':  exercice,
        'questions': questions,
    }
    return render(request, 'website/exercice/qcm/configurer.html', context)


# ─────────────────────────────────────────────────────────────────────
# 3. AJAX — Ajouter une question
# ─────────────────────────────────────────────────────────────────────
@login_required
def qcm_question_ajouter(request, exercice_id):
    from .models import Exercice, Question, Answer

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    try:
        data          = json.loads(request.body)
        texte         = data.get('texte', '').strip()
        choix         = data.get('choix', [])
        correct       = data.get('correct', 0)       # index ou liste
        multi         = data.get('multi', False)      # multi-réponses ?
        explication   = data.get('explication', '')
        points        = int(data.get('points', 1))
        type_question = data.get('type_question', 'qcm')

        if not texte:
            return JsonResponse({'error': 'Énoncé requis'}, status=400)
        if len(choix) < 2:
            return JsonResponse({'error': 'Minimum 2 réponses'}, status=400)

        # Créer la question
        ordre    = exercice.questions.count() + 1
        question = Question.objects.create(
            exercice=exercice,
            texte=texte,
            type_question=type_question,
            explication=explication,
            ordre=ordre,
            points=points,
        )

        # Créer les réponses
        reponses_creees = []
        corrects = correct if isinstance(correct, list) else [correct]

        for i, texte_choix in enumerate(choix):
            texte_choix = texte_choix.strip()
            if not texte_choix:
                continue
            ans = Answer.objects.create(
                question=question,
                texte=texte_choix,
                est_correcte=(i in corrects),
                ordre=i,
            )
            reponses_creees.append({
                'id':          ans.id,
                'texte':       ans.texte,
                'est_correcte': ans.est_correcte,
            })

        return JsonResponse({
            'success': True,
            'question': {
                'id':           question.id,
                'texte':        question.texte,
                'ordre':        question.ordre,
                'points':       question.points,
                'explication':  question.explication,
                'type_question': question.type_question,
                'choix':        [c['texte'] for c in reponses_creees],
                'corrects':     [i for i, c in enumerate(reponses_creees) if c['est_correcte']],
                'reponses':     reponses_creees,
            }
        })

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        return JsonResponse({'error': str(e)}, status=400)


# ─────────────────────────────────────────────────────────────────────
# 4. AJAX — Supprimer une question
# ─────────────────────────────────────────────────────────────────────
@login_required
def qcm_question_supprimer(request, exercice_id, question_id):
    from .models import Exercice, Question

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    exercice = get_object_or_404(Exercice, id=exercice_id)
    question = get_object_or_404(Question, id=question_id, exercice=exercice)

    if not _check_enseignant(request):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    question.delete()

    # Réordonner
    for i, q in enumerate(exercice.questions.order_by('ordre'), 1):
        if q.ordre != i:
            Question.objects.filter(pk=q.pk).update(ordre=i)

    return JsonResponse({'success': True, 'nb_questions': exercice.questions.count()})


# ─────────────────────────────────────────────────────────────────────
# 5. AJAX — Modifier une question
# ─────────────────────────────────────────────────────────────────────
@login_required
def qcm_question_modifier(request, question_id):
    from .models import Question, Answer

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    question = get_object_or_404(Question, id=question_id)
    if not _check_enseignant(request):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    try:
        data        = json.loads(request.body)
        texte       = data.get('texte', '').strip()
        choix       = data.get('choix', [])
        corrects    = data.get('corrects', [0])
        explication = data.get('explication', '')
        points      = int(data.get('points', question.points))

        if texte:
            question.texte       = texte
            question.explication = explication
            question.points      = points
            question.save(update_fields=['texte', 'explication', 'points'])

        if choix:
            question.reponses.all().delete()
            for i, txt in enumerate(choix):
                if txt.strip():
                    Answer.objects.create(
                        question=question,
                        texte=txt.strip(),
                        est_correcte=(i in corrects),
                        ordre=i,
                    )

        return JsonResponse({'success': True})
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)
# ─────────────────────────────────────────────────────────────────────
# 6. LANCER / ARRÊTER UN EXERCICE
# ─────────────────────────────────────────────────────────────────────
@login_required
def exercice_lancer(request, exercice_id):
    from .models import Exercice

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    if exercice.questions.count() == 0:
        messages.error(request, 'Ajoutez au moins une question avant de lancer.')
        return redirect('qcm_configurer', exercice_id=exercice.id)

    exercice.est_lance  = not exercice.est_lance
    exercice.est_publie = exercice.est_lance
    if exercice.est_lance:
        exercice.lance_a = timezone.now()
        messages.success(request, f'✅ Exercice "{exercice.titre}" lancé — les étudiants peuvent y accéder.')
    else:
        messages.info(request, f'Exercice "{exercice.titre}" arrêté.')
    exercice.save(update_fields=['est_lance', 'est_publie', 'lance_a'])

    if exercice.seance:
        return redirect('seance_detail', seance_id=exercice.seance.id)
    return redirect('dashboard')


# ─────────────────────────────────────────────────────────────────────
# 7. PUBLIER LES RÉSULTATS
# ─────────────────────────────────────────────────────────────────────
@login_required
def exercice_publier_resultats(request, exercice_id):
    from .models import Exercice

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    exercice.resultats_publies = True
    exercice.save(update_fields=['resultats_publies'])
    messages.success(request, 'Résultats publiés — les étudiants peuvent voir leur note.')

    if exercice.seance:
        return redirect('seance_detail', seance_id=exercice.seance.id)
    return redirect('dashboard')


# ─────────────────────────────────────────────────────────────────────
# 8. PUBLIER LA CORRECTION
# ─────────────────────────────────────────────────────────────────────
@login_required
def exercice_publier_correction(request, exercice_id):
    from .models import Exercice

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    exercice.correction_publiee = True
    exercice.save(update_fields=['correction_publiee'])
    messages.success(request, 'Correction publiée — les étudiants voient les bonnes réponses.')

    if exercice.seance:
        return redirect('seance_detail', seance_id=exercice.seance.id)
    return redirect('dashboard')


# ─────────────────────────────────────────────────────────────────────
# 9. MODIFIER UN EXERCICE (titre, consignes, durée, options)
# ─────────────────────────────────────────────────────────────────────
@login_required
def exercice_modifier(request, exercice_id):
    from .models import Exercice

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    if request.method == 'POST':
        exercice.titre     = request.POST.get('titre', exercice.titre).strip()
        exercice.consignes = request.POST.get('consignes', exercice.consignes).strip()
        try:
            exercice.duree  = int(request.POST.get('duree', exercice.duree))
            exercice.points = int(request.POST.get('points', exercice.points))
            exercice.nb_tentatives_max = int(request.POST.get('nb_tentatives_max', exercice.nb_tentatives_max))
        except (ValueError, TypeError):
            pass

        exercice.melanger_questions            = 'melanger_questions' in request.POST
        exercice.melanger_reponses             = 'melanger_reponses' in request.POST
        exercice.afficher_note_immediate       = 'afficher_note_immediate' in request.POST
        exercice.afficher_correction_immediate = 'afficher_correction_immediate' in request.POST
        exercice.multi_reponse                 = 'multi_reponse' in request.POST
        exercice.save()

        messages.success(request, 'Exercice modifié avec succès.')
        return redirect('qcm_configurer', exercice_id=exercice.id)

    return render(request, 'website/exercice/modifier.html', {'exercice': exercice})


# ─────────────────────────────────────────────────────────────────────
# 10. SUPPRIMER UN EXERCICE
# ─────────────────────────────────────────────────────────────────────
@login_required
def exercice_supprimer(request, exercice_id):
    from .models import Exercice

    exercice  = get_object_or_404(Exercice, id=exercice_id)
    seance_id = exercice.seance.id if exercice.seance else None

    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    titre = exercice.titre
    exercice.delete()
    messages.success(request, f'Exercice "{titre}" supprimé.')

    if seance_id:
        return redirect('seance_detail', seance_id=seance_id)
    return redirect('dashboard')


# ─────────────────────────────────────────────────────────────────────
# 11. PASSER UN EXERCICE (vue étudiant)
# ─────────────────────────────────────────────────────────────────────
@login_required
def exercice_passer(request, exercice_id):
    from .models import Exercice, SoumissionExercice, SauvegardeQCM
    import random

    exercice = get_object_or_404(Exercice, id=exercice_id)

    # Vérifications
    if not exercice.est_lance:
        messages.error(request, 'Cet exercice n\'est pas encore disponible.')
        return redirect('dashboard')

    # Vérifier tentatives
    soumissions_existantes = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='termine'
    )
    nb_tentatives = soumissions_existantes.count()

    if exercice.nb_tentatives_max > 0 and nb_tentatives >= exercice.nb_tentatives_max:
        messages.error(request, f'Vous avez atteint le nombre maximum de tentatives ({exercice.nb_tentatives_max}).')
        return redirect('exercice_resultat', exercice_id=exercice_id)

    # Créer ou récupérer une soumission en cours
    soumission, created = SoumissionExercice.objects.get_or_create(
        exercice=exercice,
        etudiant=request.user,
        status='en_cours',
        defaults={'nb_tentative': nb_tentatives + 1}
    )

    # Récupérer sauvegarde existante
    sauvegarde_data = {}
    try:
        sauvegarde = SauvegardeQCM.objects.get(etudiant=request.user, exercice=exercice)
        sauvegarde_data = sauvegarde.donnees_json
    except SauvegardeQCM.DoesNotExist:
        pass

    # Questions (avec mélange si activé)
    questions = list(exercice.questions.prefetch_related('reponses').all())
    if exercice.melanger_questions:
        random.shuffle(questions)

    for q in questions:
        reponses = list(q.reponses.all())
        if exercice.melanger_reponses:
            random.shuffle(reponses)
        q.reponses_melangees = reponses

    # Temps restant
    temps_restant = exercice.duree
    if not created and soumission.date_debut:
        elapsed = (timezone.now() - soumission.date_debut).total_seconds() / 60
        temps_restant = max(0, exercice.duree - int(elapsed))

    context = {
        'exercice':      exercice,
        'questions':     questions,
        'soumission':    soumission,
        'temps_restant': temps_restant,
        'sauvegarde':    json.dumps(sauvegarde_data),
    }
    return render(request, 'website/exercice/qcm/passer.html', context)


# ─────────────────────────────────────────────────────────────────────
# 12. AJAX — Sauvegarder les réponses en cours
# ─────────────────────────────────────────────────────────────────────
@login_required
def exercice_sauvegarder(request, exercice_id):
    from .models import Exercice, SauvegardeQCM

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    exercice = get_object_or_404(Exercice, id=exercice_id)

    try:
        data    = json.loads(request.body)
        reponses = data.get('reponses', {})

        SauvegardeQCM.objects.update_or_create(
            etudiant=request.user,
            exercice=exercice,
            defaults={'donnees_json': reponses}
        )
        return JsonResponse({'success': True})
    except (json.JSONDecodeError, Exception) as e:
        return JsonResponse({'error': str(e)}, status=400)


# ─────────────────────────────────────────────────────────────────────
# 13. SOUMETTRE UN EXERCICE (correction automatique)
# ─────────────────────────────────────────────────────────────────────
@login_required
def exercice_soumettre(request, exercice_id):
    from .models import Exercice, SoumissionExercice, ReponseEtudiant, Answer, SauvegardeQCM

    if request.method != 'POST':
        return redirect('exercice_passer', exercice_id=exercice_id)

    exercice = get_object_or_404(Exercice, id=exercice_id)

    soumission = SoumissionExercice.objects.filter(
        exercice=exercice,
        etudiant=request.user,
        status='en_cours'
    ).first()

    if not soumission:
        messages.error(request, 'Aucune session en cours.')
        return redirect('dashboard')

    # Corriger automatiquement
    total_points  = 0
    points_obtenus = 0

    for question in exercice.questions.prefetch_related('reponses').all():
        total_points += question.points

        # Récupérer la réponse soumise
        reponse_obj, _ = ReponseEtudiant.objects.get_or_create(
            soumission=soumission,
            question=question,
        )

        if question.type_question == 'multi':
            # Multi-réponses : cases à cocher
            ids_soumis = request.POST.getlist(f'question_{question.id}')
            ids_corrects = set(str(a.id) for a in question.reponses.filter(est_correcte=True))
            ids_soumis_set = set(ids_soumis)
            est_correct = ids_soumis_set == ids_corrects

            reponse_obj.reponses_choisies.set(ids_soumis)
            reponse_obj.est_correcte   = est_correct
            reponse_obj.points_obtenus = question.points if est_correct else 0

        elif question.type_question == 'texte_libre':
            texte = request.POST.get(f'question_{question.id}', '').strip()
            reponse_obj.reponse_texte  = texte
            reponse_obj.est_correcte   = False  # correction manuelle
            reponse_obj.points_obtenus = 0

        else:
            # QCM ou Vrai/Faux : une seule réponse
            answer_id = request.POST.get(f'question_{question.id}')
            if answer_id:
                try:
                    answer = Answer.objects.get(id=answer_id, question=question)
                    reponse_obj.reponse_choisie = answer
                    reponse_obj.est_correcte    = answer.est_correcte
                    reponse_obj.points_obtenus  = question.points if answer.est_correcte else 0
                except Answer.DoesNotExist:
                    reponse_obj.est_correcte   = False
                    reponse_obj.points_obtenus = 0
            else:
                reponse_obj.est_correcte   = False
                reponse_obj.points_obtenus = 0

        reponse_obj.save()
        points_obtenus += float(reponse_obj.points_obtenus)

    # Finaliser la soumission
    soumission.status          = 'termine'
    soumission.date_soumission = timezone.now()
    soumission.note            = round(points_obtenus, 2)
    soumission.note_sur        = total_points
    soumission.save(update_fields=['status', 'date_soumission', 'note', 'note_sur'])

    # Supprimer la sauvegarde
    SauvegardeQCM.objects.filter(etudiant=request.user, exercice=exercice).delete()

    messages.success(request, 'Exercice soumis avec succès !')
    return redirect('exercice_resultat', exercice_id=exercice_id)

@login_required
def exercice_tableau_resultats(request, exercice_id):
    from .models import Exercice, SoumissionExercice, Question

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    soumissions = SoumissionExercice.objects.filter(
        exercice=exercice, status='termine'
    ).select_related('etudiant').order_by('-note')

    stats = soumissions.aggregate(
        moyenne=Avg('note'),
        nb_total=Count('id'),
    )

    # Distribution des notes par question
    questions_stats = []
    for question in exercice.questions.prefetch_related('reponses').order_by('ordre'):
        from .models import ReponseEtudiant
        nb_correct = ReponseEtudiant.objects.filter(
            question=question,
            soumission__exercice=exercice,
            soumission__status='termine',
            est_correcte=True
        ).count()
        nb_total = soumissions.count()
        questions_stats.append({
            'question':   question,
            'nb_correct': nb_correct,
            'nb_total':   nb_total,
            'pct':        round(nb_correct / nb_total * 100) if nb_total else 0,
        })

    context = {
        'exercice':        exercice,
        'soumissions':     soumissions,
        'stats':           stats,
        'questions_stats': questions_stats,
        'nb_etudiants':    soumissions.count(),
    }
    return render(request, 'website/exercice/qcm/tableau_resultats.html', context)



# =====================================================================
# website/views.py — VUES VRAI / FAUX
# Réutilise Question/Answer (comme le QCM) avec type_question='vrai_faux'
# =====================================================================


# ─────────────────────────────────────────────────────────────────────
# 1. CONFIGURER UN EXERCICE VRAI/FAUX
# ─────────────────────────────────────────────────────────────────────
@login_required
def vrai_faux_configurer(request, exercice_id):
    from .models import Exercice

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    questions = exercice.questions.filter(type_question='vrai_faux').prefetch_related('reponses').order_by('ordre')

    context = {
        'exercice':  exercice,
        'questions': questions,
    }
    return render(request, 'website/exercice/vrai_faux/configurer.html', context)


# ─────────────────────────────────────────────────────────────────────
# 2. AJAX — Ajouter une affirmation Vrai/Faux
# ─────────────────────────────────────────────────────────────────────
@login_required
def vrai_faux_ajouter(request, exercice_id):
    from .models import Exercice, Question, Answer

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    try:
        data        = json.loads(request.body)
        texte       = data.get('texte', '').strip()
        est_vrai    = bool(data.get('est_vrai', True))
        explication = data.get('explication', '')
        points      = int(data.get('points', 1))

        if not texte:
            return JsonResponse({'error': 'Énoncé requis'}, status=400)

        ordre    = exercice.questions.count() + 1
        question = Question.objects.create(
            exercice=exercice,
            texte=texte,
            type_question='vrai_faux',
            explication=explication,
            ordre=ordre,
            points=points,
        )

        # Création automatique des 2 réponses fixes
        Answer.objects.create(question=question, texte='Vrai', est_correcte=est_vrai, ordre=0)
        Answer.objects.create(question=question, texte='Faux', est_correcte=not est_vrai, ordre=1)

        return JsonResponse({
            'success': True,
            'question': {
                'id':          question.id,
                'texte':       question.texte,
                'ordre':       question.ordre,
                'points':      question.points,
                'explication': question.explication,
                'est_vrai':    est_vrai,
            }
        })
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)


# ─────────────────────────────────────────────────────────────────────
# 3. AJAX — Modifier une affirmation
# ─────────────────────────────────────────────────────────────────────
@login_required
def vrai_faux_modifier(request, question_id):
    from .models import Question, Answer

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    question = get_object_or_404(Question, id=question_id, type_question='vrai_faux')
    if not _check_enseignant(request):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    try:
        data        = json.loads(request.body)
        texte       = data.get('texte', '').strip()
        est_vrai    = bool(data.get('est_vrai', True))
        explication = data.get('explication', '')
        points      = int(data.get('points', question.points))

        if texte:
            question.texte       = texte
            question.explication = explication
            question.points      = points
            question.save(update_fields=['texte', 'explication', 'points'])

        question.reponses.filter(texte='Vrai').update(est_correcte=est_vrai)
        question.reponses.filter(texte='Faux').update(est_correcte=not est_vrai)

        return JsonResponse({'success': True})
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)


# ─────────────────────────────────────────────────────────────────────
# 4. AJAX — Supprimer une affirmation
# ─────────────────────────────────────────────────────────────────────
@login_required
def vrai_faux_supprimer(request, exercice_id, question_id):
    from .models import Exercice, Question

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    exercice = get_object_or_404(Exercice, id=exercice_id)
    question = get_object_or_404(Question, id=question_id, exercice=exercice, type_question='vrai_faux')

    if not _check_enseignant(request):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    question.delete()

    for i, q in enumerate(exercice.questions.filter(type_question='vrai_faux').order_by('ordre'), 1):
        if q.ordre != i:
            Question.objects.filter(pk=q.pk).update(ordre=i)

    return JsonResponse({'success': True, 'nb_questions': exercice.questions.count()})
# =====================================================================
# website/views.py — VUES TEXTE À TROUS
# =====================================================================
# ─────────────────────────────────────────────────────────────────────
# 1. CONFIGURER (créer/éditer le texte à trous)
# ─────────────────────────────────────────────────────────────────────
@login_required
def texte_trous_configurer(request, exercice_id):
    from .models import Exercice, TexteATrous, TrouReponse

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    texte_trous, _ = TexteATrous.objects.get_or_create(exercice=exercice)

    if request.method == 'POST':
        texte_brut = request.POST.get('texte_brut', '').strip()
        if not texte_brut:
            messages.error(request, 'Le texte est obligatoire.')
            return redirect('texte_trous_configurer', exercice_id=exercice_id)

        texte_trous.texte_brut = texte_brut
        texte_trous.save()

        # Détecter automatiquement les numéros de trous {{N}}
        numeros_trouves = sorted(set(int(n) for n in re.findall(r'\{\{(\d+)\}\}', texte_brut)))

        for numero in numeros_trouves:
            reponses_key = f'reponses_{numero}'
            points_key   = f'points_{numero}'
            reponses_acceptees = request.POST.get(reponses_key, '').strip()
            points = int(request.POST.get(points_key, 1) or 1)

            TrouReponse.objects.update_or_create(
                texte_a_trous=texte_trous,
                numero=numero,
                defaults={
                    'reponses_acceptees': reponses_acceptees,
                    'points': points,
                }
            )

        # Supprimer les trous qui n'existent plus dans le texte
        texte_trous.trous.exclude(numero__in=numeros_trouves).delete()

        # Mettre à jour le total de points de l'exercice
        exercice.points = sum(t.points for t in texte_trous.trous.all())
        exercice.save(update_fields=['points'])

        messages.success(request, 'Texte à trous configuré avec succès.')
        return redirect('texte_trous_configurer', exercice_id=exercice_id)

    # Numéros de trous détectés pour affichage du formulaire
    numeros_detectes = sorted(set(int(n) for n in re.findall(r'\{\{(\d+)\}\}', texte_trous.texte_brut or '')))
    trous_existants   = {t.numero: t for t in texte_trous.trous.all()}

    context = {
        'exercice':         exercice,
        'texte_trous':       texte_trous,
        'numeros_detectes':  numeros_detectes,
        'trous_existants':   trous_existants,
    }
    return render(request, 'website/exercice/texte_trous/configurer.html', context)


# ─────────────────────────────────────────────────────────────────────
# 2. AJAX — Prévisualiser la détection des trous (en live, sans sauver)
# ─────────────────────────────────────────────────────────────────────
@login_required
def texte_trous_previsualiser(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    try:
        data       = json.loads(request.body)
        texte_brut = data.get('texte_brut', '')
        numeros    = sorted(set(int(n) for n in re.findall(r'\{\{(\d+)\}\}', texte_brut)))

        # Rendu HTML avec les trous remplacés par des inputs visuels
        rendu = texte_brut
        for n in numeros:
            rendu = rendu.replace(f'{{{{{n}}}}}', f'<span class="trou-preview">___{n}___</span>')

        return JsonResponse({'success': True, 'numeros': numeros, 'rendu_html': rendu})
    except json.JSONDecodeError as e:
        return JsonResponse({'error': str(e)}, status=400)


# ─────────────────────────────────────────────────────────────────────
# 3. PASSER (vue étudiant)
# ─────────────────────────────────────────────────────────────────────
@login_required
def texte_trous_passer(request, exercice_id):
    from .models import Exercice, SoumissionExercice, SauvegardeQCM
    import re as _re

    exercice = get_object_or_404(Exercice, id=exercice_id)

    if not exercice.est_lance:
        messages.error(request, 'Cet exercice n\'est pas encore disponible.')
        return redirect('dashboard')

    texte_trous = getattr(exercice, 'texte_a_trous', None)
    if not texte_trous:
        messages.error(request, 'Cet exercice n\'a pas encore été configuré.')
        return redirect('dashboard')

    nb_tentatives = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='termine'
    ).count()

    if exercice.nb_tentatives_max > 0 and nb_tentatives >= exercice.nb_tentatives_max:
        messages.error(request, 'Nombre maximum de tentatives atteint.')
        return redirect('exercice_resultat', exercice_id=exercice_id)

    soumission, created = SoumissionExercice.objects.get_or_create(
        exercice=exercice, etudiant=request.user, status='en_cours',
        defaults={'nb_tentative': nb_tentatives + 1}
    )

    # Sauvegarde existante
    sauvegarde_data = {}
    try:
        sauvegarde = SauvegardeQCM.objects.get(etudiant=request.user, exercice=exercice)
        sauvegarde_data = sauvegarde.donnees_json
    except SauvegardeQCM.DoesNotExist:
        pass

    # Construire le texte avec des placeholders d'input numérotés
    trous = list(texte_trous.trous.order_by('numero'))
    segments = _re.split(r'\{\{\d+\}\}', texte_trous.texte_brut)
    numeros  = [t.numero for t in trous]

    temps_restant = exercice.duree
    if not created and soumission.date_debut:
        elapsed = (timezone.now() - soumission.date_debut).total_seconds() / 60
        temps_restant = max(0, exercice.duree - int(elapsed))

    context = {
        'exercice':      exercice,
        'texte_trous':   texte_trous,
        'segments':      segments,
        'numeros':       numeros,
        'trous':         trous,
        'soumission':    soumission,
        'temps_restant': temps_restant,
        'sauvegarde':    json.dumps(sauvegarde_data),
    }
    return render(request, 'website/exercice/texte_trous/passer.html', context)


# ─────────────────────────────────────────────────────────────────────
# 4. SOUMETTRE (correction automatique)
# ─────────────────────────────────────────────────────────────────────
@login_required
def texte_trous_soumettre(request, exercice_id):
    from .models import Exercice, SoumissionExercice, ReponseTrouEtudiant, SauvegardeQCM

    if request.method != 'POST':
        return redirect('texte_trous_passer', exercice_id=exercice_id)

    exercice    = get_object_or_404(Exercice, id=exercice_id)
    texte_trous = getattr(exercice, 'texte_a_trous', None)

    soumission = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='en_cours'
    ).first()

    if not soumission or not texte_trous:
        messages.error(request, 'Aucune session en cours.')
        return redirect('dashboard')

    total_points    = 0
    points_obtenus  = 0

    for trou in texte_trous.trous.all():
        total_points += trou.points
        reponse_donnee = request.POST.get(f'trou_{trou.numero}', '').strip()
        est_correcte   = trou.verifier(reponse_donnee)

        ReponseTrouEtudiant.objects.update_or_create(
            soumission=soumission,
            trou=trou,
            defaults={
                'reponse_donnee': reponse_donnee,
                'est_correcte':   est_correcte,
                'points_obtenus': trou.points if est_correcte else 0,
            }
        )
        if est_correcte:
            points_obtenus += trou.points

    soumission.status          = 'termine'
    soumission.date_soumission = timezone.now()
    soumission.note            = round(points_obtenus, 2)
    soumission.note_sur         = total_points
    soumission.save(update_fields=['status', 'date_soumission', 'note', 'note_sur'])

    SauvegardeQCM.objects.filter(etudiant=request.user, exercice=exercice).delete()

    messages.success(request, 'Exercice soumis avec succès !')
    return redirect('exercice_resultat', exercice_id=exercice_id)


# ─────────────────────────────────────────────────────────────────────
# 5. RÉSULTAT (vue spécifique texte à trous)
# ─────────────────────────────────────────────────────────────────────
@login_required
def texte_trous_resultat(request, exercice_id):
    from .models import Exercice, SoumissionExercice, ReponseTrouEtudiant
    import re as _re

    exercice    = get_object_or_404(Exercice, id=exercice_id)
    texte_trous = getattr(exercice, 'texte_a_trous', None)

    soumission = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='termine'
    ).order_by('-date_soumission').first()

    if not soumission:
        messages.warning(request, 'Vous n\'avez pas encore soumis cet exercice.')
        return redirect('texte_trous_passer', exercice_id=exercice_id)

    reponses = ReponseTrouEtudiant.objects.filter(
        soumission=soumission
    ).select_related('trou').order_by('trou__numero')

    segments = _re.split(r'\{\{\d+\}\}', texte_trous.texte_brut) if texte_trous else []

    context = {
        'exercice':    exercice,
        'soumission':  soumission,
        'reponses':    reponses,
        'segments':    segments,
        'afficher_correction': exercice.correction_publiee or exercice.afficher_correction_immediate,
        'afficher_note':       exercice.resultats_publies  or exercice.afficher_note_immediate,
    }
    return render(request, 'website/exercice/texte_trous/resultat.html', context)


# ─────────────────────────────────────────────────────────────────────
# 6. TABLEAU DE BORD ENSEIGNANT
# ─────────────────────────────────────────────────────────────────────
@login_required
def texte_trous_tableau_resultats(request, exercice_id):
    from .models import Exercice, SoumissionExercice, ReponseTrouEtudiant
    from django.db.models import Avg, Count

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    soumissions = SoumissionExercice.objects.filter(
        exercice=exercice, status='termine'
    ).select_related('etudiant').order_by('-note')

    stats = soumissions.aggregate(moyenne=Avg('note'), nb_total=Count('id'))

    trous_stats = []
    texte_trous = getattr(exercice, 'texte_a_trous', None)
    if texte_trous:
        for trou in texte_trous.trous.order_by('numero'):
            nb_correct = ReponseTrouEtudiant.objects.filter(
                trou=trou, soumission__status='termine', est_correcte=True
            ).count()
            nb_total = soumissions.count()
            trous_stats.append({
                'trou': trou,
                'nb_correct': nb_correct,
                'nb_total': nb_total,
                'pct': round(nb_correct / nb_total * 100) if nb_total else 0,
            })

    context = {
        'exercice':    exercice,
        'soumissions': soumissions,
        'stats':       stats,
        'trous_stats': trous_stats,
        'nb_etudiants': soumissions.count(),
    }
    return render(request, 'website/exercice/texte_trous/tableau_resultats.html', context)

# =====================================================================
# website/views.py — VUES RÉPONSE COURTE
# =====================================================================

@login_required
def reponse_courte_configurer(request, exercice_id):
    from .models import Exercice

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    questions = exercice.questions_courtes.order_by('ordre')

    context = {
        'exercice':  exercice,
        'questions': questions,
    }
    return render(request, 'website/exercice/reponse_courte/configurer.html', context)

# ─────────────────────────────────────────────────────────────────────
# 2. AJAX — Ajouter une question
# ─────────────────────────────────────────────────────────────────────
@login_required
def reponse_courte_ajouter(request, exercice_id):
    from .models import Exercice, QuestionReponseCourte

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    try:
        # multipart si image jointe, sinon JSON
        if request.content_type and 'multipart' in request.content_type:
            texte         = request.POST.get('texte', '').strip()
            reponses      = request.POST.get('reponses_acceptees', '').strip()
            sensible_casse = 'sensible_casse' in request.POST
            explication   = request.POST.get('explication', '')
            points        = int(request.POST.get('points', 1))
            image         = request.FILES.get('image')
        else:
            data           = json.loads(request.body)
            texte          = data.get('texte', '').strip()
            reponses       = data.get('reponses_acceptees', '').strip()
            sensible_casse = bool(data.get('sensible_casse', False))
            explication    = data.get('explication', '')
            points         = int(data.get('points', 1))
            image          = None

        if not texte or not reponses:
            return JsonResponse({'error': 'Question et réponses acceptées requises'}, status=400)

        ordre    = exercice.questions_courtes.count() + 1
        question = QuestionReponseCourte.objects.create(
            exercice=exercice,
            texte=texte,
            reponses_acceptees=reponses,
            sensible_casse=sensible_casse,
            explication=explication,
            ordre=ordre,
            points=points,
        )
        if image:
            question.image = image
            question.save(update_fields=['image'])

        return JsonResponse({
            'success': True,
            'question': {
                'id':       question.id,
                'texte':    question.texte,
                'ordre':    question.ordre,
                'points':   question.points,
                'reponses_acceptees': question.reponses_acceptees,
                'image_url': question.image.url if question.image else None,
            }
        })
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)
# ─────────────────────────────────────────────────────────────────────
# 3. AJAX — Modifier une question
# ─────────────────────────────────────────────────────────────────────
@login_required
def reponse_courte_modifier(request, question_id):
    from .models import QuestionReponseCourte

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    question = get_object_or_404(QuestionReponseCourte, id=question_id)
    if not _check_enseignant(request):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    try:
        data = json.loads(request.body)
        question.texte              = data.get('texte', question.texte).strip()
        question.reponses_acceptees = data.get('reponses_acceptees', question.reponses_acceptees).strip()
        question.sensible_casse     = bool(data.get('sensible_casse', question.sensible_casse))
        question.explication        = data.get('explication', question.explication)
        question.points             = int(data.get('points', question.points))
        question.save()
        return JsonResponse({'success': True})
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)


# ─────────────────────────────────────────────────────────────────────
# 4. AJAX — Supprimer une question
# ─────────────────────────────────────────────────────────────────────
@login_required
def reponse_courte_supprimer(request, exercice_id, question_id):
    from .models import Exercice, QuestionReponseCourte

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    exercice = get_object_or_404(Exercice, id=exercice_id)
    question = get_object_or_404(QuestionReponseCourte, id=question_id, exercice=exercice)

    if not _check_enseignant(request):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    question.delete()

    for i, q in enumerate(exercice.questions_courtes.order_by('ordre'), 1):
        if q.ordre != i:
            QuestionReponseCourte.objects.filter(pk=q.pk).update(ordre=i)

    return JsonResponse({'success': True, 'nb_questions': exercice.questions_courtes.count()})


# ─────────────────────────────────────────────────────────────────────
# 5. PASSER (vue étudiant)
# ─────────────────────────────────────────────────────────────────────
@login_required
def reponse_courte_passer(request, exercice_id):
    from .models import Exercice, SoumissionExercice, SauvegardeQCM

    exercice = get_object_or_404(Exercice, id=exercice_id)

    if not exercice.est_lance:
        messages.error(request, 'Cet exercice n\'est pas encore disponible.')
        return redirect('dashboard')

    nb_tentatives = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='termine'
    ).count()

    if exercice.nb_tentatives_max > 0 and nb_tentatives >= exercice.nb_tentatives_max:
        messages.error(request, 'Nombre maximum de tentatives atteint.')
        return redirect('exercice_resultat', exercice_id=exercice_id)

    soumission, created = SoumissionExercice.objects.get_or_create(
        exercice=exercice, etudiant=request.user, status='en_cours',
        defaults={'nb_tentative': nb_tentatives + 1}
    )

    sauvegarde_data = {}
    try:
        sauvegarde = SauvegardeQCM.objects.get(etudiant=request.user, exercice=exercice)
        sauvegarde_data = sauvegarde.donnees_json
    except SauvegardeQCM.DoesNotExist:
        pass

    questions = exercice.questions_courtes.order_by('ordre')

    temps_restant = exercice.duree
    if not created and soumission.date_debut:
        elapsed = (timezone.now() - soumission.date_debut).total_seconds() / 60
        temps_restant = max(0, exercice.duree - int(elapsed))

    context = {
        'exercice':      exercice,
        'questions':     questions,
        'soumission':    soumission,
        'temps_restant': temps_restant,
        'sauvegarde':    json.dumps(sauvegarde_data),
    }
    return render(request, 'website/exercice/reponse_courte/passer.html', context)

# ─────────────────────────────────────────────────────────────────────
# 6. SOUMETTRE (correction automatique)
# ─────────────────────────────────────────────────────────────────────
@login_required
def reponse_courte_soumettre(request, exercice_id):
    from .models import Exercice, SoumissionExercice, ReponseCourteEtudiant, SauvegardeQCM

    if request.method != 'POST':
        return redirect('reponse_courte_passer', exercice_id=exercice_id)

    exercice   = get_object_or_404(Exercice, id=exercice_id)
    soumission = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='en_cours'
    ).first()

    if not soumission:
        messages.error(request, 'Aucune session en cours.')
        return redirect('dashboard')

    total_points   = 0
    points_obtenus = 0

    for question in exercice.questions_courtes.all():
        total_points += question.points
        reponse_donnee = request.POST.get(f'question_{question.id}', '').strip()
        est_correcte   = question.verifier(reponse_donnee)

        ReponseCourteEtudiant.objects.update_or_create(
            soumission=soumission,
            question=question,
            defaults={
                'reponse_donnee': reponse_donnee,
                'est_correcte':   est_correcte,
                'points_obtenus': question.points if est_correcte else 0,
            }
        )
        if est_correcte:
            points_obtenus += question.points

    soumission.status          = 'termine'
    soumission.date_soumission = timezone.now()
    soumission.note            = round(points_obtenus, 2)
    soumission.note_sur        = total_points
    soumission.save(update_fields=['status', 'date_soumission', 'note', 'note_sur'])

    SauvegardeQCM.objects.filter(etudiant=request.user, exercice=exercice).delete()

    messages.success(request, 'Exercice soumis avec succès !')
    return redirect('exercice_resultat', exercice_id=exercice_id)
# ─────────────────────────────────────────────────────────────────────
# 7. RÉSULTAT
# ─────────────────────────────────────────────────────────────────────
@login_required
def reponse_courte_resultat(request, exercice_id):
    from .models import Exercice, SoumissionExercice, ReponseCourteEtudiant

    exercice = get_object_or_404(Exercice, id=exercice_id)

    soumission = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='termine'
    ).order_by('-date_soumission').first()

    if not soumission:
        messages.warning(request, 'Vous n\'avez pas encore soumis cet exercice.')
        return redirect('reponse_courte_passer', exercice_id=exercice_id)

    reponses = ReponseCourteEtudiant.objects.filter(
        soumission=soumission
    ).select_related('question').order_by('question__ordre')

    context = {
        'exercice':   exercice,
        'soumission': soumission,
        'reponses':   reponses,
        'afficher_correction': exercice.correction_publiee or exercice.afficher_correction_immediate,
        'afficher_note':       exercice.resultats_publies  or exercice.afficher_note_immediate,
    }
    return render(request, 'website/exercice/reponse_courte/resultat.html', context)
# ─────────────────────────────────────────────────────────────────────
# 8. TABLEAU DE BORD ENSEIGNANT
# ─────────────────────────────────────────────────────────────────────
@login_required
def reponse_courte_tableau_resultats(request, exercice_id):
    from .models import Exercice, SoumissionExercice, ReponseCourteEtudiant
    from django.db.models import Avg, Count

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    soumissions = SoumissionExercice.objects.filter(
        exercice=exercice, status='termine'
    ).select_related('etudiant').order_by('-note')

    stats = soumissions.aggregate(moyenne=Avg('note'), nb_total=Count('id'))

    questions_stats = []
    for question in exercice.questions_courtes.order_by('ordre'):
        nb_correct = ReponseCourteEtudiant.objects.filter(
            question=question, soumission__status='termine', est_correcte=True
        ).count()
        nb_total = soumissions.count()
        questions_stats.append({
            'question': question,
            'nb_correct': nb_correct,
            'nb_total': nb_total,
            'pct': round(nb_correct / nb_total * 100) if nb_total else 0,
        })

    context = {
        'exercice': exercice,
        'soumissions': soumissions,
        'stats': stats,
        'questions_stats': questions_stats,
        'nb_etudiants': soumissions.count(),
    }
    return render(request, 'website/exercice/reponse_courte/tableau_resultats.html', context)

# =====================================================================
# website/views.py — VUES RÉDACTION (correction manuelle)
# =====================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

# ─────────────────────────────────────────────────────────────────────
# 1. CONFIGURER (créer/éditer le sujet de rédaction)
# ─────────────────────────────────────────────────────────────────────
@login_required
def redaction_configurer(request, exercice_id):
    from .models import Exercice, ConsigneRedaction

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    consigne, _ = ConsigneRedaction.objects.get_or_create(exercice=exercice)

    if request.method == 'POST':
        consigne.sujet       = request.POST.get('sujet', '').strip()
        try:
            consigne.nb_mots_min = int(request.POST.get('nb_mots_min', 0) or 0)
            consigne.nb_mots_max = int(request.POST.get('nb_mots_max', 0) or 0)
        except ValueError:
            pass
        consigne.criteres_evaluation = request.POST.get('criteres_evaluation', '').strip()

        if 'document_ressource' in request.FILES:
            consigne.document_ressource = request.FILES['document_ressource']

        if not consigne.sujet:
            messages.error(request, 'Le sujet est obligatoire.')
            return redirect('redaction_configurer', exercice_id=exercice_id)

        consigne.save()
        messages.success(request, 'Sujet de rédaction configuré.')
        return redirect('redaction_configurer', exercice_id=exercice_id)

    context = {'exercice': exercice, 'consigne': consigne}
    return render(request, 'website/exercice/redaction/configurer.html', context)


# ─────────────────────────────────────────────────────────────────────
# 2. PASSER (vue étudiant — rédiger)
# ─────────────────────────────────────────────────────────────────────
@login_required
def redaction_passer(request, exercice_id):
    from .models import Exercice, ConsigneRedaction, SoumissionExercice, ReponseRedaction, SauvegardeQCM

    exercice = get_object_or_404(Exercice, id=exercice_id)
    consigne = getattr(exercice, 'redaction', None)

    if not exercice.est_lance:
        messages.error(request, 'Cet exercice n\'est pas encore disponible.')
        return redirect('dashboard')
    if not consigne:
        messages.error(request, 'Cet exercice n\'a pas encore été configuré.')
        return redirect('dashboard')

    nb_tentatives = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='termine'
    ).count()
    if exercice.nb_tentatives_max > 0 and nb_tentatives >= exercice.nb_tentatives_max:
        messages.error(request, 'Nombre maximum de tentatives atteint.')
        return redirect('redaction_resultat', exercice_id=exercice_id)

    soumission, created = SoumissionExercice.objects.get_or_create(
        exercice=exercice, etudiant=request.user, status='en_cours',
        defaults={'nb_tentative': nb_tentatives + 1}
    )

    # Récupérer le brouillon sauvegardé (sauvegarde générique en JSON)
    texte_sauvegarde = ''
    try:
        sauvegarde = SauvegardeQCM.objects.get(etudiant=request.user, exercice=exercice)
        texte_sauvegarde = sauvegarde.donnees_json.get('texte_redige', '')
    except SauvegardeQCM.DoesNotExist:
        pass

    temps_restant = exercice.duree
    if not created and soumission.date_debut:
        elapsed = (timezone.now() - soumission.date_debut).total_seconds() / 60
        temps_restant = max(0, exercice.duree - int(elapsed))

    context = {
        'exercice':         exercice,
        'consigne':         consigne,
        'soumission':       soumission,
        'temps_restant':    temps_restant,
        'texte_sauvegarde': texte_sauvegarde,
    }
    return render(request, 'website/exercice/redaction/passer.html', context)


# ─────────────────────────────────────────────────────────────────────
# 3. AJAX — Sauvegarder le brouillon
# ─────────────────────────────────────────────────────────────────────
@login_required
def redaction_sauvegarder(request, exercice_id):
    from .models import Exercice, SauvegardeQCM
    import json

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    exercice = get_object_or_404(Exercice, id=exercice_id)

    try:
        data  = json.loads(request.body)
        texte = data.get('texte_redige', '')
        nb_mots = len(texte.split()) if texte else 0

        SauvegardeQCM.objects.update_or_create(
            etudiant=request.user, exercice=exercice,
            defaults={'donnees_json': {'texte_redige': texte}}
        )
        return JsonResponse({'success': True, 'nb_mots': nb_mots})
    except json.JSONDecodeError as e:
        return JsonResponse({'error': str(e)}, status=400)


# ─────────────────────────────────────────────────────────────────────
# 4. SOUMETTRE (pas de correction auto — en attente de l'enseignant)
# ─────────────────────────────────────────────────────────────────────
@login_required
def redaction_soumettre(request, exercice_id):
    from .models import Exercice, SoumissionExercice, ReponseRedaction, SauvegardeQCM

    if request.method != 'POST':
        return redirect('redaction_passer', exercice_id=exercice_id)

    exercice   = get_object_or_404(Exercice, id=exercice_id)
    soumission = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='en_cours'
    ).first()

    if not soumission:
        messages.error(request, 'Aucune session en cours.')
        return redirect('dashboard')

    texte_redige = request.POST.get('texte_redige', '').strip()

    if not texte_redige:
        messages.error(request, 'Votre rédaction ne peut pas être vide.')
        return redirect('redaction_passer', exercice_id=exercice_id)

    ReponseRedaction.objects.update_or_create(
        soumission=soumission,
        defaults={'texte_redige': texte_redige}
    )

    soumission.status          = 'termine'
    soumission.date_soumission = timezone.now()
    soumission.note            = None  # en attente de correction manuelle
    soumission.note_sur        = exercice.points
    soumission.save(update_fields=['status', 'date_soumission', 'note', 'note_sur'])

    SauvegardeQCM.objects.filter(etudiant=request.user, exercice=exercice).delete()

    messages.success(request, 'Rédaction soumise — elle sera corrigée par votre enseignant.')
    return redirect('redaction_resultat', exercice_id=exercice_id)


# ─────────────────────────────────────────────────────────────────────
# 5. RÉSULTAT (étudiant — affiche le statut et la correction si dispo)
# ─────────────────────────────────────────────────────────────────────
@login_required
def redaction_resultat(request, exercice_id):
    from .models import Exercice, SoumissionExercice, ReponseRedaction

    exercice = get_object_or_404(Exercice, id=exercice_id)

    soumission = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='termine'
    ).order_by('-date_soumission').first()

    if not soumission:
        messages.warning(request, 'Vous n\'avez pas encore soumis cette rédaction.')
        return redirect('redaction_passer', exercice_id=exercice_id)

    reponse = ReponseRedaction.objects.filter(soumission=soumission).first()

    context = {
        'exercice':   exercice,
        'soumission': soumission,
        'reponse':    reponse,
        'est_corrigee': reponse.est_corrigee if reponse else False,
    }
    return render(request, 'website/exercice/redaction/resultat.html', context)


# ─────────────────────────────────────────────────────────────────────
# 6. LISTE DES COPIES À CORRIGER (enseignant)
# ─────────────────────────────────────────────────────────────────────
@login_required
def redaction_liste_a_corriger(request, exercice_id):
    from .models import Exercice, SoumissionExercice, ReponseRedaction

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    soumissions = SoumissionExercice.objects.filter(
        exercice=exercice, status='termine'
    ).select_related('etudiant', 'redaction_reponse').order_by('date_soumission')

    a_corriger = [s for s in soumissions if not (hasattr(s, 'redaction_reponse') and s.redaction_reponse.est_corrigee)]
    corrigees  = [s for s in soumissions if hasattr(s, 'redaction_reponse') and s.redaction_reponse.est_corrigee]

    context = {
        'exercice':   exercice,
        'a_corriger': a_corriger,
        'corrigees':  corrigees,
        'nb_total':   soumissions.count(),
    }
    return render(request, 'website/exercice/redaction/liste_a_corriger.html', context)
# ─────────────────────────────────────────────────────────────────────
# 7. CORRIGER UNE COPIE (enseignant)
# ─────────────────────────────────────────────────────────────────────
@login_required
def redaction_corriger(request, soumission_id):
    from .models import SoumissionExercice, ReponseRedaction

    soumission = get_object_or_404(SoumissionExercice, id=soumission_id, status='termine')
    exercice   = soumission.exercice

    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    reponse, _ = ReponseRedaction.objects.get_or_create(soumission=soumission)

    if request.method == 'POST':
        try:
            note = float(request.POST.get('note_donnee', 0))
        except ValueError:
            note = 0

        reponse.note_donnee           = note
        reponse.commentaire_correcteur = request.POST.get('commentaire', '').strip()
        reponse.corrige_par           = request.user
        reponse.date_correction       = timezone.now()
        reponse.save()

        soumission.note = note
        soumission.save(update_fields=['note'])

        messages.success(request, f'Copie de {soumission.etudiant.username} corrigée.')
        return redirect('redaction_liste_a_corriger', exercice_id=exercice.id)

    context = {
        'exercice':   exercice,
        'soumission': soumission,
        'reponse':    reponse,
        'criteres':   exercice.redaction.liste_criteres if hasattr(exercice, 'redaction') else [],
    }
    return render(request, 'website/exercice/redaction/corriger.html', context)
# ─────────────────────────────────────────────────────────────────────
# 8. TABLEAU DE BORD ENSEIGNANT (statistiques)
# ─────────────────────────────────────────────────────────────────────
@login_required
def redaction_tableau_resultats(request, exercice_id):
    from .models import Exercice, SoumissionExercice
    from django.db.models import Avg, Count

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    soumissions = SoumissionExercice.objects.filter(
        exercice=exercice, status='termine'
    ).select_related('etudiant', 'redaction_reponse').order_by('-note')

    notees = soumissions.exclude(note__isnull=True)
    stats  = notees.aggregate(moyenne=Avg('note'), nb_total=Count('id'))

    context = {
        'exercice':       exercice,
        'soumissions':    soumissions,
        'stats':          stats,
        'nb_corrigees':   notees.count(),
        'nb_en_attente':  soumissions.filter(note__isnull=True).count(),
        'nb_etudiants':   soumissions.count(),
    }
    return render(request, 'website/exercice/redaction/tableau_resultats.html', context)

# =====================================================================
# website/views.py — VUES DÉPÔT DE FICHIER
# =====================================================================

# ─────────────────────────────────────────────────────────────────────
# 1. CONFIGURER (enseignant)
# ─────────────────────────────────────────────────────────────────────
@login_required
def depot_fichier_configurer(request, exercice_id):
    from .models import Exercice, ConsigneDepotFichier

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    consigne, _ = ConsigneDepotFichier.objects.get_or_create(exercice=exercice)

    if request.method == 'POST':
        consigne.instructions = request.POST.get('instructions', '').strip()
        consigne.extensions_autorisees = request.POST.get('extensions_autorisees', 'pdf,doc,docx,jpg,png,zip')
        try:
            consigne.taille_max_mo = int(request.POST.get('taille_max_mo', 10))
            consigne.nb_fichiers_max = int(request.POST.get('nb_fichiers_max', 1))
        except ValueError:
            pass
        consigne.grille_correction = request.POST.get('grille_correction', '').strip()

        if 'document_ressource' in request.FILES:
            consigne.document_ressource = request.FILES['document_ressource']

        if not consigne.instructions:
            messages.error(request, 'Les instructions sont obligatoires.')
            return redirect('depot_fichier_configurer', exercice_id=exercice_id)

        consigne.save()
        messages.success(request, 'Configuration du dépôt de fichier enregistrée.')
        return redirect('depot_fichier_configurer', exercice_id=exercice_id)

    context = {
        'exercice': exercice,
        'consigne': consigne,
    }
    return render(request, 'website/exercice/depot_fichier/configurer.html', context)


# ─────────────────────────────────────────────────────────────────────
# 2. PASSER (vue étudiant)
# ─────────────────────────────────────────────────────────────────────
@login_required
def depot_fichier_passer(request, exercice_id):
    from .models import Exercice, ConsigneDepotFichier, SoumissionExercice, FichierDepose

    exercice = get_object_or_404(Exercice, id=exercice_id)
    consigne = getattr(exercice, 'depot_fichier', None)

    if not exercice.est_lance:
        messages.error(request, 'Cet exercice n\'est pas encore disponible.')
        return redirect('dashboard')
    if not consigne:
        messages.error(request, 'Cet exercice n\'a pas encore été configuré.')
        return redirect('dashboard')

    nb_tentatives = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='termine'
    ).count()
    if exercice.nb_tentatives_max > 0 and nb_tentatives >= exercice.nb_tentatives_max:
        messages.error(request, 'Nombre maximum de tentatives atteint.')
        return redirect('depot_fichier_resultat', exercice_id=exercice_id)

    soumission, created = SoumissionExercice.objects.get_or_create(
        exercice=exercice, etudiant=request.user, status='en_cours',
        defaults={'nb_tentative': nb_tentatives + 1}
    )

    # Récupérer les fichiers déjà déposés
    fichiers_existants = FichierDepose.objects.filter(soumission=soumission)

    temps_restant = exercice.duree
    if not created and soumission.date_debut:
        elapsed = (timezone.now() - soumission.date_debut).total_seconds() / 60
        temps_restant = max(0, exercice.duree - int(elapsed))

    context = {
        'exercice': exercice,
        'consigne': consigne,
        'soumission': soumission,
        'temps_restant': temps_restant,
        'fichiers_existants': fichiers_existants,
    }
    return render(request, 'website/exercice/depot_fichier/passer.html', context)


# ─────────────────────────────────────────────────────────────────────
# 3. SOUMETTRE
# ─────────────────────────────────────────────────────────────────────
@login_required
def depot_fichier_soumettre(request, exercice_id):
    from .models import Exercice, SoumissionExercice, FichierDepose, SauvegardeQCM
    import os

    if request.method != 'POST':
        return redirect('depot_fichier_passer', exercice_id=exercice_id)

    exercice = get_object_or_404(Exercice, id=exercice_id)
    soumission = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='en_cours'
    ).first()

    if not soumission:
        messages.error(request, 'Aucune session en cours.')
        return redirect('dashboard')

    # Récupérer les fichiers envoyés
    fichiers = request.FILES.getlist('fichiers')
    if not fichiers:
        messages.error(request, 'Veuillez déposer au moins un fichier.')
        return redirect('depot_fichier_passer', exercice_id=exercice_id)

    consigne = getattr(exercice, 'depot_fichier', None)
    if consigne:
        # Vérifier le nombre max
        if len(fichiers) > consigne.nb_fichiers_max:
            messages.error(request, f'Maximum {consigne.nb_fichiers_max} fichier(s) autorisé(s).')
            return redirect('depot_fichier_passer', exercice_id=exercice_id)

        # Vérifier les extensions
        extensions_autorisees = consigne.liste_extensions
        for fichier in fichiers:
            ext = fichier.name.split('.')[-1].lower()
            if ext not in extensions_autorisees:
                messages.error(request, f'Extension .{ext} non autorisée.')
                return redirect('depot_fichier_passer', exercice_id=exercice_id)

            # Vérifier la taille
            if fichier.size > consigne.taille_max_mo * 1024 * 1024:
                messages.error(request, f'Le fichier {fichier.name} dépasse la taille maximale.')
                return redirect('depot_fichier_passer', exercice_id=exercice_id)

    # Sauvegarder les fichiers
    for fichier in fichiers:
        FichierDepose.objects.create(
            soumission=soumission,
            fichier=fichier,
            nom_original=fichier.name,
            taille=fichier.size
        )

    soumission.status = 'termine'
    soumission.date_soumission = timezone.now()
    soumission.note = None  # Correction manuelle
    soumission.note_sur = exercice.points
    soumission.save(update_fields=['status', 'date_soumission', 'note', 'note_sur'])

    SauvegardeQCM.objects.filter(etudiant=request.user, exercice=exercice).delete()

    messages.success(request, 'Fichier(s) déposé(s) avec succès.')
    return redirect('depot_fichier_resultat', exercice_id=exercice_id)


# ─────────────────────────────────────────────────────────────────────
# 4. RÉSULTAT (étudiant)
# ─────────────────────────────────────────────────────────────────────
@login_required
def depot_fichier_resultat(request, exercice_id):
    from .models import Exercice, SoumissionExercice, FichierDepose, CorrectionDepotFichier

    exercice = get_object_or_404(Exercice, id=exercice_id)

    soumission = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='termine'
    ).order_by('-date_soumission').first()

    if not soumission:
        messages.warning(request, 'Vous n\'avez pas encore soumis de fichier.')
        return redirect('depot_fichier_passer', exercice_id=exercice_id)

    fichiers = FichierDepose.objects.filter(soumission=soumission)
    correction = getattr(soumission, 'correction_depot', None)

    context = {
        'exercice': exercice,
        'soumission': soumission,
        'fichiers': fichiers,
        'correction': correction,
    }
    return render(request, 'website/exercice/depot_fichier/resultat.html', context)


# ─────────────────────────────────────────────────────────────────────
# 5. LISTE DES DÉPÔTS À CORRIGER (enseignant)
# ─────────────────────────────────────────────────────────────────────
@login_required
def depot_fichier_liste_a_corriger(request, exercice_id):
    from .models import Exercice, SoumissionExercice

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    soumissions = SoumissionExercice.objects.filter(
        exercice=exercice, status='termine'
    ).select_related('etudiant', 'correction_depot').order_by('date_soumission')

    a_corriger = [s for s in soumissions if not (hasattr(s, 'correction_depot') and s.correction_depot.est_corrigee)]
    corriges = [s for s in soumissions if hasattr(s, 'correction_depot') and s.correction_depot.est_corrigee]

    context = {
        'exercice': exercice,
        'a_corriger': a_corriger,
        'corriges': corriges,
        'nb_total': soumissions.count(),
    }
    return render(request, 'website/exercice/depot_fichier/liste_a_corriger.html', context)


# ─────────────────────────────────────────────────────────────────────
# 6. CORRIGER UN DÉPÔT (enseignant)
# ─────────────────────────────────────────────────────────────────────
@login_required
def depot_fichier_corriger(request, soumission_id):
    from .models import SoumissionExercice, CorrectionDepotFichier

    soumission = get_object_or_404(SoumissionExercice, id=soumission_id, status='termine')
    exercice = soumission.exercice

    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    correction, _ = CorrectionDepotFichier.objects.get_or_create(soumission=soumission)

    if request.method == 'POST':
        try:
            note = float(request.POST.get('note_donnee', 0))
        except ValueError:
            note = 0

        correction.note_donnee = note
        correction.commentaire = request.POST.get('commentaire', '').strip()
        correction.corrige_par = request.user
        correction.date_correction = timezone.now()

        if 'fichier_annote' in request.FILES:
            correction.fichier_annote = request.FILES['fichier_annote']

        correction.save()

        soumission.note = note
        soumission.save(update_fields=['note'])

        messages.success(request, f'Dépôt de {soumission.etudiant.username} corrigé.')
        return redirect('depot_fichier_liste_a_corriger', exercice_id=exercice.id)

    context = {
        'exercice': exercice,
        'soumission': soumission,
        'correction': correction,
    }
    return render(request, 'website/exercice/depot_fichier/corriger.html', context)


# ─────────────────────────────────────────────────────────────────────
# 7. TABLEAU DE BORD ENSEIGNANT
# ─────────────────────────────────────────────────────────────────────
@login_required
def depot_fichier_tableau_resultats(request, exercice_id):
    from .models import Exercice, SoumissionExercice
    from django.db.models import Avg, Count

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    soumissions = SoumissionExercice.objects.filter(
        exercice=exercice, status='termine'
    ).select_related('etudiant', 'correction_depot').order_by('-note')

    notees = soumissions.exclude(note__isnull=True)
    stats = notees.aggregate(moyenne=Avg('note'), nb_total=Count('id'))

    context = {
        'exercice': exercice,
        'soumissions': soumissions,
        'stats': stats,
        'nb_corriges': notees.count(),
        'nb_en_attente': soumissions.filter(note__isnull=True).count(),
        'nb_etudiants': soumissions.count(),
    }
    return render(request, 'website/exercice/depot_fichier/tableau_resultats.html', context)

# =====================================================================
# website/views.py — VUES ÉTUDE DE CAS
# =====================================================================

# ─────────────────────────────────────────────────────────────────────
# 1. CONFIGURER (enseignant)
# ─────────────────────────────────────────────────────────────────────
@login_required
def etude_cas_configurer(request, exercice_id):
    from .models import Exercice, EtudeCas, SousQuestionEtudeCas

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    etude_cas, _ = EtudeCas.objects.get_or_create(exercice=exercice)

    # Traiter le formulaire du contexte
    if request.method == 'POST' and 'save_contexte' in request.POST:
        contexte = request.POST.get('contexte', '').strip()
        if not contexte:
            messages.error(request, 'Le contexte est obligatoire.')
            return redirect('etude_cas_configurer', exercice_id=exercice_id)

        etude_cas.contexte = contexte
        if 'document_cas' in request.FILES:
            etude_cas.document_cas = request.FILES['document_cas']
        if 'image_cas' in request.FILES:
            etude_cas.image_cas = request.FILES['image_cas']
        etude_cas.save()
        messages.success(request, 'Contexte enregistré.')
        return redirect('etude_cas_configurer', exercice_id=exercice_id)

    sous_questions = etude_cas.sous_questions.all().order_by('ordre')

    context = {
        'exercice': exercice,
        'etude_cas': etude_cas,
        'sous_questions': sous_questions,
    }
    return render(request, 'website/exercice/etude_cas/configurer.html', context)


# ─────────────────────────────────────────────────────────────────────
# 2. AJAX — Ajouter une sous-question
# ─────────────────────────────────────────────────────────────────────
@login_required
def etude_cas_sous_question_ajouter(request, exercice_id):
    from .models import Exercice, EtudeCas, SousQuestionEtudeCas, ChoixSousQuestionEtudeCas

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    etude_cas = getattr(exercice, 'etude_cas', None)
    if not etude_cas:
        etude_cas = EtudeCas.objects.create(exercice=exercice, contexte='')

    try:
        data = json.loads(request.body)
        texte = data.get('texte', '').strip()
        type_question = data.get('type', 'texte_libre')
        points = int(data.get('points', 2))

        if not texte:
            return JsonResponse({'error': 'Texte requis'}, status=400)

        ordre = etude_cas.sous_questions.count() + 1
        sq = SousQuestionEtudeCas.objects.create(
            etude_cas=etude_cas,
            texte=texte,
            type_question=type_question,
            ordre=ordre,
            points=points,
        )

        # Si QCM, ajouter les choix
        if type_question == 'qcm':
            choix = data.get('choix', [])
            corrects = data.get('corrects', [0])
            for i, txt in enumerate(choix):
                if txt.strip():
                    ChoixSousQuestionEtudeCas.objects.create(
                        sous_question=sq,
                        texte=txt.strip(),
                        est_correct=(i in corrects),
                        ordre=i,
                    )

        # Mettre à jour le total de points
        exercice.points = sum(q.points for q in etude_cas.sous_questions.all())
        exercice.save(update_fields=['points'])

        return JsonResponse({'success': True, 'sq_id': sq.id})
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)
# ─────────────────────────────────────────────────────────────────────
# 3. AJAX — Modifier une sous-question
# ─────────────────────────────────────────────────────────────────────
@login_required
def etude_cas_sous_question_modifier(request, sous_question_id):
    from .models import SousQuestionEtudeCas, ChoixSousQuestionEtudeCas

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    sq = get_object_or_404(SousQuestionEtudeCas, id=sous_question_id)
    if not _check_enseignant(request):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    try:
        data = json.loads(request.body)
        sq.texte = data.get('texte', sq.texte).strip()
        sq.type_question = data.get('type', sq.type_question)
        sq.points = int(data.get('points', sq.points))
        sq.save()

        # Si QCM, mettre à jour les choix
        if sq.type_question == 'qcm' and 'choix' in data:
            sq.choix.all().delete()
            choix = data.get('choix', [])
            corrects = data.get('corrects', [0])
            for i, txt in enumerate(choix):
                if txt.strip():
                    ChoixSousQuestionEtudeCas.objects.create(
                        sous_question=sq,
                        texte=txt.strip(),
                        est_correct=(i in corrects),
                        ordre=i,
                    )

        # Mettre à jour le total de points
        exercice = sq.etude_cas.exercice
        exercice.points = sum(q.points for q in sq.etude_cas.sous_questions.all())
        exercice.save(update_fields=['points'])

        return JsonResponse({'success': True})
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)


# ─────────────────────────────────────────────────────────────────────
# 4. AJAX — Supprimer une sous-question
# ─────────────────────────────────────────────────────────────────────
@login_required
def etude_cas_sous_question_supprimer(request, exercice_id, sous_question_id):
    from .models import Exercice, SousQuestionEtudeCas

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    exercice = get_object_or_404(Exercice, id=exercice_id)
    sq = get_object_or_404(SousQuestionEtudeCas, id=sous_question_id, etude_cas__exercice=exercice)

    if not _check_enseignant(request):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    sq.delete()

    # Réordonner
    for i, q in enumerate(exercice.etude_cas.sous_questions.order_by('ordre'), 1):
        if q.ordre != i:
            SousQuestionEtudeCas.objects.filter(pk=q.pk).update(ordre=i)

    exercice.points = sum(q.points for q in exercice.etude_cas.sous_questions.all())
    exercice.save(update_fields=['points'])

    return JsonResponse({'success': True, 'nb_questions': exercice.etude_cas.sous_questions.count()})


# ─────────────────────────────────────────────────────────────────────
# 5. PASSER (vue étudiant)
# ─────────────────────────────────────────────────────────────────────
@login_required
def etude_cas_passer(request, exercice_id):
    from .models import Exercice, EtudeCas, SoumissionExercice, SauvegardeQCM

    exercice = get_object_or_404(Exercice, id=exercice_id)
    etude_cas = getattr(exercice, 'etude_cas', None)

    if not exercice.est_lance:
        messages.error(request, 'Cet exercice n\'est pas encore disponible.')
        return redirect('dashboard')
    if not etude_cas or not etude_cas.contexte:
        messages.error(request, 'Cet exercice n\'a pas encore été configuré.')
        return redirect('dashboard')

    nb_tentatives = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='termine'
    ).count()
    if exercice.nb_tentatives_max > 0 and nb_tentatives >= exercice.nb_tentatives_max:
        messages.error(request, 'Nombre maximum de tentatives atteint.')
        return redirect('etude_cas_resultat', exercice_id=exercice_id)

    soumission, created = SoumissionExercice.objects.get_or_create(
        exercice=exercice, etudiant=request.user, status='en_cours',
        defaults={'nb_tentative': nb_tentatives + 1}
    )

    sauvegarde_data = {}
    try:
        sauvegarde = SauvegardeQCM.objects.get(etudiant=request.user, exercice=exercice)
        sauvegarde_data = sauvegarde.donnees_json
    except SauvegardeQCM.DoesNotExist:
        pass

    sous_questions = etude_cas.sous_questions.all().order_by('ordre')

    temps_restant = exercice.duree
    if not created and soumission.date_debut:
        elapsed = (timezone.now() - soumission.date_debut).total_seconds() / 60
        temps_restant = max(0, exercice.duree - int(elapsed))

    context = {
        'exercice': exercice,
        'etude_cas': etude_cas,
        'sous_questions': sous_questions,
        'soumission': soumission,
        'temps_restant': temps_restant,
        'sauvegarde': json.dumps(sauvegarde_data),
    }
    return render(request, 'website/exercice/etude_cas/passer.html', context)


# ─────────────────────────────────────────────────────────────────────
# 6. SOUMETTRE
# ─────────────────────────────────────────────────────────────────────
@login_required
def etude_cas_soumettre(request, exercice_id):
    from .models import Exercice, SoumissionExercice, ReponseSousQuestionEtudeCas, ChoixSousQuestionEtudeCas, SauvegardeQCM

    if request.method != 'POST':
        return redirect('etude_cas_passer', exercice_id=exercice_id)

    exercice = get_object_or_404(Exercice, id=exercice_id)
    soumission = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='en_cours'
    ).first()

    if not soumission:
        messages.error(request, 'Aucune session en cours.')
        return redirect('dashboard')

    total_points = 0
    points_obtenus = 0

    for sq in exercice.etude_cas.sous_questions.all():
        total_points += sq.points

        if sq.type_question == 'qcm':
            choix_id = request.POST.get(f'sq_{sq.id}')
            if choix_id:
                try:
                    choix = ChoixSousQuestionEtudeCas.objects.get(id=choix_id, sous_question=sq)
                    est_correcte = choix.est_correct
                    points = sq.points if est_correcte else 0
                except ChoixSousQuestionEtudeCas.DoesNotExist:
                    est_correcte = False
                    points = 0
                    choix = None
            else:
                est_correcte = False
                points = 0
                choix = None

            ReponseSousQuestionEtudeCas.objects.update_or_create(
                soumission=soumission,
                sous_question=sq,
                defaults={
                    'choix_selectionne': choix,
                    'est_correcte': est_correcte,
                    'points_obtenus': points,
                }
            )
            if est_correcte:
                points_obtenus += points

        else:  # texte_libre
            texte = request.POST.get(f'sq_{sq.id}_texte', '').strip()
            ReponseSousQuestionEtudeCas.objects.update_or_create(
                soumission=soumission,
                sous_question=sq,
                defaults={
                    'reponse_texte': texte,
                    'est_correcte': False,  # correction manuelle
                    'points_obtenus': 0,
                }
            )

    soumission.status = 'termine'
    soumission.date_soumission = timezone.now()
    soumission.note = round(points_obtenus, 2) if points_obtenus > 0 else None
    soumission.note_sur = total_points
    soumission.save(update_fields=['status', 'date_soumission', 'note', 'note_sur'])

    SauvegardeQCM.objects.filter(etudiant=request.user, exercice=exercice).delete()

    messages.success(request, 'Étude de cas soumise avec succès !')
    return redirect('etude_cas_resultat', exercice_id=exercice_id)
# ─────────────────────────────────────────────────────────────────────
# 7. RÉSULTAT (étudiant)
# ─────────────────────────────────────────────────────────────────────
@login_required
def etude_cas_resultat(request, exercice_id):
    from .models import Exercice, SoumissionExercice, ReponseSousQuestionEtudeCas

    exercice = get_object_or_404(Exercice, id=exercice_id)

    soumission = SoumissionExercice.objects.filter(
        exercice=exercice, etudiant=request.user, status='termine'
    ).order_by('-date_soumission').first()

    if not soumission:
        messages.warning(request, 'Vous n\'avez pas encore soumis cet exercice.')
        return redirect('etude_cas_passer', exercice_id=exercice_id)

    reponses = ReponseSousQuestionEtudeCas.objects.filter(
        soumission=soumission
    ).select_related('sous_question', 'choix_selectionne').order_by('sous_question__ordre')

    context = {
        'exercice': exercice,
        'soumission': soumission,
        'reponses': reponses,
        'afficher_correction': exercice.correction_publiee or exercice.afficher_correction_immediate,
        'afficher_note': exercice.resultats_publies or exercice.afficher_note_immediate,
    }
    return render(request, 'website/exercice/etude_cas/resultat.html', context)
# ─────────────────────────────────────────────────────────────────────
# 8. TABLEAU DE BORD ENSEIGNANT
# ─────────────────────────────────────────────────────────────────────
@login_required
def etude_cas_tableau_resultats(request, exercice_id):
    from .models import Exercice, SoumissionExercice, ReponseSousQuestionEtudeCas
    from django.db.models import Avg, Count

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not _check_enseignant(request):
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')

    soumissions = SoumissionExercice.objects.filter(
        exercice=exercice, status='termine'
    ).select_related('etudiant').order_by('-note')

    stats = soumissions.aggregate(moyenne=Avg('note'), nb_total=Count('id'))

    sous_questions_stats = []
    for sq in exercice.etude_cas.sous_questions.order_by('ordre'):
        nb_correct = ReponseSousQuestionEtudeCas.objects.filter(
            sous_question=sq, soumission__status='termine', est_correcte=True
        ).count()
        nb_total = soumissions.count()
        sous_questions_stats.append({
            'sous_question': sq,
            'nb_correct': nb_correct,
            'nb_total': nb_total,
            'pct': round(nb_correct / nb_total * 100) if nb_total else 0,
        })

    context = {
        'exercice': exercice,
        'soumissions': soumissions,
        'stats': stats,
        'sous_questions_stats': sous_questions_stats,
        'nb_etudiants': soumissions.count(),
    }
    return render(request, 'website/exercice/etude_cas/tableau_resultats.html', context)

@login_required
def seance_correction_config(request, seance_id):
    """Configurer une séance de correction (enseignant)."""
    from .models import SeanceBase, SeanceCorrection

    seance = get_object_or_404(SeanceBase, id=seance_id, type_seance=SeanceBase.TYPE_CORRECTION)

    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits.')
        return redirect('dashboard')

    correction, _ = SeanceCorrection.objects.get_or_create(seance=seance)

    # Séances candidates à corriger (intégration/devoirs du même cours)
    seances_a_corriger = SeanceBase.objects.filter(
        cours=seance.cours,
        type_seance__in=[SeanceBase.TYPE_INTEGRATION]
    ).exclude(id=seance.id).order_by('-date_creation')

    if request.method == 'POST':
        seance_corrigee_id = request.POST.get('seance_corrigee_id')
        correction.seance_corrigee_id = seance_corrigee_id or None
        correction.corrige_texte      = request.POST.get('corrige_texte', '').strip()
        correction.corrige_video_url  = request.POST.get('corrige_video_url', '').strip()
        correction.points_cles        = request.POST.get('points_cles', '').strip()

        if 'corrige_fichier' in request.FILES:
            correction.corrige_fichier = request.FILES['corrige_fichier']

        correction.save()
        messages.success(request, 'Configuration de la correction enregistrée.')
        return redirect('seance_correction_config', seance_id=seance.id)

    context = {
        'seance':              seance,
        'correction':          correction,
        'seances_a_corriger':  seances_a_corriger,
    }
    return render(request, 'website/seance/correction_config.html', context)


# ─────────────────────────────────────────────────────────────────────
# AJOUTÉ : publier la correction (la rendre visible aux étudiants)
# ─────────────────────────────────────────────────────────────────────
@login_required
def seance_correction_publier(request, seance_id):
    from .models import SeanceBase, SeanceCorrection

    seance = get_object_or_404(SeanceBase, id=seance_id, type_seance=SeanceBase.TYPE_CORRECTION)

    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits.')
        return redirect('dashboard')

    correction = getattr(seance, 'correction', None)
    if not correction:
        messages.error(request, 'Aucune correction configurée.')
        return redirect('seance_correction_config', seance_id=seance.id)

    if not correction.a_du_contenu:
        messages.error(request, 'Ajoutez du contenu (texte, fichier ou vidéo) avant de publier.')
        return redirect('seance_correction_config', seance_id=seance.id)

    correction.publier()
    messages.success(request, 'Correction publiée — visible par les étudiants.')
    return redirect('seance_detail', seance_id=seance.id)

@login_required
def seance_correction_depublier(request, seance_id):
    from .models import SeanceBase

    seance = get_object_or_404(SeanceBase, id=seance_id, type_seance=SeanceBase.TYPE_CORRECTION)

    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits.')
        return redirect('dashboard')

    correction = getattr(seance, 'correction', None)
    if correction:
        correction.publie = False
        correction.save(update_fields=['publie'])
        messages.info(request, 'Correction masquée aux étudiants.')

    return redirect('seance_correction_config', seance_id=seance.id)

@login_required
def seance_correction_supprimer_fichier(request, seance_id):
    from .models import SeanceBase

    seance = get_object_or_404(SeanceBase, id=seance_id, type_seance=SeanceBase.TYPE_CORRECTION)

    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits.')
        return redirect('dashboard')

    correction = getattr(seance, 'correction', None)
    if correction and correction.corrige_fichier:
        correction.corrige_fichier.delete(save=False)
        correction.corrige_fichier = None
        correction.save(update_fields=['corrige_fichier'])
        messages.success(request, 'Fichier de correction supprimé.')

    return redirect('seance_correction_config', seance_id=seance.id)

@login_required
def seance_visio_ajouter_enregistrement(request, seance_id):
    from .models import SeanceBase

    seance = get_object_or_404(SeanceBase, id=seance_id, type_seance=SeanceBase.TYPE_VISIO)

    if request.user.role not in ['enseignant', 'admin_ecole', 'super_admin']:
        messages.error(request, 'Vous n\'avez pas les droits.')
        return redirect('dashboard')

    visio = getattr(seance, 'visio', None)
    if not visio:
        messages.error(request, 'Aucune configuration de visio trouvée.')
        return redirect('seance_detail', seance_id=seance.id)

    if request.method == 'POST':
        url = request.POST.get('enregistrement_url', '').strip()
        if url:
            from datetime import timedelta
            visio.enregistrement_url = url
            visio.enregistrement_disponible_jusqua = timezone.now() + timedelta(days=30)
            visio.save(update_fields=['enregistrement_url', 'enregistrement_disponible_jusqua'])
            messages.success(request, 'Enregistrement ajouté — disponible 30 jours.')
        else:
            messages.error(request, 'URL invalide.')

    return redirect('seance_detail', seance_id=seance.id)

@login_required
def integration_marquer_vu(request, exercice_id):
    from .models import Exercice, ProgressionEtudiantSeance

    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    exercice = get_object_or_404(Exercice, id=exercice_id)
    if not exercice.seance:
        return JsonResponse({'error': 'Exercice non rattaché à une séance'}, status=400)

    progression, _ = ProgressionEtudiantSeance.objects.get_or_create(
        seance=exercice.seance, etudiant=request.user
    )
    if not progression.vu:
        progression.vu      = True
        progression.date_vu = timezone.now()
        progression.save(update_fields=['vu', 'date_vu'])

    return JsonResponse({'success': True})
@login_required
def admin_ecole_parametres(request):
    """Page des paramètres pour l'admin_ecole"""
    if request.user.role != 'admin_ecole':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    ecole = request.user.ecole_admin
    if not ecole:
        messages.error(request, 'Aucune école associée à votre compte.')
        return redirect('dashboard')
    
    return render(request, 'website/admin_ecole/parametres.html', {
        'ecole': ecole,
    })


@login_required
def devenir_formateur(request):
    """Page pour devenir formateur"""
    config = ParametresDemandesFormateur.get_config()
    
    # Vérifier si l'utilisateur est déjà enseignant
    if request.user.role == 'enseignant':
        messages.info(request, 'Vous êtes déjà formateur sur Academia Net.')
        return redirect('dashboard')
    
    # Récupérer la dernière demande de l'utilisateur
    derniere_demande = DemandeFormateur.objects.filter(
        utilisateur=request.user
    ).order_by('-date_demande').first()
    
    if request.method == 'POST':
        if not config.demandes_actives:
            messages.error(request, 'Les demandes de formateur sont actuellement désactivées.')
            return redirect('devenir_formateur')
        
        form = DemandeFormateurForm(request.POST, request.FILES)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.utilisateur = request.user
            demande.save()
            
            # Envoyer un email à l'équipe technique
            # (à implémenter)
            
            messages.success(request, 'Votre demande a été envoyée avec succès. Elle sera examinée par notre équipe technique.')
            return redirect('mes_demandes')
    else:
        form = DemandeFormateurForm()
    
    # Statistiques des demandes
    statut = 'aucune'
    if derniere_demande:
        statut = derniere_demande.statut
    
    context = {
        'form': form,
        'config': config,
        'derniere_demande': derniere_demande,
        'statut': statut,
    }
    return render(request, 'website/gestion/devenir_formateur.html', context)


@login_required
def creer_ecole(request):
    """Page pour créer une école"""
    config = ParametresDemandesFormateur.get_config()
    whatsapp_url = f"https://wa.me/{config.whatsapp_number}"
    whatsapp_message = "Bonjour%2C%20je%20souhaite%20cr%C3%A9er%20une%20%C3%A9cole%20sur%20Academia%20Net."
    
    context = {
        'config': config,
        'whatsapp_url': whatsapp_url + '?text=' + whatsapp_message,
        'whatsapp_number': config.whatsapp_number,
    }
    return render(request, 'website/gestion/creer_ecole.html', context)


@login_required
def mes_demandes(request):
    """Page des demandes de l'utilisateur"""
    demandes_formateur = DemandeFormateur.objects.filter(
        utilisateur=request.user
    ).order_by('-date_demande')
    
    context = {
        'demandes_formateur': demandes_formateur,
    }
    return render(request, 'website/gestion/mes_demandes.html', context)


# ============================================
# VUES - ADMIN (Équipe technique)
# ============================================

from django.contrib.admin.views.decorators import staff_member_required

@login_required
def admin_demandes_formateur(request):
    """Liste des demandes formateur pour l'équipe technique"""
    if request.user.role != 'super_admin':
        messages.error(request, 'Accès réservé à l\'équipe technique.')
        return redirect('dashboard')
    
    demandes = DemandeFormateur.objects.all().order_by('-date_demande')
    
    # Compter les demandes par statut
    nb_en_attente = demandes.filter(statut='en_attente').count()
    nb_validees = demandes.filter(statut='valide').count()
    nb_refusees = demandes.filter(statut='refuse').count()
    
    context = {
        'demandes': demandes,
        'nb_en_attente': nb_en_attente,
        'nb_validees': nb_validees,
        'nb_refusees': nb_refusees,
    }
    return render(request, 'website/super_admin/demandes_formateur.html', context)


@login_required
def admin_demande_formateur_action(request, demande_id, action):
    """Accepter ou refuser une demande formateur"""
    if request.user.role != 'super_admin':
        messages.error(request, 'Accès réservé à l\'équipe technique.')
        return redirect('dashboard')
    
    demande = get_object_or_404(DemandeFormateur, id=demande_id)
    config = ParametresDemandesFormateur.get_config()
    
    if action == 'accepter':
        demande.accepter(request.user)
        messages.success(request, f'Demande de {demande.utilisateur.username} acceptée.')
        
        # Envoyer un email d'acceptation
        sujet = '✅ Demande acceptée - Academia Net'
        message = f"""
Bonjour {demande.utilisateur.prenom or demande.utilisateur.username},

{config.message_acceptation}

Pour activer votre rôle d'enseignant :
1. Déconnectez-vous de votre compte
2. Reconnectez-vous

Si le rôle ne s'affiche pas, contactez l'équipe technique.

Cordialement,
L'équipe Academia Net
"""
        send_mail(sujet, message, settings.DEFAULT_FROM_EMAIL, [demande.utilisateur.email])
        
    elif action == 'refuser':
        if request.method == 'POST':
            commentaire = request.POST.get('commentaire', '')
            if not commentaire:
                messages.error(request, 'Veuillez fournir un motif de refus.')
                return redirect('admin_demandes_formateur')
            
            demande.refuser(request.user, commentaire)
            messages.success(request, f'Demande de {demande.utilisateur.username} refusée.')
            
            # Envoyer un email de refus
            sujet = '❌ Demande refusée - Academia Net'
            message = f"""
Bonjour {demande.utilisateur.prenom or demande.utilisateur.username},

{config.message_refus}

Motif : {commentaire}

Cordialement,
L'équipe Academia Net
"""
            send_mail(sujet, message, settings.DEFAULT_FROM_EMAIL, [demande.utilisateur.email])
            
            return redirect('admin_demandes_formateur')
        
        # Afficher le formulaire de refus
        context = {
            'demande': demande,
            'config': config,
        }
        return render(request, 'website/super_admin/refuser_demande.html', context)
    
    return redirect('admin_demandes_formateur')


@login_required
def admin_demande_formateur_voir(request, demande_id):
    """Voir les détails d'une demande"""
    if request.user.role != 'super_admin':
        messages.error(request, 'Accès réservé à l\'équipe technique.')
        return redirect('dashboard')
    
    demande = get_object_or_404(DemandeFormateur, id=demande_id)
    
    context = {
        'demande': demande,
    }
    return render(request, 'website/super_admin/voir_demande.html', context)
