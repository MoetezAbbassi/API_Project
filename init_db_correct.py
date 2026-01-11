import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Delete old database
db_path = 'fitness_app.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"🗑️  Deleted old database")

# Import and create app
from app import create_app
from app.extensions import db

print("📦 Creating Flask app...")
app = create_app()

# The tables should now be created by create_app()
with app.app_context():
    print("\n✅ App created successfully!")
    print("✅ Database initialized!")
    
    # Verify tables exist
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    
    print(f"\n📊 Database has {len(tables)} tables:")
    for table in sorted(tables):
        print(f"   ✅ {table}")
    
    if len(tables) >= 11:
        print("\n🎉 Database is ready to use!")
    else:
        print(f"\n❌ Expected at least 11 tables, but got {len(tables)}")

print("\n✅ Done! Now run: python run.py")
