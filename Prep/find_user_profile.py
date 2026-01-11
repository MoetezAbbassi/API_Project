import os
import re

print("🔍 Scanning for db.query issues (should be db.session.query)...\n")

routes_dir = 'app/routes'
fixes_needed = []

pattern = r'db\.query\('

for filename in os.listdir(routes_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(routes_dir, filename)
        with open(filepath, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        issues = []
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line):
                issues.append((i, line.strip()))
        
        if issues:
            fixes_needed.append((filename, filepath, issues))
            print(f"❌ {filename}:")
            for line_num, line_content in issues:
                print(f"   Line {line_num}: {line_content[:80]}...")

if fixes_needed:
    print(f"\n\n🔧 Found {len(fixes_needed)} files with issues\n")
    print("🚀 Auto-fixing...\n")
    
    for filename, filepath, issues in fixes_needed:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Replace db.query with db.session.query
        new_content = content.replace('db.query(', 'db.session.query(')
        
        with open(filepath, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Fixed {filename} ({len(issues)} occurrences)")
else:
    print("✅ No issues found!")

print("\n✅ All fixes applied! Restart Flask now.")