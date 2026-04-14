import sqlite3
import os

db_path = os.path.join('instance', 'tontine.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 50)
print("VÉRIFICATION DES ÉVÉNEMENTS")
print("=" * 50)

# Vérifier si la table existe
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evenements'")
if cursor.fetchone():
    print("✅ Table 'evenements' existe")
    
    # Compter les événements
    cursor.execute("SELECT COUNT(*) FROM evenements")
    count = cursor.fetchone()[0]
    print(f"📊 Nombre d'événements: {count}")
    
    # Afficher les événements
    cursor.execute("SELECT * FROM evenements")
    events = cursor.fetchall()
    for evt in events:
        print(f"   - {evt[1]} ({evt[4]}) - {evt[3]} FCFA")
else:
    print("❌ Table 'evenements' n'existe pas")

conn.close()
print("=" * 50)