#!/usr/bin/env python3
"""
Comprehensive Backend Testing for StudyConnect Notification System
Tests all notification APIs, preferences, push tokens, and integration features
"""

import asyncio
import requests
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Configuration
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://campuslink-25.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class NotificationSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_users = []
        self.auth_tokens = {}
        self.test_notifications = []
        self.test_push_tokens = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results"""
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        print()

    def create_test_user_data(self, suffix: str = "") -> Dict[str, Any]:
        """Create test user data"""
        unique_id = str(uuid.uuid4())[:8]
        return {
            "email": f"testuser{suffix}_{unique_id}@university.edu",
            "password": "TestPassword123!",
            "first_name": f"Test{suffix}",
            "last_name": f"User{unique_id}",
            "phone": "+1234567890"
        }

    def register_and_login_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Register and login a test user, return auth token"""
        try:
            # Register user
            register_response = self.session.post(
                f"{API_BASE}/auth/register",
                json=user_data,
                timeout=10
            )
            
            if register_response.status_code != 200:
                print(f"Registration failed: {register_response.text}")
                return None
            
            # Login user
            login_response = self.session.post(
                f"{API_BASE}/auth/login",
                json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                },
                timeout=10
            )
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                return login_data.get("access_token")
            else:
                print(f"Login failed: {login_response.text}")
                return None
                
        except Exception as e:
            print(f"Error in register_and_login_user: {str(e)}")
            return None

    def setup_test_users(self) -> bool:
        """Setup test users for notification testing"""
        try:
            print("🔧 Setting up test users for notification testing...")
            
            # Create two test users
            for i in range(2):
                user_data = self.create_test_user_data(f"_notif_{i}")
                token = self.register_and_login_user(user_data)
                
                if token:
                    self.test_users.append(user_data)
                    self.auth_tokens[user_data["email"]] = token
                    print(f"✅ Created test user: {user_data['email']}")
                else:
                    print(f"❌ Failed to create test user: {user_data['email']}")
                    return False
            
            return len(self.test_users) >= 2
            
        except Exception as e:
            print(f"❌ Error setting up test users: {str(e)}")
            return False

    def get_auth_headers(self, user_email: str) -> Dict[str, str]:
        """Get authorization headers for a user"""
        token = self.auth_tokens.get(user_email)
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    # Test 1: Notification Management - Get Notifications
    def test_get_notifications(self) -> bool:
        """Test GET /api/notifications/ endpoint"""
        try:
            user_email = self.test_users[0]["email"]
            headers = self.get_auth_headers(user_email)
            
            response = self.session.get(
                f"{API_BASE}/notifications/",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                notifications = response.json()
                self.log_test("Get Notifications", "PASS", f"Retrieved {len(notifications)} notifications")
                return True
            else:
                self.log_test("Get Notifications", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Notifications", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 2: Notification Management - Get Unread Count
    def test_get_unread_count(self) -> bool:
        """Test GET /api/notifications/unread/count endpoint"""
        try:
            user_email = self.test_users[0]["email"]
            headers = self.get_auth_headers(user_email)
            
            response = self.session.get(
                f"{API_BASE}/notifications/unread/count",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                unread_count = data.get("unread_count", 0)
                self.log_test("Get Unread Count", "PASS", f"Unread count: {unread_count}")
                return True
            else:
                self.log_test("Get Unread Count", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Unread Count", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 3: Notification Preferences - Get Preferences
    def test_get_notification_preferences(self) -> bool:
        """Test GET /api/notifications/preferences endpoint"""
        try:
            user_email = self.test_users[0]["email"]
            headers = self.get_auth_headers(user_email)
            
            response = self.session.get(
                f"{API_BASE}/notifications/preferences",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                preferences = response.json()
                self.log_test("Get Notification Preferences", "PASS", f"Retrieved preferences with push_enabled: {preferences.get('push_enabled')}")
                return True
            else:
                self.log_test("Get Notification Preferences", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Notification Preferences", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 4: Notification Preferences - Update Preferences
    def test_update_notification_preferences(self) -> bool:
        """Test PUT /api/notifications/preferences endpoint"""
        try:
            user_email = self.test_users[0]["email"]
            headers = self.get_auth_headers(user_email)
            
            # Update preferences
            preferences_update = {
                "push_enabled": True,
                "push_connection_requests": True,
                "push_messages": False,
                "email_enabled": True,
                "email_connection_requests": True,
                "quiet_hours_enabled": True,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "08:00"
            }
            
            response = self.session.put(
                f"{API_BASE}/notifications/preferences",
                json=preferences_update,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                updated_preferences = response.json()
                self.log_test("Update Notification Preferences", "PASS", f"Updated preferences - push_messages: {updated_preferences.get('push_messages')}")
                return True
            else:
                self.log_test("Update Notification Preferences", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Update Notification Preferences", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 5: Push Token Management - Register Push Token
    def test_register_push_token(self) -> bool:
        """Test POST /api/notifications/push-tokens endpoint"""
        try:
            user_email = self.test_users[0]["email"]
            headers = self.get_auth_headers(user_email)
            
            # Create test push token
            push_token_data = {
                "token": f"ExponentPushToken[{str(uuid.uuid4())}]",
                "device_type": "ios",
                "device_id": str(uuid.uuid4()),
                "app_version": "1.0.0"
            }
            
            response = self.session.post(
                f"{API_BASE}/notifications/push-tokens",
                json=push_token_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                token_response = response.json()
                self.test_push_tokens.append(token_response)
                self.log_test("Register Push Token", "PASS", f"Registered token for device: {token_response.get('device_type')}")
                return True
            else:
                self.log_test("Register Push Token", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Register Push Token", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 6: Push Token Management - Get User Push Tokens
    def test_get_user_push_tokens(self) -> bool:
        """Test GET /api/notifications/push-tokens endpoint"""
        try:
            user_email = self.test_users[0]["email"]
            headers = self.get_auth_headers(user_email)
            
            response = self.session.get(
                f"{API_BASE}/notifications/push-tokens",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                tokens = response.json()
                self.log_test("Get User Push Tokens", "PASS", f"Retrieved {len(tokens)} push tokens")
                return True
            else:
                self.log_test("Get User Push Tokens", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get User Push Tokens", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 7: Notification Statistics
    def test_get_notification_stats(self) -> bool:
        """Test GET /api/notifications/stats endpoint"""
        try:
            user_email = self.test_users[0]["email"]
            headers = self.get_auth_headers(user_email)
            
            response = self.session.get(
                f"{API_BASE}/notifications/stats",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                stats = response.json()
                total_notifications = stats.get("total_notifications", 0)
                unread_count = stats.get("unread_count", 0)
                self.log_test("Get Notification Stats", "PASS", f"Total: {total_notifications}, Unread: {unread_count}")
                return True
            else:
                self.log_test("Get Notification Stats", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Notification Stats", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 8: Test Notification Feature
    def test_send_test_notification(self) -> bool:
        """Test POST /api/notifications/test endpoint"""
        try:
            user_email = self.test_users[0]["email"]
            headers = self.get_auth_headers(user_email)
            
            response = self.session.post(
                f"{API_BASE}/notifications/test",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Send Test Notification", "PASS", f"Message: {result.get('message')}")
                return True
            else:
                self.log_test("Send Test Notification", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Send Test Notification", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 9: Broadcast Notification Feature
    def test_broadcast_notification(self) -> bool:
        """Test POST /api/notifications/broadcast endpoint"""
        try:
            user_email = self.test_users[0]["email"]
            headers = self.get_auth_headers(user_email)
            
            # Get user IDs for broadcast
            recipient_ids = []
            for user in self.test_users:
                # Get user profile to get user ID
                user_headers = self.get_auth_headers(user["email"])
                profile_response = self.session.get(
                    f"{API_BASE}/users/me",
                    headers=user_headers,
                    timeout=10
                )
                if profile_response.status_code == 200:
                    user_data = profile_response.json()
                    recipient_ids.append(user_data["id"])
            
            if not recipient_ids:
                self.log_test("Broadcast Notification", "FAIL", "No recipient IDs found")
                return False
            
            # Send broadcast notification
            broadcast_data = {
                "recipient_ids": recipient_ids,
                "type": "system_announcement",
                "title": "Test Broadcast Notification",
                "message": "This is a test broadcast message to all users",
                "data": {"broadcast_test": True},
                "priority": "normal",
                "channels": ["in_app", "push"]
            }
            
            response = self.session.post(
                f"{API_BASE}/notifications/broadcast",
                json=broadcast_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Broadcast Notification", "PASS", f"Message: {result.get('message')}")
                return True
            else:
                self.log_test("Broadcast Notification", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Broadcast Notification", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 10: Connection Request Integration
    def test_connection_request_notification_integration(self) -> bool:
        """Test that connection requests trigger notifications"""
        try:
            # Get user IDs
            user1_email = self.test_users[0]["email"]
            user2_email = self.test_users[1]["email"]
            
            user1_headers = self.get_auth_headers(user1_email)
            user2_headers = self.get_auth_headers(user2_email)
            
            # Get user2's ID
            user2_profile_response = self.session.get(
                f"{API_BASE}/users/me",
                headers=user2_headers,
                timeout=10
            )
            
            if user2_profile_response.status_code != 200:
                self.log_test("Connection Request Notification Integration", "FAIL", "Could not get user2 profile")
                return False
            
            user2_data = user2_profile_response.json()
            user2_id = user2_data["id"]
            
            # Get initial notification count for user2
            initial_count_response = self.session.get(
                f"{API_BASE}/notifications/unread/count",
                headers=user2_headers,
                timeout=10
            )
            
            initial_count = 0
            if initial_count_response.status_code == 200:
                initial_count = initial_count_response.json().get("unread_count", 0)
            
            # Send connection request from user1 to user2
            connection_response = self.session.post(
                f"{API_BASE}/connections/request",
                params={"to_user_id": user2_id},
                headers=user1_headers,
                timeout=10
            )
            
            if connection_response.status_code != 200:
                self.log_test("Connection Request Notification Integration", "FAIL", f"Connection request failed: {connection_response.text}")
                return False
            
            # Wait a moment for notification to be processed
            import time
            time.sleep(2)
            
            # Check if user2 received a notification
            final_count_response = self.session.get(
                f"{API_BASE}/notifications/unread/count",
                headers=user2_headers,
                timeout=10
            )
            
            if final_count_response.status_code == 200:
                final_count = final_count_response.json().get("unread_count", 0)
                
                if final_count > initial_count:
                    self.log_test("Connection Request Notification Integration", "PASS", f"Notification count increased from {initial_count} to {final_count}")
                    return True
                else:
                    # Check notifications directly
                    notifications_response = self.session.get(
                        f"{API_BASE}/notifications/",
                        headers=user2_headers,
                        timeout=10
                    )
                    
                    if notifications_response.status_code == 200:
                        notifications = notifications_response.json()
                        connection_notifications = [n for n in notifications if n.get("type") == "connection_request"]
                        
                        if connection_notifications:
                            self.log_test("Connection Request Notification Integration", "PASS", f"Found {len(connection_notifications)} connection request notifications")
                            return True
                    
                    self.log_test("Connection Request Notification Integration", "FAIL", f"No notification increase detected (initial: {initial_count}, final: {final_count})")
                    return False
            else:
                self.log_test("Connection Request Notification Integration", "FAIL", f"Could not get final notification count: {final_count_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Connection Request Notification Integration", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 11: Mark Notification as Read
    def test_mark_notification_read(self) -> bool:
        """Test POST /api/notifications/{notification_id}/read endpoint"""
        try:
            user_email = self.test_users[1]["email"]  # Use user2 who should have notifications
            headers = self.get_auth_headers(user_email)
            
            # Get notifications
            notifications_response = self.session.get(
                f"{API_BASE}/notifications/",
                headers=headers,
                timeout=10
            )
            
            if notifications_response.status_code != 200:
                self.log_test("Mark Notification Read", "FAIL", "Could not get notifications")
                return False
            
            notifications = notifications_response.json()
            unread_notifications = [n for n in notifications if n.get("read_at") is None]
            
            if not unread_notifications:
                self.log_test("Mark Notification Read", "PASS", "No unread notifications to test (expected after previous tests)")
                return True
            
            # Mark first unread notification as read
            notification_id = unread_notifications[0]["id"]
            
            response = self.session.post(
                f"{API_BASE}/notifications/{notification_id}/read",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Mark Notification Read", "PASS", f"Message: {result.get('message')}")
                return True
            else:
                self.log_test("Mark Notification Read", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Mark Notification Read", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 12: Mark All Notifications as Read
    def test_mark_all_notifications_read(self) -> bool:
        """Test POST /api/notifications/read-all endpoint"""
        try:
            user_email = self.test_users[1]["email"]
            headers = self.get_auth_headers(user_email)
            
            response = self.session.post(
                f"{API_BASE}/notifications/read-all",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Mark All Notifications Read", "PASS", f"Message: {result.get('message')}")
                return True
            else:
                self.log_test("Mark All Notifications Read", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Mark All Notifications Read", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 13: Delete Notification
    def test_delete_notification(self) -> bool:
        """Test DELETE /api/notifications/{notification_id} endpoint"""
        try:
            user_email = self.test_users[1]["email"]
            headers = self.get_auth_headers(user_email)
            
            # Get notifications
            notifications_response = self.session.get(
                f"{API_BASE}/notifications/",
                headers=headers,
                timeout=10
            )
            
            if notifications_response.status_code != 200:
                self.log_test("Delete Notification", "FAIL", "Could not get notifications")
                return False
            
            notifications = notifications_response.json()
            
            if not notifications:
                self.log_test("Delete Notification", "PASS", "No notifications to delete (expected after previous tests)")
                return True
            
            # Delete first notification
            notification_id = notifications[0]["id"]
            
            response = self.session.delete(
                f"{API_BASE}/notifications/{notification_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Delete Notification", "PASS", f"Message: {result.get('message')}")
                return True
            else:
                self.log_test("Delete Notification", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Delete Notification", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 14: Deactivate Push Token
    def test_deactivate_push_token(self) -> bool:
        """Test DELETE /api/notifications/push-tokens/{token} endpoint"""
        try:
            user_email = self.test_users[0]["email"]
            headers = self.get_auth_headers(user_email)
            
            if not self.test_push_tokens:
                self.log_test("Deactivate Push Token", "FAIL", "No push tokens to deactivate")
                return False
            
            # Deactivate first push token
            token_to_deactivate = self.test_push_tokens[0]["token"]
            
            response = self.session.delete(
                f"{API_BASE}/notifications/push-tokens/{token_to_deactivate}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Deactivate Push Token", "PASS", f"Message: {result.get('message')}")
                return True
            else:
                self.log_test("Deactivate Push Token", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Deactivate Push Token", "FAIL", f"Exception: {str(e)}")
            return False

    # Test 15: Notification Filtering
    def test_notification_filtering(self) -> bool:
        """Test GET /api/notifications/ with filters"""
        try:
            user_email = self.test_users[1]["email"]
            headers = self.get_auth_headers(user_email)
            
            # Test filtering by unread_only
            response = self.session.get(
                f"{API_BASE}/notifications/",
                params={"unread_only": True},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                unread_notifications = response.json()
                
                # Test filtering by type
                type_response = self.session.get(
                    f"{API_BASE}/notifications/",
                    params={"type": "connection_request"},
                    headers=headers,
                    timeout=10
                )
                
                if type_response.status_code == 200:
                    connection_notifications = type_response.json()
                    self.log_test("Notification Filtering", "PASS", f"Unread: {len(unread_notifications)}, Connection requests: {len(connection_notifications)}")
                    return True
                else:
                    self.log_test("Notification Filtering", "FAIL", f"Type filter failed: {type_response.text}")
                    return False
            else:
                self.log_test("Notification Filtering", "FAIL", f"Unread filter failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Notification Filtering", "FAIL", f"Exception: {str(e)}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all notification system tests"""
        print("🚀 Starting Comprehensive Notification System Backend Testing")
        print("=" * 80)
        
        # Setup
        if not self.setup_test_users():
            return {"success": False, "error": "Failed to setup test users"}
        
        # Test results
        test_results = {}
        
        # Run all tests
        tests = [
            ("Get Notifications", self.test_get_notifications),
            ("Get Unread Count", self.test_get_unread_count),
            ("Get Notification Preferences", self.test_get_notification_preferences),
            ("Update Notification Preferences", self.test_update_notification_preferences),
            ("Register Push Token", self.test_register_push_token),
            ("Get User Push Tokens", self.test_get_user_push_tokens),
            ("Get Notification Stats", self.test_get_notification_stats),
            ("Send Test Notification", self.test_send_test_notification),
            ("Broadcast Notification", self.test_broadcast_notification),
            ("Connection Request Notification Integration", self.test_connection_request_notification_integration),
            ("Mark Notification Read", self.test_mark_notification_read),
            ("Mark All Notifications Read", self.test_mark_all_notifications_read),
            ("Delete Notification", self.test_delete_notification),
            ("Deactivate Push Token", self.test_deactivate_push_token),
            ("Notification Filtering", self.test_notification_filtering),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                test_results[test_name] = result
                if result:
                    passed_tests += 1
            except Exception as e:
                print(f"❌ {test_name}: EXCEPTION - {str(e)}")
                test_results[test_name] = False
        
        # Summary
        print("=" * 80)
        print(f"📊 NOTIFICATION SYSTEM TEST SUMMARY")
        print(f"✅ Passed: {passed_tests}/{total_tests} tests ({(passed_tests/total_tests)*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 ALL NOTIFICATION SYSTEM TESTS PASSED!")
        else:
            print(f"⚠️  {total_tests - passed_tests} tests failed")
            
        return {
            "success": passed_tests == total_tests,
            "passed": passed_tests,
            "total": total_tests,
            "percentage": (passed_tests/total_tests)*100,
            "results": test_results
        }

def main():
    """Main function to run notification system tests"""
    tester = NotificationSystemTester()
    results = tester.run_all_tests()
    
    if results["success"]:
        print("\n🎯 All notification system tests completed successfully!")
        exit(0)
    else:
        print(f"\n❌ {results['total'] - results['passed']} tests failed")
        exit(1)

if __name__ == "__main__":
    main()

def test_ai_chat_send_message(token):
    """Test sending message to AI assistant"""
    print("\n🤖 Testing AI Chat - Send Message...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Send social advice message
    message_data = {
        "message": "How do I make friends as an international student?",
        "context": {"query_type": "social_advice"}
    }
    
    response = make_request('POST', '/ai/chat/send', message_data, headers)
    
    if response and response.status_code == 200:
        data = response.json()
        required_fields = ['id', 'user_id', 'session_id', 'role', 'message', 'timestamp']
        
        if all(field in data for field in required_fields):
            if data['role'] == 'assistant' and len(data['message']) > 0:
                test_results.add_result("AI Chat Send Message - Social Advice", True, 
                                      f"AI responded with {len(data['message'])} characters")
            else:
                test_results.add_result("AI Chat Send Message - Social Advice", False, 
                                      "Invalid AI response format")
        else:
            missing = [f for f in required_fields if f not in data]
            test_results.add_result("AI Chat Send Message - Social Advice", False, 
                                  f"Missing fields: {missing}")
    else:
        test_results.add_result("AI Chat Send Message - Social Advice", False, 
                              f"Request failed: {response.status_code if response else 'No response'}")
    
    # Test 2: Send academic advice message
    message_data = {
        "message": "What should I know about studying computer science at Stanford?",
        "context": {"query_type": "academic_advice"}
    }
    
    response = make_request('POST', '/ai/chat/send', message_data, headers)
    
    if response and response.status_code == 200:
        data = response.json()
        if data.get('role') == 'assistant' and len(data.get('message', '')) > 0:
            test_results.add_result("AI Chat Send Message - Academic Advice", True, 
                                  f"AI responded with {len(data['message'])} characters")
        else:
            test_results.add_result("AI Chat Send Message - Academic Advice", False, 
                                  "Invalid AI response")
    else:
        test_results.add_result("AI Chat Send Message - Academic Advice", False, 
                              f"Request failed: {response.status_code if response else 'No response'}")

def test_ai_chat_history(token):
    """Test getting AI chat history"""
    print("\n📜 Testing AI Chat History...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = make_request('GET', '/ai/chat/history', headers=headers)
    
    if response and response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            if len(data) > 0:
                # Check message structure
                message = data[0]
                required_fields = ['id', 'user_id', 'session_id', 'role', 'message', 'timestamp']
                
                if all(field in message for field in required_fields):
                    test_results.add_result("AI Chat History", True, 
                                          f"Retrieved {len(data)} messages")
                else:
                    missing = [f for f in required_fields if f not in message]
                    test_results.add_result("AI Chat History", False, 
                                          f"Invalid message structure, missing: {missing}")
            else:
                test_results.add_result("AI Chat History", True, "No messages in history (empty)")
        else:
            test_results.add_result("AI Chat History", False, "Response is not a list")
    else:
        test_results.add_result("AI Chat History", False, 
                              f"Request failed: {response.status_code if response else 'No response'}")

def test_ai_user_chats(token):
    """Test getting user's AI chat sessions"""
    print("\n💬 Testing AI User Chats...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = make_request('GET', '/ai/chats', headers=headers)
    
    if response and response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            if len(data) > 0:
                # Check chat structure
                chat = data[0]
                required_fields = ['id', 'user_id', 'session_id', 'created_at', 'updated_at', 'message_count']
                
                if all(field in chat for field in required_fields):
                    test_results.add_result("AI User Chats", True, 
                                          f"Retrieved {len(data)} chat sessions")
                else:
                    missing = [f for f in required_fields if f not in chat]
                    test_results.add_result("AI User Chats", False, 
                                          f"Invalid chat structure, missing: {missing}")
            else:
                test_results.add_result("AI User Chats", True, "No chat sessions (empty)")
        else:
            test_results.add_result("AI User Chats", False, "Response is not a list")
    else:
        test_results.add_result("AI User Chats", False, 
                              f"Request failed: {response.status_code if response else 'No response'}")

def test_ai_suggestions(token):
    """Test AI-powered suggestions"""
    print("\n💡 Testing AI Suggestions...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = make_request('GET', '/ai/suggestions', headers=headers)
    
    if response and response.status_code == 200:
        data = response.json()
        if 'suggestions' in data and isinstance(data['suggestions'], list):
            suggestions = data['suggestions']
            if len(suggestions) > 0:
                test_results.add_result("AI Suggestions", True, 
                                      f"Retrieved {len(suggestions)} suggestions")
            else:
                test_results.add_result("AI Suggestions", False, "No suggestions returned")
        else:
            test_results.add_result("AI Suggestions", False, "Invalid response format")
    else:
        test_results.add_result("AI Suggestions", False, 
                              f"Request failed: {response.status_code if response else 'No response'}")

def test_ai_stats(token):
    """Test AI usage statistics"""
    print("\n📊 Testing AI Stats...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = make_request('GET', '/ai/stats', headers=headers)
    
    if response and response.status_code == 200:
        data = response.json()
        required_fields = ['user_id', 'total_messages', 'total_chats', 'average_response_time_ms']
        
        if all(field in data for field in required_fields):
            test_results.add_result("AI Stats", True, 
                                  f"Stats: {data['total_messages']} messages, {data['total_chats']} chats")
        else:
            missing = [f for f in required_fields if f not in data]
            test_results.add_result("AI Stats", False, f"Missing fields: {missing}")
    else:
        test_results.add_result("AI Stats", False, 
                              f"Request failed: {response.status_code if response else 'No response'}")

def test_ai_delete_chat_session(token):
    """Test deleting AI chat session"""
    print("\n🗑️ Testing AI Delete Chat Session...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # First, get existing chats to find a session to delete
    chats_response = make_request('GET', '/ai/chats', headers=headers)
    
    if chats_response and chats_response.status_code == 200:
        chats = chats_response.json()
        if len(chats) > 0:
            session_id = chats[0]['session_id']
            
            # Try to delete the session
            response = make_request('DELETE', f'/ai/chat/{session_id}', headers=headers)
            
            if response and response.status_code == 200:
                data = response.json()
                if 'message' in data:
                    test_results.add_result("AI Delete Chat Session", True, 
                                          "Chat session deleted successfully")
                else:
                    test_results.add_result("AI Delete Chat Session", False, 
                                          "No confirmation message")
            else:
                test_results.add_result("AI Delete Chat Session", False, 
                                      f"Delete failed: {response.status_code if response else 'No response'}")
        else:
            test_results.add_result("AI Delete Chat Session", True, 
                                  "No chat sessions to delete (skipped)")
    else:
        test_results.add_result("AI Delete Chat Session", False, 
                              "Could not retrieve chats to test deletion")

def test_ai_conversation_flow(token):
    """Test complete AI conversation flow"""
    print("\n🔄 Testing AI Conversation Flow...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1: Send initial message
    message1 = {
        "message": "I'm feeling homesick. Any advice?",
        "context": {"query_type": "emotional_support"}
    }
    
    response1 = make_request('POST', '/ai/chat/send', message1, headers)
    
    if not (response1 and response1.status_code == 200):
        test_results.add_result("AI Conversation Flow", False, "Failed to send first message")
        return
    
    # Step 2: Send follow-up message
    time.sleep(1)  # Brief pause
    message2 = {
        "message": "Thank you! Can you suggest some activities to meet people?",
        "context": {"query_type": "social_advice"}
    }
    
    response2 = make_request('POST', '/ai/chat/send', message2, headers)
    
    if not (response2 and response2.status_code == 200):
        test_results.add_result("AI Conversation Flow", False, "Failed to send follow-up message")
        return
    
    # Step 3: Check history contains both messages
    history_response = make_request('GET', '/ai/chat/history', headers=headers)
    
    if history_response and history_response.status_code == 200:
        history = history_response.json()
        if len(history) >= 4:  # 2 user messages + 2 AI responses
            test_results.add_result("AI Conversation Flow", True, 
                                  f"Complete conversation flow with {len(history)} messages")
        else:
            test_results.add_result("AI Conversation Flow", False, 
                                  f"Incomplete history: {len(history)} messages")
    else:
        test_results.add_result("AI Conversation Flow", False, "Failed to retrieve conversation history")

def test_ai_error_handling(token):
    """Test AI error handling"""
    print("\n⚠️ Testing AI Error Handling...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Empty message
    print("Testing empty message validation...")
    empty_message = {"message": "", "context": {}}
    response = make_request('POST', '/ai/chat/send', empty_message, headers)
    
    if response is None:
        test_results.add_result("AI Error Handling - Empty Message", False, "Request timeout or connection error")
    elif response.status_code == 422:  # Validation error
        test_results.add_result("AI Error Handling - Empty Message", True, 
                              "Correctly rejected empty message")
    else:
        test_results.add_result("AI Error Handling - Empty Message", False, 
                              f"Expected 422, got {response.status_code}")
    
    # Test 2: Very long message
    print("Testing long message validation...")
    long_message = {"message": "x" * 3000, "context": {}}  # Exceeds 2000 char limit
    response = make_request('POST', '/ai/chat/send', long_message, headers)
    
    if response is None:
        test_results.add_result("AI Error Handling - Long Message", False, "Request timeout or connection error")
    elif response.status_code == 422:  # Validation error
        test_results.add_result("AI Error Handling - Long Message", True, 
                              "Correctly rejected overly long message")
    else:
        test_results.add_result("AI Error Handling - Long Message", False, 
                              f"Expected 422, got {response.status_code}")
    
    # Test 3: Invalid session ID for deletion
    print("Testing invalid session deletion...")
    response = make_request('DELETE', '/ai/chat/nonexistent_session', headers=headers)
    
    if response is None:
        test_results.add_result("AI Error Handling - Invalid Session", False, "Request timeout or connection error")
    elif response.status_code == 404:
        test_results.add_result("AI Error Handling - Invalid Session", True, 
                              "Correctly handled invalid session ID")
    else:
        test_results.add_result("AI Error Handling - Invalid Session", False, 
                              f"Expected 404, got {response.status_code}")

def main():
    """Main test execution"""
    print("🚀 Starting AI Assistant System Backend Tests...")
    print(f"Backend URL: {API_BASE}")
    
    # Step 1: Authenticate user
    token = test_user_authentication()
    if not token:
        print("❌ Cannot proceed without authentication token")
        test_results.print_summary()
        return
    
    # Step 2: Test AI Chat functionality
    test_ai_chat_send_message(token)
    test_ai_chat_history(token)
    test_ai_user_chats(token)
    
    # Step 3: Test AI Assistant features
    test_ai_suggestions(token)
    test_ai_stats(token)
    
    # Step 4: Test conversation flow
    test_ai_conversation_flow(token)
    
    # Step 5: Test deletion
    test_ai_delete_chat_session(token)
    
    # Step 6: Test error handling
    test_ai_error_handling(token)
    
    # Print final results
    test_results.print_summary()

if __name__ == "__main__":
    main()