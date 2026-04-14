from django.urls import path
from . import views

urlpatterns = [
    # Pages publiques
    path('', views.accueil, name='accueil'),
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('mot-de-passe-oublie/', views.mot_de_passe_oublie, name='mot_de_passe_oublie'),
    path('reinitialisation/<str:token>/', views.reinitialisation_mot_de_passe, name='reinitialisation_mot_de_passe'),
    
    # Dashboard général
    path('dashboard/', views.dashboard, name='dashboard'),
    
    
    # Messages
    path('messages/', views.messages_liste, name='messages_liste'),
    path('messages/envoyer/', views.message_envoyer, name='message_envoyer'),
    path('messages/conv/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    
    # Super Admin - Écoles
    path('super-admin/ecoles/', views.super_admin_ecole_liste, name='super_admin_ecole_liste'),
    path('super-admin/ecoles/creer/', views.super_admin_ecole_creer, name='super_admin_ecole_creer'),
    path('super-admin/ecoles/<int:ecole_id>/modifier/', views.super_admin_ecole_modifier, name='super_admin_ecole_modifier'),
    
    # Super Admin - Abonnements
    path('super-admin/abonnements/', views.super_admin_abonnement_liste, name='super_admin_abonnement_liste'),
    path('super-admin/abonnements/creer/', views.super_admin_abonnement_creer, name='super_admin_abonnement_creer'),
    
    # Admin École - Filières
    path('admin-ecole/filieres/', views.admin_ecole_filiere_liste, name='admin_ecole_filiere_liste'),
    path('admin-ecole/ecole/<int:ecole_id>/filieres/creer/', views.admin_ecole_filiere_creer, name='admin_ecole_filiere_creer'),
    
    # Admin École - Spécialités
    path('admin-ecole/filiere/<int:filiere_id>/specialites/', views.admin_ecole_specialite_liste, name='admin_ecole_specialite_liste'),
    path('admin-ecole/filiere/<int:filiere_id>/specialites/creer/', views.admin_ecole_specialite_creer, name='admin_ecole_specialite_creer'),
    
    # Étudiant - Inscription avec clé
    path('etudiant/inscription-cle/', views.etudiant_inscription_cle, name='etudiant_inscription_cle'),
    
    # ==================== COURS ====================
    path('cours/creer/', views.cours_creer, name='cours_creer'),
   
    
    path('cours/<int:cours_id>/seance/ajouter/', views.seance_ajouter, name='seance_ajouter'),
    path('seance/<int:seance_id>/', views.seance_detail, name='seance_detail'),
    path('seance/<int:seance_id>/terminer/', views.seance_terminer, name='seance_terminer'),

# ==================== DEVOIRS ====================
    path('devoir/creer/<int:specialite_id>/', views.devoir_creer, name='devoir_creer'),
    path('devoir/<int:devoir_id>/', views.devoir_detail, name='devoir_detail'),
    path('devoir/<int:devoir_id>/soumettre/', views.devoir_soumettre, name='devoir_soumettre'),
    path('devoir/<int:devoir_id>/corriger/<int:soumission_id>/', views.devoir_corriger, name='devoir_corriger'),
    path('enseignant/cours/', views.enseignant_cours_liste, name='enseignant_cours_liste'),
    path('super-admin/utilisateurs/', views.super_admin_utilisateurs, name='super_admin_utilisateurs'),
    path('super-admin/utilisateur/<int:user_id>/modifier/', views.super_admin_utilisateur_modifier, name='super_admin_utilisateur_modifier'),
    path('super-admin/utilisateur/<int:user_id>/supprimer/', views.super_admin_utilisateur_supprimer, name='super_admin_utilisateur_supprimer'),
    
    path('super-admin/utilisateur/<int:user_id>/changer-role/<str:nouveau_role>/', views.super_admin_changer_role, name='super_admin_changer_role'),
    # Super Admin - Abonnements
path('super-admin/abonnements/', views.super_admin_abonnement_liste, name='super_admin_abonnement_liste'),
path('super-admin/abonnements/creer/', views.super_admin_abonnement_creer, name='super_admin_abonnement_creer'),
path('super-admin/abonnements/<int:abonnement_id>/modifier/', views.super_admin_abonnement_modifier, name='super_admin_abonnement_modifier'),
path('super-admin/abonnements/<int:abonnement_id>/supprimer/', views.super_admin_abonnement_supprimer, name='super_admin_abonnement_supprimer'),
path('ecoles/', views.ecoles_liste, name='ecoles_liste'),
path('ecole/<slug:slug>/', views.ecole_detail, name='ecole_detail'),

# Admin École - Gestion de l'école
path('admin-ecole/modifier/', views.admin_ecole_modifier, name='admin_ecole_modifier'),
path('admin-ecole/changer-logo/', views.admin_ecole_changer_logo, name='admin_ecole_changer_logo'),
path('admin-ecole/galerie/', views.admin_ecole_galerie, name='admin_ecole_galerie'),
path('admin-ecole/galerie/ajouter/', views.admin_ecole_galerie_ajouter, name='admin_ecole_galerie_ajouter'),
path('admin-ecole/galerie/supprimer/<int:image_id>/', views.admin_ecole_galerie_supprimer, name='admin_ecole_galerie_supprimer'),

# Admin École - Gestion des utilisateurs
path('admin-ecole/utilisateurs/', views.admin_ecole_utilisateurs, name='admin_ecole_utilisateurs'),
path('admin-ecole/generer-cle/', views.admin_ecole_generer_cle, name='admin_ecole_generer_cle'),
path('admin-ecole/utilisateur/<int:user_id>/modifier/', views.admin_ecole_utilisateur_modifier, name='admin_ecole_utilisateur_modifier'),
path('admin-ecole/utilisateur/<int:user_id>/supprimer/', views.admin_ecole_utilisateur_supprimer, name='admin_ecole_utilisateur_supprimer'),

# Super Admin - Gestion détaillée des écoles
path('super-admin/ecole/<int:ecole_id>/', views.super_admin_ecole_detail, name='super_admin_ecole_detail'),
path('super-admin/ecole/<int:ecole_id>/changer-logo/', views.super_admin_ecole_changer_logo, name='super_admin_ecole_changer_logo'),
path('super-admin/ecole/<int:ecole_id>/galerie/', views.super_admin_ecole_galerie, name='super_admin_ecole_galerie'),
path('super-admin/ecole/<int:ecole_id>/galerie/ajouter/', views.super_admin_ecole_galerie_ajouter, name='super_admin_ecole_galerie_ajouter'),
path('super-admin/ecole/<int:ecole_id>/galerie/supprimer/<int:image_id>/', views.super_admin_ecole_galerie_supprimer, name='super_admin_ecole_galerie_supprimer'),
path('super-admin/ecole/<int:ecole_id>/utilisateurs/', views.super_admin_ecole_utilisateurs, name='super_admin_ecole_utilisateurs'),
path('super-admin/ecole/<int:ecole_id>/utilisateur/<int:user_id>/modifier/', views.super_admin_ecole_utilisateur_modifier, name='super_admin_ecole_utilisateur_modifier'),
path('super-admin/ecole/<int:ecole_id>/utilisateur/<int:user_id>/supprimer/', views.super_admin_ecole_utilisateur_supprimer, name='super_admin_ecole_utilisateur_supprimer'),
path('super-admin/ecole/<int:ecole_id>/generer-cle/', views.super_admin_ecole_generer_cle, name='super_admin_ecole_generer_cle'),
path('super-admin/ecole/<int:ecole_id>/cours/', views.super_admin_ecole_cours, name='super_admin_ecole_cours'),
path('super-admin/ecole/<int:ecole_id>/supprimer/', views.super_admin_ecole_supprimer, name='super_admin_ecole_supprimer'),
path('super-admin/ecole/<int:ecole_id>/filiere/creer/', views.super_admin_filiere_creer, name='super_admin_filiere_creer'),
path('super-admin/filiere/<int:filiere_id>/specialite/creer/', views.super_admin_specialite_creer, name='super_admin_specialite_creer'),
path('super-admin/ecole/<int:ecole_id>/utilisateur/ajouter/', views.super_admin_utilisateur_ajouter, name='super_admin_utilisateur_ajouter'),
# Admin École - Filières
path('admin-ecole/filieres/', views.admin_ecole_filiere_liste, name='admin_ecole_filiere_liste'),
path('admin-ecole/ecole/<int:ecole_id>/filieres/creer/', views.admin_ecole_filiere_creer, name='admin_ecole_filiere_creer'),

# Admin École - Spécialités
path('admin-ecole/filiere/<int:filiere_id>/specialites/', views.admin_ecole_specialite_liste, name='admin_ecole_specialite_liste'),
path('admin-ecole/filiere/<int:filiere_id>/specialites/creer/', views.admin_ecole_specialite_creer, name='admin_ecole_specialite_creer'),
path('super-admin/utilisateurs/ajouter/', views.super_admin_utilisateur_ajouter, name='super_admin_utilisateur_ajouter_sans_ecole'),
path('super-admin/utilisateur/<int:user_id>/desactiver/', views.super_admin_utilisateur_desactiver, name='super_admin_utilisateur_desactiver'),
path('super-admin/utilisateur/<int:user_id>/activer/', views.super_admin_utilisateur_activer, name='super_admin_utilisateur_activer'),
path('super-admin/utilisateur/<int:user_id>/desactiver/', views.super_admin_utilisateur_desactiver, name='super_admin_utilisateur_desactiver'),
path('super-admin/utilisateur/<int:user_id>/activer/', views.super_admin_utilisateur_activer, name='super_admin_utilisateur_activer'),
path('super-admin/ecole/<int:ecole_id>/desactiver/', views.super_admin_ecole_desactiver, name='super_admin_ecole_desactiver'),
path('super-admin/ecole/<int:ecole_id>/activer/', views.super_admin_ecole_activer, name='super_admin_ecole_activer'),
path('admin-ecole/enseignants/', views.admin_ecole_enseignants, name='admin_ecole_enseignants'),
path('admin-ecole/etudiants/', views.admin_ecole_etudiants, name='admin_ecole_etudiants'),
# Admin École - Désactiver/Activer utilisateur
path('admin-ecole/utilisateur/<int:user_id>/desactiver/', views.admin_ecole_utilisateur_desactiver, name='admin_ecole_utilisateur_desactiver'),
path('admin-ecole/utilisateur/<int:user_id>/activer/', views.admin_ecole_utilisateur_activer, name='admin_ecole_utilisateur_activer'),
# Admin École - Modifier/Supprimer Filière
path('admin-ecole/filiere/<int:filiere_id>/modifier/', views.admin_ecole_filiere_modifier, name='admin_ecole_filiere_modifier'),
path('admin-ecole/filiere/<int:filiere_id>/supprimer/', views.admin_ecole_filiere_supprimer, name='admin_ecole_filiere_supprimer'),
# Admin École - Modifier/Supprimer Spécialité
path('admin-ecole/specialite/<int:specialite_id>/modifier/', views.admin_ecole_specialite_modifier, name='admin_ecole_specialite_modifier'),
path('admin-ecole/specialite/<int:specialite_id>/supprimer/', views.admin_ecole_specialite_supprimer, name='admin_ecole_specialite_supprimer'),
# Cours
path('cours/creer/<int:specialite_id>/', views.cours_creer, name='cours_creer'),
path('cours/<int:cours_id>/seance/ajouter/', views.seance_ajouter, name='seance_ajouter'),
path('specialite/<int:specialite_id>/', views.specialite_detail, name='specialite_detail'),
path('admin-ecole/specialites/', views.admin_ecole_specialites_liste, name='admin_ecole_specialites_liste'),
# Séances (enseignant)
path('seance/ajouter/<int:cours_id>/', views.seance_ajouter, name='seance_ajouter'),
path('seance/<int:seance_id>/modifier/', views.seance_modifier, name='seance_modifier'),
path('seance/<int:seance_id>/supprimer/', views.seance_supprimer, name='seance_supprimer'),
path('enseignant/cours/<int:cours_id>/', views.cours_detail_enseignant, name='cours_detail_enseignant'),
path('super-admin/cours/<int:cours_id>/', views.cours_detail_superadmin, name='cours_detail_superadmin'),
path('enseignant/mes-cours/', views.mes_cours_enseignant, name='mes_cours_enseignant'),
path('seance/<int:seance_id>/marquer-vue/', views.seance_marquer_vue, name='seance_marquer_vue'),
# Étudiant
path('etudiant/mes-cours/', views.etudiant_mes_cours, name='etudiant_mes_cours'),
path('etudiant/specialite/<int:specialite_id>/', views.etudiant_specialite_detail, name='etudiant_specialite_detail'),
path('etudiant/cours/<int:cours_id>/', views.etudiant_cours_detail, name='etudiant_cours_detail'),
path('enseignant/devoirs-a-corriger/', views.enseignant_devoirs_a_corriger, name='enseignant_devoirs_a_corriger'),
path('enseignant/corriger-devoir/<int:soumission_id>/', views.enseignant_corriger_devoir, name='enseignant_corriger_devoir'),
# Enseignant
path('enseignant/mes-cours/', views.enseignant_mes_cours, name='enseignant_mes_cours'),

# Forum (temporaire)
path('forum/', views.forum_liste, name='forum_liste'),
path('enseignant/devoirs-a-corriger/', views.enseignant_devoirs_a_corriger, name='enseignant_devoirs_a_corriger'),
path('enseignant/corriger-devoir/<int:soumission_id>/', views.enseignant_corriger_devoir, name='enseignant_corriger_devoir'),
path('etudiant/presentation/deposer/<int:seance_id>/', views.deposer_presentation, name='deposer_presentation'),
path('enseignant/presentations/<int:seance_id>/', views.enseignant_presentations, name='enseignant_presentations'),
path('cours/<int:cours_id>/', views.cours_detail_superadmin, name='cours_detail_superadmin'),
path('cours/<int:cours_id>/modifier/', views.cours_modifier, name='cours_modifier'),

# Exercices
path('enseignant/exercice/ajouter/<int:seance_id>/', views.exercice_ajouter, name='exercice_ajouter'),
path('enseignant/exercice/<int:exercice_id>/demarrer/', views.exercice_demarrer, name='exercice_demarrer'),
path('enseignant/exercice/<int:exercice_id>/terminer/', views.exercice_terminer, name='exercice_terminer'),
path('etudiant/exercice/<int:exercice_id>/faire/', views.exercice_faire, name='exercice_faire'),
path('etudiant/exercice/resultat/<int:reponse_id>/', views.exercice_resultat, name='exercice_resultat'),

# Devoirs
path('enseignant/devoir/ajouter/<int:seance_id>/', views.devoir_ajouter, name='devoir_ajouter'),
path('etudiant/devoir/<int:devoir_id>/soumettre/', views.devoir_soumettre, name='devoir_soumettre'),

# Visio
path('enseignant/visio/creer/<int:seance_id>/', views.creer_visio, name='creer_visio'),
path('etudiant/visio/rejoindre/<int:seance_id>/', views.rejoindre_visio, name='rejoindre_visio'),
path('cours/<int:cours_id>/modifier/', views.cours_modifier, name='cours_modifier'),
path('cours/<int:cours_id>/supprimer/', views.cours_supprimer, name='cours_supprimer'),
path('enseignant/exercice/ajouter/<int:seance_id>/', views.exercice_ajouter, name='exercice_ajouter'),
path('enseignant/exercice/<int:exercice_id>/demarrer/', views.exercice_demarrer, name='exercice_demarrer'),
path('enseignant/exercice/<int:exercice_id>/terminer/', views.exercice_terminer, name='exercice_terminer'),
path('etudiant/exercice/<int:exercice_id>/faire/', views.exercice_faire, name='exercice_faire'),
path('etudiant/exercice/resultat/<int:reponse_id>/', views.exercice_resultat, name='exercice_resultat'),
path('enseignant/devoir/ajouter/<int:seance_id>/', views.devoir_ajouter, name='devoir_ajouter'),
path('enseignant/devoir/soumissions/<int:devoir_id>/', views.devoir_soumissions, name='devoir_soumissions'),
path('enseignant/devoir/corriger/<int:soumission_id>/', views.devoir_corriger, name='devoir_corriger'),
path('etudiant/devoir/<int:devoir_id>/soumettre/', views.devoir_soumettre, name='devoir_soumettre'),
path('etudiant/cours/<int:cours_id>/', views.etudiant_cours_detail, name='etudiant_cours_detail'),
path('seance/<int:seance_id>/', views.seance_detail, name='seance_detail'),
path('seance/<int:seance_id>/', views.seance_detail, name='seance_detail'),
path('seance/<int:seance_id>/modifier/', views.seance_modifier, name='seance_modifier'),
path('seance/<int:seance_id>/supprimer/', views.seance_supprimer, name='seance_supprimer'),
path('exercice/<int:exercice_id>/modifier/', views.exercice_modifier, name='exercice_modifier'),
path('exercice/<int:exercice_id>/supprimer/', views.exercice_supprimer, name='exercice_supprimer'),
path('devoir/<int:devoir_id>/modifier/', views.devoir_modifier, name='devoir_modifier'),
path('devoir/<int:devoir_id>/supprimer/', views.devoir_supprimer, name='devoir_supprimer'),
# Quiz
path('quiz/creer/<int:seance_id>/', views.quiz_creer, name='quiz_creer'),
path('quiz/exercice/<int:exercice_id>/', views.quiz_detail, name='quiz_detail'),
path('quiz/exercice/<int:exercice_id>/question/ajouter/', views.question_ajouter, name='question_ajouter'),
path('question/<int:question_id>/reponse/ajouter/', views.reponse_ajouter, name='reponse_ajouter'),
path('quiz/exercice/<int:exercice_id>/question/ajouter/', views.question_ajouter, name='ajouter_question_quiz'),
path('etudiant/quiz/<int:exercice_id>/repondre/', views.repondre_quiz, name='repondre_quiz'),
path('enseignant/quiz/<int:exercice_id>/publier/', views.publier_resultats_quiz, name='publier_resultats_quiz'),
path('quiz/<int:exercice_id>/resultats/', views.quiz_resultats, name='quiz_resultats'),
path('seance/<int:seance_id>/demarrer-visio/', views.demarrer_visio, name='demarrer_visio'),



]