import os
import re

print("🔍 Scanning all route files for tuple return issues...\n")

routes_dir = 'app/routes'
fixes_needed = []

# Pattern to find returns with double tuples
# Examples: "return success_response(...), 200" or "return error_response(...), 404"
pattern = r'return\s+(success_response|error_response)\([^)]*\),\s*\d{3}'

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
            fixes_needed.append((filename, issues))
            print(f"❌ {filename}:")
            for line_num, line_content in issues:
                print(f"   Line {line_num}: {line_content[:80]}...")

if not fixes_needed:
    print("✅ No issues found!")
else:
    print(f"\n\n🔧 Found issues in {len(fixes_needed)} files")
    print("\n📝 FIX: Remove the ', XXX' at the end of success_response/error_response calls")
    print("   Before: return success_response(...), 200")
    print("   After:  return success_response(...)")
    print("\n   These functions ALREADY return (dict, status_code)")
