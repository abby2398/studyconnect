#!/usr/bin/env python3
"""
Script to verify test users for posts testing
"""

import requests
import json

BASE_URL = "https://password-reset-39.preview.emergentagent.com/api"

def verify_user(token, user_name):
    """Verify a user with the given token"""
    try:
        response = requests.post(f"{BASE_URL}/auth/verify-email", params={"token": token})
        
        if response.status_code == 200:
            print(f"✅ {user_name} verified successfully")
            return True
        else:
            print(f"❌ Failed to verify {user_name}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error verifying {user_name}: {str(e)}")
        return False

def main():
    print("Verifying test users...")
    
    # Tokens from backend logs
    sarah_token = "JO2frIp1SfmRtzHgM-vCdBGXLnmeA1YJJqtJv5swOYs"
    mike_token = "8TODkPElFzWDv0QhLMv-MNGF7GSnet3NfhhzgJsLxPI"
    
    # Verify both users
    sarah_verified = verify_user(sarah_token, "Sarah Johnson")
    mike_verified = verify_user(mike_token, "Mike Chen")
    
    if sarah_verified and mike_verified:
        print("\n🎉 Both users verified successfully! Ready for posts testing.")
    else:
        print("\n⚠️ Some users could not be verified.")

if __name__ == "__main__":
    main()