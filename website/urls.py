from django.urls import path
from . import views

urlpatterns = [
    # ==================== PAGES PUBLIQUES ====================
    path('', views.accueil, name='accueil'),
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('mot-de-passe-oublie/', views.mot_de_passe_oublie, name='mot_de_passe_oublie'),
    path('reinitialisation/<str:token>/', views.reinitialisation_mot_de_passe, name='reinitialisation_mot_de_passe'),
    
    # ==================== DASHBOARD ====================
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profil/<int:user_id>/', views.profil_public, name='profil_public'),
    
    # ==================== MESSAGES ====================
    path('messages/envoyer/', views.message_envoyer, name='message_envoyer'),
    path('messages/configuration/', views.super_admin_configuration, name='configurer_messagerie'),
    path('messages/', views.messages_liste, name='messages_liste'),
    path('messages/<int:conversation_id>/', views.messages_liste, name='conversation_detail'),
    
    # ==================== FORUM ====================
    path('forum/<int:forum_id>/', views.forum_detail, name='forum_detail'),
    
    # ==================== SUPER ADMIN - ÉCOLES ====================
    path('super-admin/ecoles/', views.super_admin_ecole_liste, name='super_admin_ecole_liste'),
    path('super-admin/ecoles/creer/', views.super_admin_ecole_creer, name='super_admin_ecole_creer'),
    path('super-admin/ecoles/<int:ecole_id>/modifier/', views.super_admin_ecole_modifier, name='super_admin_ecole_modifier'),
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
    path('super-admin/ecole/<int:ecole_id>/desactiver/', views.super_admin_ecole_desactiver, name='super_admin_ecole_desactiver'),
    path('super-admin/ecole/<int:ecole_id>/activer/', views.super_admin_ecole_activer, name='super_admin_ecole_activer'),
    path('super-admin/ecole/<int:ecole_id>/filiere/creer/', views.super_admin_filiere_creer, name='super_admin_filiere_creer'),
    path('super-admin/filiere/<int:filiere_id>/specialite/creer/', views.super_admin_specialite_creer, name='super_admin_specialite_creer'),
    path('super-admin/ecole/<int:ecole_id>/utilisateur/ajouter/', views.super_admin_utilisateur_ajouter, name='super_admin_utilisateur_ajouter'),
    
    # ==================== SUPER ADMIN - ABONNEMENTS ====================
    path('super-admin/abonnements/', views.super_admin_abonnement_liste, name='super_admin_abonnement_liste'),
    path('super-admin/abonnements/creer/', views.super_admin_abonnement_creer, name='super_admin_abonnement_creer'),
    path('super-admin/abonnements/<int:abonnement_id>/modifier/', views.super_admin_abonnement_modifier, name='super_admin_abonnement_modifier'),
    path('super-admin/abonnements/<int:abonnement_id>/supprimer/', views.super_admin_abonnement_supprimer, name='super_admin_abonnement_supprimer'),
    
    # ==================== SUPER ADMIN - UTILISATEURS ====================
    path('super-admin/utilisateurs/', views.super_admin_utilisateurs, name='super_admin_utilisateurs'),
    path('super-admin/utilisateurs/ajouter/', views.super_admin_utilisateur_ajouter, name='super_admin_utilisateur_ajouter_sans_ecole'),
    path('super-admin/utilisateur/<int:user_id>/modifier/', views.super_admin_utilisateur_modifier, name='super_admin_utilisateur_modifier'),
    path('super-admin/utilisateur/<int:user_id>/supprimer/', views.super_admin_utilisateur_supprimer, name='super_admin_utilisateur_supprimer'),
    path('super-admin/utilisateur/<int:user_id>/changer-role/<str:nouveau_role>/', views.super_admin_changer_role, name='super_admin_changer_role'),
    path('super-admin/utilisateur/<int:user_id>/desactiver/', views.super_admin_utilisateur_desactiver, name='super_admin_utilisateur_desactiver'),
    path('super-admin/utilisateur/<int:user_id>/activer/', views.super_admin_utilisateur_activer, name='super_admin_utilisateur_activer'),
    path('super-admin/utilisateurs/certifier/<int:user_id>/', views.certifier_utilisateur, name='certifier_utilisateur'),
    path('super-admin/utilisateur/decertifier/<int:user_id>/', views.decertifier_utilisateur, name='decertifier_utilisateur'),
    path('super-admin/auto-validation/activer/<int:user_id>/', views.activer_auto_validation, name='activer_auto_validation'),
    path('super-admin/auto-validation/desactiver/<int:user_id>/', views.desactiver_auto_validation, name='desactiver_auto_validation'),
    
    # ==================== SUPER ADMIN - CONFIGURATION ====================
    path('super-admin/configuration/', views.super_admin_configuration, name='super_admin_configuration'),
    path('super-admin/parametres-messagerie/', views.parametres_messagerie, name='parametres_messagerie'),
    
    # ==================== SUPER ADMIN - SLIDES & BANNIÈRES ====================
    path('super-admin/slides/creer/', views.super_admin_slide_create, name='super_admin_slide_create'),
    path('super-admin/slides/<int:slide_id>/modifier/', views.super_admin_slide_edit, name='super_admin_slide_edit'),
    path('super-admin/slides/<int:slide_id>/supprimer/', views.super_admin_slide_delete, name='super_admin_slide_delete'),
    path('super-admin/temoignages/creer/', views.super_admin_temoignage_create, name='super_admin_temoignage_create'),
    path('super-admin/temoignages/<int:t_id>/modifier/', views.super_admin_temoignage_edit, name='super_admin_temoignage_edit'),
    path('super-admin/temoignages/<int:t_id>/supprimer/', views.super_admin_temoignage_delete, name='super_admin_temoignage_delete'),
    path('super-admin/bannieres/creer/', views.super_admin_banniere_create, name='super_admin_banniere_create'),
    path('super-admin/bannieres/<int:b_id>/modifier/', views.super_admin_banniere_edit, name='super_admin_banniere_edit'),
    
    # ==================== SUPER ADMIN - FORMATIONS ====================
    path('super-admin/gerer-formations/', views.super_admin_gerer_formations, name='super_admin_gerer_formations'),
    path('super-admin/formations/valider/<int:formation_id>/', views.valider_formation, name='valider_formation'),
    path('super-admin/formations/refuser/<int:formation_id>/', views.refuser_formation, name='refuser_formation'),
    path('super-admin/formations/certifier/<int:formation_id>/', views.certifier_formation, name='certifier_formation'),
    path('super-admin/formation/supprimer/<int:formation_id>/', views.supprimer_formation, name='supprimer_formation'),
    path('super-admin/formations/conditions/', views.formation_configurer_conditions, name='formation_configurer_conditions'),
    path('super-admin/formations/coupons/', views.formation_gerer_coupons, name='formation_gerer_coupons'),
    path('super-admin/formations/regles/', views.regles_liste, name='regles_liste'),
    path('super-admin/formations/regles/ajouter/', views.regle_ajouter, name='regle_ajouter'),
    path('super-admin/formations/regles/modifier/<int:pk>/', views.regle_modifier, name='regle_modifier'),
    path('super-admin/formations/regles/supprimer/<int:pk>/', views.regle_supprimer, name='regle_supprimer'),
    
    # ==================== SUPER ADMIN - SIGNALEMENTS ====================
    path('super-admin/signalement/traiter/<int:signalement_id>/', views.traiter_signalement, name='traiter_signalement'),
    # ==================== ADMIN ÉCOLE - PARAMÈTRES ====================
    path('admin-ecole/parametres/', views.admin_ecole_parametres, name='admin_ecole_parametres'),
    # ==================== ÉCOLES PUBLIQUES ====================
    path('ecoles/', views.ecoles_liste, name='ecoles_liste'),
    path('ecole/<slug:slug>/', views.ecole_detail, name='ecole_detail'),
    
    # ==================== ADMIN ÉCOLE ====================
    path('admin-ecole/modifier/', views.admin_ecole_modifier, name='admin_ecole_modifier'),
    path('admin-ecole/changer-logo/', views.admin_ecole_changer_logo, name='admin_ecole_changer_logo'),
    path('admin-ecole/galerie/', views.admin_ecole_galerie, name='admin_ecole_galerie'),
    path('admin-ecole/galerie/ajouter/', views.admin_ecole_galerie_ajouter, name='admin_ecole_galerie_ajouter'),
    path('admin-ecole/galerie/supprimer/<int:image_id>/', views.admin_ecole_galerie_supprimer, name='admin_ecole_galerie_supprimer'),
    path('admin-ecole/utilisateurs/', views.admin_ecole_utilisateurs, name='admin_ecole_utilisateurs'),
    path('admin-ecole/generer-cle/', views.admin_ecole_generer_cle, name='admin_ecole_generer_cle'),
    path('admin-ecole/utilisateur/<int:user_id>/modifier/', views.admin_ecole_utilisateur_modifier, name='admin_ecole_utilisateur_modifier'),
    path('admin-ecole/utilisateur/<int:user_id>/supprimer/', views.admin_ecole_utilisateur_supprimer, name='admin_ecole_utilisateur_supprimer'),
    path('admin-ecole/utilisateur/<int:user_id>/desactiver/', views.admin_ecole_utilisateur_desactiver, name='admin_ecole_utilisateur_desactiver'),
    path('admin-ecole/utilisateur/<int:user_id>/activer/', views.admin_ecole_utilisateur_activer, name='admin_ecole_utilisateur_activer'),
    path('admin-ecole/enseignants/', views.admin_ecole_enseignants, name='admin_ecole_enseignants'),
    path('admin-ecole/etudiants/', views.admin_ecole_etudiants, name='admin_ecole_etudiants'),
    path('admin-ecole/filieres/', views.admin_ecole_filiere_liste, name='admin_ecole_filiere_liste'),
    path('admin-ecole/ecole/<int:ecole_id>/filieres/creer/', views.admin_ecole_filiere_creer, name='admin_ecole_filiere_creer'),
    path('admin-ecole/filiere/<int:filiere_id>/modifier/', views.admin_ecole_filiere_modifier, name='admin_ecole_filiere_modifier'),
    path('admin-ecole/filiere/<int:filiere_id>/supprimer/', views.admin_ecole_filiere_supprimer, name='admin_ecole_filiere_supprimer'),
    path('admin-ecole/filiere/<int:filiere_id>/specialites/', views.admin_ecole_specialite_liste, name='admin_ecole_specialite_liste'),
    path('admin-ecole/filiere/<int:filiere_id>/specialites/creer/', views.admin_ecole_specialite_creer, name='admin_ecole_specialite_creer'),
    path('admin-ecole/specialite/<int:specialite_id>/modifier/', views.admin_ecole_specialite_modifier, name='admin_ecole_specialite_modifier'),
    path('admin-ecole/specialite/<int:specialite_id>/supprimer/', views.admin_ecole_specialite_supprimer, name='admin_ecole_specialite_supprimer'),
    path('admin-ecole/specialites/', views.admin_ecole_specialites_liste, name='admin_ecole_specialites_liste'),
    
    # ==================== COURS & SPÉCIALITÉS ====================
    path('specialite/<int:specialite_id>/', views.specialite_detail, name='specialite_detail'),
    path('cours/creer/<int:specialite_id>/', views.cours_creer, name='cours_creer'),
    path('cours/<int:cours_id>/modifier/', views.cours_modifier, name='cours_modifier'),
    path('cours/<int:cours_id>/supprimer/', views.cours_supprimer, name='cours_supprimer'),
    path('cours/<int:cours_id>/', views.cours_detail_superadmin, name='cours_detail_superadmin'),
    
    # ==================== ÉTUDIANTS ====================
    path('etudiant/inscription-cle/', views.etudiant_inscription_cle, name='etudiant_inscription_cle'),
    path('etudiant/mes-cours/', views.etudiant_mes_cours, name='etudiant_mes_cours'),
    path('etudiant/specialite/<int:specialite_id>/', views.etudiant_specialite_detail, name='etudiant_specialite_detail'),
    path('etudiant/cours/<int:cours_id>/', views.etudiant_cours_detail, name='etudiant_cours_detail'),
    path('etudiant/presentation/deposer/<int:seance_id>/', views.deposer_presentation, name='deposer_presentation'),
    
    # ==================== ENSEIGNANTS ====================
    path('enseignant/mes-cours/', views.enseignant_mes_cours, name='enseignant_mes_cours'),
    path('enseignant/cours/<int:cours_id>/', views.cours_detail_enseignant, name='cours_detail_enseignant'),
    path('enseignant/cours/', views.enseignant_cours_liste, name='enseignant_cours_liste'),
    path('enseignant/presentations/<int:seance_id>/', views.enseignant_presentations, name='enseignant_presentations'),
    
    # ==================== FORUM ====================
    path('forum/', views.forum_liste, name='forum_liste'),
    
    # ==================== FORUM SIMPLIFIÉ ====================
    # Forum principal
    path('forum/', views.forum_liste, name='forum_liste'),
    path('forum/<int:forum_id>/', views.forum_detail, name='forum_detail'),

    # Messages (AJAX)
    path('forum/<int:forum_id>/message/', views.forum_envoyer_message, name='forum_envoyer_message'),
    path('forum/<int:forum_id>/messages/nouveaux/', views.forum_charger_nouveaux_messages, name='forum_charger_nouveaux_messages'),

    # Signalement et modération
    path('forum/message/signaler/<int:message_id>/', views.forum_signalement, name='forum_signalement'),
    path('forum/message/masquer/<int:message_id>/', views.forum_masquer_message, name='forum_masquer_message'),

    # Blocage utilisateur
    path('forum/<int:forum_id>/bloquer/<int:user_id>/', views.forum_bloquer_utilisateur, name='forum_bloquer_utilisateur'),
    path('forum/<int:forum_id>/debloquer/<int:user_id>/', views.forum_debloquer_utilisateur, name='forum_debloquer_utilisateur'),

    # Sujet du jour (admin)
    path('admin/forum/<int:forum_id>/sujet-jour/', views.admin_sujet_jour, name='admin_sujet_jour'),
        # ==================== SÉANCES ====================
    path('seance/ajouter/<int:cours_id>/', views.seance_ajouter, name='seance_ajouter'),
    path('seance/<int:seance_id>/', views.seance_detail, name='seance_detail'),
    path('seance/<int:seance_id>/publier/', views.seance_publier, name='seance_publier'),
    path('seance/<int:seance_id>/supprimer/', views.seance_supprimer, name='seance_supprimer'),
    path('seance/<int:seance_id>/modifier/', views.seance_modifier, name='seance_modifier'),
    
    # ── TYPE VISIO (déjà existant — vérifiez la présence) ──────────
    path('seance/<int:seance_id>/visio/config/', views.seance_visio_config, name='seance_visio_config'),
    path('seance/<int:seance_id>/visio/demarrer/', views.seance_visio_demarrer, name='seance_visio_demarrer'),
    path('seance/<int:seance_id>/visio/rejoindre/', views.seance_visio_rejoindre, name='seance_visio_rejoindre'),
    path('seance/<int:seance_id>/visio/terminer/', views.seance_visio_terminer, name='seance_visio_terminer'),
    # NOUVEAU — manquait, utile pour lier l'enregistrement après coup
    path('seance/<int:seance_id>/visio/enregistrement/', views.seance_visio_ajouter_enregistrement, name='seance_visio_ajouter_enregistrement'),

    # ── TYPE ASYNCHRONE (déjà existant) ─────────────────────────────
    path('seance/<int:seance_id>/asynchrone/config/', views.seance_asynchrone_config, name='seance_asynchrone_config'),
    path('ressource/<int:ressource_id>/supprimer/', views.seance_asynchrone_ressource_supprimer, name='seance_asynchrone_ressource_supprimer'),

    # ── TYPE INTÉGRATION (vue remplacée, URL déjà existante) ────────
    path('seance/<int:seance_id>/integration/config/', views.seance_integration_config, name='seance_integration_config'),
    # NOUVEAU — marquer un exercice d'intégration comme vu
    path('exercice/<int:exercice_id>/integration/marquer-vu/', views.integration_marquer_vu, name='integration_marquer_vu'),

    # ── TYPE CORRECTION (TOUT NOUVEAU — n'existait pas du tout) ─────
    path('seance/<int:seance_id>/correction/config/', views.seance_correction_config, name='seance_correction_config'),
    path('seance/<int:seance_id>/correction/publier/', views.seance_correction_publier, name='seance_correction_publier'),
    path('seance/<int:seance_id>/correction/depublier/', views.seance_correction_depublier, name='seance_correction_depublier'),
    path('seance/<int:seance_id>/correction/supprimer-fichier/', views.seance_correction_supprimer_fichier, name='seance_correction_supprimer_fichier'),
    # ==================== EXERCICES ====================
    path('exercice/ajouter/<int:seance_id>/', views.exercice_ajouter, name='exercice_ajouter'),
    path('exercice/<int:exercice_id>/configurer/', views.exercice_configurer, name='exercice_configurer'),
    path('exercice/<int:exercice_id>/lancer/', views.exercice_lancer, name='exercice_lancer'),
    path('exercice/<int:exercice_id>/publier-resultats/', views.exercice_publier_resultats, name='exercice_publier_resultats'),
    path('exercice/<int:exercice_id>/publier-correction/', views.exercice_publier_correction, name='exercice_publier_correction'),
    path('exercice/<int:exercice_id>/modifier/', views.exercice_modifier, name='exercice_modifier'),
    path('exercice/<int:exercice_id>/supprimer/', views.exercice_supprimer, name='exercice_supprimer'),
    path('etudiant/exercice/<int:exercice_id>/resultat/', views.exercice_resultat, name='exercice_resultat'),
        
    # ==================== DEVOIRS ====================
    path('devoir/ajouter/<int:seance_id>/', views.devoir_ajouter, name='devoir_ajouter'),
    path('devoir/<int:devoir_id>/modifier/', views.devoir_modifier, name='devoir_modifier'),
    path('devoir/<int:devoir_id>/supprimer/', views.devoir_supprimer, name='devoir_supprimer'),
    path('devoir/<int:devoir_id>/publier/', views.devoir_publier, name='devoir_publier'),
    path('devoir/<int:devoir_id>/configurer/', views.devoir_configurer, name='devoir_configurer'),  # ← AJOUTER CETTE LIGNE
    path('devoir/<int:devoir_id>/publier-correction/', views.devoir_publier_correction, name='devoir_publier_correction'),
    path('etudiant/devoir/<int:devoir_id>/soumettre/', views.devoir_soumettre, name='devoir_soumettre'),
    path('etudiant/devoir/<int:devoir_id>/voir-correction/', views.devoir_voir_correction, name='devoir_voir_correction'),
    # ==================== FORMATIONS (PUBLIC) ====================
    path('formations/', views.formations_liste, name='formations_liste'),
    path('formations/centre/<slug:slug>/', views.formations_par_centre, name='formations_par_centre'),
    path('formation/creer/', views.formation_creer, name='formation_creer'),
    path('formation/supprimer/<int:formation_id>/', views.formation_supprimer, name='formation_supprimer'),
    path('formation/<slug:slug>/', views.formation_detail, name='formation_detail'),
    path('formation/<slug:slug>/modifier/', views.formation_modifier, name='formation_modifier'),
    path('formation/<slug:slug>/fichiers/', views.formation_ajouter_fichiers, name='formation_ajouter_fichiers'),
    path('formation/<slug:slug>/fichier/supprimer/<int:fichier_id>/', views.formation_supprimer_fichier, name='formation_supprimer_fichier'),
    path('formation/<slug:slug>/publier/', views.formation_publier_confirmation, name='formation_publier_confirmation'),
    path('formation/<slug:slug>/acheter/', views.formation_acheter, name='formation_acheter'),
    path('formation/<slug:slug>/confirmation/<int:achat_id>/', views.formation_confirmation, name='formation_confirmation'),
    path('formation/<slug:slug>/avis/', views.formation_laisser_avis, name='formation_laisser_avis'),
    path('formation/<slug:slug>/signaler/', views.signaler_formation, name='signaler_formation'),
    path('mes-formations/', views.mes_formations, name='mes_formations'),

    # ==================== PANIER (ÉPREUVES) ====================
    path('epreuves/panier/', views.epreuves_panier, name='epreuves_panier'),
    path('epreuves/panier/ajouter/', views.ajouter_au_panier, name='ajouter_au_panier'),
    path('epreuves/panier/retirer/', views.retirer_du_panier, name='retirer_du_panier'),
    path('epreuves/panier/vider/', views.vider_panier, name='vider_panier'),
    path('epreuves/panier/finaliser/', views.finaliser_achat, name='finaliser_achat'),
    path('epreuves/confirmation/<int:achat_id>/', views.confirmation_achat, name='confirmation_achat'),
    path('epreuves/mes-epreuves/', views.mes_epreuves, name='mes_epreuves'),
    path('epreuves/telecharger/<int:epreuve_id>/', views.telecharger_epreuve, name='telecharger_epreuve'),
    path('epreuves/ajouter-categorie-panier/', views.ajouter_categorie_panier, name='ajouter_categorie_panier'),
    
    # ==================== ÉPREUVES (PUBLIC) ====================
    path('epreuves/', views.epreuves_accueil, name='epreuves_accueil'),
    path('epreuves/recherche/', views.epreuves_recherche, name='epreuves_recherche'),
    path('epreuves/<slug:slug>/', views.epreuves_rubrique, name='epreuves_rubrique'),
    path('epreuves/categorie/<int:categorie_id>/ajax/', views.epreuves_categorie_ajax, name='epreuves_categorie_ajax'),
    
    # ==================== ADMIN ÉPREUVES (SUPER ADMIN) ====================
    path('super-admin/epreuves/', views.admin_epreuves_dashboard, name='super_admin_epreuves_dashboard'),
    # ADMIN ÉPREUVES (SUPER ADMIN)
    path('super-admin/epreuves/', views.admin_epreuves_dashboard, name='super_admin_epreuves_dashboard'),
    path('super-admin/epreuves/', views.admin_epreuves_dashboard, name='admin_epreuves_dashboard'),  # ← ALIAS
    # Rubriques
    path('super-admin/epreuves/rubrique/ajouter/', views.admin_rubrique_ajouter, name='admin_rubrique_ajouter'),
    path('super-admin/epreuves/rubrique/modifier/<int:rubrique_id>/', views.admin_rubrique_modifier, name='admin_rubrique_modifier'),
    path('super-admin/epreuves/rubrique/supprimer/<int:rubrique_id>/', views.admin_rubrique_supprimer, name='admin_rubrique_supprimer'),
    
    # Catégories
    path('super-admin/epreuves/categorie/ajouter/', views.admin_categorie_ajouter, name='admin_categorie_ajouter'),
    path('super-admin/epreuves/categorie/modifier/', views.admin_categorie_modifier, name='admin_categorie_modifier'),
    path('super-admin/epreuves/categorie/supprimer/<int:categorie_id>/', views.admin_categorie_supprimer, name='admin_categorie_supprimer'),
    
    # Épreuves
    path('super-admin/epreuves/epreuve/ajouter/', views.admin_epreuve_ajouter, name='admin_epreuve_ajouter'),
    path('super-admin/epreuves/epreuve/modifier/<int:epreuve_id>/', views.admin_epreuve_modifier, name='admin_epreuve_modifier'),
    path('super-admin/epreuves/epreuve/supprimer/<int:epreuve_id>/', views.admin_epreuve_supprimer, name='admin_epreuve_supprimer'),
    
    # Séries
    path('super-admin/epreuves/serie/ajouter/', views.admin_serie_ajouter, name='admin_serie_ajouter'),
    path('super-admin/epreuves/serie/modifier/<int:id>/', views.admin_serie_modifier, name='admin_serie_modifier'),
    path('super-admin/epreuves/serie/supprimer/<int:id>/', views.admin_serie_supprimer, name='admin_serie_supprimer'),
    
    # ==================== API ====================
    path('api/panier/count/', views.api_panier_count, name='api_panier_count'),
    path('api/rechercher-centres/', views.rechercher_centres_interet, name='rechercher_centres_interet'),
    
    # ==================== WISHLIST & COUPONS ====================
    path('formations/wishlist/toggle/<int:formation_id>/', views.formation_wishlist_toggle, name='formation_wishlist_toggle'),
    path('formations/coupon/verifier/', views.formation_verifier_coupon, name='formation_verifier_coupon'),
    path('formations/fichier/<int:fichier_id>/vu/', views.formation_marquer_fichier_vu, name='formation_marquer_fichier_vu'),
    
    # ==================== FORUMS (SUPER ADMIN) ====================
    path('super-admin/messagerie/configurer/', views.configurer_messagerie, name='configurer_messagerie'),
    path('admin-ecole/forums/', views.admin_ecole_forums, name='admin_ecole_forums'),
    path('super-admin/centres-interet/', views.gerer_propositions_centres, name='gerer_propositions_centres'),
    # Paramètres du site (central)
    path('super-admin/parametres/', views.super_admin_parametres, name='super_admin_parametres'),
    # Super admin - paramètres forums
    path('super-admin/forums/parametres/', views.super_admin_forums_parametres, name='super_admin_forums_parametres'),

    # Admin école - gestion forums
    path('admin-ecole/forums/', views.admin_ecole_forums, name='admin_ecole_forums'),
    path('forum/sujet/<int:sujet_id>/', views.redirection_sujet, name='forum_sujet_detail'),
    path('api/messages/non-lus/', views.api_messages_non_lus, name='api_messages_non_lus'),
    path('messagerie/api/', views.messagerie_api, name='messagerie_api'),
    path('forum/<int:forum_id>/sujet-jour/', views.forum_sujet_jour, name='forum_sujet_jour'),

    # Paiement et abonnement
    path('paiement/choix/', views.choix_abonnement, name='choix_abonnement'),
    path('paiement/initier/', views.initier_paiement, name='initier_paiement'),
    path('paiement/confirmer/<str:reference>/', views.confirmer_paiement, name='confirmer_paiement'),
    path('paiement/callback/', views.paiement_callback, name='paiement_callback'),
    path('api/verifier-abonnement/', views.verifier_abonnement, name='verifier_abonnement'),

    # Logs transactions (super admin)
    path('super-admin/logs-transactions/', views.logs_transactions, name='logs_transactions'),
    path('super-admin/logs-transactions/supprimer/<int:transaction_id>/', views.supprimer_transaction, name='supprimer_transaction'),
    path('super-admin/logs-transactions/exporter/', views.export_transactions_csv, name='export_transactions_csv'),

    # Gestion utilisateurs (à ajouter dans la page existante)
    path('super-admin/utilisateur/<int:user_id>/reinitialiser-mdp/', views.reinitialiser_mot_de_passe, name='reinitialiser_mot_de_passe'),
    path('paiement/demarrer-essai/', views.demarrer_essai, name='demarrer_essai'),
    path('mon-abonnement/', views.mon_abonnement, name='mon_abonnement'),    
    path('inscription/abandonner/', views.abandonner_inscription, name='abandonner_inscription'),    
   
        # ==================== QCM (Configuration AJAX) ====================
    path('qcm/configurer/<int:exercice_id>/', views.qcm_configurer, name='qcm_configurer'),
    path('qcm/question/ajouter/<int:exercice_id>/', views.qcm_question_ajouter, name='qcm_question_ajouter'),
    path('qcm/question/supprimer/<int:exercice_id>/<int:question_id>/', views.qcm_question_supprimer, name='qcm_question_supprimer'),
    path('qcm/question/modifier/<int:question_id>/', views.qcm_question_modifier, name='qcm_question_modifier'),
    # ==================== ÉTUDIANT - EXERCICES ====================
    path('etudiant/exercice/<int:exercice_id>/passer/', views.exercice_passer, name='exercice_passer'),
    path('etudiant/exercice/<int:exercice_id>/soumettre/', views.exercice_soumettre, name='exercice_soumettre'),
    path('etudiant/exercice/<int:exercice_id>/sauvegarder/', views.exercice_sauvegarder, name='exercice_sauvegarder'),
    # ==================== ENSEIGNANT - RÉSULTATS ====================
    path('enseignant/exercice/<int:exercice_id>/tableau-resultats/', views.exercice_tableau_resultats, name='exercice_tableau_resultats'),
    
    # ==================== VRAI/FAUX ====================
    path('vrai_faux/configurer/<int:exercice_id>/', views.vrai_faux_configurer, name='vrai_faux_configurer'),
    path('vrai_faux/ajouter/<int:exercice_id>/', views.vrai_faux_ajouter, name='vrai_faux_ajouter'),
    path('vrai_faux/modifier/<int:question_id>/', views.vrai_faux_modifier, name='vrai_faux_modifier'),
    path('vrai_faux/supprimer/<int:exercice_id>/<int:question_id>/', views.vrai_faux_supprimer, name='vrai_faux_supprimer'),

    # ==================== TEXTE À TROUS ====================
    path('texte_trous/configurer/<int:exercice_id>/', views.texte_trous_configurer, name='texte_trous_configurer'),
    path('texte_trous/previsualiser/', views.texte_trous_previsualiser, name='texte_trous_previsualiser'),
    path('texte_trous/passer/<int:exercice_id>/', views.texte_trous_passer, name='texte_trous_passer'),
    path('texte_trous/soumettre/<int:exercice_id>/', views.texte_trous_soumettre, name='texte_trous_soumettre'),
    path('texte_trous/resultat/<int:exercice_id>/', views.texte_trous_resultat, name='texte_trous_resultat'),
    path('texte_trous/tableau_resultats/<int:exercice_id>/', views.texte_trous_tableau_resultats, name='texte_trous_tableau_resultats'),   
    
    # ==================== RÉDACTION ====================
    path('redaction/configurer/<int:exercice_id>/', views.redaction_configurer, name='redaction_configurer'),
    path('redaction/passer/<int:exercice_id>/', views.redaction_passer, name='redaction_passer'),
    path('redaction/sauvegarder/<int:exercice_id>/', views.redaction_sauvegarder, name='redaction_sauvegarder'),
    path('redaction/soumettre/<int:exercice_id>/', views.redaction_soumettre, name='redaction_soumettre'),
    path('redaction/resultat/<int:exercice_id>/', views.redaction_resultat, name='redaction_resultat'),
    path('redaction/liste-a-corriger/<int:exercice_id>/', views.redaction_liste_a_corriger, name='redaction_liste_a_corriger'),
    path('redaction/corriger/<int:soumission_id>/', views.redaction_corriger, name='redaction_corriger'),
    path('redaction/tableau-resultats/<int:exercice_id>/', views.redaction_tableau_resultats, name='redaction_tableau_resultats'),

    # ==================== DÉPÔT DE FICHIER ====================
    path('depot_fichier/configurer/<int:exercice_id>/', views.depot_fichier_configurer, name='depot_fichier_configurer'),
    path('depot_fichier/passer/<int:exercice_id>/', views.depot_fichier_passer, name='depot_fichier_passer'),
    path('depot_fichier/soumettre/<int:exercice_id>/', views.depot_fichier_soumettre, name='depot_fichier_soumettre'),
    path('depot_fichier/resultat/<int:exercice_id>/', views.depot_fichier_resultat, name='depot_fichier_resultat'),
    path('depot_fichier/liste-a-corriger/<int:exercice_id>/', views.depot_fichier_liste_a_corriger, name='depot_fichier_liste_a_corriger'),
    path('depot_fichier/corriger/<int:soumission_id>/', views.depot_fichier_corriger, name='depot_fichier_corriger'),
    path('depot_fichier/tableau-resultats/<int:exercice_id>/', views.depot_fichier_tableau_resultats, name='depot_fichier_tableau_resultats'),

    # ==================== ÉTUDE DE CAS ====================
    path('etude_cas/configurer/<int:exercice_id>/', views.etude_cas_configurer, name='etude_cas_configurer'),
    path('etude_cas/sous_question/ajouter/<int:exercice_id>/', views.etude_cas_sous_question_ajouter, name='etude_cas_sous_question_ajouter'),
    path('etude_cas/sous_question/modifier/<int:sous_question_id>/', views.etude_cas_sous_question_modifier, name='etude_cas_sous_question_modifier'),
    path('etude_cas/sous_question/supprimer/<int:exercice_id>/<int:sous_question_id>/', views.etude_cas_sous_question_supprimer, name='etude_cas_sous_question_supprimer'),
    path('etude_cas/passer/<int:exercice_id>/', views.etude_cas_passer, name='etude_cas_passer'),
    path('etude_cas/soumettre/<int:exercice_id>/', views.etude_cas_soumettre, name='etude_cas_soumettre'),
    path('etude_cas/resultat/<int:exercice_id>/', views.etude_cas_resultat, name='etude_cas_resultat'),
    path('etude_cas/tableau_resultats/<int:exercice_id>/', views.etude_cas_tableau_resultats, name='etude_cas_tableau_resultats'),

    # Pour les utilisateurs
    path('gestion/devenir-formateur/', views.devenir_formateur, name='devenir_formateur'),
    path('gestion/creer-ecole/', views.creer_ecole, name='creer_ecole'),
    path('gestion/mes-demandes/', views.mes_demandes, name='mes_demandes'),

    # Pour l'équipe technique (super_admin)
    path('super-admin/demandes-formateurs/', views.admin_demandes_formateur, name='admin_demandes_formateur'),
    path('super-admin/demande-formateur/<int:demande_id>/voir/', views.admin_demande_formateur_voir, name='admin_demande_formateur_voir'),
    path('super-admin/demande-formateur/<int:demande_id>/<str:action>/', views.admin_demande_formateur_action, name='admin_demande_formateur_action'),

    
    ]