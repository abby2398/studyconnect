#!/usr/bin/env python3
"""
Backend Testing Suite for Push Notification Integration
Tests the integration of push notifications with messaging and connection request flows
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://password-reset-39.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class BackendTester:
    def __init__(self):
        self.session = None
        self.test_users = []
        self.test_tokens = {}
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    async def create_test_user(self, email: str, first_name: str, last_name: str) -> Dict[str, Any]:
        """Create a test user and return user data with token"""
        try:
            # Add timestamp to make email unique
            import time
            timestamp = str(int(time.time()))
            unique_email = email.replace('@', f'+{timestamp}@')
            
            # Register user
            register_data = {
                "email": unique_email,
                "password": "TestPass123!",
                "first_name": first_name,
                "last_name": last_name
            }
            
            async with self.session.post(f"{API_BASE}/auth/register", json=register_data) as resp:
                if resp.status == 400:
                    # User might already exist, try to login
                    login_data = {"email": unique_email, "password": "TestPass123!"}
                    async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as login_resp:
                        if login_resp.status == 200:
                            login_result = await login_resp.json()
                            return {
                                "user": login_result["user"],
                                "token": login_result["access_token"]
                            }
                        else:
                            raise Exception(f"Failed to login existing user: {await login_resp.text()}")
                elif resp.status != 200:
                    raise Exception(f"Failed to register user: {await resp.text()}")
            
            # Login to get token
            login_data = {"email": unique_email, "password": "TestPass123!"}
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to login: {await resp.text()}")
                
                result = await resp.json()
                return {
                    "user": result["user"],
                    "token": result["access_token"]
                }
                
        except Exception as e:
            print(f"Error creating test user {email}: {str(e)}")
            raise
    
    async def make_authenticated_request(self, method: str, endpoint: str, token: str, **kwargs) -> aiohttp.ClientResponse:
        """Make authenticated API request"""
        headers = {"Authorization": f"Bearer {token}"}
        if "headers" in kwargs:
            kwargs["headers"].update(headers)
        else:
            kwargs["headers"] = headers
            
        return await self.session.request(method, f"{API_BASE}{endpoint}", **kwargs)
    
    async def test_push_token_registration(self) -> Dict[str, Any]:
        """Test push token registration functionality"""
        print("🔧 Testing Push Token Registration...")
        
        try:
            # Use first test user
            user_data = self.test_users[0]
            token = user_data["token"]
            
            # Test 1: Register push token
            push_token_data = {
                "token": "ExponentPushToken[test-token-123]",
                "device_type": "ios",
                "device_id": "test-device-123",
                "app_version": "1.0.0"
            }
            
            async with await self.make_authenticated_request("POST", "/notifications/push-tokens", token, json=push_token_data) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to register push token: {await resp.text()}"}
                
                result = await resp.json()
                push_token_id = result["id"]
            
            # Test 2: Get user's push tokens
            async with await self.make_authenticated_request("GET", "/notifications/push-tokens", token) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get push tokens: {await resp.text()}"}
                
                tokens = await resp.json()
                if not any(t["token"] == push_token_data["token"] for t in tokens):
                    return {"success": False, "error": "Push token not found in user's tokens"}
            
            # Test 3: Deactivate push token
            async with await self.make_authenticated_request("DELETE", f"/notifications/push-tokens/{push_token_data['token']}", token) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to deactivate push token: {await resp.text()}"}
            
            return {
                "success": True,
                "message": "✅ Push token registration, retrieval, and deactivation working correctly"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Push token registration test failed: {str(e)}"}
    
    async def test_connection_request_notifications(self) -> Dict[str, Any]:
        """Test connection request notification integration"""
        print("🔗 Testing Connection Request Notifications...")
        
        try:
            user1 = self.test_users[0]
            user2 = self.test_users[1]
            
            # Register push tokens for both users
            for i, user in enumerate([user1, user2]):
                push_token_data = {
                    "token": f"ExponentPushToken[connection-test-{i}]",
                    "device_type": "ios",
                    "device_id": f"connection-device-{i}",
                    "app_version": "1.0.0"
                }
                
                async with await self.make_authenticated_request("POST", "/notifications/push-tokens", user["token"], json=push_token_data) as resp:
                    if resp.status != 200:
                        return {"success": False, "error": f"Failed to register push token for user {i}: {await resp.text()}"}
            
            # Get initial notification count for user2
            async with await self.make_authenticated_request("GET", "/notifications/unread/count", user2["token"]) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get initial notification count: {await resp.text()}"}
                initial_count = (await resp.json())["unread_count"]
            
            # Test 1: Send connection request (should trigger notification)
            async with await self.make_authenticated_request("POST", "/connections/request", user1["token"], params={"to_user_id": user2["user"]["id"]}) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to send connection request: {await resp.text()}"}
            
            # Wait a moment for notification processing
            await asyncio.sleep(1)
            
            # Check if notification was created
            async with await self.make_authenticated_request("GET", "/notifications/unread/count", user2["token"]) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get notification count after connection request: {await resp.text()}"}
                new_count = (await resp.json())["unread_count"]
            
            if new_count <= initial_count:
                return {"success": False, "error": "No notification created for connection request"}
            
            # Get the notification details
            async with await self.make_authenticated_request("GET", "/notifications/", user2["token"], params={"limit": 1}) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get notifications: {await resp.text()}"}
                notifications = await resp.json()
                
                if not notifications:
                    return {"success": False, "error": "No notifications found"}
                
                latest_notification = notifications[0]
                if latest_notification["type"] != "connection_request":
                    return {"success": False, "error": f"Expected connection_request notification, got {latest_notification['type']}"}
                
                if latest_notification["sender_id"] != user1["user"]["id"]:
                    return {"success": False, "error": "Notification sender_id doesn't match connection request sender"}
            
            # Test 2: Accept connection request (should trigger notification to original sender)
            # Get connection requests for user2
            async with await self.make_authenticated_request("GET", "/connections/requests", user2["token"]) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get connection requests: {await resp.text()}"}
                requests_data = await resp.json()
                
                if not requests_data["incoming"]:
                    return {"success": False, "error": "No incoming connection requests found"}
                
                request_id = requests_data["incoming"][0]["id"]
            
            # Get initial notification count for user1 (original sender)
            async with await self.make_authenticated_request("GET", "/notifications/unread/count", user1["token"]) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get initial notification count for user1: {await resp.text()}"}
                user1_initial_count = (await resp.json())["unread_count"]
            
            # Accept the connection request
            async with await self.make_authenticated_request("POST", "/connections/respond", user2["token"], params={"request_id": request_id, "action": "accept"}) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to accept connection request: {await resp.text()}"}
            
            # Wait for notification processing
            await asyncio.sleep(1)
            
            # Check if notification was sent to user1
            async with await self.make_authenticated_request("GET", "/notifications/unread/count", user1["token"]) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get notification count for user1 after acceptance: {await resp.text()}"}
                user1_new_count = (await resp.json())["unread_count"]
            
            if user1_new_count <= user1_initial_count:
                return {"success": False, "error": "No notification created for connection acceptance"}
            
            # Verify the acceptance notification
            async with await self.make_authenticated_request("GET", "/notifications/", user1["token"], params={"limit": 1}) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get notifications for user1: {await resp.text()}"}
                user1_notifications = await resp.json()
                
                if not user1_notifications:
                    return {"success": False, "error": "No notifications found for user1"}
                
                latest_notification = user1_notifications[0]
                if latest_notification["type"] != "connection_accepted":
                    return {"success": False, "error": f"Expected connection_accepted notification, got {latest_notification['type']}"}
            
            return {
                "success": True,
                "message": "✅ Connection request and acceptance notifications working correctly"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Connection request notification test failed: {str(e)}"}
    
    async def test_message_notifications(self) -> Dict[str, Any]:
        """Test message notification integration"""
        print("💬 Testing Message Notifications...")
        
        try:
            user1 = self.test_users[0]
            user2 = self.test_users[1]
            
            # Register push tokens for both users
            for i, user in enumerate([user1, user2]):
                push_token_data = {
                    "token": f"ExponentPushToken[message-test-{i}]",
                    "device_type": "android",
                    "device_id": f"message-device-{i}",
                    "app_version": "1.0.0"
                }
                
                async with await self.make_authenticated_request("POST", "/notifications/push-tokens", user["token"], json=push_token_data) as resp:
                    if resp.status != 200:
                        return {"success": False, "error": f"Failed to register push token for user {i}: {await resp.text()}"}
            
            # Create a conversation between users
            conversation_data = {
                "participants": [user1["user"]["id"], user2["user"]["id"]],
                "is_group_chat": False
            }
            
            async with await self.make_authenticated_request("POST", "/chat/conversations", user1["token"], json=conversation_data) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to create conversation: {await resp.text()}"}
                conversation = await resp.json()
                conversation_id = conversation["id"]
            
            # Get initial notification count for user2
            async with await self.make_authenticated_request("GET", "/notifications/unread/count", user2["token"]) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get initial notification count: {await resp.text()}"}
                initial_count = (await resp.json())["unread_count"]
            
            # Test 1: Send text message (should trigger notification)
            message_data = {
                "conversation_id": conversation_id,
                "message_type": "text",
                "content": "Hello! This is a test message for notification testing."
            }
            
            async with await self.make_authenticated_request("POST", "/chat/messages", user1["token"], json=message_data) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to send message: {await resp.text()}"}
                message_result = await resp.json()
            
            # Wait for notification processing
            await asyncio.sleep(1)
            
            # Check if notification was created
            async with await self.make_authenticated_request("GET", "/notifications/unread/count", user2["token"]) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get notification count after message: {await resp.text()}"}
                new_count = (await resp.json())["unread_count"]
            
            if new_count <= initial_count:
                return {"success": False, "error": "No notification created for message"}
            
            # Verify the message notification
            async with await self.make_authenticated_request("GET", "/notifications/", user2["token"], params={"limit": 1}) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get notifications: {await resp.text()}"}
                notifications = await resp.json()
                
                if not notifications:
                    return {"success": False, "error": "No notifications found"}
                
                latest_notification = notifications[0]
                if latest_notification["type"] != "message_received":
                    return {"success": False, "error": f"Expected message_received notification, got {latest_notification['type']}"}
                
                if latest_notification["sender_id"] != user1["user"]["id"]:
                    return {"success": False, "error": "Notification sender_id doesn't match message sender"}
                
                # Check if message preview is included
                if "message_preview" not in latest_notification.get("data", {}):
                    return {"success": False, "error": "Message preview not included in notification data"}
            
            # Test 2: Send media message (should also trigger notification)
            media_message_data = {
                "conversation_id": conversation_id,
                "message_type": "image",
                "content": "Shared an image",
                "file_attachment": {
                    "filename": "test_image.jpg",
                    "file_size": 1024,
                    "file_type": "image/jpeg",
                    "file_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA=="
                }
            }
            
            async with await self.make_authenticated_request("POST", "/chat/messages", user1["token"], json=media_message_data) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to send media message: {await resp.text()}"}
            
            # Wait for notification processing
            await asyncio.sleep(1)
            
            # Check if another notification was created
            async with await self.make_authenticated_request("GET", "/notifications/unread/count", user2["token"]) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get notification count after media message: {await resp.text()}"}
                final_count = (await resp.json())["unread_count"]
            
            if final_count <= new_count:
                return {"success": False, "error": "No notification created for media message"}
            
            return {
                "success": True,
                "message": "✅ Message notifications working correctly for both text and media messages"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Message notification test failed: {str(e)}"}
    
    async def test_notification_service_integration(self) -> Dict[str, Any]:
        """Test notification service integration and templates"""
        print("🔔 Testing Notification Service Integration...")
        
        try:
            user = self.test_users[0]
            
            # Test 1: Send test notification
            async with await self.make_authenticated_request("POST", "/notifications/test", user["token"]) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to send test notification: {await resp.text()}"}
            
            # Wait for processing
            await asyncio.sleep(1)
            
            # Check if test notification was created
            async with await self.make_authenticated_request("GET", "/notifications/", user["token"], params={"limit": 1}) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get notifications: {await resp.text()}"}
                notifications = await resp.json()
                
                if not notifications:
                    return {"success": False, "error": "Test notification not found"}
                
                test_notification = notifications[0]
                if test_notification["type"] != "system_announcement":
                    return {"success": False, "error": f"Expected system_announcement notification, got {test_notification['type']}"}
            
            # Test 2: Get notification preferences
            async with await self.make_authenticated_request("GET", "/notifications/preferences", user["token"]) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get notification preferences: {await resp.text()}"}
                preferences = await resp.json()
                
                # Verify default preferences structure
                required_fields = ["push_enabled", "push_messages", "push_connection_requests", "email_enabled"]
                for field in required_fields:
                    if field not in preferences:
                        return {"success": False, "error": f"Missing preference field: {field}"}
            
            # Test 3: Update notification preferences
            preference_updates = {
                "push_messages": False,
                "email_connection_requests": False
            }
            
            async with await self.make_authenticated_request("PUT", "/notifications/preferences", user["token"], json=preference_updates) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to update notification preferences: {await resp.text()}"}
                updated_preferences = await resp.json()
                
                if updated_preferences["push_messages"] != False:
                    return {"success": False, "error": "Preference update not applied correctly"}
            
            # Test 4: Get notification statistics
            async with await self.make_authenticated_request("GET", "/notifications/stats", user["token"]) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get notification stats: {await resp.text()}"}
                stats = await resp.json()
                
                required_stats = ["total_notifications", "unread_count", "notifications_by_type"]
                for stat in required_stats:
                    if stat not in stats:
                        return {"success": False, "error": f"Missing stat field: {stat}"}
            
            return {
                "success": True,
                "message": "✅ Notification service integration working correctly - test notifications, preferences, and statistics"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Notification service integration test failed: {str(e)}"}
    
    async def test_notification_error_handling(self) -> Dict[str, Any]:
        """Test notification error handling and core functionality preservation"""
        print("⚠️ Testing Notification Error Handling...")
        
        try:
            # Create fresh users for this test to avoid conflicts with previous tests
            user3_data = await self.create_test_user("charlie.brown@university.edu", "Charlie", "Brown")
            user4_data = await self.create_test_user("diana.prince@college.edu", "Diana", "Prince")
            
            # Test 1: Ensure connection requests work even if notifications fail
            # Send connection request
            async with await self.make_authenticated_request("POST", "/connections/request", user3_data["token"], params={"to_user_id": user4_data["user"]["id"]}) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Connection request failed: {await resp.text()}"}
            
            # Verify connection request was created
            async with await self.make_authenticated_request("GET", "/connections/requests", user4_data["token"]) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get connection requests: {await resp.text()}"}
                requests_data = await resp.json()
                
                # Should have the incoming request from user3
                has_request_from_user3 = any(
                    req["from_user_id"] == user3_data["user"]["id"] 
                    for req in requests_data.get("incoming", [])
                )
                
                if not has_request_from_user3:
                    return {"success": False, "error": "Connection request not created properly"}
            
            # Test 2: Ensure messages work even if notifications fail
            # Create conversation
            conversation_data = {
                "participants": [user3_data["user"]["id"], user4_data["user"]["id"]],
                "is_group_chat": False
            }
            
            async with await self.make_authenticated_request("POST", "/chat/conversations", user3_data["token"], json=conversation_data) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to create conversation: {await resp.text()}"}
                conversation = await resp.json()
                conversation_id = conversation["id"]
            
            # Send message
            message_data = {
                "conversation_id": conversation_id,
                "message_type": "text",
                "content": "Test message for error handling verification"
            }
            
            async with await self.make_authenticated_request("POST", "/chat/messages", user3_data["token"], json=message_data) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to send message: {await resp.text()}"}
            
            # Verify message was created regardless of notification status
            async with await self.make_authenticated_request("GET", f"/chat/messages/{conversation_id}", user4_data["token"]) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to get messages: {await resp.text()}"}
                messages = await resp.json()
                
                if not messages:
                    return {"success": False, "error": "Message not created"}
                
                # Find our test message
                test_message_found = any(msg["content"] == "Test message for error handling verification" for msg in messages)
                if not test_message_found:
                    return {"success": False, "error": "Test message not found in conversation"}
            
            return {
                "success": True,
                "message": "✅ Core functionality (connections, messages) works correctly regardless of notification status"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error handling test failed: {str(e)}"}
    
    async def run_all_tests(self):
        """Run all push notification integration tests"""
        print("🚀 Starting Push Notification Integration Tests...")
        print("=" * 60)
        
        try:
            await self.setup_session()
            
            # Create test users
            print("👥 Creating test users...")
            user1_data = await self.create_test_user("alice.johnson@university.edu", "Alice", "Johnson")
            user2_data = await self.create_test_user("bob.smith@college.edu", "Bob", "Smith")
            
            self.test_users = [user1_data, user2_data]
            print(f"✅ Created test users: {user1_data['user']['first_name']} and {user2_data['user']['first_name']}")
            
            # Run tests
            tests = [
                ("Push Token Registration", self.test_push_token_registration),
                ("Connection Request Notifications", self.test_connection_request_notifications),
                ("Message Notifications", self.test_message_notifications),
                ("Notification Service Integration", self.test_notification_service_integration),
                ("Notification Error Handling", self.test_notification_error_handling)
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            for test_name, test_func in tests:
                print(f"\n📋 Running: {test_name}")
                try:
                    result = await test_func()
                    if result["success"]:
                        print(f"✅ {result['message']}")
                        passed_tests += 1
                        self.test_results.append({"test": test_name, "status": "PASSED", "message": result["message"]})
                    else:
                        print(f"❌ {result['error']}")
                        self.test_results.append({"test": test_name, "status": "FAILED", "error": result["error"]})
                except Exception as e:
                    print(f"❌ Test failed with exception: {str(e)}")
                    self.test_results.append({"test": test_name, "status": "ERROR", "error": str(e)})
            
            # Print summary
            print("\n" + "=" * 60)
            print("📊 PUSH NOTIFICATION INTEGRATION TEST SUMMARY")
            print("=" * 60)
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {total_tests - passed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            if passed_tests == total_tests:
                print("\n🎉 ALL PUSH NOTIFICATION INTEGRATION TESTS PASSED!")
                print("✅ Push notifications are properly integrated with:")
                print("   • Connection request flows")
                print("   • Message sending flows") 
                print("   • Connection acceptance flows")
                print("   • Push token management")
                print("   • Notification service functionality")
                print("   • Error handling (core functionality preserved)")
            else:
                print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. See details above.")
            
            return passed_tests == total_tests
            
        except Exception as e:
            print(f"❌ Test suite failed: {str(e)}")
            return False
        finally:
            await self.cleanup_session()

async def main():
    """Main test runner"""
    tester = BackendTester()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)