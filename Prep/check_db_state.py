import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
import sqlite3

app = create_app()

with app.app_context():
    print("🔍 Checking database state...\n")
    
    # Check SQLAlchemy
    try:
        from app.models import Exercise
        existing = db.session.query(Exercise).count()
        print(f"✅ SQLAlchemy: Found {existing} exercises")
    except Exception as e:
        print(f"❌ SQLAlchemy error: {e}")
    
    # Check raw SQLite
    try:
        conn = sqlite3.connect('fitness_app.db')
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\n✅ SQLite: Found {len(tables)} tables:")
        for (table,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   - {table}: {count} rows")
        
        conn.close()
    except Exception as e:
        print(f"❌ SQLite error: {e}")
