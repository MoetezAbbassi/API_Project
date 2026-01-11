import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import Exercise

app = create_app()

with app.app_context():
    print("🔍 Testing exercises query directly...\n")
    
    # Count exercises
    count = db.session.query(Exercise).count()
    print(f"✅ Total exercises in database: {count}\n")
    
    # Get first 5
    exercises = db.session.query(Exercise).limit(5).all()
    print(f"✅ Retrieved {len(exercises)} exercises:\n")
    
    for ex in exercises:
        print(f"   - {ex.name} ({ex.primary_muscle_group})")
    
    print("\n📊 Testing pagination...")
    from sqlalchemy import select
    stmt = select(Exercise).limit(10)
    result = db.session.execute(stmt)
    items = result.scalars().all()
    print(f"✅ Pagination test: {len(items)} items")