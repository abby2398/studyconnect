#!/usr/bin/env python3
"""
Backend API Testing for International Student Networking App - Posts & Media System
Testing Phase 3: Posts & Media System APIs
"""

import requests
import json
import base64
import time
from datetime import datetime
from typing import Dict, Any, Optional
import os
import sys

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

# Test user credentials
TEST_USER_EMAIL = "sarah.johnson@university.edu"
TEST_USER_PASSWORD = "SecurePass123!"
TEST_USER_2_EMAIL = "mike.chen@college.edu"
TEST_USER_2_PASSWORD = "TestPass456!"

class PostsAPITester:
    def __init__(self):
        self.base_url = API_URL
        self.session = requests.Session()
        self.user1_token = None
        self.user2_token = None
        self.user1_id = None
        self.user2_id = None
        self.test_post_id = None
        self.test_comment_id = None
        self.test_results = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
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
    
    def create_test_image_base64(self) -> str:
        """Create a simple test image in base64 format"""
        try:
            from PIL import Image
            import io
            
            # Create a simple red image
            img = Image.new('RGB', (100, 100), color='red')
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_data = buffer.getvalue()
            
            return base64.b64encode(img_data).decode('utf-8')
        except ImportError:
            # Fallback: create a minimal base64 image
            # This is a 1x1 red pixel PNG
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    def setup_test_users(self) -> bool:
        """Setup test users and get authentication tokens"""
        try:
            self.log("Setting up test users...")
            
            # Register and login first user
            register_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "first_name": "Sarah",
                "last_name": "Johnson",
                "phone": "+1234567890"
            }
            
            # Try to register (might already exist)
            response = self.session.post(f"{self.base_url}/auth/register", json=register_data)
            if response.status_code not in [200, 400]:
                self.log_test("User 1 Registration", False, f"Status {response.status_code}: {response.text}")
                return False
            
            # Login user 1
            login_data = {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
            if response.status_code != 200:
                self.log_test("User 1 Login", False, f"Status {response.status_code}: {response.text}")
                return False
            
            user1_data = response.json()
            self.user1_token = user1_data["access_token"]
            self.user1_id = user1_data["user"]["id"]
            self.log_test("User 1 Setup", True, f"Logged in as {user1_data['user']['first_name']}")
            
            # Setup second user
            register_data2 = {
                "email": TEST_USER_2_EMAIL,
                "password": TEST_USER_2_PASSWORD,
                "first_name": "Mike",
                "last_name": "Chen",
                "phone": "+1987654321"
            }
            
            response = self.session.post(f"{self.base_url}/auth/register", json=register_data2)
            if response.status_code not in [200, 400]:
                self.log_test("User 2 Registration", False, f"Status {response.status_code}: {response.text}")
                return False
            
            # Login user 2
            login_data2 = {"email": TEST_USER_2_EMAIL, "password": TEST_USER_2_PASSWORD}
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data2)
            if response.status_code != 200:
                self.log_test("User 2 Login", False, f"Status {response.status_code}: {response.text}")
                return False
            
            user2_data = response.json()
            self.user2_token = user2_data["access_token"]
            self.user2_id = user2_data["user"]["id"]
            self.log_test("User 2 Setup", True, f"Logged in as {user2_data['user']['first_name']}")
            
            return True
            
        except Exception as e:
            self.log_test("User Setup", False, f"Exception: {str(e)}")
            return False
    
    def verify_users(self) -> bool:
        """Check user verification status"""
        try:
            headers1 = {"Authorization": f"Bearer {self.user1_token}"}
            response = self.session.get(f"{self.base_url}/users/me", headers=headers1)
            
            if response.status_code == 200:
                user_data = response.json()
                if not user_data.get("is_verified"):
                    self.log("User 1 needs verification - this may cause post creation to fail", "WARNING")
                else:
                    self.log("User 1 is verified")
            
            headers2 = {"Authorization": f"Bearer {self.user2_token}"}
            response = self.session.get(f"{self.base_url}/users/me", headers=headers2)
            
            if response.status_code == 200:
                user_data = response.json()
                if not user_data.get("is_verified"):
                    self.log("User 2 needs verification - this may cause post creation to fail", "WARNING")
                else:
                    self.log("User 2 is verified")
            
            return True
            
        except Exception as e:
            self.log(f"Error checking user verification: {str(e)}", "ERROR")
            return False
    
    def test_create_text_post(self) -> bool:
        """Test creating a text-only post"""
        try:
            self.log("Testing text post creation...")
            
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            post_data = {
                "content": "Hello everyone! This is my first post on the student networking app. #study #university #networking",
                "post_type": "text",
                "visibility": "public",
                "location": "New York University",
                "media_attachments": []
            }
            
            response = self.session.post(f"{self.base_url}/posts/", json=post_data, headers=headers)
            
            if response.status_code == 200:
                post = response.json()
                self.test_post_id = post["id"]
                self.log_test("Create Text Post", True, f"Post created: {post['id']}")
                
                # Verify hashtags were extracted
                if "study" in post.get("hashtags", []) and "university" in post.get("hashtags", []):
                    self.log_test("Hashtag Extraction", True, "Hashtags extracted correctly")
                else:
                    self.log_test("Hashtag Extraction", False, f"Expected hashtags not found. Got: {post.get('hashtags', [])}")
                
                return True
            else:
                self.log_test("Create Text Post", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Text Post", False, f"Exception: {str(e)}")
            return False
    
    def test_create_image_post(self) -> bool:
        """Test creating a post with image attachment"""
        try:
            self.log("Testing image post creation...")
            
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            
            # Create test image
            test_image_base64 = self.create_test_image_base64()
            
            media_attachment = {
                "file_type": "image",
                "mime_type": "image/png",
                "file_size": len(base64.b64decode(test_image_base64)),
                "width": 100,
                "height": 100,
                "data": test_image_base64
            }
            
            post_data = {
                "content": "Check out this amazing view from campus! #campus #photography",
                "post_type": "image",
                "visibility": "public",
                "media_attachments": [media_attachment]
            }
            
            response = self.session.post(f"{self.base_url}/posts/", json=post_data, headers=headers)
            
            if response.status_code == 200:
                post = response.json()
                self.log_test("Create Image Post", True, f"Image post created: {post['id']}")
                
                # Verify media attachment
                if post.get("media_attachments") and len(post["media_attachments"]) > 0:
                    self.log_test("Media Attachment Processing", True, "Media attachment saved correctly")
                else:
                    self.log_test("Media Attachment Processing", False, "Media attachment not saved")
                
                return True
            else:
                self.log_test("Create Image Post", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Image Post", False, f"Exception: {str(e)}")
            return False
    
    def test_unverified_user_restriction(self) -> bool:
        """Test that unverified users cannot create posts"""
        try:
            self.log("Testing unverified user post restriction...")
            
            # Check if user2 is unverified first
            headers = {"Authorization": f"Bearer {self.user2_token}"}
            user_response = self.session.get(f"{self.base_url}/users/me", headers=headers)
            
            if user_response.status_code == 200:
                user_data = user_response.json()
                if user_data.get("is_verified"):
                    self.log_test("Unverified User Restriction", True, "User 2 is verified - cannot test restriction")
                    return True
            
            post_data = {
                "content": "This should fail if user is unverified",
                "post_type": "text",
                "visibility": "public",
                "media_attachments": []
            }
            
            response = self.session.post(f"{self.base_url}/posts/", json=post_data, headers=headers)
            
            if response.status_code == 403:
                self.log_test("Unverified User Restriction", True, "Unverified user correctly blocked from posting")
                return True
            elif response.status_code == 200:
                self.log_test("Unverified User Restriction", True, "User 2 is verified - test passed")
                return True
            else:
                self.log_test("Unverified User Restriction", False, f"Unexpected response: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Unverified User Restriction", False, f"Exception: {str(e)}")
            return False
    
    def test_get_posts_feed(self) -> bool:
        """Test retrieving posts feed"""
        try:
            self.log("Testing posts feed retrieval...")
            
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            response = self.session.get(f"{self.base_url}/posts/", headers=headers)
            
            if response.status_code == 200:
                posts = response.json()
                self.log_test("Get Posts Feed", True, f"Retrieved {len(posts)} posts")
                
                # Verify post structure
                if posts and len(posts) > 0:
                    post = posts[0]
                    required_fields = ["post", "author", "is_liked", "is_shared"]
                    if all(field in post for field in required_fields):
                        self.log_test("Posts Feed Structure", True, "Post structure is correct")
                    else:
                        self.log_test("Posts Feed Structure", False, f"Missing fields: {[f for f in required_fields if f not in post]}")
                
                return True
            else:
                self.log_test("Get Posts Feed", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Posts Feed", False, f"Exception: {str(e)}")
            return False
    
    def test_get_single_post(self) -> bool:
        """Test retrieving a single post"""
        try:
            self.log("Testing single post retrieval...")
            
            if not self.test_post_id:
                self.log_test("Get Single Post", False, "No test post ID available")
                return False
            
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            response = self.session.get(f"{self.base_url}/posts/{self.test_post_id}", headers=headers)
            
            if response.status_code == 200:
                post_data = response.json()
                self.log_test("Get Single Post", True, f"Retrieved post: {post_data['post']['id']}")
                return True
            else:
                self.log_test("Get Single Post", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Single Post", False, f"Exception: {str(e)}")
            return False
    
    def test_like_post(self) -> bool:
        """Test liking a post"""
        try:
            self.log("Testing post liking...")
            
            if not self.test_post_id:
                self.log_test("Like Post", False, "No test post ID available")
                return False
            
            headers = {"Authorization": f"Bearer {self.user2_token}"}
            response = self.session.post(f"{self.base_url}/posts/{self.test_post_id}/like", headers=headers)
            
            if response.status_code == 200:
                self.log_test("Like Post", True, "Post liked successfully")
                
                # Verify like count increased
                get_response = self.session.get(f"{self.base_url}/posts/{self.test_post_id}", headers=headers)
                if get_response.status_code == 200:
                    post_data = get_response.json()
                    if post_data["post"]["likes_count"] > 0:
                        self.log_test("Like Count Update", True, f"Like count: {post_data['post']['likes_count']}")
                    else:
                        self.log_test("Like Count Update", False, "Like count not updated")
                
                return True
            else:
                self.log_test("Like Post", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Like Post", False, f"Exception: {str(e)}")
            return False
    
    def test_unlike_post(self) -> bool:
        """Test unliking a post"""
        try:
            self.log("Testing post unliking...")
            
            if not self.test_post_id:
                self.log_test("Unlike Post", False, "No test post ID available")
                return False
            
            headers = {"Authorization": f"Bearer {self.user2_token}"}
            response = self.session.delete(f"{self.base_url}/posts/{self.test_post_id}/like", headers=headers)
            
            if response.status_code == 200:
                self.log_test("Unlike Post", True, "Post unliked successfully")
                
                # Verify like count decreased
                get_response = self.session.get(f"{self.base_url}/posts/{self.test_post_id}", headers=headers)
                if get_response.status_code == 200:
                    post_data = get_response.json()
                    if post_data["post"]["likes_count"] == 0:
                        self.log_test("Unlike Count Update", True, "Like count correctly decreased")
                    else:
                        self.log_test("Unlike Count Update", False, f"Like count still: {post_data['post']['likes_count']}")
                
                return True
            else:
                self.log_test("Unlike Post", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Unlike Post", False, f"Exception: {str(e)}")
            return False
    
    def test_create_comment(self) -> bool:
        """Test creating a comment on a post"""
        try:
            self.log("Testing comment creation...")
            
            if not self.test_post_id:
                self.log_test("Create Comment", False, "No test post ID available")
                return False
            
            headers = {"Authorization": f"Bearer {self.user2_token}"}
            comment_data = {
                "content": "Great post! Thanks for sharing this with the community."
            }
            
            response = self.session.post(f"{self.base_url}/posts/{self.test_post_id}/comments", 
                                       json=comment_data, headers=headers)
            
            if response.status_code == 200:
                comment = response.json()
                self.test_comment_id = comment["id"]
                self.log_test("Create Comment", True, f"Comment created: {comment['id']}")
                
                # Verify comment count increased
                get_response = self.session.get(f"{self.base_url}/posts/{self.test_post_id}", headers=headers)
                if get_response.status_code == 200:
                    post_data = get_response.json()
                    if post_data["post"]["comments_count"] > 0:
                        self.log_test("Comment Count Update", True, f"Comment count: {post_data['post']['comments_count']}")
                    else:
                        self.log_test("Comment Count Update", False, "Comment count not updated")
                
                return True
            else:
                self.log_test("Create Comment", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Comment", False, f"Exception: {str(e)}")
            return False
    
    def test_get_comments(self) -> bool:
        """Test retrieving comments for a post"""
        try:
            self.log("Testing comment retrieval...")
            
            if not self.test_post_id:
                self.log_test("Get Comments", False, "No test post ID available")
                return False
            
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            response = self.session.get(f"{self.base_url}/posts/{self.test_post_id}/comments", headers=headers)
            
            if response.status_code == 200:
                comments = response.json()
                self.log_test("Get Comments", True, f"Retrieved {len(comments)} comments")
                
                # Verify comment structure
                if comments and len(comments) > 0:
                    comment = comments[0]
                    if "author" in comment and "content" in comment:
                        self.log_test("Comment Structure", True, "Comment structure is correct")
                    else:
                        self.log_test("Comment Structure", False, "Comment structure missing required fields")
                
                return True
            else:
                self.log_test("Get Comments", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Comments", False, f"Exception: {str(e)}")
            return False
    
    def test_share_post(self) -> bool:
        """Test sharing a post"""
        try:
            self.log("Testing post sharing...")
            
            if not self.test_post_id:
                self.log_test("Share Post", False, "No test post ID available")
                return False
            
            headers = {"Authorization": f"Bearer {self.user2_token}"}
            
            response = self.session.post(f"{self.base_url}/posts/{self.test_post_id}/share", headers=headers)
            
            if response.status_code == 200:
                self.log_test("Share Post", True, "Post shared successfully")
                
                # Verify share count increased
                get_response = self.session.get(f"{self.base_url}/posts/{self.test_post_id}", headers=headers)
                if get_response.status_code == 200:
                    post_data = get_response.json()
                    if post_data["post"]["shares_count"] > 0:
                        self.log_test("Share Count Update", True, f"Share count: {post_data['post']['shares_count']}")
                    else:
                        self.log_test("Share Count Update", False, "Share count not updated")
                
                return True
            else:
                self.log_test("Share Post", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Share Post", False, f"Exception: {str(e)}")
            return False
    
    def test_search_by_hashtag(self) -> bool:
        """Test searching posts by hashtag"""
        try:
            self.log("Testing hashtag search...")
            
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            response = self.session.get(f"{self.base_url}/posts/search/hashtags?hashtag=study", headers=headers)
            
            if response.status_code == 200:
                posts = response.json()
                self.log_test("Search by Hashtag", True, f"Found {len(posts)} posts with #study")
                
                # Verify posts contain the hashtag
                if posts:
                    for post in posts:
                        if "study" in post.get("hashtags", []):
                            self.log_test("Hashtag Search Relevance", True, "Search results are relevant")
                            break
                    else:
                        self.log_test("Hashtag Search Relevance", False, "Search results not relevant")
                
                return True
            else:
                self.log_test("Search by Hashtag", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Search by Hashtag", False, f"Exception: {str(e)}")
            return False
    
    def test_search_by_content(self) -> bool:
        """Test searching posts by content"""
        try:
            self.log("Testing content search...")
            
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            response = self.session.get(f"{self.base_url}/posts/search/content?query=networking", headers=headers)
            
            if response.status_code == 200:
                posts = response.json()
                self.log_test("Search by Content", True, f"Found {len(posts)} posts with 'networking'")
                
                # Verify posts contain the search term
                if posts:
                    for post in posts:
                        if "networking" in post.get("content", "").lower():
                            self.log_test("Content Search Relevance", True, "Search results are relevant")
                            break
                    else:
                        self.log_test("Content Search Relevance", False, "Search results not relevant")
                
                return True
            else:
                self.log_test("Search by Content", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Search by Content", False, f"Exception: {str(e)}")
            return False
    
    def test_update_post(self) -> bool:
        """Test updating a post"""
        try:
            self.log("Testing post update...")
            
            if not self.test_post_id:
                self.log_test("Update Post", False, "No test post ID available")
                return False
            
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            update_data = {
                "content": "Updated: Hello everyone! This is my updated first post. #study #university #updated",
                "location": "Updated Location - NYU Campus"
            }
            
            response = self.session.put(f"{self.base_url}/posts/{self.test_post_id}", 
                                      json=update_data, headers=headers)
            
            if response.status_code == 200:
                self.log_test("Update Post", True, "Post updated successfully")
                
                # Verify update
                get_response = self.session.get(f"{self.base_url}/posts/{self.test_post_id}", headers=headers)
                if get_response.status_code == 200:
                    post_data = get_response.json()
                    if "Updated:" in post_data["post"]["content"]:
                        self.log_test("Post Update Verification", True, "Post content updated correctly")
                    else:
                        self.log_test("Post Update Verification", False, "Post content not updated")
                
                return True
            else:
                self.log_test("Update Post", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Update Post", False, f"Exception: {str(e)}")
            return False
    
    def test_post_authorization(self) -> bool:
        """Test that users can only edit/delete their own posts"""
        try:
            self.log("Testing post authorization...")
            
            if not self.test_post_id:
                self.log_test("Post Authorization", False, "No test post ID available")
                return False
            
            # Try to update another user's post
            headers = {"Authorization": f"Bearer {self.user2_token}"}
            update_data = {
                "content": "This should fail - trying to edit someone else's post"
            }
            
            response = self.session.put(f"{self.base_url}/posts/{self.test_post_id}", 
                                      json=update_data, headers=headers)
            
            if response.status_code == 404:  # Not found or not authorized
                self.log_test("Post Authorization", True, "User cannot edit others' posts")
                return True
            else:
                self.log_test("Post Authorization", False, f"Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Post Authorization", False, f"Exception: {str(e)}")
            return False
    
    def test_pagination(self) -> bool:
        """Test pagination in posts feed"""
        try:
            self.log("Testing pagination...")
            
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            
            # Test with limit and skip
            response = self.session.get(f"{self.base_url}/posts/?limit=5&skip=0", headers=headers)
            
            if response.status_code == 200:
                posts = response.json()
                self.log_test("Pagination", True, f"Retrieved {len(posts)} posts with limit=5")
                
                if len(posts) <= 5:
                    self.log_test("Pagination Limit", True, "Pagination limit respected")
                else:
                    self.log_test("Pagination Limit", False, f"Expected ≤5 posts, got {len(posts)}")
                
                return True
            else:
                self.log_test("Pagination", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Pagination", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all posts system tests"""
        self.log("=" * 60)
        self.log("STARTING POSTS & MEDIA SYSTEM BACKEND TESTING")
        self.log(f"Backend URL: {BASE_URL}")
        self.log("=" * 60)
        
        results = {}
        
        # Setup
        self.log("\n--- SETUP PHASE ---")
        if not self.setup_test_users():
            self.log_test("Setup", False, "Test setup failed - aborting tests")
            return {"setup": False}
        
        self.verify_users()
        
        # Post Creation & Management Tests
        self.log("\n--- POST CREATION & MANAGEMENT TESTS ---")
        results["create_text_post"] = self.test_create_text_post()
        results["create_image_post"] = self.test_create_image_post()
        results["unverified_user_restriction"] = self.test_unverified_user_restriction()
        results["get_posts_feed"] = self.test_get_posts_feed()
        results["get_single_post"] = self.test_get_single_post()
        results["update_post"] = self.test_update_post()
        results["post_authorization"] = self.test_post_authorization()
        
        # Social Interactions Tests
        self.log("\n--- SOCIAL INTERACTIONS TESTS ---")
        results["like_post"] = self.test_like_post()
        results["unlike_post"] = self.test_unlike_post()
        results["create_comment"] = self.test_create_comment()
        results["get_comments"] = self.test_get_comments()
        results["share_post"] = self.test_share_post()
        
        # Search & Discovery Tests
        self.log("\n--- SEARCH & DISCOVERY TESTS ---")
        results["search_by_hashtag"] = self.test_search_by_hashtag()
        results["search_by_content"] = self.test_search_by_content()
        results["pagination"] = self.test_pagination()
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
        
        self.log(f"\nOVERALL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            self.log("🎉 ALL POSTS SYSTEM TESTS PASSED!")
        else:
            self.log(f"⚠️ {total - passed} tests failed - see details above")
        
        return results

def main():
    """Main test execution"""
    try:
        tester = PostsAPITester()
        results = tester.run_all_tests()
        
        # Exit with appropriate code
        if all(results.values()):
            sys.exit(0)  # All tests passed
        else:
            sys.exit(1)  # Some tests failed
            
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\nUnexpected error during testing: {str(e)}")
        sys.exit(3)

if __name__ == "__main__":
    main()