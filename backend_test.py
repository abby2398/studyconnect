#!/usr/bin/env python3
"""
Backend Testing Suite for International Student Networking App
Testing Password Reset System (MOCK MODE)
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
import time

# Get backend URL from environment
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://password-reset-39.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class PasswordResetTester:
    def __init__(self):
        self.session = None
        import time
        timestamp = str(int(time.time()))
        self.test_user_email = f"testuser{timestamp}@university.edu"
        self.test_user_password = "TestPassword123"
        self.new_password = "NewPassword456"
        self.reset_token = None
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name, success, message="", details=None):
        """Log test result"""
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
        
    async def register_test_user(self):
        """Register a test user for password reset testing"""
        try:
            user_data = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "first_name": "Test",
                "last_name": "User",
                "phone": "+1234567890"
            }
            
            async with self.session.post(f"{API_BASE}/auth/register", json=user_data) as response:
                if response.status == 200:
                    self.log_test("User Registration", True, "Test user registered successfully")
                    return True
                elif response.status == 400:
                    # User might already exist
                    response_data = await response.json()
                    if "already registered" in response_data.get("detail", ""):
                        self.log_test("User Registration", True, "Test user already exists")
                        return True
                    else:
                        self.log_test("User Registration", False, f"Registration failed: {response_data.get('detail')}")
                        return False
                else:
                    self.log_test("User Registration", False, f"Registration failed with status {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
            return False
            
    async def test_forgot_password_existing_user(self):
        """Test forgot password with existing user email"""
        try:
            request_data = {"email": self.test_user_email}
            
            async with self.session.post(f"{API_BASE}/auth/forgot-password", json=request_data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    
                    # Check for mock mode response
                    if response_data.get("mock_mode"):
                        self.reset_token = response_data.get("reset_token")
                        self.log_test("Forgot Password (Existing User)", True, 
                                    f"Mock mode active, reset token received: {self.reset_token[:10]}...")
                        return True
                    else:
                        self.log_test("Forgot Password (Existing User)", False, 
                                    "Expected mock_mode=true in response")
                        return False
                else:
                    response_data = await response.json()
                    self.log_test("Forgot Password (Existing User)", False, 
                                f"Request failed: {response_data.get('detail')}")
                    return False
                    
        except Exception as e:
            self.log_test("Forgot Password (Existing User)", False, f"Exception: {str(e)}")
            return False
            
    async def test_forgot_password_nonexistent_user(self):
        """Test forgot password with non-existent user email"""
        try:
            request_data = {"email": "nonexistent@university.edu"}
            
            async with self.session.post(f"{API_BASE}/auth/forgot-password", json=request_data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    # Should still return success for security (don't reveal if email exists)
                    self.log_test("Forgot Password (Non-existent User)", True, 
                                "Security: Returns success even for non-existent email")
                    return True
                else:
                    response_data = await response.json()
                    self.log_test("Forgot Password (Non-existent User)", False, 
                                f"Unexpected error: {response_data.get('detail')}")
                    return False
                    
        except Exception as e:
            self.log_test("Forgot Password (Non-existent User)", False, f"Exception: {str(e)}")
            return False
            
    async def test_rate_limiting(self):
        """Test rate limiting - 5 minute cooldown between requests"""
        try:
            # First request
            request_data = {"email": "ratelimit@university.edu"}
            
            async with self.session.post(f"{API_BASE}/auth/forgot-password", json=request_data) as response:
                if response.status != 200:
                    self.log_test("Rate Limiting Setup", False, "Failed to send first request")
                    return False
            
            # Immediate second request (should be rate limited)
            async with self.session.post(f"{API_BASE}/auth/forgot-password", json=request_data) as response:
                if response.status == 400:
                    response_data = await response.json()
                    if "wait" in response_data.get("detail", "").lower():
                        self.log_test("Rate Limiting", True, 
                                    "Rate limiting working - second request blocked")
                        return True
                    else:
                        self.log_test("Rate Limiting", False, 
                                    f"Expected rate limit message, got: {response_data.get('detail')}")
                        return False
                else:
                    self.log_test("Rate Limiting", False, 
                                f"Expected 400 status for rate limit, got {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test("Rate Limiting", False, f"Exception: {str(e)}")
            return False
            
    async def test_verify_reset_token_valid(self):
        """Test verifying a valid reset token"""
        if not self.reset_token:
            self.log_test("Verify Reset Token (Valid)", False, "No reset token available from previous test")
            return False
            
        try:
            async with self.session.get(f"{API_BASE}/auth/verify-reset-token/{self.reset_token}") as response:
                if response.status == 200:
                    response_data = await response.json()
                    
                    if (response_data.get("valid") and 
                        response_data.get("email") == self.test_user_email and
                        response_data.get("expires_at")):
                        self.log_test("Verify Reset Token (Valid)", True, 
                                    f"Token valid for email: {response_data.get('email')}")
                        return True
                    else:
                        self.log_test("Verify Reset Token (Valid)", False, 
                                    f"Invalid response structure: {response_data}")
                        return False
                else:
                    response_data = await response.json()
                    self.log_test("Verify Reset Token (Valid)", False, 
                                f"Token verification failed: {response_data.get('detail')}")
                    return False
                    
        except Exception as e:
            self.log_test("Verify Reset Token (Valid)", False, f"Exception: {str(e)}")
            return False
            
    async def test_verify_reset_token_invalid(self):
        """Test verifying an invalid reset token"""
        try:
            invalid_token = "invalid_token_12345"
            
            async with self.session.get(f"{API_BASE}/auth/verify-reset-token/{invalid_token}") as response:
                if response.status == 400:
                    response_data = await response.json()
                    self.log_test("Verify Reset Token (Invalid)", True, 
                                "Invalid token properly rejected")
                    return True
                else:
                    self.log_test("Verify Reset Token (Invalid)", False, 
                                f"Expected 400 status for invalid token, got {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test("Verify Reset Token (Invalid)", False, f"Exception: {str(e)}")
            return False
            
    async def test_reset_password_valid_token(self):
        """Test resetting password with valid token"""
        if not self.reset_token:
            self.log_test("Reset Password (Valid Token)", False, "No reset token available")
            return False
            
        try:
            reset_data = {
                "token": self.reset_token,
                "new_password": self.new_password
            }
            
            async with self.session.post(f"{API_BASE}/auth/reset-password", json=reset_data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    self.log_test("Reset Password (Valid Token)", True, 
                                "Password reset successful")
                    return True
                else:
                    response_data = await response.json()
                    self.log_test("Reset Password (Valid Token)", False, 
                                f"Password reset failed: {response_data.get('detail')}")
                    return False
                    
        except Exception as e:
            self.log_test("Reset Password (Valid Token)", False, f"Exception: {str(e)}")
            return False
            
    async def test_token_invalidated_after_use(self):
        """Test that token is invalidated after successful password reset"""
        if not self.reset_token:
            self.log_test("Token Invalidation After Use", False, "No reset token available")
            return False
            
        try:
            # Try to verify the token again (should be invalid now)
            async with self.session.get(f"{API_BASE}/auth/verify-reset-token/{self.reset_token}") as response:
                if response.status == 400:
                    self.log_test("Token Invalidation After Use", True, 
                                "Token properly invalidated after use")
                    return True
                else:
                    self.log_test("Token Invalidation After Use", False, 
                                f"Token still valid after use (status: {response.status})")
                    return False
                    
        except Exception as e:
            self.log_test("Token Invalidation After Use", False, f"Exception: {str(e)}")
            return False
            
    async def test_login_with_new_password(self):
        """Test login with new password after reset"""
        try:
            login_data = {
                "email": self.test_user_email,
                "password": self.new_password
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("access_token"):
                        self.log_test("Login with New Password", True, 
                                    "Login successful with new password")
                        return True
                    else:
                        self.log_test("Login with New Password", False, 
                                    "No access token in response")
                        return False
                else:
                    response_data = await response.json()
                    self.log_test("Login with New Password", False, 
                                f"Login failed: {response_data.get('detail')}")
                    return False
                    
        except Exception as e:
            self.log_test("Login with New Password", False, f"Exception: {str(e)}")
            return False
            
    async def test_login_with_old_password(self):
        """Test that login with old password fails"""
        try:
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password  # Old password
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 401:
                    self.log_test("Login with Old Password", True, 
                                "Old password properly rejected")
                    return True
                else:
                    self.log_test("Login with Old Password", False, 
                                f"Expected 401 for old password, got {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test("Login with Old Password", False, f"Exception: {str(e)}")
            return False
            
    async def test_password_validation(self):
        """Test password validation (minimum 8 characters)"""
        # Need a fresh token for this test
        await self.test_forgot_password_existing_user()
            
        try:
            reset_data = {
                "token": self.reset_token,
                "new_password": "short"  # Too short
            }
            
            async with self.session.post(f"{API_BASE}/auth/reset-password", json=reset_data) as response:
                if response.status == 422:  # Validation error
                    self.log_test("Password Validation", True, 
                                "Short password properly rejected")
                    return True
                else:
                    self.log_test("Password Validation", False, 
                                f"Expected 422 for short password, got {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test("Password Validation", False, f"Exception: {str(e)}")
            return False
            
    async def run_all_tests(self):
        """Run all password reset tests"""
        print("🔐 Starting Password Reset System Tests (MOCK MODE)")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Test sequence
            await self.register_test_user()
            await self.test_forgot_password_existing_user()
            await self.test_forgot_password_nonexistent_user()
            await self.test_rate_limiting()
            await self.test_verify_reset_token_valid()
            await self.test_verify_reset_token_invalid()
            await self.test_reset_password_valid_token()
            await self.test_token_invalidated_after_use()
            await self.test_login_with_new_password()
            await self.test_login_with_old_password()
            await self.test_password_validation()
            
        finally:
            await self.cleanup_session()
            
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🚨 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
                    
        return passed_tests, failed_tests

async def main():
    """Main test runner"""
    tester = PasswordResetTester()
    passed, failed = await tester.run_all_tests()
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Password Reset System is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the implementation.")
        
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)