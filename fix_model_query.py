import os
import re

print("🔍 Scanning for Model.query issues...\n")

routes_dir = 'app/routes'
fixes_needed = []

# Pattern to find .query on model classes
pattern = r'(\w+)\.query\b'

for filename in os.listdir(routes_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(routes_dir, filename)
        with open(filepath, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        issues = []
        for i, line in enumerate(lines, 1):
            matches = re.finditer(pattern, line)
            for match in matches:
                model_name = match.group(1)
                # Only flag if it looks like a model (starts with capital letter)
                if model_name[0].isupper() and model_name not in ['Blueprint', 'Dict']:
                    issues.append((i, line.strip(), model_name))
        
        if issues:
            fixes_needed.append((filename, filepath, issues))
            print(f"❌ {filename}:")
            for line_num, line_content, model in issues:
                print(f"   Line {line_num}: {model}.query ...")

if fixes_needed:
    print(f"\n\n🔧 Found issues in {len(fixes_needed)} files\n")
    print("🚀 Auto-fixing...\n")
    
    for filename, filepath, issues in fixes_needed:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Replace Model.query with db.session.query(Model)
        for line_num, line_content, model_name in issues:
            # Replace pattern: Model.query -> db.session.query(Model)
            old_pattern = rf'{model_name}\.query\b'
            new_pattern = f'db.session.query({model_name})'
            content = re.sub(old_pattern, new_pattern, content)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"✅ Fixed {filename} ({len(issues)} occurrences)")
else:
    print("✅ No issues found!")

print("\n✅ All fixes applied! Restart Flask now.")
