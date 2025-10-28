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

def test_user_authentication():
    """Test user authentication to get access token"""
    print("\n🔐 Testing User Authentication...")
    
    # Try to register a new user for testing
    register_data = {
        "email": "ai.test.new@stanford.edu",
        "password": "testpass123",
        "first_name": "AI",
        "last_name": "TestUser",
        "phone": "+1234567890"
    }
    
    reg_response = make_request('POST', '/auth/register', register_data)
    # Registration might fail if user already exists (400), which is fine
    
    # Try login
    login_data = {
        "email": "ai.test.new@stanford.edu",
        "password": "testpass123"
    }
    
    response = make_request('POST', '/auth/login', login_data)
    
    if response and response.status_code == 200:
        data = response.json()
        if 'access_token' in data:
            test_results.add_result("User Authentication", True, "Login successful")
            return data['access_token']
        else:
            test_results.add_result("User Authentication", False, "No access token in response")
            return None
    else:
        test_results.add_result("User Authentication", False, f"Login failed: {response.status_code if response else 'No response'}")
        return None

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