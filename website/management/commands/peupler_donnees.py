from django.core.management.base import BaseCommand
from website.models import (
    ConfigurationPlateforme, Ecole, Formation, Temoignage,
    DiapositiveHero, Utilisateur, Filiere, Specialite
)

class Command(BaseCommand):
    help = 'Peuple la base de données avec des données de démonstration'

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Début du peuplement des données...")

        # ============================================
        # 1. CONFIGURATION DE LA PLATEFORME
        # ============================================
        config, created = ConfigurationPlateforme.objects.get_or_create(id=1)
        
        config.nom_site = "EduMax"
        config.slogan_site = "La plateforme éducative qui révolutionne l'apprentissage"
        config.hero_titre = "Bienvenue sur"
        config.hero_titre_accent = "EduMax"
        config.hero_description = "La plateforme éducative qui révolutionne l'apprentissage en Afrique."
        config.hero_bouton1_texte = "Explorer"
        config.hero_bouton1_lien = "/formations/"
        config.hero_bouton2_texte = "Commencer"
        config.hero_bouton2_lien = "/inscription/"
        config.hero_afficher_stats = True
        
        config.couleur_principale = "#1e3a8a"
        config.couleur_secondaire = "#d97706"
        config.couleur_accent = "#10b981"
        
        config.stat1_label = "Étudiants"
        config.stat1_valeur_fixe = "15,000+"
        config.stat1_valeur_auto = True
        config.stat2_label = "Formations"
        config.stat2_valeur_fixe = "500+"
        config.stat2_valeur_auto = True
        config.stat3_label = "Épreuves"
        config.stat3_valeur_fixe = "2,000+"
        config.stat3_valeur_auto = True
        config.stat4_label = "Écoles"
        config.stat4_valeur_fixe = "50+"
        config.stat4_valeur_auto = True
        
        config.titre_section_formations = "Formations populaires"
        config.sous_titre_section_formations = "Développez vos compétences"
        config.titre_section_epreuves = "Épreuves et examens"
        config.sous_titre_section_epreuves = "Préparez-vous efficacement"
        config.titre_section_ecoles = "Nos écoles partenaires"
        config.titre_section_temoignages = "Ce que disent nos étudiants"
        config.titre_section_cta = "Prêt à commencer ?"
        config.sous_titre_section_cta = "Rejoignez des milliers d'étudiants"
        
        config.section_services_visible = True
        config.section_formations_visible = True
        config.section_epreuves_visible = True
        config.section_ecoles_visible = True
        config.section_temoignages_visible = True
        config.section_cta_visible = True
        
        config.nb_formations_accueil = 6
        config.nb_epreuves_accueil = 4
        config.nb_ecoles_accueil = 6
        
        config.afficher_formations_gratuites_badge = True
        config.afficher_prix_formations = True
        config.afficher_note_formations = True
        config.afficher_nb_ventes_formations = True
        
        config.footer_texte = "EduMax - La plateforme éducative de référence"
        config.footer_email_contact = "contact@edumax.com"
        config.footer_telephone = "+237 600 000 000"
        config.footer_adresse = "Yaoundé, Cameroun"
        
        config.mode_maintenance = False
        config.auto_publication_active = True
        config.auto_publication_delai_minutes = 60
        
        config.save()
        self.stdout.write(self.style.SUCCESS("✅ Configuration plateforme enregistrée"))

        # ============================================
        # 2. ÉCOLES
        # ============================================
        ecoles_data = [
            {"nom": "École Polytechnique", "description": "Excellence en ingénierie", "ville": "Yaoundé", "actif": True},
            {"nom": "Université de Douala", "description": "Formation académique", "ville": "Douala", "actif": True},
            {"nom": "Institut Supérieur de Gestion", "description": "Leadership", "ville": "Yaoundé", "actif": True},
            {"nom": "École de Commerce", "description": "Commerce international", "ville": "Douala", "actif": True},
            {"nom": "Institut des Sciences Info", "description": "Numérique", "ville": "Yaoundé", "actif": True},
            {"nom": "École des Arts", "description": "Formation technique", "ville": "Garoua", "actif": True},
        ]
        
        for ecole_data in ecoles_data:
            ecole, created = Ecole.objects.get_or_create(nom=ecole_data["nom"])
            ecole.description = ecole_data["description"]
            ecole.ville = ecole_data["ville"]
            ecole.actif = ecole_data["actif"]
            ecole.save()
        
        self.stdout.write(self.style.SUCCESS(f"✅ {len(ecoles_data)} écoles enregistrées"))

        # ============================================
        # 3. FILIÈRES ET SPÉCIALITÉS
        # ============================================
        filieres_data = ["Informatique", "Gestion", "Marketing", "Droit", "Sciences"]
        for fil_nom in filieres_data:
            filiere, created = Filiere.objects.get_or_create(nom=fil_nom)
            
            if fil_nom == "Informatique":
                specialites = ["Développement Web", "Data Science", "Cybersécurité", "IA"]
            elif fil_nom == "Gestion":
                specialites = ["Finance", "RH", "Logistique", "Comptabilité"]
            elif fil_nom == "Marketing":
                specialites = ["Digital", "Communication", "Vente", "Branding"]
            elif fil_nom == "Droit":
                specialites = ["Droit des affaires", "Droit public", "Justice"]
            else:
                specialites = ["Mathématiques", "Physique", "Chimie", "Biologie"]
            
            for spec_nom in specialites:
                Specialite.objects.get_or_create(nom=spec_nom, filiere=filiere)
        
        self.stdout.write(self.style.SUCCESS("✅ Filières et spécialités enregistrées"))

        # ============================================
        # 4. FORMATIONS
        # ============================================
        formations_data = [
            {"titre": "Développement Web Full Stack", "description": "Maîtrisez les technologies web modernes", "prix": 150000, "statut": "publie", "duree_heures": 120, "certifiante": True},
            {"titre": "Marketing Digital", "description": "Stratégies de marketing digital", "prix": 0, "statut": "publie", "duree_heures": 40, "certifiante": True},
            {"titre": "Data Science & IA", "description": "Python, Machine Learning", "prix": 250000, "statut": "publie", "duree_heures": 150, "certifiante": True},
            {"titre": "Comptabilité Générale", "description": "Bases de la comptabilité", "prix": 75000, "statut": "publie", "duree_heures": 60, "certifiante": False},
            {"titre": "Gestion de Projet", "description": "Méthodologies Agile", "prix": 120000, "statut": "publie", "duree_heures": 50, "certifiante": True},
            {"titre": "Anglais Professionnel", "description": "Anglais des affaires", "prix": 0, "statut": "publie", "duree_heures": 80, "certifiante": True},
        ]
        
        for form_data in formations_data:
            formation, created = Formation.objects.get_or_create(
                titre=form_data["titre"],
                defaults=form_data
            )
        
        self.stdout.write(self.style.SUCCESS(f"✅ {len(formations_data)} formations enregistrées"))

        # ============================================
        # 5. TÉMOIGNAGES
        # ============================================
        Temoignage.objects.all().delete()
        
        temoignages_data = [
            {"nom": "Marie K.", "role": "Étudiante", "texte": "Une plateforme exceptionnelle !", "note": 5, "ordre": 1},
            {"nom": "Jean P.", "role": "Développeur", "texte": "Je recommande chaudement !", "note": 5, "ordre": 2},
            {"nom": "Aminata D.", "role": "Marketing", "texte": "J'ai trouvé un emploi grâce à EduMax", "note": 5, "ordre": 3},
        ]
        
        for tem_data in temoignages_data:
            Temoignage.objects.create(**tem_data)
        
        self.stdout.write(self.style.SUCCESS(f"✅ {len(temoignages_data)} témoignages enregistrés"))

        # ============================================
        # 6. DIAPOSITIVES
        # ============================================
        DiapositiveHero.objects.all().delete()
        
        slides_data = [
            {"titre": "Formations de qualité", "sous_titre": "Par des experts", "bouton_texte": "Découvrir", "bouton_lien": "/formations/", "ordre": 1, "actif": True},
            {"titre": "Certifications reconnues", "sous_titre": "Valorisez vos compétences", "bouton_texte": "En savoir plus", "bouton_lien": "/formations/", "ordre": 2, "actif": True},
            {"titre": "Accompagnement personnalisé", "sous_titre": "Suivi individuel", "bouton_texte": "Nous contacter", "bouton_lien": "/contact/", "ordre": 3, "actif": True},
        ]
        
        for slide_data in slides_data:
            DiapositiveHero.objects.create(**slide_data)
        
        self.stdout.write(self.style.SUCCESS(f"✅ {len(slides_data)} diapositives enregistrées"))

        # ============================================
        # 7. ADMIN
        # ============================================
        try:
            admin = Utilisateur.objects.get(username='admin')
            admin.role = 'super_admin'
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()
            self.stdout.write(self.style.SUCCESS("✅ Rôle admin mis à jour"))
        except Utilisateur.DoesNotExist:
            self.stdout.write(self.style.WARNING("⚠️ Admin non trouvé"))

        # ============================================
        # FIN
        # ============================================
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("🎉 PEUPLEMENT TERMINÉ !"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write("")
        self.stdout.write("👉 Allez dans : http://127.0.0.1:8000/super-admin/configuration/")