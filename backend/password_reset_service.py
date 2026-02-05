"""
Password Reset Service for StudyConnect
Handles password reset token generation, validation, and email sending
"""

import os
from typing import Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
import requests

# Load environment variables
load_dotenv()

from password_reset_models import (
    PasswordResetToken, PasswordResetRequest, PasswordResetConfirm,
    generate_reset_token, verify_reset_token,
    RESET_TOKEN_EXPIRY_HOURS, MAX_RESET_ATTEMPTS_PER_DAY, RESET_COOLDOWN_MINUTES
)
import motor.motor_asyncio
from passlib.context import CryptContext

# MongoDB connection
client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"))
db = client[os.getenv("DB_NAME", "test_database")]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PasswordResetService:
    def __init__(self):
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@studyconnect.com')
        self.app_url = os.getenv('APP_URL', 'https://studyconnect.com')
        
    async def initiate_password_reset(self, email: str, ip_address: str = None, user_agent: str = None) -> dict:
        """Initiate password reset process"""
        try:
            # Find user by email
            user_doc = await db.users.find_one({"email": email})
            if not user_doc:
                # Don't reveal if email exists or not for security
                return {
                    "success": True,
                    "message": "If an account with that email exists, you will receive a password reset link."
                }
            
            # Check rate limiting
            rate_limit_check = await self._check_rate_limits(email)
            if not rate_limit_check["allowed"]:
                return {
                    "success": False,
                    "message": rate_limit_check["message"]
                }
            
            # Generate reset token
            token, token_hash = generate_reset_token()
            expires_at = datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRY_HOURS)
            
            # Create reset token record
            reset_token = PasswordResetToken(
                user_id=user_doc["id"],
                email=email,
                token=token,  # Store plain token temporarily for email
                token_hash=token_hash,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Store in database (without plain token)
            token_data = reset_token.dict()
            del token_data["token"]  # Remove plain token before storage
            await db.password_reset_tokens.insert_one(token_data)
            
            # Send reset email
            email_sent = await self._send_reset_email(
                email=email,
                name=f"{user_doc['first_name']} {user_doc['last_name']}",
                reset_token=token,
                token_id=reset_token.id
            )
            
            if email_sent:
                logger.info(f"Password reset email sent to {email}")
                return {
                    "success": True,
                    "message": "Password reset link has been sent to your email address.",
                    "token_id": reset_token.id  # For tracking
                }
            else:
                # Clean up token if email failed
                await db.password_reset_tokens.delete_one({"id": reset_token.id})
                return {
                    "success": False,
                    "message": "Failed to send password reset email. Please try again later."
                }
                
        except Exception as e:
            logger.error(f"Error initiating password reset: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred. Please try again later."
            }
    
    async def reset_password(self, token: str, new_password: str) -> dict:
        """Reset password using token"""
        try:
            # Find token record
            token_doc = await db.password_reset_tokens.find_one({
                "is_used": False,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not token_doc:
                return {
                    "success": False,
                    "message": "Invalid or expired reset token."
                }
            
            # Verify token hash
            if not verify_reset_token(token, token_doc["token_hash"]):
                return {
                    "success": False,
                    "message": "Invalid reset token."
                }
            
            # Find user
            user_doc = await db.users.find_one({"id": token_doc["user_id"]})
            if not user_doc:
                return {
                    "success": False,
                    "message": "User account not found."
                }
            
            # Hash new password
            hashed_password = pwd_context.hash(new_password)
            
            # Update user password
            await db.users.update_one(
                {"id": token_doc["user_id"]},
                {
                    "$set": {
                        "password": hashed_password,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Mark token as used
            await db.password_reset_tokens.update_one(
                {"id": token_doc["id"]},
                {
                    "$set": {
                        "is_used": True,
                        "used_at": datetime.utcnow()
                    }
                }
            )
            
            # Invalidate all other reset tokens for this user
            await db.password_reset_tokens.update_many(
                {
                    "user_id": token_doc["user_id"],
                    "is_used": False,
                    "id": {"$ne": token_doc["id"]}
                },
                {
                    "$set": {
                        "is_used": True,
                        "used_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Password reset successful for user {user_doc['email']}")
            
            return {
                "success": True,
                "message": "Password has been reset successfully. You can now log in with your new password."
            }
            
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while resetting password. Please try again."
            }
    
    async def verify_reset_token(self, token: str) -> dict:
        """Verify if reset token is valid"""
        try:
            # Find token record
            token_docs = await db.password_reset_tokens.find({
                "is_used": False,
                "expires_at": {"$gt": datetime.utcnow()}
            }).to_list(100)
            
            # Check each token (since we can't query by hash directly)
            for token_doc in token_docs:
                if verify_reset_token(token, token_doc["token_hash"]):
                    # Get user info
                    user_doc = await db.users.find_one({"id": token_doc["user_id"]})
                    if user_doc:
                        return {
                            "valid": True,
                            "email": user_doc["email"],
                            "expires_at": token_doc["expires_at"].isoformat()
                        }
            
            return {
                "valid": False,
                "message": "Invalid or expired reset token."
            }
            
        except Exception as e:
            logger.error(f"Error verifying reset token: {str(e)}")
            return {
                "valid": False,
                "message": "Error verifying token."
            }
    
    async def _check_rate_limits(self, email: str) -> dict:
        """Check rate limiting for password reset requests"""
        try:
            # Check requests in last 24 hours
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_requests = await db.password_reset_tokens.count_documents({
                "email": email,
                "created_at": {"$gt": yesterday}
            })
            
            if recent_requests >= MAX_RESET_ATTEMPTS_PER_DAY:
                return {
                    "allowed": False,
                    "message": f"Too many password reset requests. Please wait 24 hours before requesting another reset."
                }
            
            # Check cooldown period
            cooldown_time = datetime.utcnow() - timedelta(minutes=RESET_COOLDOWN_MINUTES)
            recent_request = await db.password_reset_tokens.find_one({
                "email": email,
                "created_at": {"$gt": cooldown_time}
            })
            
            if recent_request:
                return {
                    "allowed": False,
                    "message": f"Please wait {RESET_COOLDOWN_MINUTES} minutes before requesting another password reset."
                }
            
            return {"allowed": True}
            
        except Exception as e:
            logger.error(f"Error checking rate limits: {str(e)}")
            return {"allowed": True}  # Allow on error to not block legitimate requests
    
    async def _send_reset_email(self, email: str, name: str, reset_token: str, token_id: str) -> bool:
        """Send password reset email"""
        try:
            # Create reset URL
            reset_url = f"{self.app_url}/auth/reset-password?token={reset_token}"
            
            # For development, log the reset URL
            logger.info(f"Password reset URL for {email}: {reset_url}")
            
            # Email subject and content
            subject = "Reset Your StudyConnect Password"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Reset Your Password</title>
            </head>
            <body style="margin: 0; padding: 0; background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 40px 30px;">
                    <div style="text-align: center; margin-bottom: 40px;">
                        <div style="background-color: #6c5ce7; color: white; width: 60px; height: 60px; border-radius: 30px; display: inline-flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold;">S</div>
                        <h1 style="color: #1a1a2e; margin-top: 20px; margin-bottom: 10px;">StudyConnect</h1>
                        <p style="color: #666; margin: 0;">Connect. Study. Succeed.</p>
                    </div>
                    
                    <div style="background-color: #fff3cd; padding: 30px; border-radius: 12px; border-left: 4px solid #ffc107; margin-bottom: 30px;">
                        <h2 style="color: #1a1a2e; margin-top: 0; margin-bottom: 20px;">🔐 Password Reset Request</h2>
                        <p style="color: #333; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
                            Hi {name},
                        </p>
                        <p style="color: #333; font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                            You recently requested to reset your password for your StudyConnect account. 
                            Click the button below to reset it. This link will expire in {RESET_TOKEN_EXPIRY_HOURS} hour(s).
                        </p>
                        <div style="text-align: center; margin-bottom: 30px;">
                            <a href="{reset_url}" style="background-color: #6c5ce7; color: white; padding: 15px 30px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold; font-size: 16px;">
                                Reset Your Password
                            </a>
                        </div>
                        <p style="color: #666; font-size: 14px; line-height: 1.6;">
                            If you didn't request this password reset, please ignore this email or contact our support team if you have concerns.
                        </p>
                    </div>
                    
                    <div style="background-color: #f8f9ff; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
                        <h3 style="color: #1a1a2e; margin-top: 0; margin-bottom: 15px;">Security Tips:</h3>
                        <ul style="color: #666; font-size: 14px; line-height: 1.6; margin: 0; padding-left: 20px;">
                            <li>Use a strong, unique password</li>
                            <li>Don't share your password with anyone</li>
                            <li>Enable two-factor authentication when available</li>
                            <li>Log out from shared or public computers</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; padding-top: 30px; border-top: 1px solid #eee;">
                        <p style="color: #666; font-size: 12px; margin-bottom: 10px;">
                            This password reset link will expire in {RESET_TOKEN_EXPIRY_HOURS} hour(s) for your security.
                        </p>
                        <p style="color: #666; font-size: 12px;">
                            If you're having trouble clicking the button, copy and paste this URL into your browser:<br>
                            <span style="color: #6c5ce7; word-break: break-all;">{reset_url}</span>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Reset Your StudyConnect Password
            
            Hi {name},
            
            You recently requested to reset your password for your StudyConnect account.
            
            Click the link below to reset your password (expires in {RESET_TOKEN_EXPIRY_HOURS} hour(s)):
            {reset_url}
            
            If you didn't request this password reset, please ignore this email or contact our support team.
            
            Security Tips:
            - Use a strong, unique password
            - Don't share your password with anyone
            - Log out from shared or public computers
            
            ---
            StudyConnect Team
            """
            
            # Try to send via SendGrid if configured
            if self.sendgrid_api_key:
                try:
                    from sendgrid import SendGridAPIClient
                    from sendgrid.helpers.mail import Mail, Email, To, Content
                    
                    sg = SendGridAPIClient(api_key=self.sendgrid_api_key)
                    mail = Mail(
                        from_email=Email(self.from_email, "StudyConnect"),
                        to_emails=To(email),
                        subject=subject,
                        html_content=Content("text/html", html_content),
                        plain_text_content=Content("text/plain", text_content)
                    )
                    
                    response = sg.send(mail)
                    
                    if response.status_code in [200, 202]:
                        logger.info(f"Password reset email sent successfully to {email}")
                        return True
                    else:
                        logger.error(f"SendGrid error: {response.body}")
                        return False
                        
                except Exception as e:
                    logger.error(f"SendGrid email error: {str(e)}")
                    return False
            else:
                # For development - just log the email content
                logger.info(f"SendGrid not configured. Password reset email for {email}:")
                logger.info(f"Subject: {subject}")
                logger.info(f"Reset URL: {reset_url}")
                return True  # Consider it "sent" for development
                
        except Exception as e:
            logger.error(f"Error sending reset email: {str(e)}")
            return False
    
    async def cleanup_expired_tokens(self):
        """Clean up expired reset tokens (can be run as a cron job)"""
        try:
            result = await db.password_reset_tokens.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} expired reset tokens")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {str(e)}")

# Export singleton instance
password_reset_service = PasswordResetService()