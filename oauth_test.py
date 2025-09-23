#!/usr/bin/env python3

import requests
import json
import os
from datetime import datetime
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://campuslink-25.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def add_result(self, test_name, passed, message=""):
        self.results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
    
    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"GOOGLE OAUTH INTEGRATION TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/total*100):.1f}%" if total > 0 else "0%")
        
        if self.failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['message']}")

def test_oauth_callback():
    """Test GET /api/auth/callback endpoint"""
    results = TestResults()
    
    try:
        response = requests.get(f"{API_BASE}/auth/callback", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "OAuth callback received" in data["message"]:
                results.add_result("OAuth Callback Endpoint", True, "Returns proper callback message")
            else:
                results.add_result("OAuth Callback Endpoint", False, f"Unexpected response format: {data}")
        else:
            results.add_result("OAuth Callback Endpoint", False, f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        results.add_result("OAuth Callback Endpoint", False, f"Request failed: {str(e)}")
    
    return results

def test_google_oauth_login():
    """Test POST /api/auth/google-oauth with various scenarios"""
    results = TestResults()
    
    # Test Case 1: Valid Google OAuth with .edu email (new user)
    try:
        oauth_data = {
            "google_data": {
                "id": "google_user_123456",
                "email": "john.doe@stanford.edu",
                "name": "John Doe",
                "picture": "https://lh3.googleusercontent.com/a/sample-photo.jpg"
            },
            "session_token": f"session_token_{uuid.uuid4()}"
        }
        
        response = requests.post(f"{API_BASE}/auth/google-oauth", 
                               json=oauth_data, 
                               headers={"Content-Type": "application/json"},
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if all(key in data for key in ["access_token", "token_type", "user"]):
                user_data = data["user"]
                if (user_data["email"] == oauth_data["google_data"]["email"] and
                    user_data["first_name"] == "John" and
                    user_data["last_name"] == "Doe" and
                    user_data["is_verified"] == True):
                    results.add_result("Google OAuth - New .edu User Creation", True, 
                                     "Successfully created new user with Google data")
                else:
                    results.add_result("Google OAuth - New .edu User Creation", False, 
                                     f"User data mismatch: {user_data}")
            else:
                results.add_result("Google OAuth - New .edu User Creation", False, 
                                 f"Missing required fields in response: {data}")
        else:
            results.add_result("Google OAuth - New .edu User Creation", False, 
                             f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        results.add_result("Google OAuth - New .edu User Creation", False, f"Request failed: {str(e)}")
    
    # Test Case 2: Existing user login
    try:
        # Use same email as above to test existing user login
        oauth_data = {
            "google_data": {
                "id": "google_user_123456",
                "email": "john.doe@stanford.edu",
                "name": "John Doe Updated",
                "picture": "https://lh3.googleusercontent.com/a/updated-photo.jpg"
            },
            "session_token": f"session_token_{uuid.uuid4()}"
        }
        
        response = requests.post(f"{API_BASE}/auth/google-oauth", 
                               json=oauth_data, 
                               headers={"Content-Type": "application/json"},
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if all(key in data for key in ["access_token", "token_type", "user"]):
                results.add_result("Google OAuth - Existing User Login", True, 
                                 "Successfully logged in existing user")
            else:
                results.add_result("Google OAuth - Existing User Login", False, 
                                 f"Missing required fields: {data}")
        else:
            results.add_result("Google OAuth - Existing User Login", False, 
                             f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        results.add_result("Google OAuth - Existing User Login", False, f"Request failed: {str(e)}")
    
    # Test Case 3: Non-.edu email rejection (new user)
    try:
        oauth_data = {
            "google_data": {
                "id": "google_user_789",
                "email": "user@gmail.com",
                "name": "Regular User",
                "picture": "https://lh3.googleusercontent.com/a/regular-photo.jpg"
            },
            "session_token": f"session_token_{uuid.uuid4()}"
        }
        
        response = requests.post(f"{API_BASE}/auth/google-oauth", 
                               json=oauth_data, 
                               headers={"Content-Type": "application/json"},
                               timeout=10)
        
        if response.status_code == 400:
            data = response.json()
            if "Only .edu email addresses are allowed" in data.get("detail", ""):
                results.add_result("Google OAuth - Non-.edu Email Rejection", True, 
                                 "Correctly rejected non-.edu email")
            else:
                results.add_result("Google OAuth - Non-.edu Email Rejection", False, 
                                 f"Wrong error message: {data}")
        else:
            results.add_result("Google OAuth - Non-.edu Email Rejection", False, 
                             f"Expected HTTP 400, got {response.status_code}: {response.text}")
            
    except Exception as e:
        results.add_result("Google OAuth - Non-.edu Email Rejection", False, f"Request failed: {str(e)}")
    
    # Test Case 4: Missing email validation
    try:
        oauth_data = {
            "google_data": {
                "id": "google_user_no_email",
                "name": "No Email User",
                "picture": "https://lh3.googleusercontent.com/a/no-email-photo.jpg"
            },
            "session_token": f"session_token_{uuid.uuid4()}"
        }
        
        response = requests.post(f"{API_BASE}/auth/google-oauth", 
                               json=oauth_data, 
                               headers={"Content-Type": "application/json"},
                               timeout=10)
        
        if response.status_code == 400:
            data = response.json()
            if "Email is required from Google OAuth" in data.get("detail", ""):
                results.add_result("Google OAuth - Missing Email Validation", True, 
                                 "Correctly rejected request without email")
            else:
                results.add_result("Google OAuth - Missing Email Validation", False, 
                                 f"Wrong error message: {data}")
        else:
            results.add_result("Google OAuth - Missing Email Validation", False, 
                             f"Expected HTTP 400, got {response.status_code}: {response.text}")
            
    except Exception as e:
        results.add_result("Google OAuth - Missing Email Validation", False, f"Request failed: {str(e)}")
    
    # Test Case 5: Invalid request format
    try:
        invalid_data = {
            "invalid_field": "test"
        }
        
        response = requests.post(f"{API_BASE}/auth/google-oauth", 
                               json=invalid_data, 
                               headers={"Content-Type": "application/json"},
                               timeout=10)
        
        if response.status_code in [400, 422]:  # 422 for validation errors
            results.add_result("Google OAuth - Invalid Request Format", True, 
                             "Correctly rejected invalid request format")
        else:
            results.add_result("Google OAuth - Invalid Request Format", False, 
                             f"Expected HTTP 400/422, got {response.status_code}: {response.text}")
            
    except Exception as e:
        results.add_result("Google OAuth - Invalid Request Format", False, f"Request failed: {str(e)}")
    
    return results

def test_session_management():
    """Test that sessions are stored correctly after OAuth"""
    results = TestResults()
    
    try:
        # Create a user via OAuth and check if we can use the token
        oauth_data = {
            "google_data": {
                "id": "session_test_user",
                "email": "session.test@mit.edu",
                "name": "Session Test User",
                "picture": "https://lh3.googleusercontent.com/a/session-photo.jpg"
            },
            "session_token": f"session_token_{uuid.uuid4()}"
        }
        
        response = requests.post(f"{API_BASE}/auth/google-oauth", 
                               json=oauth_data, 
                               headers={"Content-Type": "application/json"},
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            
            if access_token:
                # Test using the token to access protected endpoint
                headers = {"Authorization": f"Bearer {access_token}"}
                profile_response = requests.get(f"{API_BASE}/users/me", 
                                              headers=headers, 
                                              timeout=10)
                
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    if profile_data["email"] == oauth_data["google_data"]["email"]:
                        results.add_result("Session Management - Token Validation", True, 
                                         "OAuth token works for protected endpoints")
                    else:
                        results.add_result("Session Management - Token Validation", False, 
                                         f"Token returned wrong user data: {profile_data}")
                else:
                    results.add_result("Session Management - Token Validation", False, 
                                     f"Token validation failed: HTTP {profile_response.status_code}")
            else:
                results.add_result("Session Management - Token Validation", False, 
                                 "No access token in OAuth response")
        else:
            results.add_result("Session Management - Token Validation", False, 
                             f"OAuth failed: HTTP {response.status_code}")
            
    except Exception as e:
        results.add_result("Session Management - Token Validation", False, f"Request failed: {str(e)}")
    
    return results

def main():
    print("🔐 TESTING GOOGLE OAUTH INTEGRATION")
    print("="*60)
    
    all_results = TestResults()
    
    # Test OAuth Callback Endpoint
    print("\n📞 Testing OAuth Callback Endpoint...")
    callback_results = test_oauth_callback()
    all_results.passed += callback_results.passed
    all_results.failed += callback_results.failed
    all_results.results.extend(callback_results.results)
    
    # Test Google OAuth Login Endpoint
    print("\n🔑 Testing Google OAuth Login Endpoint...")
    oauth_results = test_google_oauth_login()
    all_results.passed += oauth_results.passed
    all_results.failed += oauth_results.failed
    all_results.results.extend(oauth_results.results)
    
    # Test Session Management
    print("\n🎫 Testing Session Management...")
    session_results = test_session_management()
    all_results.passed += session_results.passed
    all_results.failed += session_results.failed
    all_results.results.extend(session_results.results)
    
    # Print final summary
    all_results.print_summary()
    
    return all_results.failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)