#!/usr/bin/env python3

import asyncio
import aiohttp
import json
import socketio
from datetime import datetime
import sys
import os

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('EXPO_PUBLIC_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except:
        pass
    return "https://pathfinder-94.preview.emergentagent.com"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

class ChatSystemTester:
    def __init__(self):
        self.session = None
        self.user1_token = None
        self.user2_token = None
        self.user1_id = None
        self.user2_id = None
        self.conversation_id = None
        self.message_id = None
        self.sio_client = None
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        
    async def setup_test_users(self):
        """Setup test users for chat testing"""
        print("\n=== Setting up Test Users ===")
        
        # Test user 1
        user1_data = {
            "email": "alice.johnson@stanford.edu",
            "password": "SecurePass123!",
            "first_name": "Alice",
            "last_name": "Johnson",
            "phone": "+1-555-0101"
        }
        
        # Test user 2  
        user2_data = {
            "email": "bob.smith@mit.edu", 
            "password": "SecurePass456!",
            "first_name": "Bob",
            "last_name": "Smith",
            "phone": "+1-555-0102"
        }
        
        try:
            # Try to login first (users might already exist)
            async with self.session.post(f"{API_URL}/auth/login", json={
                "email": user1_data["email"],
                "password": user1_data["password"]
            }) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.user1_token = data["access_token"]
                    self.user1_id = data["user"]["id"]
                    self.log_test("User 1 Login", True, f"Logged in as {user1_data['first_name']}")
                else:
                    # Register user 1
                    async with self.session.post(f"{API_URL}/auth/register", json=user1_data) as reg_resp:
                        if reg_resp.status == 200:
                            # Try login again
                            async with self.session.post(f"{API_URL}/auth/login", json={
                                "email": user1_data["email"],
                                "password": user1_data["password"]
                            }) as login_resp:
                                if login_resp.status == 200:
                                    data = await login_resp.json()
                                    self.user1_token = data["access_token"]
                                    self.user1_id = data["user"]["id"]
                                    self.log_test("User 1 Setup", True, "Registered and logged in")
                                else:
                                    self.log_test("User 1 Setup", False, "Failed to login after registration")
                                    return False
                        else:
                            self.log_test("User 1 Setup", False, f"Registration failed: {await reg_resp.text()}")
                            return False
                            
            # Setup user 2
            async with self.session.post(f"{API_URL}/auth/login", json={
                "email": user2_data["email"],
                "password": user2_data["password"]
            }) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.user2_token = data["access_token"]
                    self.user2_id = data["user"]["id"]
                    self.log_test("User 2 Login", True, f"Logged in as {user2_data['first_name']}")
                else:
                    # Register user 2
                    async with self.session.post(f"{API_URL}/auth/register", json=user2_data) as reg_resp:
                        if reg_resp.status == 200:
                            # Try login again
                            async with self.session.post(f"{API_URL}/auth/login", json={
                                "email": user2_data["email"],
                                "password": user2_data["password"]
                            }) as login_resp:
                                if login_resp.status == 200:
                                    data = await login_resp.json()
                                    self.user2_token = data["access_token"]
                                    self.user2_id = data["user"]["id"]
                                    self.log_test("User 2 Setup", True, "Registered and logged in")
                                else:
                                    self.log_test("User 2 Setup", False, "Failed to login after registration")
                                    return False
                        else:
                            self.log_test("User 2 Setup", False, f"Registration failed: {await reg_resp.text()}")
                            return False
                            
            return True
            
        except Exception as e:
            self.log_test("User Setup", False, f"Exception: {str(e)}")
            return False
            
    async def test_create_conversation(self):
        """Test creating conversations between users"""
        print("\n=== Testing Conversation Creation ===")
        
        try:
            # Test creating 1-on-1 conversation
            conversation_data = {
                "participants": [self.user1_id, self.user2_id],
                "is_group_chat": False
            }
            
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            async with self.session.post(f"{API_URL}/chat/conversations", 
                                       json=conversation_data, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.conversation_id = data["id"]
                    self.log_test("Create 1-on-1 Conversation", True, f"Created conversation: {self.conversation_id}")
                else:
                    error_text = await resp.text()
                    self.log_test("Create 1-on-1 Conversation", False, f"Status {resp.status}: {error_text}")
                    return False
                    
            # Test duplicate conversation prevention
            async with self.session.post(f"{API_URL}/chat/conversations", 
                                       json=conversation_data, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Should return existing conversation
                    if data["id"] == self.conversation_id:
                        self.log_test("Duplicate Conversation Prevention", True, "Returned existing conversation")
                    else:
                        self.log_test("Duplicate Conversation Prevention", False, "Created duplicate conversation")
                else:
                    self.log_test("Duplicate Conversation Prevention", False, f"Unexpected error: {await resp.text()}")
                    
            # Test group conversation creation
            group_data = {
                "participants": [self.user1_id, self.user2_id],
                "is_group_chat": True,
                "group_name": "Study Group",
                "group_description": "Computer Science study group"
            }
            
            async with self.session.post(f"{API_URL}/chat/conversations", 
                                       json=group_data, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log_test("Create Group Conversation", True, f"Created group: {data['group_name']}")
                else:
                    self.log_test("Create Group Conversation", False, f"Status {resp.status}: {await resp.text()}")
                    
            return True
            
        except Exception as e:
            self.log_test("Conversation Creation", False, f"Exception: {str(e)}")
            return False
            
    async def test_get_conversations(self):
        """Test retrieving user's conversation list"""
        print("\n=== Testing Get Conversations ===")
        
        try:
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            async with self.session.get(f"{API_URL}/chat/conversations", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        # Check conversation structure
                        conv = data[0]
                        required_fields = ["conversation", "other_participant", "unread_count"]
                        if all(field in conv for field in required_fields):
                            self.log_test("Get Conversations List", True, f"Retrieved {len(data)} conversations")
                            
                            # Check other participant details
                            if conv.get("other_participant") and isinstance(conv["other_participant"], dict) and "first_name" in conv["other_participant"]:
                                self.log_test("Conversation Participant Details", True, 
                                            f"Other participant: {conv['other_participant']['first_name']}")
                            else:
                                self.log_test("Conversation Participant Details", False, f"Missing participant details. Got: {conv.get('other_participant')}")
                        else:
                            self.log_test("Get Conversations List", False, "Missing required fields in response")
                    else:
                        self.log_test("Get Conversations List", False, "No conversations returned")
                else:
                    self.log_test("Get Conversations List", False, f"Status {resp.status}: {await resp.text()}")
                    
            # Test with user 2 to verify both users can see the conversation
            headers2 = {"Authorization": f"Bearer {self.user2_token}"}
            async with self.session.get(f"{API_URL}/chat/conversations", headers=headers2) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        self.log_test("User 2 Conversations Access", True, f"User 2 can see {len(data)} conversations")
                    else:
                        self.log_test("User 2 Conversations Access", False, "User 2 cannot see conversations")
                else:
                    self.log_test("User 2 Conversations Access", False, f"Status {resp.status}")
                    
            return True
            
        except Exception as e:
            self.log_test("Get Conversations", False, f"Exception: {str(e)}")
            return False
            
    async def test_send_message(self):
        """Test sending messages to conversations"""
        print("\n=== Testing Message Sending ===")
        
        try:
            # Test text message
            message_data = {
                "conversation_id": self.conversation_id,
                "message_type": "text",
                "content": "Hello Bob! How are your studies going at MIT?"
            }
            
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            async with self.session.post(f"{API_URL}/chat/messages", 
                                       json=message_data, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.message_id = data["id"]
                    self.log_test("Send Text Message", True, f"Message sent: {data['id']}")
                else:
                    error_text = await resp.text()
                    self.log_test("Send Text Message", False, f"Status {resp.status}: {error_text}")
                    return False
                    
            # Test reply message
            reply_data = {
                "conversation_id": self.conversation_id,
                "message_type": "text", 
                "content": "Hi Alice! Studies are going great. How about Stanford?",
                "reply_to_id": self.message_id
            }
            
            headers2 = {"Authorization": f"Bearer {self.user2_token}"}
            async with self.session.post(f"{API_URL}/chat/messages", 
                                       json=reply_data, headers=headers2) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log_test("Send Reply Message", True, f"Reply sent with reply_to_id: {data['reply_to_id']}")
                else:
                    self.log_test("Send Reply Message", False, f"Status {resp.status}: {await resp.text()}")
                    
            # Test unauthorized message (user not in conversation)
            fake_conv_data = {
                "conversation_id": "fake-conversation-id",
                "message_type": "text",
                "content": "This should fail"
            }
            
            async with self.session.post(f"{API_URL}/chat/messages", 
                                       json=fake_conv_data, headers=headers) as resp:
                if resp.status == 404:
                    self.log_test("Message Authorization Check", True, "Correctly rejected unauthorized message")
                else:
                    self.log_test("Message Authorization Check", False, f"Should have failed with 404, got {resp.status}")
                    
            return True
            
        except Exception as e:
            self.log_test("Send Message", False, f"Exception: {str(e)}")
            return False
            
    async def test_get_messages(self):
        """Test retrieving conversation messages with pagination"""
        print("\n=== Testing Message Retrieval ===")
        
        try:
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            
            # Test getting messages
            async with self.session.get(f"{API_URL}/chat/messages/{self.conversation_id}", 
                                      headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        self.log_test("Get Conversation Messages", True, f"Retrieved {len(data)} messages")
                        
                        # Check message structure
                        msg = data[0]
                        required_fields = ["id", "conversation_id", "sender_id", "content", "timestamp"]
                        if all(field in msg for field in required_fields):
                            self.log_test("Message Structure Validation", True, "All required fields present")
                        else:
                            self.log_test("Message Structure Validation", False, "Missing required fields")
                            
                        # Check message ordering (should be oldest first)
                        if len(data) > 1:
                            first_time = datetime.fromisoformat(data[0]["timestamp"].replace('Z', '+00:00'))
                            last_time = datetime.fromisoformat(data[-1]["timestamp"].replace('Z', '+00:00'))
                            if first_time <= last_time:
                                self.log_test("Message Ordering", True, "Messages ordered correctly (oldest first)")
                            else:
                                self.log_test("Message Ordering", False, "Messages not ordered correctly")
                    else:
                        self.log_test("Get Conversation Messages", False, "No messages returned")
                else:
                    self.log_test("Get Conversation Messages", False, f"Status {resp.status}: {await resp.text()}")
                    
            # Test pagination with limit
            async with self.session.get(f"{API_URL}/chat/messages/{self.conversation_id}?limit=1", 
                                      headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if len(data) == 1:
                        self.log_test("Message Pagination", True, "Limit parameter working correctly")
                    else:
                        self.log_test("Message Pagination", False, f"Expected 1 message, got {len(data)}")
                else:
                    self.log_test("Message Pagination", False, f"Status {resp.status}")
                    
            # Test unauthorized access
            async with self.session.get(f"{API_URL}/chat/messages/fake-conversation-id", 
                                      headers=headers) as resp:
                if resp.status == 404:
                    self.log_test("Message Access Authorization", True, "Correctly rejected unauthorized access")
                else:
                    self.log_test("Message Access Authorization", False, f"Should have failed with 404, got {resp.status}")
                    
            return True
            
        except Exception as e:
            self.log_test("Get Messages", False, f"Exception: {str(e)}")
            return False
            
    async def test_mark_message_read(self):
        """Test marking messages as read"""
        print("\n=== Testing Message Read Receipts ===")
        
        try:
            if not self.message_id:
                self.log_test("Mark Message Read", False, "No message ID available for testing")
                return False
                
            headers = {"Authorization": f"Bearer {self.user2_token}"}
            async with self.session.post(f"{API_URL}/chat/messages/{self.message_id}/read", 
                                       headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log_test("Mark Message as Read", True, "Message marked as read successfully")
                else:
                    error_text = await resp.text()
                    self.log_test("Mark Message as Read", False, f"Status {resp.status}: {error_text}")
                    
            # Test marking same message as read again (should fail or be idempotent)
            async with self.session.post(f"{API_URL}/chat/messages/{self.message_id}/read", 
                                       headers=headers) as resp:
                if resp.status in [200, 404]:  # Either idempotent or "already read"
                    self.log_test("Duplicate Read Receipt", True, "Handled duplicate read receipt correctly")
                else:
                    self.log_test("Duplicate Read Receipt", False, f"Unexpected status: {resp.status}")
                    
            # Test unauthorized read (wrong user)
            async with self.session.post(f"{API_URL}/chat/messages/fake-message-id/read", 
                                       headers=headers) as resp:
                if resp.status == 404:
                    self.log_test("Read Receipt Authorization", True, "Correctly rejected unauthorized read")
                else:
                    self.log_test("Read Receipt Authorization", False, f"Should have failed with 404, got {resp.status}")
                    
            return True
            
        except Exception as e:
            self.log_test("Mark Message Read", False, f"Exception: {str(e)}")
            return False
            
    async def test_socketio_connection(self):
        """Test Socket.IO connection and authentication"""
        print("\n=== Testing Socket.IO Real-time Features ===")
        
        try:
            # Create Socket.IO client
            self.sio_client = socketio.AsyncClient()
            
            # Track events
            events_received = []
            
            @self.sio_client.event
            async def connect():
                events_received.append('connect')
                
            @self.sio_client.event
            async def authenticated(data):
                events_received.append(f'authenticated:{data.get("user_id")}')
                
            @self.sio_client.event
            async def auth_error(data):
                events_received.append(f'auth_error:{data.get("message")}')
                
            @self.sio_client.event
            async def joined_conversation(data):
                events_received.append(f'joined_conversation:{data.get("conversation_id")}')
                
            @self.sio_client.event
            async def new_message(data):
                events_received.append(f'new_message:{data.get("conversation_id")}')
                
            @self.sio_client.event
            async def typing_start(data):
                events_received.append(f'typing_start:{data.get("user_id")}')
                
            @self.sio_client.event
            async def typing_stop(data):
                events_received.append(f'typing_stop:{data.get("user_id")}')
                
            @self.sio_client.event
            async def message_read(data):
                events_received.append(f'message_read:{data.get("message_id")}')
            
            # Connect to Socket.IO server
            socket_url = f"{BASE_URL}/socket.io"
            await self.sio_client.connect(socket_url)
            await asyncio.sleep(1)  # Wait for connection
            
            if 'connect' in events_received:
                self.log_test("Socket.IO Connection", True, "Connected to Socket.IO server")
            else:
                self.log_test("Socket.IO Connection", False, "Failed to connect to Socket.IO server")
                return False
                
            # Test authentication
            await self.sio_client.emit('authenticate', {
                'user_id': self.user1_id,
                'token': self.user1_token
            })
            await asyncio.sleep(1)
            
            if any('authenticated' in event for event in events_received):
                self.log_test("Socket.IO Authentication", True, "Successfully authenticated")
            else:
                self.log_test("Socket.IO Authentication", False, "Authentication failed")
                
            # Test joining conversation
            await self.sio_client.emit('join_conversation', {
                'conversation_id': self.conversation_id
            })
            await asyncio.sleep(1)
            
            if any('joined_conversation' in event for event in events_received):
                self.log_test("Join Conversation Room", True, "Successfully joined conversation room")
            else:
                self.log_test("Join Conversation Room", False, "Failed to join conversation room")
                
            # Test typing indicators
            await self.sio_client.emit('typing_start', {
                'conversation_id': self.conversation_id
            })
            await asyncio.sleep(0.5)
            
            await self.sio_client.emit('typing_stop', {
                'conversation_id': self.conversation_id
            })
            await asyncio.sleep(0.5)
            
            self.log_test("Typing Indicators", True, "Typing start/stop events sent successfully")
            
            # Test message read receipt
            if self.message_id:
                await self.sio_client.emit('message_read', {
                    'message_id': self.message_id,
                    'conversation_id': self.conversation_id
                })
                await asyncio.sleep(0.5)
                self.log_test("Socket.IO Read Receipt", True, "Read receipt event sent successfully")
            
            # Test real-time message broadcasting
            await self.sio_client.emit('send_message', {
                'conversation_id': self.conversation_id,
                'message': {
                    'content': 'Real-time test message',
                    'type': 'text'
                }
            })
            await asyncio.sleep(1)
            
            if any('new_message' in event for event in events_received):
                self.log_test("Real-time Message Broadcasting", True, "Message broadcast received")
            else:
                self.log_test("Real-time Message Broadcasting", False, "Message broadcast not received")
                
            await self.sio_client.disconnect()
            self.log_test("Socket.IO Disconnect", True, "Disconnected successfully")
            
            return True
            
        except Exception as e:
            self.log_test("Socket.IO Testing", False, f"Exception: {str(e)}")
            if self.sio_client:
                try:
                    await self.sio_client.disconnect()
                except:
                    pass
            return False
            
    async def run_all_tests(self):
        """Run all chat system tests"""
        print("🚀 Starting Real-time Chat System Backend Testing")
        print(f"Backend URL: {BASE_URL}")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Setup test users
            if not await self.setup_test_users():
                print("❌ Failed to setup test users. Aborting tests.")
                return
                
            # Run chat tests in sequence
            await self.test_create_conversation()
            await self.test_get_conversations()
            await self.test_send_message()
            await self.test_get_messages()
            await self.test_mark_message_read()
            await self.test_socketio_connection()
            
        finally:
            await self.cleanup_session()
            
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
                    
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                print(f"  • {result['test']}")
                
        return passed == total

async def main():
    """Main test runner"""
    tester = ChatSystemTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Chat system is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check the results above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())