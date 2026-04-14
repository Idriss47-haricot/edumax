import sqlite3
import os
from datetime import datetime

def get_db():
    """Retourne une connexion à la base de données"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'tontine.db')
    # Créer le dossier instance s'il n'existe pas
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise la base de données avec les tables nécessaires"""
    conn = get_db()
    cursor = conn.cursor()
    
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
            date_seance DATE NOT NULL,
            theme TEXT,
            lieu TEXT,
            statut TEXT DEFAULT 'prevue'
        )
    ''')
    
    # Table des cotisations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cotisations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            membre_id INTEGER NOT NULL,
            seance_id INTEGER NOT NULL,
            montant REAL NOT NULL,
            date_cotisation DATE NOT NULL,
            mode_paiement TEXT,
            FOREIGN KEY (membre_id) REFERENCES membres (id),
            FOREIGN KEY (seance_id) REFERENCES seances (id)
        )
    ''')
    
    # Table des fonds de caisse
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fonds_caisse (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_operation DATE NOT NULL,
            montant_entree REAL DEFAULT 0,
            montant_sortie REAL DEFAULT 0,
            solde_cumule REAL NOT NULL,
            description TEXT
        )
    ''')
    
    # Table des prêts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            membre_id INTEGER NOT NULL,
            montant REAL NOT NULL,
            date_octroi DATE NOT NULL,
            date_echeance DATE,
            interets REAL DEFAULT 0,
            statut TEXT DEFAULT 'en_cours',
            FOREIGN KEY (membre_id) REFERENCES membres (id)
        )
    ''')
    
    # Table des sanctions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sanctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            membre_id INTEGER NOT NULL,
            type_sanction TEXT NOT NULL,
            motif TEXT,
            montant_amende REAL DEFAULT 0,
            date_sanction DATE NOT NULL,
            statut TEXT DEFAULT 'appliquee',
            FOREIGN KEY (membre_id) REFERENCES membres (id)
        )
    ''')
    
    # Table des événements
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evenements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            description TEXT,
            date_evenement DATE NOT NULL,
            lieu TEXT,
            budget REAL,
            organisateur TEXT
        )
    ''')
    
    # Table des règlements
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reglements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            membre_id INTEGER NOT NULL,
            pret_id INTEGER,
            montant REAL NOT NULL,
            date_reglement DATE NOT NULL,
            type_reglement TEXT,
            FOREIGN KEY (membre_id) REFERENCES membres (id),
            FOREIGN KEY (pret_id) REFERENCES prets (id)
        )
    ''')
    
    # Table des rapports
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rapports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_rapport TEXT NOT NULL,
            date_generation DATE NOT NULL,
            contenu TEXT,
            format TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Base de données initialisée avec succès!")

def insert_sample_data():
    """Insère des données d'exemple pour les tests"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Vérifier si des données existent déjà
    cursor.execute("SELECT COUNT(*) FROM membres")
    if cursor.fetchone()[0] == 0:
        # Ajouter des membres exemple
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
        
        # Ajouter des séances exemple
        seances = [
            ('2024-03-01', 'Séance ordinaire', 'Salle 1'),
            ('2024-03-08', 'Séance ordinaire', 'Salle 2'),
            ('2024-03-15', 'Séance spéciale', 'Salle 1'),
        ]
        
        cursor.executemany(
            "INSERT INTO seances (date_seance, theme, lieu) VALUES (?, ?, ?)",
            seances
        )
        
        print("✅ Données d'exemple insérées!")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    insert_sample_data()