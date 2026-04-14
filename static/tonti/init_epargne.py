import sqlite3
import os

def init_tous_les_comptes_epargne():
    """Crée un compte épargne pour TOUS les membres (même inactifs)"""
    db_path = os.path.join('instance', 'tontine.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Récupérer tous les membres
    cursor.execute("SELECT id, nom, prenom, statut FROM membres")
    membres = cursor.fetchall()
    
    comptes_crees = 0
    comptes_existants = 0
    
    for membre in membres:
        cursor.execute("SELECT id FROM epargne WHERE membre_id = ?", (membre[0],))
        if cursor.fetchone():
            comptes_existants += 1
        else:
            cursor.execute('''
                INSERT INTO epargne (membre_id, solde_actuel, depot_total, retrait_total, created_at, updated_at)
                VALUES (?, 0, 0, 0, date('now'), date('now'))
            ''', (membre[0],))
            comptes_crees += 1
            print(f"✅ Compte épargne créé pour {membre[1]} {membre[2]} (statut: {membre[3]})")
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 RÉSULTAT:")
    print(f"   - Comptes déjà existants : {comptes_existants}")
    print(f"   - Nouveaux comptes créés : {comptes_crees}")
    print(f"   - Total membres : {len(membres)}")

if __name__ == '__main__':
    init_tous_les_comptes_epargne()
    print("\n✅ Initialisation terminée !")