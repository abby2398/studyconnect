"""
Password Reset Models for StudyConnect
Handles password reset tokens and validation
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import uuid
import secrets
import hashlib

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetToken(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email: str
    token: str
    token_hash: str  # Hashed version of token for security
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    used_at: Optional[datetime] = None
    is_used: bool = False
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)

class PasswordResetResponse(BaseModel):
    message: str
    reset_token_id: Optional[str] = None  # For tracking purposes

def generate_reset_token() -> tuple[str, str]:
    """Generate a secure reset token and its hash"""
    # Generate a secure random token
    token = secrets.token_urlsafe(32)  # 32 bytes = 256 bits of randomness
    
    # Create hash for storage (more secure than storing plain token)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    return token, token_hash

def verify_reset_token(token: str, stored_hash: str) -> bool:
    """Verify that a token matches the stored hash"""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token_hash == stored_hash

# Password reset configuration
RESET_TOKEN_EXPIRY_HOURS = 1  # Token expires in 1 hour
MAX_RESET_ATTEMPTS_PER_DAY = 3  # Maximum reset requests per email per day
RESET_COOLDOWN_MINUTES = 5  # Minimum time between reset requests