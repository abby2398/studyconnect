#!/usr/bin/env python3
"""
Backend API Testing for International Student Networking App - Events System
Tests all Events System APIs including CRUD operations, attendance, and discussions
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://campuslink-25.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class EventsSystemTester:
    def __init__(self):
        self.session = None
        self.test_users = []
        self.test_events = []
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    async def create_test_user(self, email: str, first_name: str, last_name: str) -> Dict[str, Any]:
        """Create a test user and return auth token"""
        try:
            # Register user
            register_data = {
                "email": email,
                "password": "TestPassword123!",
                "first_name": first_name,
                "last_name": last_name
            }
            
            async with self.session.post(f"{API_BASE}/auth/register", json=register_data) as response:
                if response.status != 200:
                    print(f"Registration failed for {email}: {await response.text()}")
                    return None
            
            # Login user
            login_data = {
                "email": email,
                "password": "TestPassword123!"
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    result = await response.json()
                    user_data = {
                        "token": result["access_token"],
                        "user": result["user"],
                        "email": email,
                        "first_name": first_name,
                        "last_name": last_name
                    }
                    self.test_users.append(user_data)
                    return user_data
                else:
                    print(f"Login failed for {email}: {await response.text()}")
                    return None
                    
        except Exception as e:
            print(f"Error creating test user {email}: {str(e)}")
            return None
    
    def get_auth_headers(self, user_data: Dict[str, Any]) -> Dict[str, str]:
        """Get authorization headers for user"""
        return {"Authorization": f"Bearer {user_data['token']}"}
    
    async def test_event_crud_operations(self):
        """Test Event CRUD Operations"""
        print("\n=== Testing Event CRUD Operations ===")
        
        if len(self.test_users) < 2:
            print("❌ Need at least 2 test users for CRUD testing")
            return
        
        creator = self.test_users[0]
        other_user = self.test_users[1]
        
        # Test 1: Create Event
        print("\n1. Testing Event Creation...")
        event_data = {
            "title": "Machine Learning Study Group",
            "description": "Weekly study group for ML students. We'll cover algorithms, implement projects, and prepare for exams together.",
            "category": "study_group",
            "start_datetime": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "end_datetime": (datetime.now(timezone.utc) + timedelta(days=7, hours=2)).isoformat(),
            "location": {
                "address": "Engineering Building Room 301",
                "city": "Stanford",
                "country": "USA",
                "venue_name": "Stanford University",
                "is_online": False
            },
            "max_attendees": 15,
            "tags": ["machine-learning", "study", "algorithms"],
            "registration_required": True
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/events/",
                json=event_data,
                headers=self.get_auth_headers(creator)
            ) as response:
                if response.status == 200:
                    event = await response.json()
                    self.test_events.append(event)
                    print(f"✅ Event created successfully: {event['title']}")
                    print(f"   Event ID: {event['id']}")
                    print(f"   Creator: {event['creator_id']}")
                    print(f"   Current attendees: {event['current_attendees']}")
                    self.test_results.append("✅ POST /api/events/ - Create event")
                else:
                    error_text = await response.text()
                    print(f"❌ Event creation failed: {response.status} - {error_text}")
                    self.test_results.append("❌ POST /api/events/ - Create event failed")
                    return
        except Exception as e:
            print(f"❌ Event creation error: {str(e)}")
            self.test_results.append("❌ POST /api/events/ - Create event error")
            return
        
        event_id = self.test_events[0]['id']
        
        # Test 2: Get Events List
        print("\n2. Testing Get Events List...")
        try:
            async with self.session.get(
                f"{API_BASE}/events/",
                headers=self.get_auth_headers(other_user)
            ) as response:
                if response.status == 200:
                    events = await response.json()
                    print(f"✅ Retrieved {len(events)} events")
                    if events:
                        print(f"   First event: {events[0]['event']['title']}")
                        print(f"   Creator info: {events[0]['creator']['first_name']} {events[0]['creator']['last_name']}")
                        print(f"   Can join: {events[0]['can_join']}")
                    self.test_results.append("✅ GET /api/events/ - List events")
                else:
                    error_text = await response.text()
                    print(f"❌ Get events failed: {response.status} - {error_text}")
                    self.test_results.append("❌ GET /api/events/ - List events failed")
        except Exception as e:
            print(f"❌ Get events error: {str(e)}")
            self.test_results.append("❌ GET /api/events/ - List events error")
        
        # Test 3: Get Single Event
        print("\n3. Testing Get Single Event...")
        try:
            async with self.session.get(
                f"{API_BASE}/events/{event_id}",
                headers=self.get_auth_headers(other_user)
            ) as response:
                if response.status == 200:
                    event_details = await response.json()
                    print(f"✅ Retrieved event details: {event_details['event']['title']}")
                    print(f"   Description: {event_details['event']['description'][:50]}...")
                    print(f"   Location: {event_details['event']['location']['city']}")
                    print(f"   Is creator: {event_details['is_creator']}")
                    self.test_results.append("✅ GET /api/events/{event_id} - Get event details")
                else:
                    error_text = await response.text()
                    print(f"❌ Get event details failed: {response.status} - {error_text}")
                    self.test_results.append("❌ GET /api/events/{event_id} - Get event details failed")
        except Exception as e:
            print(f"❌ Get event details error: {str(e)}")
            self.test_results.append("❌ GET /api/events/{event_id} - Get event details error")
        
        # Test 4: Update Event (Creator Only)
        print("\n4. Testing Event Update (Creator Only)...")
        update_data = {
            "title": "Advanced Machine Learning Study Group",
            "description": "Updated description: Advanced ML study group with focus on deep learning and neural networks.",
            "max_attendees": 20
        }
        
        try:
            async with self.session.put(
                f"{API_BASE}/events/{event_id}",
                json=update_data,
                headers=self.get_auth_headers(creator)
            ) as response:
                if response.status == 200:
                    updated_event = await response.json()
                    print(f"✅ Event updated successfully: {updated_event['title']}")
                    print(f"   New max attendees: {updated_event['max_attendees']}")
                    self.test_results.append("✅ PUT /api/events/{event_id} - Update event (creator)")
                else:
                    error_text = await response.text()
                    print(f"❌ Event update failed: {response.status} - {error_text}")
                    self.test_results.append("❌ PUT /api/events/{event_id} - Update event failed")
        except Exception as e:
            print(f"❌ Event update error: {str(e)}")
            self.test_results.append("❌ PUT /api/events/{event_id} - Update event error")
        
        # Test 5: Update Event (Non-Creator - Should Fail)
        print("\n5. Testing Event Update (Non-Creator - Should Fail)...")
        try:
            async with self.session.put(
                f"{API_BASE}/events/{event_id}",
                json={"title": "Unauthorized Update"},
                headers=self.get_auth_headers(other_user)
            ) as response:
                if response.status == 403:
                    print("✅ Non-creator update correctly rejected (403)")
                    self.test_results.append("✅ PUT /api/events/{event_id} - Non-creator authorization check")
                else:
                    print(f"❌ Non-creator update should have failed with 403, got {response.status}")
                    self.test_results.append("❌ PUT /api/events/{event_id} - Authorization check failed")
        except Exception as e:
            print(f"❌ Non-creator update test error: {str(e)}")
            self.test_results.append("❌ PUT /api/events/{event_id} - Authorization test error")
    
    async def test_event_attendance_system(self):
        """Test Event Attendance System"""
        print("\n=== Testing Event Attendance System ===")
        
        if not self.test_events or len(self.test_users) < 2:
            print("❌ Need test event and users for attendance testing")
            return
        
        event_id = self.test_events[0]['id']
        attendee = self.test_users[1]  # Non-creator user
        
        # Test 1: Join Event
        print("\n1. Testing Join Event...")
        join_data = {
            "status": "joined",
            "notes": "Looking forward to learning ML!"
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/events/{event_id}/join",
                json=join_data,
                headers=self.get_auth_headers(attendee)
            ) as response:
                if response.status == 200:
                    attendee_record = await response.json()
                    print(f"✅ Successfully joined event")
                    print(f"   Attendee ID: {attendee_record['id']}")
                    print(f"   Status: {attendee_record['status']}")
                    print(f"   Notes: {attendee_record['notes']}")
                    self.test_results.append("✅ POST /api/events/{event_id}/join - Join event")
                else:
                    error_text = await response.text()
                    print(f"❌ Join event failed: {response.status} - {error_text}")
                    self.test_results.append("❌ POST /api/events/{event_id}/join - Join event failed")
                    return
        except Exception as e:
            print(f"❌ Join event error: {str(e)}")
            self.test_results.append("❌ POST /api/events/{event_id}/join - Join event error")
            return
        
        # Test 2: Get Event Attendees
        print("\n2. Testing Get Event Attendees...")
        try:
            async with self.session.get(
                f"{API_BASE}/events/{event_id}/attendees",
                headers=self.get_auth_headers(self.test_users[0])  # Creator
            ) as response:
                if response.status == 200:
                    attendees = await response.json()
                    print(f"✅ Retrieved {len(attendees)} attendees")
                    for attendee_info in attendees:
                        user_info = attendee_info['user']
                        attendee_data = attendee_info['attendee']
                        print(f"   - {user_info['first_name']} {user_info['last_name']} ({attendee_data['status']})")
                    self.test_results.append("✅ GET /api/events/{event_id}/attendees - Get attendees")
                else:
                    error_text = await response.text()
                    print(f"❌ Get attendees failed: {response.status} - {error_text}")
                    self.test_results.append("❌ GET /api/events/{event_id}/attendees - Get attendees failed")
        except Exception as e:
            print(f"❌ Get attendees error: {str(e)}")
            self.test_results.append("❌ GET /api/events/{event_id}/attendees - Get attendees error")
        
        # Test 3: Try to Join Again (Should Fail)
        print("\n3. Testing Duplicate Join (Should Fail)...")
        try:
            async with self.session.post(
                f"{API_BASE}/events/{event_id}/join",
                json=join_data,
                headers=self.get_auth_headers(attendee)
            ) as response:
                if response.status == 400:
                    print("✅ Duplicate join correctly rejected (400)")
                    self.test_results.append("✅ POST /api/events/{event_id}/join - Duplicate join prevention")
                else:
                    print(f"❌ Duplicate join should have failed with 400, got {response.status}")
                    self.test_results.append("❌ POST /api/events/{event_id}/join - Duplicate join check failed")
        except Exception as e:
            print(f"❌ Duplicate join test error: {str(e)}")
            self.test_results.append("❌ POST /api/events/{event_id}/join - Duplicate join test error")
        
        # Test 4: Leave Event
        print("\n4. Testing Leave Event...")
        try:
            async with self.session.delete(
                f"{API_BASE}/events/{event_id}/leave",
                headers=self.get_auth_headers(attendee)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Successfully left event: {result['message']}")
                    self.test_results.append("✅ DELETE /api/events/{event_id}/leave - Leave event")
                else:
                    error_text = await response.text()
                    print(f"❌ Leave event failed: {response.status} - {error_text}")
                    self.test_results.append("❌ DELETE /api/events/{event_id}/leave - Leave event failed")
        except Exception as e:
            print(f"❌ Leave event error: {str(e)}")
            self.test_results.append("❌ DELETE /api/events/{event_id}/leave - Leave event error")
        
        # Test 5: Try to Leave Again (Should Fail)
        print("\n5. Testing Leave Non-Attended Event (Should Fail)...")
        try:
            async with self.session.delete(
                f"{API_BASE}/events/{event_id}/leave",
                headers=self.get_auth_headers(attendee)
            ) as response:
                if response.status == 404:
                    print("✅ Leave non-attended event correctly rejected (404)")
                    self.test_results.append("✅ DELETE /api/events/{event_id}/leave - Non-attendee check")
                else:
                    print(f"❌ Leave non-attended should have failed with 404, got {response.status}")
                    self.test_results.append("❌ DELETE /api/events/{event_id}/leave - Non-attendee check failed")
        except Exception as e:
            print(f"❌ Leave non-attended test error: {str(e)}")
            self.test_results.append("❌ DELETE /api/events/{event_id}/leave - Non-attendee test error")
    
    async def test_event_discussion_system(self):
        """Test Event Discussion System"""
        print("\n=== Testing Event Discussion System ===")
        
        if not self.test_events or len(self.test_users) < 2:
            print("❌ Need test event and users for discussion testing")
            return
        
        event_id = self.test_events[0]['id']
        creator = self.test_users[0]
        attendee = self.test_users[1]
        
        # First, make sure attendee joins the event for discussion access
        join_data = {"status": "joined", "notes": "Rejoining for discussion test"}
        try:
            async with self.session.post(
                f"{API_BASE}/events/{event_id}/join",
                json=join_data,
                headers=self.get_auth_headers(attendee)
            ) as response:
                if response.status not in [200, 400]:  # 400 if already joined
                    print(f"❌ Failed to join event for discussion test: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Error joining event for discussion: {str(e)}")
            return
        
        # Test 1: Send Message in Event Discussion
        print("\n1. Testing Send Message in Event Discussion...")
        message_data = {
            "message": "Hello everyone! Excited to be part of this study group. What topics should we cover first?",
            "is_announcement": False
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/events/{event_id}/messages",
                json=message_data,
                headers=self.get_auth_headers(attendee)
            ) as response:
                if response.status == 200:
                    message = await response.json()
                    print(f"✅ Message sent successfully")
                    print(f"   Message ID: {message['id']}")
                    print(f"   Content: {message['message'][:50]}...")
                    print(f"   Is announcement: {message['is_announcement']}")
                    self.test_results.append("✅ POST /api/events/{event_id}/messages - Send message")
                else:
                    error_text = await response.text()
                    print(f"❌ Send message failed: {response.status} - {error_text}")
                    self.test_results.append("❌ POST /api/events/{event_id}/messages - Send message failed")
                    return
        except Exception as e:
            print(f"❌ Send message error: {str(e)}")
            self.test_results.append("❌ POST /api/events/{event_id}/messages - Send message error")
            return
        
        # Test 2: Send Announcement (Creator Only)
        print("\n2. Testing Send Announcement (Creator Only)...")
        announcement_data = {
            "message": "📢 Important: Please bring your laptops and notebooks to the next session. We'll be doing hands-on coding!",
            "is_announcement": True
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/events/{event_id}/messages",
                json=announcement_data,
                headers=self.get_auth_headers(creator)
            ) as response:
                if response.status == 200:
                    announcement = await response.json()
                    print(f"✅ Announcement sent successfully")
                    print(f"   Message: {announcement['message'][:50]}...")
                    print(f"   Is announcement: {announcement['is_announcement']}")
                    self.test_results.append("✅ POST /api/events/{event_id}/messages - Send announcement (creator)")
                else:
                    error_text = await response.text()
                    print(f"❌ Send announcement failed: {response.status} - {error_text}")
                    self.test_results.append("❌ POST /api/events/{event_id}/messages - Send announcement failed")
        except Exception as e:
            print(f"❌ Send announcement error: {str(e)}")
            self.test_results.append("❌ POST /api/events/{event_id}/messages - Send announcement error")
        
        # Test 3: Try to Send Announcement as Non-Creator (Should Fail)
        print("\n3. Testing Send Announcement as Non-Creator (Should Fail)...")
        try:
            async with self.session.post(
                f"{API_BASE}/events/{event_id}/messages",
                json=announcement_data,
                headers=self.get_auth_headers(attendee)
            ) as response:
                if response.status == 403:
                    print("✅ Non-creator announcement correctly rejected (403)")
                    self.test_results.append("✅ POST /api/events/{event_id}/messages - Non-creator announcement check")
                else:
                    print(f"❌ Non-creator announcement should have failed with 403, got {response.status}")
                    self.test_results.append("❌ POST /api/events/{event_id}/messages - Announcement authorization failed")
        except Exception as e:
            print(f"❌ Non-creator announcement test error: {str(e)}")
            self.test_results.append("❌ POST /api/events/{event_id}/messages - Announcement test error")
        
        # Test 4: Get Event Messages
        print("\n4. Testing Get Event Messages...")
        try:
            async with self.session.get(
                f"{API_BASE}/events/{event_id}/messages",
                headers=self.get_auth_headers(attendee)
            ) as response:
                if response.status == 200:
                    messages = await response.json()
                    print(f"✅ Retrieved {len(messages)} messages")
                    for msg in messages:
                        user_info = msg['user']
                        message_info = msg['message']
                        msg_type = "📢 Announcement" if message_info['is_announcement'] else "💬 Message"
                        print(f"   {msg_type} from {user_info['first_name']}: {message_info['message'][:30]}...")
                    self.test_results.append("✅ GET /api/events/{event_id}/messages - Get messages")
                else:
                    error_text = await response.text()
                    print(f"❌ Get messages failed: {response.status} - {error_text}")
                    self.test_results.append("❌ GET /api/events/{event_id}/messages - Get messages failed")
        except Exception as e:
            print(f"❌ Get messages error: {str(e)}")
            self.test_results.append("❌ GET /api/events/{event_id}/messages - Get messages error")
    
    async def test_user_events(self):
        """Test User's Events Endpoints"""
        print("\n=== Testing User's Events Endpoints ===")
        
        if not self.test_events or len(self.test_users) < 2:
            print("❌ Need test event and users for user events testing")
            return
        
        creator = self.test_users[0]
        attendee = self.test_users[1]
        
        # Test 1: Get User's Created Events
        print("\n1. Testing Get User's Created Events...")
        try:
            async with self.session.get(
                f"{API_BASE}/events/my/created",
                headers=self.get_auth_headers(creator)
            ) as response:
                if response.status == 200:
                    created_events = await response.json()
                    print(f"✅ Retrieved {len(created_events)} created events")
                    for event_detail in created_events:
                        event = event_detail['event']
                        print(f"   - {event['title']} ({event['status']})")
                        print(f"     Attendees: {event_detail['attendee_count']}")
                        print(f"     Is creator: {event_detail['is_creator']}")
                    self.test_results.append("✅ GET /api/events/my/created - Get user's created events")
                else:
                    error_text = await response.text()
                    print(f"❌ Get created events failed: {response.status} - {error_text}")
                    self.test_results.append("❌ GET /api/events/my/created - Get created events failed")
        except Exception as e:
            print(f"❌ Get created events error: {str(e)}")
            self.test_results.append("❌ GET /api/events/my/created - Get created events error")
        
        # Test 2: Get User's Attending Events
        print("\n2. Testing Get User's Attending Events...")
        try:
            async with self.session.get(
                f"{API_BASE}/events/my/attending",
                headers=self.get_auth_headers(attendee)
            ) as response:
                if response.status == 200:
                    attending_events = await response.json()
                    print(f"✅ Retrieved {len(attending_events)} attending events")
                    for event_detail in attending_events:
                        event = event_detail['event']
                        creator_info = event_detail['creator']
                        print(f"   - {event['title']} (Status: {event_detail['user_attendance_status']})")
                        print(f"     Created by: {creator_info['first_name']} {creator_info['last_name']}")
                        print(f"     Attendees: {event_detail['attendee_count']}")
                    self.test_results.append("✅ GET /api/events/my/attending - Get user's attending events")
                else:
                    error_text = await response.text()
                    print(f"❌ Get attending events failed: {response.status} - {error_text}")
                    self.test_results.append("❌ GET /api/events/my/attending - Get attending events failed")
        except Exception as e:
            print(f"❌ Get attending events error: {str(e)}")
            self.test_results.append("❌ GET /api/events/my/attending - Get attending events error")
    
    async def test_event_filters_and_search(self):
        """Test Event Filters and Search"""
        print("\n=== Testing Event Filters and Search ===")
        
        if len(self.test_users) < 1:
            print("❌ Need test user for filter testing")
            return
        
        user = self.test_users[0]
        
        # Test 1: Filter by Category
        print("\n1. Testing Filter by Category...")
        try:
            async with self.session.get(
                f"{API_BASE}/events/?category=study_group",
                headers=self.get_auth_headers(user)
            ) as response:
                if response.status == 200:
                    events = await response.json()
                    print(f"✅ Retrieved {len(events)} study_group events")
                    self.test_results.append("✅ GET /api/events/?category=study_group - Filter by category")
                else:
                    error_text = await response.text()
                    print(f"❌ Filter by category failed: {response.status} - {error_text}")
                    self.test_results.append("❌ GET /api/events/?category=study_group - Filter failed")
        except Exception as e:
            print(f"❌ Filter by category error: {str(e)}")
            self.test_results.append("❌ GET /api/events/?category=study_group - Filter error")
        
        # Test 2: Search by Title/Description
        print("\n2. Testing Search by Title/Description...")
        try:
            async with self.session.get(
                f"{API_BASE}/events/?search=machine learning",
                headers=self.get_auth_headers(user)
            ) as response:
                if response.status == 200:
                    events = await response.json()
                    print(f"✅ Retrieved {len(events)} events matching 'machine learning'")
                    self.test_results.append("✅ GET /api/events/?search=machine learning - Search functionality")
                else:
                    error_text = await response.text()
                    print(f"❌ Search failed: {response.status} - {error_text}")
                    self.test_results.append("❌ GET /api/events/?search=machine learning - Search failed")
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            self.test_results.append("❌ GET /api/events/?search=machine learning - Search error")
        
        # Test 3: Filter by Location
        print("\n3. Testing Filter by Location...")
        try:
            async with self.session.get(
                f"{API_BASE}/events/?city=Stanford&country=USA",
                headers=self.get_auth_headers(user)
            ) as response:
                if response.status == 200:
                    events = await response.json()
                    print(f"✅ Retrieved {len(events)} events in Stanford, USA")
                    self.test_results.append("✅ GET /api/events/?city=Stanford&country=USA - Location filter")
                else:
                    error_text = await response.text()
                    print(f"❌ Location filter failed: {response.status} - {error_text}")
                    self.test_results.append("❌ GET /api/events/?city=Stanford&country=USA - Location filter failed")
        except Exception as e:
            print(f"❌ Location filter error: {str(e)}")
            self.test_results.append("❌ GET /api/events/?city=Stanford&country=USA - Location filter error")
    
    async def test_delete_event(self):
        """Test Event Deletion (Creator Only)"""
        print("\n=== Testing Event Deletion ===")
        
        if not self.test_events or len(self.test_users) < 2:
            print("❌ Need test event and users for deletion testing")
            return
        
        event_id = self.test_events[0]['id']
        creator = self.test_users[0]
        non_creator = self.test_users[1]
        
        # Test 1: Try to Delete as Non-Creator (Should Fail)
        print("\n1. Testing Delete Event as Non-Creator (Should Fail)...")
        try:
            async with self.session.delete(
                f"{API_BASE}/events/{event_id}",
                headers=self.get_auth_headers(non_creator)
            ) as response:
                if response.status == 403:
                    print("✅ Non-creator deletion correctly rejected (403)")
                    self.test_results.append("✅ DELETE /api/events/{event_id} - Non-creator authorization check")
                else:
                    print(f"❌ Non-creator deletion should have failed with 403, got {response.status}")
                    self.test_results.append("❌ DELETE /api/events/{event_id} - Authorization check failed")
        except Exception as e:
            print(f"❌ Non-creator deletion test error: {str(e)}")
            self.test_results.append("❌ DELETE /api/events/{event_id} - Authorization test error")
        
        # Test 2: Delete Event as Creator
        print("\n2. Testing Delete Event as Creator...")
        try:
            async with self.session.delete(
                f"{API_BASE}/events/{event_id}",
                headers=self.get_auth_headers(creator)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Event deleted successfully: {result['message']}")
                    self.test_results.append("✅ DELETE /api/events/{event_id} - Delete event (creator)")
                else:
                    error_text = await response.text()
                    print(f"❌ Event deletion failed: {response.status} - {error_text}")
                    self.test_results.append("❌ DELETE /api/events/{event_id} - Delete event failed")
        except Exception as e:
            print(f"❌ Event deletion error: {str(e)}")
            self.test_results.append("❌ DELETE /api/events/{event_id} - Delete event error")
        
        # Test 3: Verify Event is Deleted
        print("\n3. Testing Verify Event is Deleted...")
        try:
            async with self.session.get(
                f"{API_BASE}/events/{event_id}",
                headers=self.get_auth_headers(creator)
            ) as response:
                if response.status == 404:
                    print("✅ Event correctly not found after deletion (404)")
                    self.test_results.append("✅ GET /api/events/{event_id} - Verify deletion")
                else:
                    print(f"❌ Deleted event should return 404, got {response.status}")
                    self.test_results.append("❌ GET /api/events/{event_id} - Deletion verification failed")
        except Exception as e:
            print(f"❌ Deletion verification error: {str(e)}")
            self.test_results.append("❌ GET /api/events/{event_id} - Deletion verification error")
    
    async def run_all_tests(self):
        """Run all Events System tests"""
        print("🚀 Starting Events System Backend API Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        
        await self.setup_session()
        
        try:
            # Create test users
            print("\n=== Setting up Test Users ===")
            await self.create_test_user("alice.johnson@stanford.edu", "Alice", "Johnson")
            await self.create_test_user("bob.smith@mit.edu", "Bob", "Smith")
            
            if len(self.test_users) < 2:
                print("❌ Failed to create required test users")
                return
            
            print(f"✅ Created {len(self.test_users)} test users")
            
            # Run all test suites
            await self.test_event_crud_operations()
            await self.test_event_attendance_system()
            await self.test_event_discussion_system()
            await self.test_user_events()
            await self.test_event_filters_and_search()
            await self.test_delete_event()
            
        finally:
            await self.cleanup_session()
        
        # Print summary
        print("\n" + "="*60)
        print("🏁 EVENTS SYSTEM TESTING SUMMARY")
        print("="*60)
        
        passed = len([r for r in self.test_results if r.startswith("✅")])
        failed = len([r for r in self.test_results if r.startswith("❌")])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "0%")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            print(f"  {result}")
        
        if failed == 0:
            print("\n🎉 ALL EVENTS SYSTEM TESTS PASSED!")
        else:
            print(f"\n⚠️  {failed} test(s) failed. Please check the issues above.")

async def main():
    """Main test runner"""
    tester = EventsSystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())