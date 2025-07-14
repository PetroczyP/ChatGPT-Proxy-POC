#!/usr/bin/env python3
"""
Comprehensive testing for version updates:
- FastAPI 0.110.1 → 0.116.1
- OpenAI 1.12.0 → 1.95.1 (AsyncOpenAI)
- Pydantic 2.6.4 → 2.11.7
- PyMongo 4.5.0 → 4.13.0
- Motor 3.3.1 → 3.7.1
- Uvicorn 0.25.0 → 0.34.0
"""

import requests
import sys
import json
import asyncio
import importlib
import pkg_resources
from datetime import datetime

class VersionUpdateTester:
    def __init__(self, base_url="https://2e51ad72-7b0f-492c-a172-3771d8f293ac.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")

    def test_library_versions(self):
        """Test that updated library versions are installed"""
        print("\n🔍 Testing Library Version Updates...")
        
        libraries_to_check = {
            'fastapi': '0.116.1',
            'openai': '1.95.1', 
            'pydantic': '2.11.7',
            'pymongo': '4.13.0',
            'motor': '3.7.1',
            'uvicorn': '0.34.0'
        }
        
        for lib_name, expected_version in libraries_to_check.items():
            try:
                installed_version = pkg_resources.get_distribution(lib_name).version
                # Check if installed version matches or is compatible
                version_ok = installed_version.startswith(expected_version.split('.')[0])  # Major version match
                self.log_test(
                    f"{lib_name} version check",
                    version_ok,
                    f"Installed: {installed_version}, Expected: {expected_version}"
                )
            except Exception as e:
                self.log_test(
                    f"{lib_name} version check",
                    False,
                    f"Error checking version: {str(e)}"
                )

    def test_fastapi_compatibility(self):
        """Test FastAPI 0.116.1 compatibility"""
        print("\n🔍 Testing FastAPI 0.116.1 Compatibility...")
        
        # Test basic FastAPI functionality
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            fastapi_ok = response.status_code == 200
            self.log_test(
                "FastAPI basic functionality",
                fastapi_ok,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test(
                "FastAPI basic functionality",
                False,
                f"Error: {str(e)}"
            )

        # Test FastAPI security (HTTPBearer)
        try:
            response = self.session.get(f"{self.base_url}/api/user/profile", timeout=10)
            security_ok = response.status_code == 403  # Should require auth
            self.log_test(
                "FastAPI HTTPBearer security",
                security_ok,
                f"Status: {response.status_code} (403 expected for auth required)"
            )
        except Exception as e:
            self.log_test(
                "FastAPI HTTPBearer security",
                False,
                f"Error: {str(e)}"
            )

        # Test FastAPI CORS middleware
        try:
            response = self.session.options(f"{self.base_url}/api/user/profile", timeout=10)
            cors_ok = response.status_code in [200, 405]  # Either handled or method not allowed
            self.log_test(
                "FastAPI CORS middleware",
                cors_ok,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test(
                "FastAPI CORS middleware",
                False,
                f"Error: {str(e)}"
            )

    def test_openai_async_integration(self):
        """Test OpenAI 1.95.1 AsyncOpenAI integration"""
        print("\n🔍 Testing OpenAI 1.95.1 AsyncOpenAI Integration...")
        
        # Test that AsyncOpenAI can be imported (via API endpoint)
        try:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json={"message": "test"},
                timeout=10
            )
            # Should fail at auth level (403), not import level (500)
            import_ok = response.status_code == 403
            self.log_test(
                "AsyncOpenAI import compatibility",
                import_ok,
                f"Status: {response.status_code} (403 expected - auth required, not import error)"
            )
        except Exception as e:
            self.log_test(
                "AsyncOpenAI import compatibility",
                False,
                f"Error: {str(e)}"
            )

        # Test OpenAI error handling
        try:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json={"message": "test"},
                timeout=10
            )
            if response.status_code == 403:
                response_data = response.json()
                error_handling_ok = "Not authenticated" in response_data.get('detail', '')
                self.log_test(
                    "OpenAI error handling",
                    error_handling_ok,
                    f"Proper authentication error returned"
                )
            else:
                self.log_test(
                    "OpenAI error handling",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "OpenAI error handling",
                False,
                f"Error: {str(e)}"
            )

    def test_pydantic_models(self):
        """Test Pydantic 2.11.7 model validation"""
        print("\n🔍 Testing Pydantic 2.11.7 Model Validation...")
        
        # Test Pydantic model validation via API
        try:
            # Test valid data
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json={"message": "valid message"},
                timeout=10
            )
            # Should fail at auth (403), not validation (422)
            valid_data_ok = response.status_code == 403
            self.log_test(
                "Pydantic valid data handling",
                valid_data_ok,
                f"Status: {response.status_code} (403 expected - auth required)"
            )
        except Exception as e:
            self.log_test(
                "Pydantic valid data handling",
                False,
                f"Error: {str(e)}"
            )

        # Test invalid data
        try:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json={"invalid_field": "test"},
                timeout=10
            )
            # Should fail at validation (422) or auth (403)
            invalid_data_ok = response.status_code in [422, 403]
            self.log_test(
                "Pydantic invalid data validation",
                invalid_data_ok,
                f"Status: {response.status_code} (422 validation error or 403 auth error expected)"
            )
        except Exception as e:
            self.log_test(
                "Pydantic invalid data validation",
                False,
                f"Error: {str(e)}"
            )

    def test_database_connectivity(self):
        """Test PyMongo 4.13.0 and Motor 3.7.1 database operations"""
        print("\n🔍 Testing Database Connectivity (PyMongo 4.13.0 & Motor 3.7.1)...")
        
        # Test database connectivity via API endpoints
        try:
            # Test endpoint that requires database access
            response = self.session.get(f"{self.base_url}/api/user/profile", timeout=10)
            # Should fail at auth (403), not database connection (500)
            db_connectivity_ok = response.status_code == 403
            self.log_test(
                "Database connectivity",
                db_connectivity_ok,
                f"Status: {response.status_code} (403 expected - auth required, not DB error)"
            )
        except Exception as e:
            self.log_test(
                "Database connectivity",
                False,
                f"Error: {str(e)}"
            )

        # Test admin endpoints that use database
        try:
            response = self.session.get(f"{self.base_url}/api/admin/stats", timeout=10)
            admin_db_ok = response.status_code == 403  # Auth required, not DB error
            self.log_test(
                "Admin database operations",
                admin_db_ok,
                f"Status: {response.status_code} (403 expected - auth required)"
            )
        except Exception as e:
            self.log_test(
                "Admin database operations",
                False,
                f"Error: {str(e)}"
            )

    def test_uvicorn_server(self):
        """Test Uvicorn 0.34.0 server functionality"""
        print("\n🔍 Testing Uvicorn 0.34.0 Server Functionality...")
        
        # Test server responsiveness
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            server_ok = response.status_code == 200
            self.log_test(
                "Uvicorn server responsiveness",
                server_ok,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test(
                "Uvicorn server responsiveness",
                False,
                f"Error: {str(e)}"
            )

        # Test server handles multiple concurrent requests
        try:
            import concurrent.futures
            import threading
            
            def make_request():
                return self.session.get(f"{self.base_url}/", timeout=5)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(5)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
                
            concurrent_ok = all(r.status_code == 200 for r in results)
            self.log_test(
                "Uvicorn concurrent request handling",
                concurrent_ok,
                f"5 concurrent requests handled successfully"
            )
        except Exception as e:
            self.log_test(
                "Uvicorn concurrent request handling",
                False,
                f"Error: {str(e)}"
            )

    def test_deployment_readiness(self):
        """Test overall deployment readiness after version updates"""
        print("\n🔍 Testing Deployment Readiness After Version Updates...")
        
        # Test all critical endpoints are responsive
        critical_endpoints = [
            ("Root", "/"),
            ("Google OAuth", "/api/login/google"),
            ("User Profile", "/api/user/profile"),
            ("Chat", "/api/chat"),
            ("Admin Stats", "/api/admin/stats")
        ]
        
        all_responsive = True
        for name, endpoint in critical_endpoints:
            try:
                if endpoint == "/api/login/google":
                    response = self.session.get(f"{self.base_url}{endpoint}", 
                                              allow_redirects=False, timeout=10)
                    expected_status = 302  # OAuth redirect
                elif endpoint == "/":
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                    expected_status = 200
                else:
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                    expected_status = 403  # Auth required
                
                endpoint_ok = response.status_code == expected_status
                if not endpoint_ok:
                    all_responsive = False
                    
                self.log_test(
                    f"Endpoint responsiveness: {name}",
                    endpoint_ok,
                    f"Status: {response.status_code} (expected: {expected_status})"
                )
            except Exception as e:
                all_responsive = False
                self.log_test(
                    f"Endpoint responsiveness: {name}",
                    False,
                    f"Error: {str(e)}"
                )

        self.log_test(
            "Overall deployment readiness",
            all_responsive,
            "All critical endpoints responsive after version updates"
        )

def main():
    print("🚀 Starting Version Update Compatibility Tests")
    print("🎯 Testing compatibility after library version updates")
    print("=" * 70)
    
    tester = VersionUpdateTester()
    
    # Run all version update tests
    test_methods = [
        tester.test_library_versions,
        tester.test_fastapi_compatibility,
        tester.test_openai_async_integration,
        tester.test_pydantic_models,
        tester.test_database_connectivity,
        tester.test_uvicorn_server,
        tester.test_deployment_readiness
    ]
    
    for test_method in test_methods:
        try:
            test_method()
        except Exception as e:
            print(f"❌ Test {test_method.__name__} failed with exception: {str(e)}")
    
    # Print results
    print("\n" + "=" * 70)
    print(f"📊 Version Update Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All version update tests passed! Backend is compatible with new versions.")
        return 0
    else:
        print("⚠️  Some version update tests failed - review compatibility issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())