import requests
import sys
import json
from datetime import datetime

class ChatGPTAPITester:
    def __init__(self, base_url="https://248cf560-4be9-4bc2-bc7a-19f6b0adaa19.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None

    def test_root_endpoint(self):
        """Test root endpoint"""
        success, response = self.run_test(
            "Root Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_google_login_redirect(self):
        """Test Google login redirect"""
        success, response = self.run_test(
            "Google Login Redirect",
            "GET",
            "api/login/google",
            302  # Should redirect to Google OAuth
        )
        return success

    def test_user_profile_without_auth(self):
        """Test user profile endpoint without authentication"""
        success, response = self.run_test(
            "User Profile (No Auth)",
            "GET",
            "api/user/profile",
            403  # FastAPI HTTPBearer returns 403
        )
        return success

    def test_chat_without_auth(self):
        """Test chat endpoint without authentication"""
        success, response = self.run_test(
            "Chat (No Auth)",
            "POST",
            "api/chat",
            403,  # FastAPI HTTPBearer returns 403
            data={"message": "Hello"}
        )
        return success

    def test_admin_stats_without_auth(self):
        """Test admin stats endpoint without authentication"""
        success, response = self.run_test(
            "Admin Stats (No Auth)",
            "GET",
            "api/admin/stats",
            403  # FastAPI HTTPBearer returns 403
        )
        return success

    def test_admin_users_without_auth(self):
        """Test admin users endpoint without authentication"""
        success, response = self.run_test(
            "Admin Users (No Auth)",
            "GET",
            "api/admin/users",
            403  # FastAPI HTTPBearer returns 403
        )
        return success

    def test_admin_configure_without_auth(self):
        """Test admin configure endpoint without authentication"""
        success, response = self.run_test(
            "Admin Configure (No Auth)",
            "POST",
            "api/admin/configure",
            403,  # FastAPI HTTPBearer returns 403
            data={"openai_key": "test-key"}
        )
        return success

    def test_chat_history_without_auth(self):
        """Test chat history endpoint without authentication"""
        success, response = self.run_test(
            "Chat History (No Auth)",
            "GET",
            "api/chat/history",
            403  # FastAPI HTTPBearer returns 403
        )
        return success

    def test_admin_manage_admin_without_auth(self):
        """Test admin manage-admin endpoint without authentication"""
        success, response = self.run_test(
            "Admin Manage Admin (No Auth)",
            "POST",
            "api/admin/manage-admin",
            403,  # FastAPI HTTPBearer returns 403
            data={"email": "test@example.com", "action": "add"}
        )
        return success

    def test_admin_manage_admin_invalid_data(self):
        """Test admin manage-admin endpoint with invalid data (no auth needed for this test)"""
        success, response = self.run_test(
            "Admin Manage Admin (Invalid Data - No Auth)",
            "POST",
            "api/admin/manage-admin",
            403,  # Will fail at auth level first
            data={"invalid": "data"}
        )
        return success

    def test_invalid_endpoints(self):
        """Test invalid endpoints"""
        success, response = self.run_test(
            "Invalid Endpoint",
            "GET",
            "api/nonexistent",
            404  # Should return not found
        )
        return success

    def test_cors_headers(self):
        """Test CORS headers"""
        print(f"\n🔍 Testing CORS Headers...")
        try:
            response = self.session.options(f"{self.base_url}/api/user/profile")
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            print(f"   CORS Headers: {cors_headers}")
            self.tests_run += 1
            if any(cors_headers.values()):
                self.tests_passed += 1
                print("✅ CORS headers present")
                return True
            else:
                print("❌ CORS headers missing")
                return False
        except Exception as e:
            print(f"❌ CORS test failed: {str(e)}")
            return False

def main():
    print("🚀 Starting ChatGPT Web Application API Tests")
    print("=" * 60)
    
    # Setup
    tester = ChatGPTAPITester()
    
    # Run all tests
    tests = [
        tester.test_root_endpoint,
        tester.test_google_login_redirect,
        tester.test_user_profile_without_auth,
        tester.test_chat_without_auth,
        tester.test_admin_stats_without_auth,
        tester.test_admin_users_without_auth,
        tester.test_admin_configure_without_auth,
        tester.test_admin_manage_admin_without_auth,
        tester.test_admin_manage_admin_invalid_data,
        tester.test_chat_history_without_auth,
        tester.test_invalid_endpoints,
        tester.test_cors_headers
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 API Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All API tests passed!")
        return 0
    else:
        print("⚠️  Some API tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())