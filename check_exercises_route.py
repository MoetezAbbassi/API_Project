import os

print("🔍 Reading exercises.py route...\n")

exercises_path = 'app/routes/exercises.py'

if os.path.exists(exercises_path):
    with open(exercises_path, 'r') as f:
        content = f.read()
    
    # Show first 2500 characters to see the GET all exercises endpoint
    print(content[:2500])
    print("\n...\n")
    
    # Find function names
    import re
    functions = re.findall(r'def (\w+)\(', content)
    print(f"📄 Found {len(functions)} functions:")
    for func in functions:
        print(f"   - {func}")
else:
    print(f"❌ File not found: {exercises_path}")
