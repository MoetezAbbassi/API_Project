import os
import sqlite3

print("🔍 Checking current database state...\n")

db_path = 'fitness_app.db'

if os.path.exists(db_path):
    print(f"✅ Database file exists: {db_path}")
    print(f"   Size: {os.path.getsize(db_path)} bytes\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    if tables:
        print(f"✅ Found {len(tables)} tables:")
        for (table,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} rows")
    else:
        print("❌ NO TABLES FOUND!")
    
    conn.close()
else:
    print(f"❌ Database file NOT found: {db_path}")
