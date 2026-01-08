#!/usr/bin/env python3
"""
Comprehensive Google OAuth "Continue with Google" Flow Testing
Tests all aspects of Google OAuth integration including backend endpoints,
user management, session handling, and integration with existing app features.
"""

import requests
import json
import os
import uuid
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Get backend URL from environment
BACKEND_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://campuslink-25.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class GoogleOAuthTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_users = []
        self.oauth_tokens = {}
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results with detailed information"""
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        print()

    def create_mock_google_data(self, email: str, name: str = None, picture: str = None) -> Dict[str, Any]:
        """Create mock Google OAuth data for testing"""
        if not name:
            name_parts = email.split('@')[0].split('.')
            name = ' '.join(part.capitalize() for part in name_parts)
        
        if not picture:
            picture = f"https://lh3.googleusercontent.com/a/mock-photo-{uuid.uuid4()}.jpg"
            
        return {
            "google_data": {
                "id": f"google_oauth_test_{uuid.uuid4()}",
                "email": email,
                "name": name,
                "picture": picture
            },
            "session_token": f"test_session_token_{uuid.uuid4()}"
        }

    # Test 1: OAuth Callback Endpoint
    def test_oauth_callback_endpoint(self) -> bool:
        """Test GET /api/auth/callback - OAuth redirect handler"""
        try:
            response = self.session.get(f"{API_BASE}/auth/callback", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "OAuth callback received" in data["message"]:
                    self.log_test("OAuth Callback Endpoint", "PASS", 
                                "Returns appropriate callback response")
                    return True
                else:
                    self.log_test("OAuth Callback Endpoint", "FAIL", 
                                f"Unexpected response format: {data}")
                    return False
            else:
                self.log_test("OAuth Callback Endpoint", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("OAuth Callback Endpoint", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 2: Google OAuth Session Data Processing - New .edu User
    def test_google_oauth_new_edu_user(self) -> bool:
        """Test POST /api/auth/google-oauth - Process Google OAuth for new .edu user"""
        try:
            oauth_data = self.create_mock_google_data("john.doe@stanford.edu", "John Doe")
            
            response = self.session.post(
                f"{API_BASE}/auth/google-oauth",
                json=oauth_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["access_token", "token_type", "user"]
                
                if all(field in data for field in required_fields):
                    user_data = data["user"]
                    
                    # Verify user creation details
                    if (user_data["email"] == oauth_data["google_data"]["email"] and
                        user_data["first_name"] == "John" and
                        user_data["last_name"] == "Doe" and
                        user_data["is_verified"] == True):
                        
                        # Store for later tests
                        self.test_users.append(oauth_data)
                        self.oauth_tokens[oauth_data["google_data"]["email"]] = data["access_token"]
                        
                        self.log_test("Google OAuth New .edu User Creation", "PASS",
                                    f"Successfully created user: {user_data['email']}")
                        return True
                    else:
                        self.log_test("Google OAuth New .edu User Creation", "FAIL",
                                    f"User data validation failed: {user_data}")
                        return False
                else:
                    self.log_test("Google OAuth New .edu User Creation", "FAIL",
                                f"Missing required response fields: {data}")
                    return False
            else:
                self.log_test("Google OAuth New .edu User Creation", "FAIL",
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Google OAuth New .edu User Creation", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 3: Google OAuth Session Data Processing - Existing User Login
    def test_google_oauth_existing_user_login(self) -> bool:
        """Test existing user login flow via Google OAuth"""
        try:
            if not self.test_users:
                self.log_test("Google OAuth Existing User Login", "FAIL", 
                            "No existing users to test login")
                return False
            
            # Use same email as previous test but with updated data
            original_oauth = self.test_users[0]
            oauth_data = self.create_mock_google_data(
                original_oauth["google_data"]["email"],
                "John Doe Updated",
                "https://lh3.googleusercontent.com/a/updated-photo.jpg"
            )
            
            response = self.session.post(
                f"{API_BASE}/auth/google-oauth",
                json=oauth_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if all(key in data for key in ["access_token", "token_type", "user"]):
                    user_data = data["user"]
                    
                    # Verify it's the same user (same email)
                    if user_data["email"] == oauth_data["google_data"]["email"]:
                        self.log_test("Google OAuth Existing User Login", "PASS",
                                    "Successfully logged in existing user")
                        return True
                    else:
                        self.log_test("Google OAuth Existing User Login", "FAIL",
                                    "Email mismatch in existing user login")
                        return False
                else:
                    self.log_test("Google OAuth Existing User Login", "FAIL",
                                f"Missing required fields in response: {data}")
                    return False
            else:
                self.log_test("Google OAuth Existing User Login", "FAIL",
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Google OAuth Existing User Login", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 4: Email Validation - .edu Domain Requirement
    def test_oauth_edu_email_validation(self) -> bool:
        """Test that only .edu emails are allowed for new OAuth users"""
        try:
            # Test non-.edu email rejection
            oauth_data = self.create_mock_google_data("user@gmail.com", "Regular User")
            
            response = self.session.post(
                f"{API_BASE}/auth/google-oauth",
                json=oauth_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 400:
                data = response.json()
                if "Only .edu email addresses are allowed" in data.get("detail", ""):
                    self.log_test("OAuth .edu Email Validation", "PASS",
                                "Correctly rejected non-.edu email for new user")
                    return True
                else:
                    self.log_test("OAuth .edu Email Validation", "FAIL",
                                f"Wrong error message: {data}")
                    return False
            else:
                self.log_test("OAuth .edu Email Validation", "FAIL",
                            f"Expected HTTP 400, got {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("OAuth .edu Email Validation", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 5: JWT Token Generation and Validation
    def test_oauth_jwt_token_generation(self) -> bool:
        """Test JWT token generation for OAuth users"""
        try:
            if not self.oauth_tokens:
                self.log_test("OAuth JWT Token Generation", "FAIL", "No OAuth tokens to test")
                return False
            
            # Get first OAuth user's token
            email = list(self.oauth_tokens.keys())[0]
            token = self.oauth_tokens[email]
            
            # Test token with protected endpoint
            headers = {"Authorization": f"Bearer {token}"}
            response = self.session.get(f"{API_BASE}/users/me", headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                if user_data["email"] == email:
                    self.log_test("OAuth JWT Token Generation", "PASS",
                                "JWT token works with protected endpoints")
                    return True
                else:
                    self.log_test("OAuth JWT Token Generation", "FAIL",
                                f"Token returned wrong user data: {user_data}")
                    return False
            else:
                self.log_test("OAuth JWT Token Generation", "FAIL",
                            f"Token validation failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("OAuth JWT Token Generation", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 6: Profile Picture Import from Google
    def test_oauth_profile_picture_import(self) -> bool:
        """Test profile picture import from Google OAuth data"""
        try:
            # Create new OAuth user with profile picture
            oauth_data = self.create_mock_google_data(
                "picture.test@mit.edu",
                "Picture Test User",
                "https://lh3.googleusercontent.com/a/test-profile-picture.jpg"
            )
            
            response = self.session.post(
                f"{API_BASE}/auth/google-oauth",
                json=oauth_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_data = data["user"]
                
                # Check if profile picture was imported
                if (user_data.get("profile") and 
                    user_data["profile"].get("profile_picture") == oauth_data["google_data"]["picture"]):
                    self.log_test("OAuth Profile Picture Import", "PASS",
                                "Profile picture successfully imported from Google")
                    return True
                else:
                    self.log_test("OAuth Profile Picture Import", "FAIL",
                                f"Profile picture not imported correctly: {user_data.get('profile', {})}")
                    return False
            else:
                self.log_test("OAuth Profile Picture Import", "FAIL",
                            f"OAuth failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("OAuth Profile Picture Import", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 7: Session Storage and Persistence
    def test_oauth_session_persistence(self) -> bool:
        """Test OAuth session storage and persistence"""
        try:
            # Create OAuth user and verify session is stored
            oauth_data = self.create_mock_google_data("session.test@harvard.edu", "Session Test User")
            
            response = self.session.post(
                f"{API_BASE}/auth/google-oauth",
                json=oauth_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                
                if access_token:
                    # Test multiple requests with same token to verify persistence
                    headers = {"Authorization": f"Bearer {access_token}"}
                    
                    # First request
                    response1 = self.session.get(f"{API_BASE}/users/me", headers=headers, timeout=10)
                    time.sleep(1)  # Brief pause
                    
                    # Second request
                    response2 = self.session.get(f"{API_BASE}/users/me", headers=headers, timeout=10)
                    
                    if response1.status_code == 200 and response2.status_code == 200:
                        user1 = response1.json()
                        user2 = response2.json()
                        
                        if user1["id"] == user2["id"]:
                            self.log_test("OAuth Session Persistence", "PASS",
                                        "Session persists across multiple requests")
                            return True
                        else:
                            self.log_test("OAuth Session Persistence", "FAIL",
                                        "Session returned different user data")
                            return False
                    else:
                        self.log_test("OAuth Session Persistence", "FAIL",
                                    f"Session validation failed: {response1.status_code}, {response2.status_code}")
                        return False
                else:
                    self.log_test("OAuth Session Persistence", "FAIL", "No access token received")
                    return False
            else:
                self.log_test("OAuth Session Persistence", "FAIL",
                            f"OAuth failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("OAuth Session Persistence", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 8: OAuth User Profile Management
    def test_oauth_user_profile_management(self) -> bool:
        """Test that OAuth users can manage their profiles"""
        try:
            if not self.oauth_tokens:
                self.log_test("OAuth User Profile Management", "FAIL", "No OAuth tokens available")
                return False
            
            email = list(self.oauth_tokens.keys())[0]
            token = self.oauth_tokens[email]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Update profile
            profile_update = {
                "profile": {
                    "age": 25,
                    "bio": "Computer Science student studying abroad",
                    "university": "Stanford University",
                    "course": "Computer Science",
                    "study_level": "Masters",
                    "origin_country": "Canada",
                    "destination_country": "USA"
                }
            }
            
            response = self.session.put(
                f"{API_BASE}/users/me",
                json=profile_update,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                # Verify the update
                get_response = self.session.get(f"{API_BASE}/users/me", headers=headers, timeout=10)
                
                if get_response.status_code == 200:
                    user_data = get_response.json()
                    profile = user_data.get("profile", {})
                    
                    if (profile.get("university") == "Stanford University" and
                        profile.get("bio") == "Computer Science student studying abroad"):
                        self.log_test("OAuth User Profile Management", "PASS",
                                    "OAuth user can update and retrieve profile")
                        return True
                    else:
                        self.log_test("OAuth User Profile Management", "FAIL",
                                    f"Profile not updated correctly: {profile}")
                        return False
                else:
                    self.log_test("OAuth User Profile Management", "FAIL",
                                f"Failed to retrieve updated profile: {get_response.status_code}")
                    return False
            else:
                self.log_test("OAuth User Profile Management", "FAIL",
                            f"Profile update failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("OAuth User Profile Management", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 9: OAuth User Connection System Integration
    def test_oauth_user_connection_system(self) -> bool:
        """Test that OAuth users can use connection system"""
        try:
            # Create two OAuth users for connection testing
            oauth_user1 = self.create_mock_google_data("connect1@yale.edu", "Connect User 1")
            oauth_user2 = self.create_mock_google_data("connect2@princeton.edu", "Connect User 2")
            
            # Create both users
            response1 = self.session.post(f"{API_BASE}/auth/google-oauth", json=oauth_user1, 
                                        headers={"Content-Type": "application/json"}, timeout=10)
            response2 = self.session.post(f"{API_BASE}/auth/google-oauth", json=oauth_user2,
                                        headers={"Content-Type": "application/json"}, timeout=10)
            
            if response1.status_code == 200 and response2.status_code == 200:
                user1_data = response1.json()
                user2_data = response2.json()
                
                user1_token = user1_data["access_token"]
                user2_token = user2_data["access_token"]
                user2_id = user2_data["user"]["id"]
                
                # Send connection request from user1 to user2
                headers1 = {"Authorization": f"Bearer {user1_token}"}
                conn_response = self.session.post(
                    f"{API_BASE}/connections/request",
                    params={"to_user_id": user2_id},
                    headers=headers1,
                    timeout=10
                )
                
                if conn_response.status_code == 200:
                    # Check if user2 received the connection request
                    headers2 = {"Authorization": f"Bearer {user2_token}"}
                    requests_response = self.session.get(
                        f"{API_BASE}/connections/requests",
                        headers=headers2,
                        timeout=10
                    )
                    
                    if requests_response.status_code == 200:
                        requests_data = requests_response.json()
                        incoming_requests = requests_data.get("incoming", [])
                        
                        if incoming_requests:
                            self.log_test("OAuth User Connection System", "PASS",
                                        "OAuth users can send and receive connection requests")
                            return True
                        else:
                            self.log_test("OAuth User Connection System", "FAIL",
                                        "No incoming connection requests found")
                            return False
                    else:
                        self.log_test("OAuth User Connection System", "FAIL",
                                    f"Failed to get connection requests: {requests_response.status_code}")
                        return False
                else:
                    self.log_test("OAuth User Connection System", "FAIL",
                                f"Connection request failed: {conn_response.status_code}")
                    return False
            else:
                self.log_test("OAuth User Connection System", "FAIL",
                            f"Failed to create OAuth users: {response1.status_code}, {response2.status_code}")
                return False
                
        except Exception as e:
            self.log_test("OAuth User Connection System", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 10: OAuth User Search Visibility
    def test_oauth_user_search_visibility(self) -> bool:
        """Test that OAuth users appear in user search when searched by other users"""
        try:
            # Create first OAuth user with searchable profile
            oauth_data1 = self.create_mock_google_data("search.oauth1@columbia.edu", "Search OAuth User 1")
            
            response1 = self.session.post(
                f"{API_BASE}/auth/google-oauth",
                json=oauth_data1,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            # Create second OAuth user to perform the search
            oauth_data2 = self.create_mock_google_data("search.oauth2@yale.edu", "Search OAuth User 2")
            
            response2 = self.session.post(
                f"{API_BASE}/auth/google-oauth",
                json=oauth_data2,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response1.status_code == 200 and response2.status_code == 200:
                data1 = response1.json()
                data2 = response2.json()
                
                token1 = data1["access_token"]
                token2 = data2["access_token"]
                
                headers1 = {"Authorization": f"Bearer {token1}"}
                headers2 = {"Authorization": f"Bearer {token2}"}
                
                # Update first user's profile with searchable data
                profile_update = {
                    "profile": {
                        "university": "Columbia University",
                        "course": "Data Science",
                        "origin_country": "India",
                        "destination_country": "USA"
                    }
                }
                
                update_response = self.session.put(
                    f"{API_BASE}/users/me",
                    json=profile_update,
                    headers=headers1,
                    timeout=10
                )
                
                if update_response.status_code == 200:
                    # Search for users by university using second user's token
                    search_response = self.session.get(
                        f"{API_BASE}/users/search",
                        params={"university": "Columbia"},
                        headers=headers2,  # Use second user's token
                        timeout=10
                    )
                    
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        users = search_data.get("users", [])
                        
                        # Check if first OAuth user appears in search results when searched by second user
                        oauth_user_found = any(
                            user["email"] == oauth_data1["google_data"]["email"] 
                            for user in users
                        )
                        
                        if oauth_user_found:
                            self.log_test("OAuth User Search Visibility", "PASS",
                                        "OAuth users appear in search results when searched by other users")
                            return True
                        else:
                            self.log_test("OAuth User Search Visibility", "FAIL",
                                        f"OAuth user not found in search results. Found {len(users)} users")
                            return False
                    else:
                        self.log_test("OAuth User Search Visibility", "FAIL",
                                    f"Search failed: {search_response.status_code}")
                        return False
                else:
                    self.log_test("OAuth User Search Visibility", "FAIL",
                                f"Profile update failed: {update_response.status_code}")
                    return False
            else:
                self.log_test("OAuth User Search Visibility", "FAIL",
                            f"OAuth user creation failed: {response1.status_code}, {response2.status_code}")
                return False
                
        except Exception as e:
            self.log_test("OAuth User Search Visibility", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 11: Invalid Request Handling
    def test_oauth_invalid_request_handling(self) -> bool:
        """Test OAuth endpoint handles invalid requests properly"""
        try:
            test_cases = [
                {
                    "name": "Missing Email",
                    "data": {
                        "google_data": {"id": "test", "name": "Test User"},
                        "session_token": "test_token"
                    },
                    "expected_status": 400
                },
                {
                    "name": "Missing Google Data",
                    "data": {"session_token": "test_token"},
                    "expected_status": [400, 422]
                },
                {
                    "name": "Invalid JSON Structure",
                    "data": {"invalid_field": "test"},
                    "expected_status": [400, 422]
                }
            ]
            
            all_passed = True
            for test_case in test_cases:
                response = self.session.post(
                    f"{API_BASE}/auth/google-oauth",
                    json=test_case["data"],
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                expected_statuses = (test_case["expected_status"] 
                                   if isinstance(test_case["expected_status"], list) 
                                   else [test_case["expected_status"]])
                
                if response.status_code not in expected_statuses:
                    self.log_test(f"OAuth Invalid Request - {test_case['name']}", "FAIL",
                                f"Expected {expected_statuses}, got {response.status_code}")
                    all_passed = False
                else:
                    self.log_test(f"OAuth Invalid Request - {test_case['name']}", "PASS",
                                f"Correctly rejected with status {response.status_code}")
            
            return all_passed
                
        except Exception as e:
            self.log_test("OAuth Invalid Request Handling", "FAIL", f"Exception: {str(e)}")
            return False

    def print_summary(self):
        """Print comprehensive test summary"""
        passed = sum(1 for result in self.test_results if result["status"] == "PASS")
        total = len(self.test_results)
        
        print("\n" + "="*80)
        print("🔐 GOOGLE OAUTH COMPREHENSIVE TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "0%")
        
        if passed < total:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result['details']}")
        
        print(f"\n📊 DETAILED RESULTS:")
        for result in self.test_results:
            status_emoji = "✅" if result["status"] == "PASS" else "❌"
            print(f"  {status_emoji} {result['test']}")
        
        return passed == total

    def run_all_tests(self) -> bool:
        """Run all Google OAuth tests"""
        print("🚀 Starting Comprehensive Google OAuth Testing")
        print("="*80)
        print(f"Backend URL: {API_BASE}")
        print()
        
        # Run all tests in sequence
        tests = [
            ("OAuth Callback Endpoint", self.test_oauth_callback_endpoint),
            ("Google OAuth New .edu User", self.test_google_oauth_new_edu_user),
            ("Google OAuth Existing User Login", self.test_google_oauth_existing_user_login),
            ("OAuth .edu Email Validation", self.test_oauth_edu_email_validation),
            ("OAuth JWT Token Generation", self.test_oauth_jwt_token_generation),
            ("OAuth Profile Picture Import", self.test_oauth_profile_picture_import),
            ("OAuth Session Persistence", self.test_oauth_session_persistence),
            ("OAuth User Profile Management", self.test_oauth_user_profile_management),
            ("OAuth User Connection System", self.test_oauth_user_connection_system),
            ("OAuth User Search Visibility", self.test_oauth_user_search_visibility),
            ("OAuth Invalid Request Handling", self.test_oauth_invalid_request_handling),
        ]
        
        for test_name, test_func in tests:
            try:
                print(f"🔍 Running: {test_name}...")
                test_func()
            except Exception as e:
                self.log_test(test_name, "FAIL", f"Unexpected exception: {str(e)}")
        
        return self.print_summary()

def main():
    """Main function to run Google OAuth comprehensive tests"""
    tester = GoogleOAuthTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All Google OAuth tests passed successfully!")
        exit(0)
    else:
        print("\n❌ Some Google OAuth tests failed")
        exit(1)

if __name__ == "__main__":
    main()