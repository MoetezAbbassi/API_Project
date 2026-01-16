#!/usr/bin/env python3
"""
Fitness API - Verification Script
Tests all major components to verify project completeness
"""

import json
import requests
from datetime import datetime

BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_health_check():
    """Test health check endpoint"""
    print("\n✓ Testing Health Check...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"  Status: {data.get('status')}")
            print(f"  Service: {data.get('service')}")
            print(f"  Version: {data.get('version')}")
            return True
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_swagger_ui():
    """Test Swagger UI accessibility"""
    print("\n✓ Testing Swagger UI...")
    try:
        response = requests.get(f"{BASE_URL}/api/docs")
        if response.status_code == 200 and "swagger" in response.text.lower():
            print(f"  ✓ Swagger UI accessible at {BASE_URL}/api/docs")
            return True
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_openapi_spec():
    """Test OpenAPI specification endpoint"""
    print("\n✓ Testing OpenAPI Specification...")
    try:
        response = requests.get(f"{BASE_URL}/apispec.json")
        if response.status_code == 200:
            spec = response.json()
            print(f"  ✓ OpenAPI spec accessible")
            print(f"  Title: {spec.get('info', {}).get('title')}")
            print(f"  Version: {spec.get('info', {}).get('version')}")
            
            # Count endpoints
            paths = spec.get('paths', {})
            endpoint_count = sum(len([m for m in methods.keys() if m not in ['parameters']]) 
                               for methods in paths.values())
            print(f"  Endpoints: {endpoint_count}")
            
            # Check security definitions
            security_defs = spec.get('securityDefinitions', {})
            print(f"  Security Methods: {list(security_defs.keys())}")
            
            return True
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_register_endpoint():
    """Test user registration endpoint"""
    print("\n✓ Testing Registration Endpoint...")
    try:
        test_user = {
            "username": f"testuser_{datetime.now().timestamp()}",
            "email": f"test_{datetime.now().timestamp()}@example.com",
            "password": "TestPass123!"
        }
        
        response = requests.post(f"{API_URL}/auth/register", json=test_user)
        
        if response.status_code == 201:
            data = response.json()
            print(f"  ✓ Registration successful")
            print(f"  User ID: {data.get('user', {}).get('user_id')}")
            print(f"  Username: {data.get('user', {}).get('username')}")
            return True, test_user['username']
        elif response.status_code == 409:
            print(f"  ✓ Endpoint responds (email exists)")
            return False, None
        else:
            print(f"  ✗ Error {response.status_code}: {response.text}")
            return False, None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False, None

def test_documentation_files():
    """Check if documentation files exist"""
    print("\n✓ Checking Documentation Files...")
    import os
    
    docs_path = "docs"
    required_files = [
        "ERROR_CATALOG.md",
        "AUTHENTICATION_GUIDE.md",
        "API_REFERENCE.md",
        "SWAGGER_SETUP_GUIDE.md"
    ]
    
    all_exist = True
    for filename in required_files:
        filepath = os.path.join(docs_path, filename)
        exists = os.path.exists(filepath)
        status = "✓" if exists else "✗"
        file_size = os.path.getsize(filepath) if exists else 0
        print(f"  {status} {filename} ({file_size:,} bytes)")
        if not exists:
            all_exist = False
    
    return all_exist

def test_swagger_config():
    """Check if swagger_config.py exists and loads"""
    print("\n✓ Checking Swagger Configuration...")
    try:
        import os
        config_path = "app/swagger_config.py"
        if os.path.exists(config_path):
            from app.swagger_config import SWAGGER_CONFIG, SWAGGER_TEMPLATE
            print(f"  ✓ Swagger config loaded")
            print(f"  Config endpoint: {SWAGGER_CONFIG.get('endpoint')}")
            print(f"  UI route: {SWAGGER_CONFIG.get('route')}")
            
            # Check template
            info = SWAGGER_TEMPLATE.get('info', {})
            print(f"  API title: {info.get('title')}")
            print(f"  API version: {info.get('version')}")
            
            # Check definitions
            definitions = SWAGGER_TEMPLATE.get('definitions', {})
            print(f"  Models defined: {len(definitions)}")
            
            # Check security
            security = SWAGGER_TEMPLATE.get('securityDefinitions', {})
            print(f"  Security methods: {list(security.keys())}")
            
            return True
        else:
            print(f"  ✗ Config file not found")
            return False
    except Exception as e:
        print(f"  ✗ Error loading config: {e}")
        return False

def main():
    """Run all verification tests"""
    print_section("FITNESS API - VERIFICATION TEST")
    print(f"Testing API at: {API_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = {}
    
    # Test basic endpoints
    print_section("ENDPOINT TESTS")
    results['health_check'] = test_health_check()
    results['swagger_ui'] = test_swagger_ui()
    results['openapi_spec'] = test_openapi_spec()
    results['register'] = test_register_endpoint()[0]
    
    # Test documentation
    print_section("DOCUMENTATION TESTS")
    results['doc_files'] = test_documentation_files()
    results['swagger_config'] = test_swagger_config()
    
    # Summary
    print_section("VERIFICATION SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL VERIFICATION TESTS PASSED")
        print("\nAPI is ready to use:")
        print(f"  • API Endpoint: {API_URL}")
        print(f"  • Swagger UI: {BASE_URL}/api/docs")
        print(f"  • OpenAPI Spec: {BASE_URL}/apispec.json")
        print(f"  • Health Check: {API_URL}/health")
        return 0
    else:
        print(f"\n✗ Some tests failed ({total - passed} failures)")
        return 1

if __name__ == "__main__":
    exit(main())
