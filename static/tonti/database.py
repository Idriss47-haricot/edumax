import sqlite3
import os
from datetime import datetime
import random

def get_db():
    """Retourne une connexion à la base de données"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'tontine.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def init_db():
    """Initialise la base de données avec toutes les tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # ============================================
    # TABLES EXISTANTES (mises à jour)
    # ============================================
    
    # Table des membres
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS membres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            telephone TEXT,
            email TEXT,
            date_adhesion DATE NOT NULL,
            statut TEXT DEFAULT 'actif'
        )
    ''')
    
    # Table des séances
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_seance TEXT UNIQUE NOT NULL,
            date_seance DATE NOT NULL,
            heure_debut TIME,
            heure_fin TIME,
            theme TEXT,
            lieu TEXT,
            ordre_du_jour TEXT,
            compte_rendu TEXT,
            statut TEXT DEFAULT 'prevue',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    
    # Table des présences
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS presences_seance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seance_id INTEGER NOT NULL,
            membre_id INTEGER NOT NULL,
            heure_arrivee TIME,
            est_present BOOLEAN DEFAULT 0,
            retard BOOLEAN DEFAULT 0,
            justificatif TEXT,
            FOREIGN KEY (seance_id) REFERENCES seances (id) ON DELETE CASCADE,
            FOREIGN KEY (membre_id) REFERENCES membres (id) ON DELETE CASCADE,
            UNIQUE(seance_id, membre_id)
        )
    ''')
    
    # Table des cotisations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cotisations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_cotisation TEXT NOT NULL,
            montant_total REAL DEFAULT 0,
            date_creation DATE NOT NULL,
            statut TEXT DEFAULT 'active'
        )
    ''')
    
    # Table de liaison cotisations-membres
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cotisation_membres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cotisation_id INTEGER NOT NULL,
            membre_id INTEGER NOT NULL,
            date_ajout DATE NOT NULL,
            a_cotise BOOLEAN DEFAULT 0,
            montant_paye REAL DEFAULT 0,
            seance_id INTEGER,
            FOREIGN KEY (cotisation_id) REFERENCES cotisations (id) ON DELETE CASCADE,
            FOREIGN KEY (membre_id) REFERENCES membres (id) ON DELETE CASCADE,
            FOREIGN KEY (seance_id) REFERENCES seances (id)
        )
    ''')
    
    # Table des sanctions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sanctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_sanction TEXT UNIQUE NOT NULL,
            membre_id INTEGER NOT NULL,
            type_sanction TEXT NOT NULL,
            motif TEXT NOT NULL,
            montant_amende REAL DEFAULT 0,
            date_sanction DATE NOT NULL,
            date_application DATE,
            statut TEXT DEFAULT 'appliquee',
            description TEXT,
            appliquee_par INTEGER,
            seance_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (membre_id) REFERENCES membres (id),
            FOREIGN KEY (appliquee_par) REFERENCES membres (id),
            FOREIGN KEY (seance_id) REFERENCES seances (id)
        )
    ''')
    
    # Table des événements
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evenements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_evenement TEXT NOT NULL,
            type_evenement TEXT NOT NULL,
            montant_fixe REAL NOT NULL,
            date_evenement DATE NOT NULL,
            date_limite_cotisation DATE,
            description TEXT,
            statut TEXT DEFAULT 'prevue',
            delai_remboursement INTEGER DEFAULT 30,
            created_at DATE NOT NULL
        )
    ''')
    
    # Table de participation aux événements
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participations_evenement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evenement_id INTEGER NOT NULL,
            membre_id INTEGER NOT NULL,
            mode_participation TEXT NOT NULL,
            montant_paye REAL NOT NULL,
            date_participation DATE NOT NULL,
            date_remboursement_prevue DATE,
            date_remboursement_effectif DATE,
            rembourse BOOLEAN DEFAULT 0,
            a_participe BOOLEAN DEFAULT 1,
            fonds_opere BOOLEAN DEFAULT 0,
            seance_id INTEGER,
            FOREIGN KEY (evenement_id) REFERENCES evenements (id) ON DELETE CASCADE,
            FOREIGN KEY (membre_id) REFERENCES membres (id) ON DELETE CASCADE,
            FOREIGN KEY (seance_id) REFERENCES seances (id)
        )
    ''')
    
    # ============================================
    # NOUVELLES TABLES PHASE 1
    # ============================================
    
    # Table des fonds de caisse (uniformisé)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fonds_caisse (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            membre_id INTEGER NOT NULL UNIQUE,
            montant_base REAL NOT NULL DEFAULT 100000,
            solde_actuel REAL DEFAULT 100000,
            date_creation DATE NOT NULL,
            date_derniere_mise_a_jour DATE,
            statut TEXT DEFAULT 'actif',
            FOREIGN KEY (membre_id) REFERENCES membres (id) ON DELETE CASCADE
        )
    ''')
    
    # Table de l'épargne
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS epargne (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            membre_id INTEGER NOT NULL UNIQUE,
            solde_actuel REAL DEFAULT 0,
            depot_total REAL DEFAULT 0,
            retrait_total REAL DEFAULT 0,
            interets_generes REAL DEFAULT 0,
            taux_interet_annuel REAL DEFAULT 0,
            date_derniere_operation DATE,
            statut TEXT DEFAULT 'actif',
            created_at DATE NOT NULL,
            updated_at DATE,
            FOREIGN KEY (membre_id) REFERENCES membres (id) ON DELETE CASCADE
        )
    ''')
    
    # Table des opérations d'épargne
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operations_epargne (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epargne_id INTEGER NOT NULL,
            type_operation TEXT NOT NULL,
            montant REAL NOT NULL,
            date_operation DATE NOT NULL,
            description TEXT,
            seance_id INTEGER,
            solde_apres REAL NOT NULL,
            FOREIGN KEY (epargne_id) REFERENCES epargne (id) ON DELETE CASCADE,
            FOREIGN KEY (seance_id) REFERENCES seances (id)
        )
    ''')
    
    # Table des conditions de prêt (paramètres)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conditions_pret (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ratio_max_epargne REAL DEFAULT 2,
            duree_max_mois INTEGER DEFAULT 12,
            taux_interet_min REAL DEFAULT 0,
            taux_interet_max REAL DEFAULT 10,
            presence_min_pourcentage REAL DEFAULT 50,
            cotisations_a_jour BOOLEAN DEFAULT 1,
            sanction_max_autorise INTEGER DEFAULT 2,
            created_at DATE NOT NULL,
            updated_at DATE
        )
    ''')
    
    # Table des demandes de prêt
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS demandes_pret (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_demande TEXT UNIQUE NOT NULL,
            membre_id INTEGER NOT NULL,
            montant_demande REAL NOT NULL,
            montant_accorde REAL,
            duree_mois INTEGER NOT NULL,
            taux_interet REAL,
            motif TEXT,
            date_demande DATE NOT NULL,
            date_decision DATE,
            statut TEXT DEFAULT 'en_attente',
            motif_refus TEXT,
            valide_par INTEGER,
            seance_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (membre_id) REFERENCES membres (id),
            FOREIGN KEY (valide_par) REFERENCES membres (id),
            FOREIGN KEY (seance_id) REFERENCES seances (id)
        )
    ''')
    
    # Table des prêts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_pret TEXT UNIQUE NOT NULL,
            demande_id INTEGER,
            preteur_id INTEGER,
            emprunteur_id INTEGER,
            membre_id INTEGER,
            montant_principal REAL NOT NULL,
            taux_interet REAL NOT NULL,
            montant_total REAL NOT NULL,
            montant_restant REAL NOT NULL,
            date_octroi DATE NOT NULL,
            date_echeance DATE NOT NULL,
            duree_mois INTEGER NOT NULL,
            type_pret TEXT DEFAULT 'standard',
            description TEXT,
            statut TEXT DEFAULT 'en_cours',
            source_fonds TEXT DEFAULT 'fonds_caisse',
            created_at DATE NOT NULL,
            updated_at DATE,
            FOREIGN KEY (demande_id) REFERENCES demandes_pret (id),
            FOREIGN KEY (preteur_id) REFERENCES membres (id),
            FOREIGN KEY (emprunteur_id) REFERENCES membres (id),
            FOREIGN KEY (membre_id) REFERENCES membres (id)
        )
    ''')
    
    # Table des échéances de prêt
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS echeances_pret (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pret_id INTEGER NOT NULL,
            numero_echeance INTEGER NOT NULL,
            montant_echeance REAL NOT NULL,
            date_echeance DATE NOT NULL,
            date_paiement DATE,
            statut TEXT DEFAULT 'en_attente',
            montant_paye REAL DEFAULT 0,
            penalite_retard REAL DEFAULT 0,
            seance_id INTEGER,
            FOREIGN KEY (pret_id) REFERENCES prets (id) ON DELETE CASCADE,
            FOREIGN KEY (seance_id) REFERENCES seances (id)
        )
    ''')
    
    # Table des remboursements
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS remboursements_pret (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pret_id INTEGER NOT NULL,
            echeance_id INTEGER,
            montant REAL NOT NULL,
            date_remboursement DATE NOT NULL,
            mode_remboursement TEXT NOT NULL,
            fonds_source_id INTEGER,
            penalite REAL DEFAULT 0,
            description TEXT,
            seance_id INTEGER,
            FOREIGN KEY (pret_id) REFERENCES prets (id) ON DELETE CASCADE,
            FOREIGN KEY (echeance_id) REFERENCES echeances_pret (id),
            FOREIGN KEY (fonds_source_id) REFERENCES fonds_caisse (id),
            FOREIGN KEY (seance_id) REFERENCES seances (id)
        )
    ''')
    
    # Table des bilans de séance
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bilans_seance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seance_id INTEGER NOT NULL,
            date_generation DATE NOT NULL,
            nb_presents INTEGER DEFAULT 0,
            nb_absents INTEGER DEFAULT 0,
            nb_retards INTEGER DEFAULT 0,
            taux_presence REAL DEFAULT 0,
            total_cotisations REAL DEFAULT 0,
            total_prets REAL DEFAULT 0,
            total_remboursements REAL DEFAULT 0,
            total_sanctions REAL DEFAULT 0,
            total_epargne_collectee REAL DEFAULT 0,
            evolution_fonds REAL DEFAULT 0,
            commentaires TEXT,
            format TEXT DEFAULT 'html',
            generated_by INTEGER,
            FOREIGN KEY (seance_id) REFERENCES seances (id) ON DELETE CASCADE,
            FOREIGN KEY (generated_by) REFERENCES membres (id)
        )
    ''')
    
    # Table des bilans individuels
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bilans_membre (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            membre_id INTEGER NOT NULL,
            date_generation DATE NOT NULL,
            periode_debut DATE,
            periode_fin DATE,
            total_cotise REAL DEFAULT 0,
            total_epargne REAL DEFAULT 0,
            solde_fonds REAL DEFAULT 0,
            solde_epargne REAL DEFAULT 0,
            prets_en_cours INTEGER DEFAULT 0,
            montant_prets_en_cours REAL DEFAULT 0,
            prets_rembourses INTEGER DEFAULT 0,
            montant_prets_rembourses REAL DEFAULT 0,
            sanctions_recues INTEGER DEFAULT 0,
            montant_sanctions REAL DEFAULT 0,
            taux_presence REAL DEFAULT 0,
            format TEXT DEFAULT 'html',
            FOREIGN KEY (membre_id) REFERENCES membres (id) ON DELETE CASCADE
        )
    ''')
    
    # Table des opérations de fonds (historique)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operations_fonds_caisse (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fonds_id INTEGER NOT NULL,
            type_operation TEXT NOT NULL,
            montant REAL NOT NULL,
            date_operation DATE NOT NULL,
            description TEXT,
            evenement_id INTEGER,
            pret_id INTEGER,
            seance_id INTEGER,
            solde_apres REAL NOT NULL,
            FOREIGN KEY (fonds_id) REFERENCES fonds_caisse (id) ON DELETE CASCADE,
            FOREIGN KEY (evenement_id) REFERENCES evenements (id),
            FOREIGN KEY (pret_id) REFERENCES prets (id),
            FOREIGN KEY (seance_id) REFERENCES seances (id)
        )
    ''')
    
    # Table des alertes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alertes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            membre_id INTEGER,
            type_alerte TEXT NOT NULL,
            message TEXT NOT NULL,
            date_alerte DATE NOT NULL,
            date_lecture DATE,
            statut TEXT DEFAULT 'non_lu',
            lien_action TEXT,
            FOREIGN KEY (membre_id) REFERENCES membres (id) ON DELETE CASCADE
        )
    ''')
    
    # ============================================
    # TABLES DE LIAISON SÉANCE
    # ============================================
    
    # Table de liaison séance-cotisations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seance_cotisations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seance_id INTEGER NOT NULL,
            cotisation_id INTEGER NOT NULL,
            montant_total REAL,
            statut TEXT DEFAULT 'en_attente',
            FOREIGN KEY (seance_id) REFERENCES seances (id) ON DELETE CASCADE,
            FOREIGN KEY (cotisation_id) REFERENCES cotisations (id) ON DELETE CASCADE
        )
    ''')
    
    # Table de liaison séance-prêts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seance_prets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seance_id INTEGER NOT NULL,
            pret_id INTEGER NOT NULL,
            montant_avant REAL,
            montant_apres REAL,
            remboursements_effectues TEXT,
            FOREIGN KEY (seance_id) REFERENCES seances (id) ON DELETE CASCADE,
            FOREIGN KEY (pret_id) REFERENCES prets (id) ON DELETE CASCADE
        )
    ''')
    
    # Table de liaison séance-sanctions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seance_sanctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seance_id INTEGER NOT NULL,
            sanction_id INTEGER NOT NULL,
            montant_amende REAL,
            appliquee BOOLEAN DEFAULT 0,
            FOREIGN KEY (seance_id) REFERENCES seances (id) ON DELETE CASCADE,
            FOREIGN KEY (sanction_id) REFERENCES sanctions (id) ON DELETE CASCADE
        )
    ''')
    
    # Table de liaison séance-événements
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seance_evenements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seance_id INTEGER NOT NULL,
            evenement_id INTEGER NOT NULL,
            statut TEXT,
            commentaires TEXT,
            FOREIGN KEY (seance_id) REFERENCES seances (id) ON DELETE CASCADE,
            FOREIGN KEY (evenement_id) REFERENCES evenements (id) ON DELETE CASCADE
        )
    ''')
    
    # Table de liaison séance-fonds
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seance_fonds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seance_id INTEGER NOT NULL,
            fonds_id INTEGER NOT NULL,
            solde_avant REAL,
            solde_apres REAL,
            operations TEXT,
            FOREIGN KEY (seance_id) REFERENCES seances (id) ON DELETE CASCADE,
            FOREIGN KEY (fonds_id) REFERENCES fonds_caisse (id) ON DELETE CASCADE
        )
    ''')
    
    # Table de liaison séance-épargne
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seance_epargne (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seance_id INTEGER NOT NULL,
            epargne_id INTEGER NOT NULL,
            operations TEXT,
            FOREIGN KEY (seance_id) REFERENCES seances (id) ON DELETE CASCADE,
            FOREIGN KEY (epargne_id) REFERENCES epargne (id) ON DELETE CASCADE
        )
    ''')
    
    # Table des transferts de cotisation
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transferts_cotisation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cotisation_id INTEGER NOT NULL,
            donneur_id INTEGER NOT NULL,
            receveur_id INTEGER NOT NULL,
            montant REAL NOT NULL,
            date_transfert DATE NOT NULL,
            description TEXT,
            statut TEXT DEFAULT 'effectue',
            pret_genere_id INTEGER,
            seance_id INTEGER,
            FOREIGN KEY (cotisation_id) REFERENCES cotisations (id),
            FOREIGN KEY (donneur_id) REFERENCES membres (id),
            FOREIGN KEY (receveur_id) REFERENCES membres (id),
            FOREIGN KEY (pret_genere_id) REFERENCES prets (id),
            FOREIGN KEY (seance_id) REFERENCES seances (id)
        )
    ''')
    
    conn.commit()
    print("✅ Base de données initialisée avec succès!")
    
    # Insérer les paramètres par défaut et données d'exemple
    insert_default_data(conn)
    insert_sample_data(conn)
    
    conn.close()

def insert_default_data(conn):
    """Insère les paramètres par défaut"""
    cursor = conn.cursor()
    
    # Insérer les conditions de prêt par défaut
    cursor.execute("SELECT COUNT(*) FROM conditions_pret")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO conditions_pret 
            (ratio_max_epargne, duree_max_mois, taux_interet_min, taux_interet_max, 
             presence_min_pourcentage, cotisations_a_jour, sanction_max_autorise, created_at)
            VALUES (2, 12, 0, 10, 50, 1, 2, date('now'))
        ''')
        print("✅ Conditions de prêt par défaut insérées")
    
    conn.commit()

def insert_sample_data(conn):
    """Insère des données d'exemple pour les tests"""
    cursor = conn.cursor()
    
    # Vérifier si des données existent déjà
    cursor.execute("SELECT COUNT(*) FROM membres")
    if cursor.fetchone()[0] == 0:
        # ========== INSERTION DES MEMBRES ==========
        membres = [
            ('Diallo', 'Amadou', '771234567', 'amadou@email.com', '2024-01-15'),
            ('Traoré', 'Fatou', '772345678', 'fatou@email.com', '2024-01-20'),
            ('Sow', 'Moussa', '773456789', 'moussa@email.com', '2024-02-01'),
            ('Bah', 'Aissatou', '774567890', 'aissatou@email.com', '2024-02-10'),
            ('Barry', 'Ibrahima', '775678901', 'ibrahima@email.com', '2024-02-15'),
        ]
        
        cursor.executemany(
            "INSERT INTO membres (nom, prenom, telephone, email, date_adhesion) VALUES (?, ?, ?, ?, ?)",
            membres
        )
        
        # Récupérer les IDs des membres
        cursor.execute("SELECT id FROM membres")
        membres_ids = [m['id'] for m in cursor.fetchall()]
        
        # ========== FONDS DE CAISSE ==========
        for membre_id in membres_ids:
            montant_base = 100000
            cursor.execute('''
                INSERT INTO fonds_caisse (membre_id, montant_base, solde_actuel, date_creation, date_derniere_mise_a_jour)
                VALUES (?, ?, ?, date('now'), date('now'))
            ''', (membre_id, montant_base, montant_base))
        
        # ========== ÉPARGNE ==========
        for membre_id in membres_ids:
            solde_initial = random.choice([50000, 100000, 150000, 200000])
            cursor.execute('''
                INSERT INTO epargne (membre_id, solde_actuel, depot_total, created_at, updated_at)
                VALUES (?, ?, ?, date('now'), date('now'))
            ''', (membre_id, solde_initial, solde_initial))
        
        # ========== SÉANCES ==========
        seances = [
            ('SE001', '2024-03-01', '18:00', '20:30', 'Séance ordinaire', 'Salle 1', 
             'Ordre du jour: Cotisations mensuelles, Prêts', None, 'terminee'),
            ('SE002', '2024-03-08', '18:00', '20:15', 'Séance ordinaire', 'Salle 2', 
             'Ordre du jour: Événements à venir, Sanctions', None, 'terminee'),
            ('SE003', '2024-03-15', '18:00', None, 'Séance spéciale', 'Salle 1', 
             'Ordre du jour: Préparation fête fin année', None, 'en_cours'),
            ('SE004', '2024-03-22', '18:00', None, 'Séance bilan', 'Salle 3', 
             'Ordre du jour: Bilan trimestriel', None, 'prevue'),
        ]
        
        for seance in seances:
            cursor.execute('''
                INSERT INTO seances (numero_seance, date_seance, heure_debut, heure_fin, theme, lieu, ordre_du_jour, compte_rendu, statut)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', seance)
        
        # Récupérer les IDs des séances
        cursor.execute("SELECT id FROM seances")
        seances_ids = [s['id'] for s in cursor.fetchall()]
        
        # ========== COTISATIONS ==========
        cotisations = [
            ('Cotisation mensuelle Mars 2024', 500000, '2024-03-01'),
            ('Cotisation spéciale Équipement', 250000, '2024-03-15'),
            ('Fond de solidarité', 250000, '2024-03-20'),
        ]
        
        for cotisation in cotisations:
            cursor.execute(
                "INSERT INTO cotisations (nom_cotisation, montant_total, date_creation) VALUES (?, ?, ?)",
                cotisation
            )
            cotisation_id = cursor.lastrowid
            
            for membre_id in membres_ids:
                a_cotise = 1 if random.choice([True, False]) else 0
                montant_paye = cotisation[1] / len(membres_ids) if a_cotise else 0
                cursor.execute('''
                    INSERT INTO cotisation_membres (cotisation_id, membre_id, date_ajout, a_cotise, montant_paye, seance_id)
                    VALUES (?, ?, date('now'), ?, ?, ?)
                ''', (cotisation_id, membre_id, a_cotise, montant_paye, random.choice(seances_ids)))
        
        # ========== DEMANDES DE PRÊT ==========
        demandes = [
            (membres_ids[0], 50000, 3, 'Besoin d\'argent pour travaux', 'en_attente'),
            (membres_ids[1], 100000, 6, 'Achat de matériel', 'approuve'),
            (membres_ids[2], 75000, 4, 'Frais de scolarité', 'refuse'),
        ]
        
        for demande in demandes:
            numero = f"DEM-{datetime.now().strftime('%Y%m')}-{str(random.randint(1,999)).zfill(3)}"
            cursor.execute('''
                INSERT INTO demandes_pret 
                (numero_demande, membre_id, montant_demande, duree_mois, motif, statut, date_demande)
                VALUES (?, ?, ?, ?, ?, ?, date('now'))
            ''', (numero, demande[0], demande[1], demande[2], demande[3], demande[4]))
        
        # ========== PRÊTS ==========
        prets = [
            ('PRET-001', membres_ids[0], membres_ids[1], 50000, 5, 52500, 52500, '2024-01-15', '2024-04-15', 3, 'standard', 'Prêt pour urgence'),
            ('PRET-002', membres_ids[2], membres_ids[3], 100000, 5, 105000, 105000, '2024-02-01', '2024-05-01', 3, 'standard', 'Prêt pour équipement'),
        ]
        
        for pret in prets:
            cursor.execute('''
                INSERT INTO prets 
                (numero_pret, preteur_id, emprunteur_id, montant_principal, taux_interet, 
                 montant_total, montant_restant, date_octroi, date_echeance, duree_mois, type_pret, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'))
            ''', pret)
            pret_id = cursor.lastrowid
            
            montant_par_echeance = pret[6] / pret[9]
            for i in range(1, pret[9] + 1):
                cursor.execute('''
                    INSERT INTO echeances_pret (pret_id, numero_echeance, montant_echeance, date_echeance)
                    VALUES (?, ?, ?, date('now', ?))
                ''', (pret_id, i, montant_par_echeance, f'+{i} months'))
        
        # ========== ÉVÉNEMENTS ==========
        evenements = [
            ('Deuil Famille Diallo', 'deuil', 25000, '2024-04-15', '2024-04-10', 
             'Deuil à Kamsar', 'prevue', 30),
            ('Fête de fin d\'année', 'culturel', 50000, '2024-12-20', '2024-12-15', 
             'Fête de fin d\'année', 'prevue', 45),
            ('Assistance médicale', 'assistance', 35000, '2024-05-01', '2024-04-28', 
             'Assistance pour soins', 'prevue', 60),
        ]
        
        for evt in evenements:
            cursor.execute('''
                INSERT INTO evenements 
                (nom_evenement, type_evenement, montant_fixe, date_evenement, 
                 date_limite_cotisation, description, statut, delai_remboursement, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, date('now'))
            ''', evt)
        
        # ========== SANCTIONS ==========
        sanctions = [
            ('SAN-2024-0001', membres_ids[1], 'retard', 'Retard de 30 minutes à la séance', 5000, '2024-03-01'),
            ('SAN-2024-0002', membres_ids[3], 'absence', 'Absence non justifiée', 10000, '2024-03-08'),
            ('SAN-2024-0003', membres_ids[0], 'non-paiement', 'Non-paiement de la cotisation', 7500, '2024-03-15'),
        ]
        
        for sanction in sanctions:
            cursor.execute('''
                INSERT INTO sanctions 
                (numero_sanction, membre_id, type_sanction, motif, montant_amende, date_sanction, statut)
                VALUES (?, ?, ?, ?, ?, ?, 'appliquee')
            ''', sanction)
        
        # ========== COMMIT FINAL ==========
        conn.commit()
        print("✅ Données d'exemple insérées!")

if __name__ == '__main__':
    init_db()