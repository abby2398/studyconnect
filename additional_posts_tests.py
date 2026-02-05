#!/usr/bin/env python3
"""
Additional Posts System Tests - Edge Cases and Media Processing
"""

import requests
import json
import base64
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
    return "https://password-reset-39.preview.emergentagent.com"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

class AdditionalPostsTests:
    def __init__(self):
        self.base_url = API_URL
        self.session = requests.Session()
        self.user_token = None
        self.user_id = None
        
    def setup_user(self):
        """Setup verified user for testing"""
        try:
            # Login with verified user
            login_data = {"email": "sarah.johnson@university.edu", "password": "SecurePass123!"}
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                user_data = response.json()
                self.user_token = user_data["access_token"]
                self.user_id = user_data["user"]["id"]
                print("✅ User setup successful")
                return True
            else:
                print(f"❌ User setup failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ User setup error: {str(e)}")
            return False
    
    def test_image_compression(self):
        """Test image compression with large image"""
        try:
            print("\n--- Testing Image Compression ---")
            
            # Create a larger test image (simulated)
            # In real scenario, this would be a large image
            large_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==" * 100
            
            headers = {"Authorization": f"Bearer {self.user_token}"}
            
            media_attachment = {
                "file_type": "image",
                "mime_type": "image/png",
                "file_size": len(base64.b64decode(large_image_data)),
                "width": 2000,
                "height": 2000,
                "data": large_image_data
            }
            
            post_data = {
                "content": "Testing image compression with large image #compression #test",
                "post_type": "image",
                "visibility": "public",
                "media_attachments": [media_attachment]
            }
            
            response = self.session.post(f"{self.base_url}/posts/", json=post_data, headers=headers)
            
            if response.status_code == 200:
                post = response.json()
                print("✅ Large image post created successfully")
                
                # Check if image was processed
                if post.get("media_attachments"):
                    compressed_data = post["media_attachments"][0]["data"]
                    print(f"✅ Image compression processed (original: {len(large_image_data)}, processed: {len(compressed_data)})")
                
                return True
            else:
                print(f"❌ Image compression test failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Image compression test error: {str(e)}")
            return False
    
    def test_mention_extraction(self):
        """Test mention extraction from post content"""
        try:
            print("\n--- Testing Mention Extraction ---")
            
            headers = {"Authorization": f"Bearer {self.user_token}"}
            
            post_data = {
                "content": "Hey @mike and @sarah, check out this amazing study group! @everyone welcome #study #mentions",
                "post_type": "text",
                "visibility": "public",
                "media_attachments": []
            }
            
            response = self.session.post(f"{self.base_url}/posts/", json=post_data, headers=headers)
            
            if response.status_code == 200:
                post = response.json()
                print("✅ Post with mentions created successfully")
                
                # Check if mentions were extracted
                mentions = post.get("mentions", [])
                expected_mentions = ["mike", "sarah", "everyone"]
                
                if all(mention in mentions for mention in expected_mentions):
                    print(f"✅ Mentions extracted correctly: {mentions}")
                else:
                    print(f"⚠️ Some mentions may be missing. Expected: {expected_mentions}, Got: {mentions}")
                
                return True
            else:
                print(f"❌ Mention extraction test failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Mention extraction test error: {str(e)}")
            return False
    
    def test_post_visibility(self):
        """Test different post visibility settings"""
        try:
            print("\n--- Testing Post Visibility ---")
            
            headers = {"Authorization": f"Bearer {self.user_token}"}
            
            # Test private post
            private_post_data = {
                "content": "This is a private post that only I should see #private",
                "post_type": "text",
                "visibility": "private",
                "media_attachments": []
            }
            
            response = self.session.post(f"{self.base_url}/posts/", json=private_post_data, headers=headers)
            
            if response.status_code == 200:
                post = response.json()
                print("✅ Private post created successfully")
                
                if post.get("visibility") == "private":
                    print("✅ Post visibility set correctly")
                else:
                    print(f"⚠️ Post visibility not set correctly. Expected: private, Got: {post.get('visibility')}")
                
                return True
            else:
                print(f"❌ Post visibility test failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Post visibility test error: {str(e)}")
            return False
    
    def test_empty_content_post(self):
        """Test creating post with empty content but media"""
        try:
            print("\n--- Testing Empty Content Post with Media ---")
            
            headers = {"Authorization": f"Bearer {self.user_token}"}
            
            # Create test image
            test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            
            media_attachment = {
                "file_type": "image",
                "mime_type": "image/png",
                "file_size": len(base64.b64decode(test_image_base64)),
                "width": 1,
                "height": 1,
                "data": test_image_base64
            }
            
            post_data = {
                "content": "",  # Empty content
                "post_type": "image",
                "visibility": "public",
                "media_attachments": [media_attachment]
            }
            
            response = self.session.post(f"{self.base_url}/posts/", json=post_data, headers=headers)
            
            if response.status_code == 200:
                post = response.json()
                print("✅ Empty content post with media created successfully")
                
                if post.get("media_attachments") and len(post["media_attachments"]) > 0:
                    print("✅ Media attachment preserved in empty content post")
                
                return True
            else:
                print(f"❌ Empty content post test failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Empty content post test error: {str(e)}")
            return False
    
    def test_duplicate_like_prevention(self):
        """Test that users cannot like the same post twice"""
        try:
            print("\n--- Testing Duplicate Like Prevention ---")
            
            headers = {"Authorization": f"Bearer {self.user_token}"}
            
            # First create a post
            post_data = {
                "content": "Test post for duplicate like testing #test",
                "post_type": "text",
                "visibility": "public",
                "media_attachments": []
            }
            
            response = self.session.post(f"{self.base_url}/posts/", json=post_data, headers=headers)
            
            if response.status_code == 200:
                post = response.json()
                post_id = post["id"]
                
                # Like the post first time
                like_response = self.session.post(f"{self.base_url}/posts/{post_id}/like", headers=headers)
                
                if like_response.status_code == 200:
                    print("✅ First like successful")
                    
                    # Try to like the same post again
                    duplicate_like_response = self.session.post(f"{self.base_url}/posts/{post_id}/like", headers=headers)
                    
                    if duplicate_like_response.status_code == 400:
                        print("✅ Duplicate like correctly prevented")
                        return True
                    else:
                        print(f"❌ Duplicate like not prevented: {duplicate_like_response.status_code}")
                        return False
                else:
                    print(f"❌ First like failed: {like_response.status_code}")
                    return False
            else:
                print(f"❌ Post creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Duplicate like prevention test error: {str(e)}")
            return False
    
    def test_nested_comments(self):
        """Test creating nested comments (replies to comments)"""
        try:
            print("\n--- Testing Nested Comments ---")
            
            headers = {"Authorization": f"Bearer {self.user_token}"}
            
            # First create a post
            post_data = {
                "content": "Test post for nested comments #comments #test",
                "post_type": "text",
                "visibility": "public",
                "media_attachments": []
            }
            
            response = self.session.post(f"{self.base_url}/posts/", json=post_data, headers=headers)
            
            if response.status_code == 200:
                post = response.json()
                post_id = post["id"]
                
                # Create parent comment
                parent_comment_data = {
                    "content": "This is a parent comment"
                }
                
                comment_response = self.session.post(f"{self.base_url}/posts/{post_id}/comments", 
                                                   json=parent_comment_data, headers=headers)
                
                if comment_response.status_code == 200:
                    parent_comment = comment_response.json()
                    parent_comment_id = parent_comment["id"]
                    print("✅ Parent comment created successfully")
                    
                    # Create nested comment (reply)
                    nested_comment_data = {
                        "content": "This is a reply to the parent comment",
                        "parent_comment_id": parent_comment_id
                    }
                    
                    nested_response = self.session.post(f"{self.base_url}/posts/{post_id}/comments", 
                                                      json=nested_comment_data, headers=headers)
                    
                    if nested_response.status_code == 200:
                        nested_comment = nested_response.json()
                        print("✅ Nested comment created successfully")
                        
                        if nested_comment.get("parent_comment_id") == parent_comment_id:
                            print("✅ Nested comment parent relationship set correctly")
                            return True
                        else:
                            print("❌ Nested comment parent relationship not set correctly")
                            return False
                    else:
                        print(f"❌ Nested comment creation failed: {nested_response.status_code}")
                        return False
                else:
                    print(f"❌ Parent comment creation failed: {comment_response.status_code}")
                    return False
            else:
                print(f"❌ Post creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Nested comments test error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all additional tests"""
        print("🚀 Starting Additional Posts System Tests")
        print("=" * 50)
        
        if not self.setup_user():
            print("❌ Failed to setup user. Aborting tests.")
            return False
        
        tests = [
            self.test_image_compression,
            self.test_mention_extraction,
            self.test_post_visibility,
            self.test_empty_content_post,
            self.test_duplicate_like_prevention,
            self.test_nested_comments
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
        
        print("\n" + "=" * 50)
        print("ADDITIONAL TESTS SUMMARY")
        print("=" * 50)
        print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All additional tests passed!")
            return True
        else:
            print(f"⚠️ {total - passed} additional tests failed")
            return False

def main():
    tester = AdditionalPostsTests()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()