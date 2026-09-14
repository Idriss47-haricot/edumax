"""
FICHIER DE SEEDING SÉCURISÉ - Données de test
À utiliser UNIQUEMENT en développement

UTILISATION:
    python seed_data.py

SUPPRESSION:
    python seed_data.py --delete

ATTENTION: Ce fichier est autonome et ne modifie pas votre code existant.
           Il ajoute simplement des données de test.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

from website.models import CentreInteret

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edumax.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.utils import timezone

User = get_user_model()

# ==================== DONNÉES DE TEST ====================

# Centres d'intérêt fiables (pas de création par utilisateur)
CENTRES_INTERET = [
    "Informatique & Programmation",
    "Développement Web",
    "Intelligence Artificielle",
    "Data Science",
    "Cybersécurité",
    "Marketing Digital",
    "E-commerce",
    "Design Graphique",
    "Photographie",
    "Vidéo & Montage",
    "Cuisine & Gastronomie",
    "Pâtisserie",
    "Bâtiment & Construction",
    "Électricité",
    "Plomberie",
    "Mécanique Auto",
    "Santé & Bien-être",
    "Sport & Fitness",
    "Langues (Anglais, Français)",
    "Comptabilité & Gestion",
    "Ressources Humaines",
    "Droit",
    "Agriculture",
    "Élevage",
    "Mode & Création",
    "Coiffure & Esthétique",
    "Musique",
    "Art & Peinture",
    "Développement Personnel",
]

# Rubriques pour les épreuves
RUBRIQUES_EPREUVES = [
    {"nom": "Baccalauréat", "ordre": 1},
    {"nom": "BEPC", "ordre": 2},
    {"nom": "Probatoire", "ordre": 3},
    {"nom": "Concours Officiels", "ordre": 4},
]

# Catégories par rubrique
CATEGORIES_EPREUVES = {
    "Baccalauréat": [
        "Série A (Littéraire)", "Série A1", "Série A2", "Série A3", "Série A4",
        "Série B (Économique)", "Série C (Scientifique)", "Série D (Technologique)",
        "Série E (STI)", "Série F", "Série G", "Série H", "Série TI"
    ],
    "BEPC": ["Toutes séries", "Session Normale", "Session de Rattrapage"],
    "Probatoire": ["Série A", "Série C", "Série D", "Série TI"],
    "Concours Officiels": ["ENAM", "ENS", "IRIC", "CONCOURS MILITAIRE", "CONCOURS DE FONCTION PUBLIQUE"],
}

# Formations de test
FORMATIONS_TEST = [
    {
        "titre": "Maîtrisez Python de A à Z",
        "description_courte": "Apprenez Python de zéro au niveau avancé avec des projets concrets.",
        "description_longue": "Cette formation complète vous permettra de maîtriser Python pour le développement web, l'analyse de données et l'automatisation.",
        "prix": Decimal("25000"),
        "prix_promo": Decimal("15000"),
        "certifiee": True,
        "mise_en_avant": True,
        "duree": "8 semaines",
        "niveau": "Débutant à Avancé",
        "centres": ["Informatique & Programmation", "Développement Web", "Data Science"],
    },
    {
        "titre": "Cuisine Africaine Traditionnelle",
        "description_courte": "Les secrets de la cuisine africaine révélés par des chefs experts.",
        "description_longue": "Découvrez les saveurs authentiques de l'Afrique avec des recettes traditionnelles revisitées.",
        "prix": Decimal("15000"),
        "prix_promo": None,
        "certifiee": False,
        "mise_en_avant": True,
        "duree": "4 semaines",
        "niveau": "Débutant",
        "centres": ["Cuisine & Gastronomie"],
    },
    {
        "titre": "Marketing Digital pour Entrepreneurs",
        "description_courte": "Boostez votre business avec le marketing digital",
        "description_longue": "Apprenez les stratégies de marketing digital qui fonctionnent vraiment pour votre entreprise.",
        "prix": Decimal("35000"),
        "prix_promo": Decimal("25000"),
        "certifiee": True,
        "mise_en_avant": True,
        "duree": "6 semaines",
        "niveau": "Intermédiaire",
        "centres": ["Marketing Digital", "E-commerce"],
    },
    {
        "titre": "Création de Sites Web avec Django",
        "description_courte": "Devenez développeur web full-stack avec Django",
        "description_longue": "Maîtrisez Django pour créer des sites web professionnels et scalables.",
        "prix": Decimal("30000"),
        "prix_promo": None,
        "certifiee": True,
        "mise_en_avant": False,
        "duree": "10 semaines",
        "niveau": "Intermédiaire",
        "centres": ["Développement Web", "Informatique & Programmation"],
    },
    {
        "titre": "Pâtisserie Fine",
        "description_courte": "Les bases de la pâtisserie française",
        "description_longue": "Apprenez à réaliser des pâtisseries dignes des plus grandes maisons.",
        "prix": Decimal("20000"),
        "prix_promo": Decimal("12000"),
        "certifiee": True,
        "mise_en_avant": False,
        "duree": "5 semaines",
        "niveau": "Débutant",
        "centres": ["Cuisine & Gastronomie"],
    },
]

# Épreuves de test (par année)
ANNEES_EPREUVES = [2020, 2021, 2022, 2023, 2024]
SERIES = ['A', 'B', 'C', 'D', 'E', 'TI']


# ==================== FONCTIONS PRINCIPALES ====================

def get_or_create_super_admin():
    """Crée ou récupère un super administrateur"""
    user, created = User.objects.get_or_create(
        username="superadmin",
        defaults={
            "email": "superadmin@academianet.com",
            "is_superuser": True,
            "is_staff": True,
            "validation_automatique": True,
        }
    )
    if created:
        user.set_password("Admin123!")
        user.save()
        print("✅ Super administrateur créé: superadmin / Admin123!")
    else:
        print("✅ Super administrateur déjà existant")
    return user


def get_or_create_formateurs():
    """Crée des formateurs de test"""
    formateurs_data = [
        {"username": "jean_formateur", "email": "jean@test.com", "password": "Formateur123!"},
        {"username": "marie_formateur", "email": "marie@test.com", "password": "Formateur123!"},
        {"username": "paul_formateur", "email": "paul@test.com", "password": "Formateur123!"},
    ]
    
    formateurs = []
    for data in formateurs_data:
        user, created = User.objects.get_or_create(
            username=data["username"],
            defaults={
                "email": data["email"],
                "validation_automatique": True,
            }
        )
        if created:
            user.set_password(data["password"])
            user.save()
            print(f"✅ Formateur créé: {data['username']} / {data['password']}")
        else:
            print(f"✅ Formateur existant: {data['username']}")
        formateurs.append(user)
    
    return formateurs


def create_centres_interet():
    """Crée les centres d'intérêt prédéfinis (super admin uniquement)"""
    centres_crees = []
    for nom in CENTRES_INTERET:
        centre, created = CentreInteret.objects.get_or_create(
            nom=nom,
            defaults={
                'slug': slugify(nom),
                'actif': True,
                'statut': 'approuve',
            }
        )
        if created:
            print(f"✅ Centre d'intérêt créé: {nom}")
        centres_crees.append(centre)
    return centres_crees


def create_epreuves():
    """Crée des épreuves de test"""
    from website.models import RubriqueEpreuve, CategorieEpreuve, Epreuve
    
    rubriques_crees = []
    for rubrique_data in RUBRIQUES_EPREUVES:
        rubrique, created = RubriqueEpreuve.objects.get_or_create(
            nom=rubrique_data["nom"],
            defaults={"ordre": rubrique_data["ordre"], "actif": True}
        )
        if created:
            print(f"✅ Rubrique épreuve créée: {rubrique.nom}")
        rubriques_crees.append(rubrique)
    
    epreuves_crees = 0
    for rubrique in rubriques_crees:
        categories_noms = CATEGORIES_EPREUVES.get(rubrique.nom, ["Général"])
        for cat_nom in categories_noms:
            categorie, created = CategorieEpreuve.objects.get_or_create(
                rubrique=rubrique,
                nom=cat_nom,
                defaults={"actif": True}
            )
            if created:
                print(f"  ✅ Catégorie créée: {cat_nom}")
            
            # Créer des épreuves pour cette catégorie
            for annee in ANNEES_EPREUVES:
                for serie in random.sample(SERIES, random.randint(1, 3)):
                    # Éviter les doublons
                    titre = f"Épreuve de {rubrique.nom} {cat_nom} - {annee} - Série {serie}"
                    if not Epreuve.objects.filter(titre=titre).exists():
                        Epreuve.objects.create(
                            categorie=categorie,
                            titre=titre,
                            annee=annee,
                            serie=serie,
                            description=f"Épreuve officielle du {rubrique.nom} session {annee} série {serie}",
                            prix=Decimal(random.randint(500, 2000)),
                            statut='publie',
                            est_populaire=random.choice([True, False]),
                        )
                        epreuves_crees += 1
    
    print(f"✅ {epreuves_crees} épreuves créées")
    return epreuves_crees


def create_formations(formateurs, centres):
    """Crée des formations de test"""
    from website.models import Formation
    
    formations_crees = 0
    for i, formateur in enumerate(formateurs):
        for j, formation_data in enumerate(FORMATIONS_TEST):
            # Alterner les formateurs pour chaque formation
            createur = formateurs[j % len(formateurs)]
            
            titre = f"{formation_data['titre']} (v{random.randint(1,3)})" if random.choice([True, False]) else formation_data['titre']
            
            formation, created = Formation.objects.get_or_create(
                titre=titre,
                createur=createur,
                defaults={
                    "slug": slugify(titre),
                    "description_courte": formation_data['description_courte'],
                    "description_longue": formation_data['description_longue'],
                    "prix": formation_data['prix'],
                    "certifiee": formation_data['certifiee'],
                    "mise_en_avant": formation_data['mise_en_avant'],
                    "statut": "publie",
                    "nb_ventes": random.randint(0, 500),
                    "note_moyenne": round(random.uniform(3.5, 5.0), 1),
                    "date_publication": timezone.now() - timedelta(days=random.randint(1, 180)),
                }
            )
            
            if created:
                # Ajouter les centres d'intérêt
                centres_a_ajouter = [c for c in centres if c.nom in formation_data['centres']]
                formation.centres_interet.set(centres_a_ajouter)
                formations_crees += 1
                print(f"✅ Formation créée: {titre} (par {createur.username})")
    
    print(f"✅ {formations_crees} formations créées")
    return formations_crees


def create_ecoles():
    """Crée des écoles de test"""
    from website.models import Ecole, Classe, Matiere
    
    ecoles_data = [
        {"nom": "Lycée Général Leclerc", "ville": "Douala", "type": "public"},
        {"nom": "Collège Saint Joseph", "ville": "Yaoundé", "type": "prive"},
        {"nom": "École Internationale", "ville": "Douala", "type": "prive"},
    ]
    
    ecoles_crees = 0
    for data in ecoles_data:
        ecole, created = Ecole.objects.get_or_create(
            nom=data["nom"],
            defaults={
                "ville": data["ville"],
                "type_ecole": data["type"],
                "actif": True,
            }
        )
        if created:
            print(f"✅ École créée: {ecole.nom}")
            ecoles_crees += 1
            
            # Créer des classes pour cette école
            classes = ["6ème", "5ème", "4ème", "3ème", "Seconde", "Première", "Terminale"]
            for classe_nom in classes:
                classe, _ = Classe.objects.get_or_create(
                    ecole=ecole,
                    nom=classe_nom,
                    defaults={"niveau": classe_nom[:2]}
                )
            
            # Créer des matières
            matieres = ["Mathématiques", "Français", "Anglais", "Physique", "Histoire-Géo"]
            for matiere_nom in matieres:
                Matiere.objects.get_or_create(nom=matiere_nom)
    
    print(f"✅ {ecoles_crees} écoles créées")
    return ecoles_crees


def delete_all_seed_data():
    """Supprime TOUTES les données créées par ce script"""
    from website.models import Formation, CentreInteret, RubriqueEpreuve, CategorieEpreuve, Epreuve, Ecole, Classe
    
    print("\n⚠️  SUPPRESSION DES DONNÉES DE TEST")
    print("=" * 50)
    
    # Supprimer les formations créées par les formateurs de test
    test_usernames = ["jean_formateur", "marie_formateur", "paul_formateur"]
    test_users = User.objects.filter(username__in=test_usernames)
    
    formations_supprimees = Formation.objects.filter(createur__in=test_users).delete()[0]
    print(f"🗑️ {formations_supprimees} formations supprimées")
    
    # Supprimer les centres d'intérêt créés par ce script
    centres_supprimes = CentreInteret.objects.filter(nom__in=CENTRES_INTERET).delete()[0]
    print(f"🗑️ {centres_supprimes} centres d'intérêt supprimés")
    
    # Supprimer les épreuves créées par ce script
    epreuves_supprimes = Epreuve.objects.filter(titre__icontains="Épreuve de").delete()[0]
    print(f"🗑️ {epreuves_supprimes} épreuves supprimées")
    
    # Supprimer les catégories et rubriques vides
    CategorieEpreuve.objects.filter(epreuves__isnull=True).delete()
    RubriqueEpreuve.objects.filter(categories__isnull=True).delete()
    
    # Supprimer les écoles créées
    ecoles_supprimes = Ecole.objects.filter(nom__in=["Lycée Général Leclerc", "Collège Saint Joseph", "École Internationale"]).delete()[0]
    print(f"🗑️ {ecoles_supprimes} écoles supprimées")
    
    # Supprimer les formateurs de test (optionnel)
    test_users.delete()
    print(f"🗑️ Formateurs de test supprimés")
    
    print("\n✅ Nettoyage terminé !")


def main():
    """Fonction principale"""
    import sys
    
    # Vérifier si mode suppression
    if '--delete' in sys.argv:
        delete_all_seed_data()
        return
    
    print("\n" + "=" * 50)
    print("🌱 SEEDING DES DONNÉES DE TEST")
    print("=" * 50)
    print("\n⚠️  ATTENTION: Ce script ajoute des données de test.")
    print("   Pour les supprimer, exécutez: python seed_data.py --delete\n")
    
    # Vérifier que les modèles existent
    try:
        from website.models import CentreInteret, Formation, Epreuve, Ecole
    except ImportError as e:
        print(f"❌ Erreur: Impossible d'importer les modèles. Vérifiez que l'application 'website' est installée.")
        print(f"   Détail: {e}")
        return
    
    # Création des données
    print("📝 Création des données...\n")
    
    # 1. Créer les utilisateurs
    super_admin = get_or_create_super_admin()
    formateurs = get_or_create_formateurs()
    
    # 2. Créer les centres d'intérêt (admin uniquement)
    centres = create_centres_interet()
    
    # 3. Créer les écoles
    create_ecoles()
    
    # 4. Créer les épreuves
    create_epreuves()
    
    # 5. Créer les formations
    create_formations(formateurs, centres)
    
    print("\n" + "=" * 50)
    print("✅ SEEDING TERMINÉ !")
    print("=" * 50)
    
    # Résumé
    print(f"""
    📊 RÉSUMÉ DES DONNÉES CRÉÉES:
    - Super Admin: superadmin
    - Formateurs: {len(formateurs)} formateurs
    - Centres d'intérêt: {len(centres)}
    - Formations: {Formation.objects.filter(createur__in=formateurs).count()}
    - Épreuves: {Epreuve.objects.count()}
    - Écoles: {Ecole.objects.filter(nom__in=["Lycée Général Leclerc", "Collège Saint Joseph", "École Internationale"]).count()}
    
    🔑 IDENTIFIANTS DE CONNEXION:
    Super Admin: superadmin / Admin123!
    Formateurs: jean_formateur / Formateur123!
               marie_formateur / Formateur123!
               paul_formateur / Formateur123!
    """)


if __name__ == "__main__":
    main()