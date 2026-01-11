import os
import re

print("🔍 Scanning response helper functions...\n")

# Check if responses.py exists
responses_path = 'app/utils/responses.py'
if os.path.exists(responses_path):
    with open(responses_path, 'r') as f:
        content = f.read()
    
    print("📄 Found app/utils/responses.py\n")
    print(content[:1000])
    print("\n...\n")
    
    # Look for function definitions
    if 'def success_response' in content:
        print("✅ success_response function found")
        # Extract just that function
        match = re.search(r'def success_response\([^)]*\):[^}]*?(?=\ndef |\Z)', content, re.DOTALL)
        if match:
            func = match.group(0)
            print(func[:500])
    
    if 'def error_response' in content:
        print("\n✅ error_response function found")
else:
    print("❌ app/utils/responses.py not found!")
    print("\nLooking for response helpers elsewhere...")
    
    # Search in all files
    for root, dirs, files in os.walk('app'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                if 'success_response' in content and 'def success_response' in content:
                    print(f"Found in: {filepath}")
