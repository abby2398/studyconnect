#!/usr/bin/env python3
"""
Backend API Testing for International Student Networking App
Focus: AI Assistant System Testing
"""

import requests
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

print(f"Testing backend at: {API_BASE}")

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def add_result(self, test_name, passed, message="", details=None):
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status}: {test_name}"
        if message:
            result += f" - {message}"
        
        print(result)
        self.results.append({
            'test': test_name,
            'passed': passed,
            'message': message,
            'details': details
        })
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"AI ASSISTANT SYSTEM TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/total*100):.1f}%" if total > 0 else "0%")
        
        if self.failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['message']}")

# Global test results
test_results = TestResults()

def make_request(method, endpoint, data=None, headers=None, params=None):
    """Make HTTP request with error handling"""
    try:
        url = f"{API_BASE}{endpoint}"
        
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=60)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers, params=params, timeout=60)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=headers, params=params, timeout=60)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, params=params, timeout=60)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.exceptions.Timeout:
        print(f"Request timed out for {method} {endpoint}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {str(e)}")
        return None

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
    empty_message = {"message": "", "context": {}}
    response = make_request('POST', '/ai/chat/send', empty_message, headers)
    
    if response and response.status_code == 422:  # Validation error
        test_results.add_result("AI Error Handling - Empty Message", True, 
                              "Correctly rejected empty message")
    else:
        test_results.add_result("AI Error Handling - Empty Message", False, 
                              f"Should reject empty message: {response.status_code if response else 'No response'}")
    
    # Test 2: Very long message
    long_message = {"message": "x" * 3000, "context": {}}  # Exceeds 2000 char limit
    response = make_request('POST', '/ai/chat/send', long_message, headers)
    
    if response and response.status_code == 422:  # Validation error
        test_results.add_result("AI Error Handling - Long Message", True, 
                              "Correctly rejected overly long message")
    else:
        test_results.add_result("AI Error Handling - Long Message", False, 
                              f"Should reject long message: {response.status_code if response else 'No response'}")
    
    # Test 3: Invalid session ID for deletion
    response = make_request('DELETE', '/ai/chat/nonexistent_session', headers=headers)
    
    if response and response.status_code == 404:
        test_results.add_result("AI Error Handling - Invalid Session", True, 
                              "Correctly handled invalid session ID")
    else:
        test_results.add_result("AI Error Handling - Invalid Session", False, 
                              f"Should return 404 for invalid session: {response.status_code if response else 'No response'}")

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