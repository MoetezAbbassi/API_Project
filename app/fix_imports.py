import os
import re

# Scan all route files for old imports
routes_dir = 'app/routes'
bad_imports = []

print("🔍 Scanning for old imports...\n")

for filename in os.listdir(routes_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(routes_dir, filename)
        with open(filepath, 'r') as f:
            content = f.read()
            if 'from app import db' in content:
                bad_imports.append(filename)
                print(f"❌ {filename} - NEEDS FIX")
            else:
                print(f"✅ {filename} - OK")

# Also check models.py
models_path = 'app/models.py'
with open(models_path, 'r') as f:
    content = f.read()
    if 'from app import db' in content:
        bad_imports.append('models.py')
        print(f"\n❌ models.py - NEEDS FIX")
    else:
        print(f"\n✅ models.py - OK")

if bad_imports:
    print(f"\n\n🚨 FILES TO FIX ({len(bad_imports)}):")
    for f in bad_imports:
        print(f"   - {f}")
    print("\nRunning fixes...\n")
    
    # Fix each file
    for filename in bad_imports:
        if filename == 'models.py':
            filepath = 'app/models.py'
        else:
            filepath = os.path.join(routes_dir, filename)
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Replace the import
        new_content = content.replace('from app import db', 'from app.extensions import db')
        
        with open(filepath, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Fixed {filename}")
else:
    print("\n\n✅ All files are correct!")

print("\n✅ All imports fixed! Restart Flask now.")
