#!/usr/bin/env python3
"""
Backend API Testing for International Student Networking App - Connection System Focus
Testing user-reported issues with connection management and profile APIs
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('EXPO_PUBLIC_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except:
        pass
    return "https://campuslink-25.preview.emergentagent.com"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

class ConnectionSystemTester:
    def __init__(self):
        self.base_url = API_URL
        self.session = requests.Session()
        self.test_users = []
        self.auth_tokens = {}
        self.test_results = []
        
    def log_test(self, test_name, success, message="", details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        })
        print()

    def create_test_users(self):
        """Create test users for connection testing"""
        test_users_data = [
            {
                "email": "sarah.johnson@stanford.edu",
                "password": "SecurePass123!",
                "first_name": "Sarah",
                "last_name": "Johnson",
                "phone": "+1-555-0123"
            },
            {
                "email": "alex.chen@mit.edu", 
                "password": "SecurePass456!",
                "first_name": "Alex",
                "last_name": "Chen",
                "phone": "+1-555-0456"
            },
            {
                "email": "maria.garcia@berkeley.edu",
                "password": "SecurePass789!",
                "first_name": "Maria", 
                "last_name": "Garcia",
                "phone": "+1-555-0789"
            }
        ]
        
        print("=== CREATING TEST USERS ===")
        
        for user_data in test_users_data:
            try:
                # Try to register user
                response = self.session.post(f"{self.base_url}/auth/register", json=user_data)
                
                if response.status_code == 200:
                    print(f"✅ Created user: {user_data['email']}")
                elif response.status_code == 400 and "already registered" in response.text:
                    print(f"ℹ️  User already exists: {user_data['email']}")
                else:
                    print(f"❌ Failed to create user {user_data['email']}: {response.text}")
                    continue
                
                # Login to get token
                login_response = self.session.post(f"{self.base_url}/auth/login", json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                })
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    self.auth_tokens[user_data["email"]] = login_data["access_token"]
                    self.test_users.append({
                        "email": user_data["email"],
                        "user_id": login_data["user"]["id"],
                        "token": login_data["access_token"],
                        "user_data": login_data["user"]
                    })
                    print(f"✅ Logged in user: {user_data['email']}")
                else:
                    print(f"❌ Failed to login user {user_data['email']}: {login_response.text}")
                    
            except Exception as e:
                print(f"❌ Error with user {user_data['email']}: {str(e)}")
        
        print(f"\n✅ Successfully set up {len(self.test_users)} test users\n")
        return len(self.test_users) >= 2

    def test_user_profile_apis(self):
        """Test user profile management APIs"""
        print("=== TESTING USER PROFILE APIS ===")
        
        if not self.test_users:
            self.log_test("Profile APIs Setup", False, "No test users available")
            return
        
        user = self.test_users[0]
        headers = {"Authorization": f"Bearer {user['token']}"}
        
        # Test GET /api/users/me
        try:
            response = self.session.get(f"{self.base_url}/users/me", headers=headers)
            
            if response.status_code == 200:
                profile_data = response.json()
                self.log_test("GET /api/users/me", True, f"Retrieved profile for {profile_data.get('first_name', 'Unknown')}")
            else:
                self.log_test("GET /api/users/me", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/users/me", False, f"Exception: {str(e)}")
        
        # Test PUT /api/users/me - Update profile
        try:
            update_data = {
                "first_name": "Sarah Updated",
                "profile": {
                    "age": 22,
                    "bio": "Computer Science student from California, passionate about AI and machine learning",
                    "origin_country": "United States",
                    "origin_city": "San Francisco",
                    "destination_country": "United States", 
                    "destination_city": "Palo Alto",
                    "university": "Stanford University",
                    "course": "Computer Science",
                    "study_level": "Masters"
                }
            }
            
            response = self.session.put(f"{self.base_url}/users/me", json=update_data, headers=headers)
            
            if response.status_code == 200:
                updated_data = response.json()
                self.log_test("PUT /api/users/me", True, "Profile updated successfully")
            else:
                self.log_test("PUT /api/users/me", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("PUT /api/users/me", False, f"Exception: {str(e)}")

    def test_user_search_apis(self):
        """Test user search functionality"""
        print("=== TESTING USER SEARCH APIS ===")
        
        if not self.test_users:
            self.log_test("User Search Setup", False, "No test users available")
            return
        
        user = self.test_users[0]
        headers = {"Authorization": f"Bearer {user['token']}"}
        
        # Test basic search
        try:
            response = self.session.get(f"{self.base_url}/users/search", headers=headers)
            
            if response.status_code == 200:
                search_data = response.json()
                users_found = len(search_data.get('users', []))
                self.log_test("GET /api/users/search (basic)", True, f"Found {users_found} users")
            else:
                self.log_test("GET /api/users/search (basic)", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/users/search (basic)", False, f"Exception: {str(e)}")
        
        # Test search with university filter
        try:
            params = {"university": "MIT"}
            response = self.session.get(f"{self.base_url}/users/search", params=params, headers=headers)
            
            if response.status_code == 200:
                search_data = response.json()
                users_found = len(search_data.get('users', []))
                self.log_test("GET /api/users/search (university filter)", True, f"Found {users_found} users from MIT")
            else:
                self.log_test("GET /api/users/search (university filter)", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/users/search (university filter)", False, f"Exception: {str(e)}")
        
        # Test search with country filter
        try:
            params = {"country": "United States"}
            response = self.session.get(f"{self.base_url}/users/search", params=params, headers=headers)
            
            if response.status_code == 200:
                search_data = response.json()
                users_found = len(search_data.get('users', []))
                self.log_test("GET /api/users/search (country filter)", True, f"Found {users_found} users from United States")
            else:
                self.log_test("GET /api/users/search (country filter)", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/users/search (country filter)", False, f"Exception: {str(e)}")

    def test_connection_system_apis(self):
        """Test connection system APIs - the main focus"""
        print("=== TESTING CONNECTION SYSTEM APIS ===")
        
        if len(self.test_users) < 2:
            self.log_test("Connection System Setup", False, "Need at least 2 test users")
            return
        
        user1 = self.test_users[0]  # Sarah
        user2 = self.test_users[1]  # Alex
        
        headers1 = {"Authorization": f"Bearer {user1['token']}"}
        headers2 = {"Authorization": f"Bearer {user2['token']}"}
        
        # Test POST /api/connections/request - Send connection request
        try:
            params = {"to_user_id": user2['user_id']}
            response = self.session.post(f"{self.base_url}/connections/request", 
                                       params=params, headers=headers1)
            
            if response.status_code == 200:
                self.log_test("POST /api/connections/request", True, f"Connection request sent from {user1['email']} to {user2['email']}")
            elif response.status_code == 400 and "already exists" in response.text:
                self.log_test("POST /api/connections/request", True, "Connection request already exists (expected)")
            else:
                self.log_test("POST /api/connections/request", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("POST /api/connections/request", False, f"Exception: {str(e)}")
        
        # Test GET /api/connections/requests - Get connection requests
        try:
            response = self.session.get(f"{self.base_url}/connections/requests", headers=headers2)
            
            if response.status_code == 200:
                requests_data = response.json()
                incoming = requests_data.get('incoming', [])
                outgoing = requests_data.get('outgoing', [])
                self.log_test("GET /api/connections/requests", True, 
                            f"Retrieved {len(incoming)} incoming and {len(outgoing)} outgoing requests")
                
                # Store request ID for response test
                self.pending_request_id = None
                if incoming:
                    self.pending_request_id = incoming[0]['id']
                    
            else:
                self.log_test("GET /api/connections/requests", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/connections/requests", False, f"Exception: {str(e)}")
        
        # Test POST /api/connections/respond - Accept connection request
        if hasattr(self, 'pending_request_id') and self.pending_request_id:
            try:
                response_data = {
                    "request_id": self.pending_request_id,
                    "action": "accept"
                }
                response = self.session.post(f"{self.base_url}/connections/respond", 
                                           json=response_data, headers=headers2)
                
                if response.status_code == 200:
                    self.log_test("POST /api/connections/respond (accept)", True, "Connection request accepted successfully")
                else:
                    self.log_test("POST /api/connections/respond (accept)", False, f"Status: {response.status_code}, Response: {response.text}")
                    
            except Exception as e:
                self.log_test("POST /api/connections/respond (accept)", False, f"Exception: {str(e)}")
        else:
            self.log_test("POST /api/connections/respond (accept)", False, "No pending request ID available for testing")
        
        # Test connection request to self (should fail)
        try:
            request_data = {"to_user_id": user1['user_id']}
            response = self.session.post(f"{self.base_url}/connections/request", 
                                       json=request_data, headers=headers1)
            
            if response.status_code == 400:
                self.log_test("POST /api/connections/request (self)", True, "Correctly rejected self-connection request")
            else:
                self.log_test("POST /api/connections/request (self)", False, f"Should reject self-connection. Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("POST /api/connections/request (self)", False, f"Exception: {str(e)}")
        
        # Test connection request to non-existent user
        try:
            fake_user_id = str(uuid.uuid4())
            request_data = {"to_user_id": fake_user_id}
            response = self.session.post(f"{self.base_url}/connections/request", 
                                       json=request_data, headers=headers1)
            
            if response.status_code == 404:
                self.log_test("POST /api/connections/request (non-existent)", True, "Correctly rejected request to non-existent user")
            else:
                self.log_test("POST /api/connections/request (non-existent)", False, f"Should reject non-existent user. Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("POST /api/connections/request (non-existent)", False, f"Exception: {str(e)}")

    def test_additional_connection_scenarios(self):
        """Test additional connection scenarios with third user"""
        print("=== TESTING ADDITIONAL CONNECTION SCENARIOS ===")
        
        if len(self.test_users) < 3:
            self.log_test("Additional Connection Tests", False, "Need at least 3 test users")
            return
        
        user1 = self.test_users[0]  # Sarah
        user3 = self.test_users[2]  # Maria
        
        headers1 = {"Authorization": f"Bearer {user1['token']}"}
        headers3 = {"Authorization": f"Bearer {user3['token']}"}
        
        # Send connection request from user1 to user3
        try:
            request_data = {"to_user_id": user3['user_id']}
            response = self.session.post(f"{self.base_url}/connections/request", 
                                       json=request_data, headers=headers1)
            
            if response.status_code == 200:
                self.log_test("Connection Request (User1 -> User3)", True, "Connection request sent successfully")
            elif response.status_code == 400 and "already exists" in response.text:
                self.log_test("Connection Request (User1 -> User3)", True, "Connection request already exists")
            else:
                self.log_test("Connection Request (User1 -> User3)", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Connection Request (User1 -> User3)", False, f"Exception: {str(e)}")
        
        # Test rejecting a connection request
        try:
            # Get pending requests for user3
            response = self.session.get(f"{self.base_url}/connections/requests", headers=headers3)
            
            if response.status_code == 200:
                requests_data = response.json()
                incoming = requests_data.get('incoming', [])
                
                if incoming:
                    request_id = incoming[0]['id']
                    response_data = {
                        "request_id": request_id,
                        "action": "reject"
                    }
                    reject_response = self.session.post(f"{self.base_url}/connections/respond", 
                                                      json=response_data, headers=headers3)
                    
                    if reject_response.status_code == 200:
                        self.log_test("POST /api/connections/respond (reject)", True, "Connection request rejected successfully")
                    else:
                        self.log_test("POST /api/connections/respond (reject)", False, f"Status: {reject_response.status_code}")
                else:
                    self.log_test("POST /api/connections/respond (reject)", False, "No incoming requests to reject")
            else:
                self.log_test("POST /api/connections/respond (reject)", False, f"Failed to get requests: {response.status_code}")
                
        except Exception as e:
            self.log_test("POST /api/connections/respond (reject)", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 STARTING BACKEND API TESTING - CONNECTION SYSTEM FOCUS")
        print("=" * 60)
        
        # Setup test users
        if not self.create_test_users():
            print("❌ Failed to create test users. Cannot proceed with testing.")
            return False
        
        # Run tests in order
        self.test_user_profile_apis()
        self.test_user_search_apis() 
        self.test_connection_system_apis()
        self.test_additional_connection_scenarios()
        
        # Print summary
        self.print_summary()
        
        return self.get_success_rate() > 0.8  # 80% success rate

    def print_summary(self):
        """Print test summary"""
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
        
        print("=" * 60)

    def get_success_rate(self):
        """Get success rate as decimal"""
        if not self.test_results:
            return 0.0
        return sum(1 for result in self.test_results if result['success']) / len(self.test_results)

if __name__ == "__main__":
    tester = ConnectionSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 Backend testing completed successfully!")
        sys.exit(0)
    else:
        print("⚠️  Backend testing completed with issues.")
        sys.exit(1)