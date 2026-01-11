import os
import re

print("🔍 Finding the verify endpoint...\n")

routes_dir = 'app/routes'

for filename in os.listdir(routes_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(routes_dir, filename)
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Find verify endpoint
        if 'verify' in content.lower():
            print(f"📄 Checking {filename}...")
            
            # Extract the verify function
            match = re.search(r"@bp\.route\(['\"].*verify.*['\"]\).*?\ndef verify\(\):(.*?)(?=\n@bp\.route|\Z)", content, re.DOTALL)
            if match:
                print(f"\n✅ Found verify endpoint in {filename}\n")
                # Get the function
                func_match = re.search(r"def verify\(\):.*?(?=\ndef |\Z)", content, re.DOTALL)
                if func_match:
                    func = func_match.group(0)
                    # Print first 80 lines or 3000 chars
                    lines = func.split('\n')[:40]
                    print('\n'.join(lines))
