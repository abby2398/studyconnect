#!/usr/bin/env python3

import requests
import json
import os
from datetime import datetime
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://password-reset-39.preview.emergentagent.com')
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
        print(f"OAUTH INTEGRATION WITH EXISTING SYSTEM TEST SUMMARY")
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

def test_oauth_user_profile_management():
    """Test that OAuth users can manage their profiles like regular users"""
    results = TestResults()
    
    try:
        # Create OAuth user
        oauth_data = {
            "google_data": {
                "id": "profile_test_user",
                "email": "profile.test@harvard.edu",
                "name": "Profile Test User",
                "picture": "https://lh3.googleusercontent.com/a/profile-photo.jpg"
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
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # Test profile update
                profile_update = {
                    "profile": {
                        "age": 25,
                        "bio": "Computer Science student from Harvard",
                        "university": "Harvard University",
                        "course": "Computer Science",
                        "study_level": "Masters",
                        "origin_country": "USA",
                        "destination_country": "USA"
                    }
                }
                
                update_response = requests.put(f"{API_BASE}/users/me", 
                                             json=profile_update, 
                                             headers=headers, 
                                             timeout=10)
                
                if update_response.status_code == 200:
                    results.add_result("OAuth User Profile Update", True, 
                                     "OAuth user can update profile successfully")
                    
                    # Verify the update
                    get_response = requests.get(f"{API_BASE}/users/me", 
                                              headers=headers, 
                                              timeout=10)
                    
                    if get_response.status_code == 200:
                        user_data = get_response.json()
                        if (user_data.get("profile", {}).get("university") == "Harvard University" and
                            user_data.get("profile", {}).get("bio") == "Computer Science student from Harvard"):
                            results.add_result("OAuth User Profile Verification", True, 
                                             "Profile updates are persisted correctly")
                        else:
                            results.add_result("OAuth User Profile Verification", False, 
                                             f"Profile not updated correctly: {user_data.get('profile', {})}")
                    else:
                        results.add_result("OAuth User Profile Verification", False, 
                                         f"Failed to retrieve updated profile: {get_response.status_code}")
                else:
                    results.add_result("OAuth User Profile Update", False, 
                                     f"Profile update failed: {update_response.status_code}")
            else:
                results.add_result("OAuth User Profile Update", False, "No access token received")
        else:
            results.add_result("OAuth User Profile Update", False, f"OAuth failed: {response.status_code}")
            
    except Exception as e:
        results.add_result("OAuth User Profile Update", False, f"Exception: {str(e)}")
    
    return results

def test_oauth_user_connections():
    """Test that OAuth users can use the connection system"""
    results = TestResults()
    
    try:
        # Create first OAuth user
        oauth_data1 = {
            "google_data": {
                "id": "connection_test_user1",
                "email": "connection1@yale.edu",
                "name": "Connection Test User 1",
                "picture": "https://lh3.googleusercontent.com/a/conn1-photo.jpg"
            },
            "session_token": f"session_token_{uuid.uuid4()}"
        }
        
        response1 = requests.post(f"{API_BASE}/auth/google-oauth", 
                                json=oauth_data1, 
                                headers={"Content-Type": "application/json"},
                                timeout=10)
        
        # Create second OAuth user
        oauth_data2 = {
            "google_data": {
                "id": "connection_test_user2",
                "email": "connection2@princeton.edu",
                "name": "Connection Test User 2",
                "picture": "https://lh3.googleusercontent.com/a/conn2-photo.jpg"
            },
            "session_token": f"session_token_{uuid.uuid4()}"
        }
        
        response2 = requests.post(f"{API_BASE}/auth/google-oauth", 
                                json=oauth_data2, 
                                headers={"Content-Type": "application/json"},
                                timeout=10)
        
        if response1.status_code == 200 and response2.status_code == 200:
            user1_data = response1.json()
            user2_data = response2.json()
            
            user1_token = user1_data.get("access_token")
            user2_token = user2_data.get("access_token")
            user2_id = user2_data.get("user", {}).get("id")
            
            if user1_token and user2_token and user2_id:
                # Test connection request from OAuth user 1 to OAuth user 2
                headers1 = {"Authorization": f"Bearer {user1_token}"}
                
                conn_response = requests.post(f"{API_BASE}/connections/request?to_user_id={user2_id}", 
                                            headers=headers1, 
                                            timeout=10)
                
                if conn_response.status_code == 200:
                    results.add_result("OAuth User Connection Request", True, 
                                     "OAuth users can send connection requests")
                    
                    # Test accepting connection from OAuth user 2
                    headers2 = {"Authorization": f"Bearer {user2_token}"}
                    
                    # Get connection requests
                    requests_response = requests.get(f"{API_BASE}/connections/requests", 
                                                   headers=headers2, 
                                                   timeout=10)
                    
                    if requests_response.status_code == 200:
                        requests_data = requests_response.json()
                        incoming_requests = requests_data.get("incoming", [])
                        
                        if incoming_requests:
                            request_id = incoming_requests[0]["id"]
                            
                            # Accept the request
                            accept_response = requests.post(f"{API_BASE}/connections/respond?request_id={request_id}&action=accept", 
                                                          headers=headers2, 
                                                          timeout=10)
                            
                            if accept_response.status_code == 200:
                                results.add_result("OAuth User Connection Accept", True, 
                                                 "OAuth users can accept connection requests")
                            else:
                                results.add_result("OAuth User Connection Accept", False, 
                                                 f"Failed to accept connection: {accept_response.status_code}")
                        else:
                            results.add_result("OAuth User Connection Accept", False, 
                                             "No incoming connection requests found")
                    else:
                        results.add_result("OAuth User Connection Accept", False, 
                                         f"Failed to get connection requests: {requests_response.status_code}")
                else:
                    results.add_result("OAuth User Connection Request", False, 
                                     f"Connection request failed: {conn_response.status_code}")
            else:
                results.add_result("OAuth User Connection Request", False, "Missing tokens or user ID")
        else:
            results.add_result("OAuth User Connection Request", False, 
                             f"Failed to create OAuth users: {response1.status_code}, {response2.status_code}")
            
    except Exception as e:
        results.add_result("OAuth User Connection Request", False, f"Exception: {str(e)}")
    
    return results

def test_oauth_user_search():
    """Test that OAuth users appear in search results"""
    results = TestResults()
    
    try:
        # Create OAuth user with specific profile
        oauth_data = {
            "google_data": {
                "id": "search_test_user",
                "email": "search.test@columbia.edu",
                "name": "Search Test User",
                "picture": "https://lh3.googleusercontent.com/a/search-photo.jpg"
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
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # Update profile with searchable data
                profile_update = {
                    "profile": {
                        "university": "Columbia University",
                        "course": "Data Science",
                        "origin_country": "Canada",
                        "destination_country": "USA"
                    }
                }
                
                update_response = requests.put(f"{API_BASE}/users/me", 
                                             json=profile_update, 
                                             headers=headers, 
                                             timeout=10)
                
                if update_response.status_code == 200:
                    # Test search by university
                    search_response = requests.get(f"{API_BASE}/users/search?university=Columbia", 
                                                 headers=headers, 
                                                 timeout=10)
                    
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        users = search_data.get("users", [])
                        
                        # Check if our OAuth user appears in search results
                        oauth_user_found = any(user["email"] == oauth_data["google_data"]["email"] for user in users)
                        
                        if oauth_user_found:
                            results.add_result("OAuth User Search Visibility", True, 
                                             "OAuth users appear in search results")
                        else:
                            results.add_result("OAuth User Search Visibility", False, 
                                             "OAuth user not found in search results")
                    else:
                        results.add_result("OAuth User Search Visibility", False, 
                                         f"Search failed: {search_response.status_code}")
                else:
                    results.add_result("OAuth User Search Visibility", False, 
                                     f"Profile update failed: {update_response.status_code}")
            else:
                results.add_result("OAuth User Search Visibility", False, "No access token received")
        else:
            results.add_result("OAuth User Search Visibility", False, f"OAuth failed: {response.status_code}")
            
    except Exception as e:
        results.add_result("OAuth User Search Visibility", False, f"Exception: {str(e)}")
    
    return results

def main():
    print("🔗 TESTING OAUTH INTEGRATION WITH EXISTING SYSTEM")
    print("="*60)
    
    all_results = TestResults()
    
    # Test OAuth user profile management
    print("\n👤 Testing OAuth User Profile Management...")
    profile_results = test_oauth_user_profile_management()
    all_results.passed += profile_results.passed
    all_results.failed += profile_results.failed
    all_results.results.extend(profile_results.results)
    
    # Test OAuth user connections
    print("\n🤝 Testing OAuth User Connections...")
    connection_results = test_oauth_user_connections()
    all_results.passed += connection_results.passed
    all_results.failed += connection_results.failed
    all_results.results.extend(connection_results.results)
    
    # Test OAuth user search visibility
    print("\n🔍 Testing OAuth User Search Visibility...")
    search_results = test_oauth_user_search()
    all_results.passed += search_results.passed
    all_results.failed += search_results.failed
    all_results.results.extend(search_results.results)
    
    # Print final summary
    all_results.print_summary()
    
    return all_results.failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)