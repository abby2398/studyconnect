#!/usr/bin/env python3
"""
Backend API Testing for International Student Networking App
Tests authentication, user profiles, and connection system
"""

import requests
import json
import time
import uuid
from datetime import datetime
import os

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('EXPO_PUBLIC_BACKEND_URL='):
                    external_url = line.split('=')[1].strip()
                    print(f"External URL from .env: {external_url}")
                    return external_url
    except:
        pass
    return "https://pathfinder-94.preview.emergentagent.com"

# Try external URL first, fallback to localhost for testing
EXTERNAL_URL = get_backend_url()
LOCAL_URL = "http://localhost:8001"

def get_working_base_url():
    """Test both external and local URLs to find working one"""
    import requests
    
    # Test external URL first
    try:
        response = requests.get(f"{EXTERNAL_URL}/docs", timeout=5)
        if response.status_code == 200:
            print(f"✅ External URL working: {EXTERNAL_URL}")
            return EXTERNAL_URL
    except:
        print(f"❌ External URL not accessible: {EXTERNAL_URL}")
    
    # Fallback to local URL
    try:
        response = requests.get(f"{LOCAL_URL}/docs", timeout=5)
        if response.status_code == 200:
            print(f"✅ Local URL working: {LOCAL_URL}")
            return LOCAL_URL
    except:
        print(f"❌ Local URL not accessible: {LOCAL_URL}")
    
    return LOCAL_URL  # Default fallback

BASE_URL = get_working_base_url()
API_BASE = f"{BASE_URL}/api"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_users = []
        self.auth_tokens = {}
        self.results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
    def log_result(self, test_name, success, message="", error_details=""):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        if error_details:
            print(f"   Error: {error_details}")
            self.results['errors'].append(f"{test_name}: {error_details}")
        
        if success:
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1
        print()
    
    def test_server_health(self):
        """Test if the backend server is running"""
        try:
            response = self.session.get(f"{BASE_URL}/docs", timeout=10)
            if response.status_code == 200:
                self.log_result("Server Health Check", True, "Backend server is running")
                return True
            else:
                self.log_result("Server Health Check", False, f"Server returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Server Health Check", False, error_details=str(e))
            return False
    
    def test_user_registration_valid_edu(self):
        """Test user registration with valid .edu email"""
        test_user = {
            "email": f"test.user.{uuid.uuid4().hex[:8]}@university.edu",
            "password": "SecurePassword123!",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890"
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/register",
                json=test_user,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "Registration successful" in data.get("message", ""):
                    self.test_users.append(test_user)
                    self.log_result("User Registration (.edu email)", True, 
                                  f"User registered successfully: {test_user['email']}")
                    return True
                else:
                    self.log_result("User Registration (.edu email)", False, 
                                  f"Unexpected response: {data}")
                    return False
            else:
                self.log_result("User Registration (.edu email)", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("User Registration (.edu email)", False, error_details=str(e))
            return False
    
    def test_user_registration_invalid_email(self):
        """Test user registration with non-.edu email (should fail)"""
        test_user = {
            "email": f"test.user.{uuid.uuid4().hex[:8]}@gmail.com",
            "password": "SecurePassword123!",
            "first_name": "Jane",
            "last_name": "Smith"
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/register",
                json=test_user,
                timeout=10
            )
            
            if response.status_code == 400:
                data = response.json()
                if "Only .edu email addresses are allowed" in data.get("detail", ""):
                    self.log_result("User Registration (non-.edu email rejection)", True, 
                                  "Non-.edu email correctly rejected")
                    return True
                else:
                    self.log_result("User Registration (non-.edu email rejection)", False, 
                                  f"Wrong error message: {data}")
                    return False
            else:
                self.log_result("User Registration (non-.edu email rejection)", False, 
                              f"Expected 400 status, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("User Registration (non-.edu email rejection)", False, error_details=str(e))
            return False
    
    def test_user_login_valid(self):
        """Test user login with valid credentials"""
        if not self.test_users:
            self.log_result("User Login (valid credentials)", False, "No test users available")
            return False
            
        test_user = self.test_users[0]
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.auth_tokens[test_user["email"]] = data["access_token"]
                    self.log_result("User Login (valid credentials)", True, 
                                  f"Login successful, token received for {test_user['email']}")
                    return True
                else:
                    self.log_result("User Login (valid credentials)", False, 
                                  f"Missing token or user data: {data}")
                    return False
            else:
                self.log_result("User Login (valid credentials)", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("User Login (valid credentials)", False, error_details=str(e))
            return False
    
    def test_user_login_invalid(self):
        """Test user login with invalid credentials"""
        login_data = {
            "email": "nonexistent@university.edu",
            "password": "wrongpassword"
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 401:
                data = response.json()
                if "Invalid credentials" in data.get("detail", ""):
                    self.log_result("User Login (invalid credentials)", True, 
                                  "Invalid credentials correctly rejected")
                    return True
                else:
                    self.log_result("User Login (invalid credentials)", False, 
                                  f"Wrong error message: {data}")
                    return False
            else:
                self.log_result("User Login (invalid credentials)", False, 
                              f"Expected 401 status, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("User Login (invalid credentials)", False, error_details=str(e))
            return False
    
    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without authentication"""
        try:
            response = self.session.get(f"{API_BASE}/users/me", timeout=10)
            
            if response.status_code in [401, 403]:  # Both 401 and 403 are acceptable for unauthorized access
                self.log_result("Protected Endpoint (no token)", True, 
                              f"Correctly rejected request without token (status: {response.status_code})")
                return True
            else:
                self.log_result("Protected Endpoint (no token)", False, 
                              f"Expected 401/403 status, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Protected Endpoint (no token)", False, error_details=str(e))
            return False
    
    def test_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token"""
        if not self.auth_tokens:
            self.log_result("Protected Endpoint (with token)", False, "No auth tokens available")
            return False
            
        token = list(self.auth_tokens.values())[0]
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = self.session.get(f"{API_BASE}/users/me", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "email" in data and "id" in data:
                    self.log_result("Protected Endpoint (with token)", True, 
                                  f"Successfully accessed user profile: {data.get('email')}")
                    return True
                else:
                    self.log_result("Protected Endpoint (with token)", False, 
                                  f"Missing user data: {data}")
                    return False
            else:
                self.log_result("Protected Endpoint (with token)", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Protected Endpoint (with token)", False, error_details=str(e))
            return False
    
    def test_update_user_profile(self):
        """Test updating user profile"""
        if not self.auth_tokens:
            self.log_result("Update User Profile", False, "No auth tokens available")
            return False
            
        token = list(self.auth_tokens.values())[0]
        headers = {"Authorization": f"Bearer {token}"}
        
        profile_update = {
            "profile": {
                "age": 25,
                "bio": "International student studying computer science",
                "origin_country": "India",
                "origin_city": "Mumbai",
                "destination_country": "USA",
                "destination_city": "New York",
                "university": "Columbia University",
                "course": "Computer Science",
                "study_level": "Masters"
            }
        }
        
        try:
            response = self.session.put(
                f"{API_BASE}/users/me",
                json=profile_update,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "Profile updated successfully" in data.get("message", ""):
                    self.log_result("Update User Profile", True, 
                                  "Profile updated successfully")
                    return True
                else:
                    self.log_result("Update User Profile", False, 
                                  f"Unexpected response: {data}")
                    return False
            else:
                self.log_result("Update User Profile", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Update User Profile", False, error_details=str(e))
            return False
    
    def test_user_search(self):
        """Test user search functionality"""
        if not self.auth_tokens:
            self.log_result("User Search", False, "No auth tokens available")
            return False
            
        token = list(self.auth_tokens.values())[0]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test search by university
        try:
            response = self.session.get(
                f"{API_BASE}/users/search?university=Columbia",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "users" in data:
                    self.log_result("User Search", True, 
                                  f"Search returned {len(data['users'])} users")
                    return True
                else:
                    self.log_result("User Search", False, 
                                  f"Missing users field: {data}")
                    return False
            else:
                self.log_result("User Search", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("User Search", False, error_details=str(e))
            return False
    
    def test_connection_system(self):
        """Test connection request system"""
        # Need at least 2 users for connection testing
        if len(self.test_users) < 2 or len(self.auth_tokens) < 2:
            # Create a second user for testing
            second_user = {
                "email": f"test.user2.{uuid.uuid4().hex[:8]}@university.edu",
                "password": "SecurePassword123!",
                "first_name": "Alice",
                "last_name": "Johnson"
            }
            
            try:
                # Register second user
                response = self.session.post(f"{API_BASE}/auth/register", json=second_user, timeout=10)
                if response.status_code == 200:
                    self.test_users.append(second_user)
                    
                    # Login second user
                    login_response = self.session.post(
                        f"{API_BASE}/auth/login",
                        json={"email": second_user["email"], "password": second_user["password"]},
                        timeout=10
                    )
                    if login_response.status_code == 200:
                        token_data = login_response.json()
                        self.auth_tokens[second_user["email"]] = token_data["access_token"]
                else:
                    self.log_result("Connection System Setup", False, "Failed to create second user")
                    return False
            except Exception as e:
                self.log_result("Connection System Setup", False, error_details=str(e))
                return False
        
        # Now test connection requests
        success1 = self._test_send_connection_request()
        success2 = self._test_get_connection_requests()
        return success1 and success2
        """Test getting connection requests"""
        if len(self.auth_tokens) < 2:
            return False
            
        tokens = list(self.auth_tokens.values())
        user2_token = tokens[1]  # User2 should have incoming request
        headers = {"Authorization": f"Bearer {user2_token}"}
        
        try:
            response = self.session.get(f"{API_BASE}/connections/requests", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "incoming" in data and "outgoing" in data:
                    incoming_count = len(data["incoming"])
                    self.log_result("Get Connection Requests", True, 
                                  f"Retrieved connection requests - Incoming: {incoming_count}")
                    return True
                else:
                    self.log_result("Get Connection Requests", False, 
                                  f"Missing request fields: {data}")
                    return False
            else:
                self.log_result("Get Connection Requests", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Get Connection Requests", False, error_details=str(e))
            return False
    
    def _test_send_connection_request(self):
        """Test sending a connection request"""
        if len(self.auth_tokens) < 2:
            return False
            
        tokens = list(self.auth_tokens.values())
        user1_token = tokens[0]
        
        # Get user2's ID first
        user2_token = tokens[1]
        headers2 = {"Authorization": f"Bearer {user2_token}"}
        
        try:
            # Get user2's profile to get their ID
            response = self.session.get(f"{API_BASE}/users/me", headers=headers2, timeout=10)
            if response.status_code != 200:
                self.log_result("Send Connection Request", False, "Failed to get user2 profile")
                return False
                
            user2_data = response.json()
            user2_id = user2_data["id"]
            
            # Send connection request from user1 to user2 using query parameter
            headers1 = {"Authorization": f"Bearer {user1_token}"}
            
            response = self.session.post(
                f"{API_BASE}/connections/request?to_user_id={user2_id}",
                headers=headers1,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "Connection request sent successfully" in data.get("message", ""):
                    self.log_result("Send Connection Request", True, 
                                  "Connection request sent successfully")
                    return True
                else:
                    self.log_result("Send Connection Request", False, 
                                  f"Unexpected response: {data}")
                    return False
            else:
                self.log_result("Send Connection Request", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Send Connection Request", False, error_details=str(e))
            return False
    
    def test_connection_response(self):
        """Test responding to connection requests"""
        if len(self.auth_tokens) < 2:
            return False
            
        tokens = list(self.auth_tokens.values())
        user2_token = tokens[1]  # User2 should have incoming request
        headers = {"Authorization": f"Bearer {user2_token}"}
        
        try:
            # First get the connection requests to find a request ID
            response = self.session.get(f"{API_BASE}/connections/requests", headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_result("Connection Response", False, "Failed to get connection requests")
                return False
                
            data = response.json()
            if not data.get("incoming"):
                self.log_result("Connection Response", False, "No incoming requests to respond to")
                return False
                
            request_id = data["incoming"][0]["id"]
            
            # Accept the connection request
            response = self.session.post(
                f"{API_BASE}/connections/respond?request_id={request_id}&action=accept",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if "Connection request accepted" in response_data.get("message", ""):
                    self.log_result("Connection Response", True, 
                                  "Connection request accepted successfully")
                    return True
                else:
                    self.log_result("Connection Response", False, 
                                  f"Unexpected response: {response_data}")
                    return False
            else:
                self.log_result("Connection Response", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Connection Response", False, error_details=str(e))
            return False
    
    def test_email_verification_invalid_token(self):
        """Test email verification with invalid token"""
        try:
            response = self.session.post(
                f"{API_BASE}/auth/verify-email?token=invalid_token_12345",
                timeout=10
            )
            
            if response.status_code == 400:
                data = response.json()
                if "Invalid or expired verification token" in data.get("detail", ""):
                    self.log_result("Email Verification (invalid token)", True, 
                                  "Invalid token correctly rejected")
                    return True
                else:
                    self.log_result("Email Verification (invalid token)", False, 
                                  f"Wrong error message: {data}")
                    return False
            else:
                self.log_result("Email Verification (invalid token)", False, 
                              f"Expected 400 status, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Email Verification (invalid token)", False, error_details=str(e))
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("BACKEND API TESTING - International Student Networking App")
        print("=" * 60)
        print(f"Testing against: {API_BASE}")
        print()
        
        # Test server health first
        if not self.test_server_health():
            print("❌ Server is not accessible. Stopping tests.")
            return self.results
        
        # Authentication Tests
        print("🔐 AUTHENTICATION TESTS")
        print("-" * 30)
        self.test_user_registration_valid_edu()
        self.test_user_registration_invalid_email()
        self.test_user_login_valid()
        self.test_user_login_invalid()
        self.test_protected_endpoint_without_token()
        self.test_protected_endpoint_with_token()
        
        # User Profile Tests
        print("👤 USER PROFILE TESTS")
        print("-" * 30)
        self.test_update_user_profile()
        self.test_user_search()
        
        # Connection System Tests
        print("🤝 CONNECTION SYSTEM TESTS")
        print("-" * 30)
        self.test_connection_system()
        self.test_connection_response()
        
        # Additional Tests
        print("🔍 ADDITIONAL TESTS")
        print("-" * 30)
        self.test_email_verification_invalid_token()
        
        # Summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📊 Total: {self.results['passed'] + self.results['failed']}")
        
        if self.results['errors']:
            print("\n🚨 ERRORS FOUND:")
            for error in self.results['errors']:
                print(f"   • {error}")
        
        return self.results

if __name__ == "__main__":
    tester = BackendTester()
    results = tester.run_all_tests()