import os

print("🔍 Checking app/models.py...\n")

models_path = 'app/models.py'

if os.path.exists(models_path):
    with open(models_path, 'r') as f:
        content = f.read()
    
    # Check for class definitions
    import re
    classes = re.findall(r'class (\w+)\(db\.Model\)', content)
    
    print(f"📄 Found {len(classes)} model classes:")
    for cls in classes:
        print(f"   - {cls}")
    
    # Show first 1500 chars
    print(f"\n📋 First 1500 characters:\n")
    print(content[:1500])
    print("\n...")
else:
    print(f"❌ File not found: {models_path}")
