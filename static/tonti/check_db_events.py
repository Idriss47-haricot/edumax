import sqlite3
import os

print("=" * 50)
print("VÉRIFICATION DE LA BASE DE DONNÉES")
print("=" * 50)

db_path = os.path.join('instance', 'tontine.db')
print(f"Chemin DB: {db_path}")
print(f"Fichier existe: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lister toutes les tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("\n📋 Tables dans la base:")
    for table in tables:
        print(f"  - {table[0]}")
        
        # Compter les enregistrements
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"      {count} enregistrements")
    
    # Vérifier spécifiquement la table evenements
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evenements'")
    if cursor.fetchone():
        print("\n✅ Table 'evenements' trouvée")
        
        cursor.execute("SELECT * FROM evenements")
        events = cursor.fetchall()
        print(f"   {len(events)} événements trouvés")
        
        for event in events:
            print(f"   - ID: {event[0]}, Nom: {event[1]}, Date: {event[4]}")
    else:
        print("\n❌ Table 'evenements' NON trouvée")
    
    conn.close()
else:
    print("❌ Base de données non trouvée!")

print("=" * 50)