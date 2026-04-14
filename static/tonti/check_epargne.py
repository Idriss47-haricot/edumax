import sqlite3
import os

def verifier_creer_comptes_epargne():
    """Vérifie que tous les membres actifs ont un compte épargne"""
    db_path = os.path.join('instance', 'tontine.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Récupérer tous les membres actifs
    cursor.execute("SELECT id, nom, prenom FROM membres WHERE statut = 'actif'")
    membres = cursor.fetchall()
    
    comptes_crees = 0
    
    for membre in membres:
        # Vérifier si le membre a un compte épargne
        cursor.execute("SELECT id FROM epargne WHERE membre_id = ?", (membre[0],))
        if not cursor.fetchone():
            # Créer le compte
            cursor.execute('''
                INSERT INTO epargne (membre_id, solde_actuel, depot_total, retrait_total, created_at, updated_at)
                VALUES (?, 0, 0, 0, date('now'), date('now'))
            ''', (membre[0],))
            comptes_crees += 1
            print(f"✅ Compte épargne créé pour {membre[1]} {membre[2]}")
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Résultat : {comptes_crees} comptes épargne créés")
    return comptes_crees

if __name__ == '__main__':
    verifier_creer_comptes_epargne()