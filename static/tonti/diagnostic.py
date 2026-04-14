import sqlite3
import os

db_path = os.path.join('instance', 'tontine.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*60)
print("DIAGNOSTIC DE LA BASE DE DONNÉES")
print("="*60)

# Lister toutes les tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("\n📋 TABLES DANS LA BASE:")
for table in tables:
    print(f"\n  📁 {table[0]}")
    
    # Afficher la structure de la table
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"     - {col[1]} ({col[2]})")
    
    # Compter les enregistrements
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f"     📊 {count} enregistrements")

conn.close()
print("\n" + "="*60)