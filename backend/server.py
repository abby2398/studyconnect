from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Form, File, UploadFile, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any, Set
import uuid
from datetime import datetime, timedelta
import bcrypt
import jwt
from email_validator import validate_email, EmailNotValidError
import re
import base64
import json
import secrets
import asyncio
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import socketio
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-this')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 1 week

# Security
security = HTTPBearer()

# Socket.IO Server
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Chat Models
class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    FILE = "file"
    SYSTEM = "system"

class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"

class FileAttachment(BaseModel):
    filename: str
    file_size: int
    file_type: str
    file_data: str  # base64 encoded

class VoiceMessage(BaseModel):
    duration: float  # in seconds
    audio_data: str  # base64 encoded audio

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    sender_id: str
    message_type: MessageType = MessageType.TEXT
    content: Optional[str] = None
    file_attachment: Optional[FileAttachment] = None
    voice_message: Optional[VoiceMessage] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: MessageStatus = MessageStatus.SENT
    read_by: List[str] = Field(default_factory=list)  # List of user IDs who read the message
    reply_to_id: Optional[str] = None  # For message replies
    edited_at: Optional[datetime] = None
    is_deleted: bool = False

class MessageCreate(BaseModel):
    conversation_id: str
    message_type: MessageType = MessageType.TEXT
    content: Optional[str] = None
    file_attachment: Optional[FileAttachment] = None
    voice_message: Optional[VoiceMessage] = None
    reply_to_id: Optional[str] = None

class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    participants: List[str]  # List of user IDs
    is_group_chat: bool = False
    group_name: Optional[str] = None
    group_description: Optional[str] = None
    group_admin: Optional[str] = None  # User ID of group admin
    last_message_id: Optional[str] = None
    last_message_timestamp: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ConversationCreate(BaseModel):
    participants: List[str]
    is_group_chat: bool = False
    group_name: Optional[str] = None
    group_description: Optional[str] = None

class ConversationWithDetails(BaseModel):
    conversation: Conversation
    other_participant: Optional[Dict[str, Any]] = None  # Other user details for 1-on-1 chats
    unread_count: int = 0
    last_message: Optional[Message] = None

# Existing User Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None  # base64 encoded
    origin_country: Optional[str] = None
    origin_city: Optional[str] = None
    destination_country: Optional[str] = None
    destination_city: Optional[str] = None
    university: Optional[str] = None
    course: Optional[str] = None
    study_level: Optional[str] = None  # Masters, Bachelors, PhD, etc.

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    profile: Optional[UserProfile] = None

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    is_verified: bool = False
    is_student_verified: bool = False
    profile: Optional[UserProfile] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EmailVerification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    token: str
    expires_at: datetime
    is_used: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ConnectionRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_user_id: str
    to_user_id: str
    status: str = "pending"  # pending, accepted, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Utility Functions
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

def is_edu_email(email: str) -> bool:
    return email.lower().endswith('.edu')

def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)

async def send_verification_email(email: str, token: str, name: str):
    # For now, we'll just log the verification link
    verification_link = f"http://localhost:3000/verify-email?token={token}"
    print(f"Verification email for {name} ({email}): {verification_link}")

# OAuth Callback Route (for handling redirects)
@api_router.get("/auth/callback")
async def oauth_callback():
    """
    Simple OAuth callback endpoint that redirects to the main app.
    The actual session processing happens in the frontend.
    """
    return {"message": "OAuth callback received. Please close this window and return to the app."}

# Google OAuth Models
class GoogleOAuthData(BaseModel):
    google_data: Dict[str, Any]
    session_token: str

# Authentication Routes
@api_router.post("/auth/google-oauth")
async def google_oauth_login(oauth_data: GoogleOAuthData):
    try:
        google_user = oauth_data.google_data
        
        # Extract user information from Google data
        email = google_user.get('email', '')
        name = google_user.get('name', '')
        picture = google_user.get('picture', '')
        
        # Validate that we have minimum required data
        if not email:
            raise HTTPException(status_code=400, detail="Email is required from Google OAuth")
        
        # Split name into first and last name
        name_parts = name.split(' ', 1) if name else ['', '']
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": email})
        
        if existing_user:
            # User exists, just login
            user = User(**{k: v for k, v in existing_user.items() if k != 'password'})
            
            # Update profile picture if we have one from Google
            if picture and (not user.profile or not user.profile.profile_picture):
                update_data = {}
                if user.profile:
                    update_data['profile'] = user.profile.dict()
                    update_data['profile']['profile_picture'] = picture
                else:
                    update_data['profile'] = {'profile_picture': picture}
                
                update_data['updated_at'] = datetime.utcnow()
                await db.users.update_one({"id": user.id}, {"$set": update_data})
        else:
            # Create new user (only for .edu emails)
            if not is_edu_email(email):
                raise HTTPException(status_code=400, detail="Only .edu email addresses are allowed")
            
            # Create new user with Google data
            user = User(
                email=email,
                first_name=first_name or 'User',
                last_name=last_name or '',
                is_verified=True,  # Google OAuth users are considered verified
                profile=UserProfile(
                    profile_picture=picture
                ) if picture else None
            )
            
            # Store user (no password needed for OAuth users)
            user_dict = user.dict()
            user_dict['oauth_provider'] = 'google'
            user_dict['oauth_id'] = google_user.get('id', '')
            
            await db.users.insert_one(user_dict)
        
        # Create access token
        access_token = create_access_token(data={"sub": user.id})
        
        # Store session token (optional - for session management)
        session_data = {
            "user_id": user.id,
            "session_token": oauth_data.session_token,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7)
        }
        await db.sessions.insert_one(session_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user.dict()
        }
        
    except Exception as e:
        print(f"Google OAuth error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process Google authentication")

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate edu email
    if not is_edu_email(user_data.email):
        raise HTTPException(status_code=400, detail="Only .edu email addresses are allowed")
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone
    )
    
    # Store user with hashed password
    user_dict = user.dict()
    user_dict['password'] = hashed_password
    
    await db.users.insert_one(user_dict)
    
    # Create email verification token
    verification_token = generate_verification_token()
    verification = EmailVerification(
        user_id=user.id,
        token=verification_token,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    
    await db.email_verifications.insert_one(verification.dict())
    
    # Send verification email
    await send_verification_email(user_data.email, verification_token, user_data.first_name)
    
    return {"message": "Registration successful. Please check your email for verification link."}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    # Find user by email
    user_doc = await db.users.find_one({"email": credentials.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(credentials.password, user_doc['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create access token
    access_token = create_access_token(data={"sub": user_doc['id']})
    
    user = User(**{k: v for k, v in user_doc.items() if k != 'password'})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.dict()
    }

@api_router.post("/auth/verify-email")
async def verify_email(token: str):
    # Find verification record
    verification = await db.email_verifications.find_one({
        "token": token,
        "is_used": False,
        "expires_at": {"$gte": datetime.utcnow()}
    })
    
    if not verification:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    
    # Mark verification as used
    await db.email_verifications.update_one(
        {"id": verification['id']},
        {"$set": {"is_used": True}}
    )
    
    # Update user as verified
    await db.users.update_one(
        {"id": verification['user_id']},
        {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Email verified successfully"}

# User Profile Routes
@api_router.get("/users/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.put("/users/me")
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    update_data = {}
    
    if user_update.first_name is not None:
        update_data['first_name'] = user_update.first_name
    if user_update.last_name is not None:
        update_data['last_name'] = user_update.last_name
    if user_update.phone is not None:
        update_data['phone'] = user_update.phone
    if user_update.profile is not None:
        update_data['profile'] = user_update.profile.dict()
    
    update_data['updated_at'] = datetime.utcnow()
    
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": update_data}
    )
    
    # Fetch updated user
    updated_user_doc = await db.users.find_one({"id": current_user.id})
    updated_user = User(**{k: v for k, v in updated_user_doc.items() if k != 'password'})
    
    return {"message": "Profile updated successfully", "user": updated_user.dict()}

# Search and Discovery Routes
@api_router.get("/users/search")
async def search_users(
    country: Optional[str] = None,
    city: Optional[str] = None,
    university: Optional[str] = None,
    course: Optional[str] = None,
    origin_country: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
    current_user: User = Depends(get_current_user)
):
    query = {"id": {"$ne": current_user.id}}  # Exclude current user
    
    if country:
        query["$or"] = [
            {"profile.destination_country": {"$regex": country, "$options": "i"}},
            {"profile.origin_country": {"$regex": country, "$options": "i"}}
        ]
    
    if city:
        query["$or"] = query.get("$or", []) + [
            {"profile.destination_city": {"$regex": city, "$options": "i"}},
            {"profile.origin_city": {"$regex": city, "$options": "i"}}
        ]
    
    if university:
        query["profile.university"] = {"$regex": university, "$options": "i"}
    
    if course:
        query["profile.course"] = {"$regex": course, "$options": "i"}
    
    if origin_country:
        query["profile.origin_country"] = {"$regex": origin_country, "$options": "i"}
    
    users_cursor = db.users.find(query).skip(skip).limit(limit)
    users_docs = await users_cursor.to_list(length=limit)
    
    users = []
    for user_doc in users_docs:
        user = User(**{k: v for k, v in user_doc.items() if k != 'password'})
        users.append(user.dict())
    
    return {"users": users, "total": len(users)}

# Connection Routes
@api_router.post("/connections/request")
async def send_connection_request(
    to_user_id: str,
    current_user: User = Depends(get_current_user)
):
    if to_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send request to yourself")
    
    # Check if target user exists
    target_user = await db.users.find_one({"id": to_user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if request already exists
    existing_request = await db.connection_requests.find_one({
        "$or": [
            {"from_user_id": current_user.id, "to_user_id": to_user_id},
            {"from_user_id": to_user_id, "to_user_id": current_user.id}
        ]
    })
    
    if existing_request:
        raise HTTPException(status_code=400, detail="Connection request already exists")
    
    # Create connection request
    connection_request = ConnectionRequest(
        from_user_id=current_user.id,
        to_user_id=to_user_id
    )
    
    await db.connection_requests.insert_one(connection_request.dict())
    
    return {"message": "Connection request sent successfully"}

@api_router.get("/connections/requests")
async def get_connection_requests(current_user: User = Depends(get_current_user)):
    # Get incoming requests
    incoming_cursor = db.connection_requests.find({
        "to_user_id": current_user.id,
        "status": "pending"
    })
    incoming_docs = await incoming_cursor.to_list(100)
    
    # Get outgoing requests
    outgoing_cursor = db.connection_requests.find({
        "from_user_id": current_user.id,
        "status": "pending"
    })
    outgoing_docs = await outgoing_cursor.to_list(100)
    
    # Convert to serializable format
    incoming_requests = []
    for doc in incoming_docs:
        request_data = ConnectionRequest(**{k: v for k, v in doc.items() if k != '_id'})
        incoming_requests.append(request_data.dict())
    
    outgoing_requests = []
    for doc in outgoing_docs:
        request_data = ConnectionRequest(**{k: v for k, v in doc.items() if k != '_id'})
        outgoing_requests.append(request_data.dict())
    
    return {
        "incoming": incoming_requests,
        "outgoing": outgoing_requests
    }

@api_router.post("/connections/respond")
async def respond_to_request(
    request_id: str,
    action: str,  # "accept" or "reject"
    current_user: User = Depends(get_current_user)
):
    if action not in ["accept", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'accept' or 'reject'")
    
    # Find the request
    request_doc = await db.connection_requests.find_one({
        "id": request_id,
        "to_user_id": current_user.id,
        "status": "pending"
    })
    
    if not request_doc:
        raise HTTPException(status_code=404, detail="Connection request not found")
    
    # Update request status
    new_status = "accepted" if action == "accept" else "rejected"
    await db.connection_requests.update_one(
        {"id": request_id},
        {"$set": {"status": new_status}}
    )
    
    # If accepted, create a conversation between users
    if action == "accept":
        # Check if conversation already exists
        existing_conversation = await db.conversations.find_one({
            "participants": {"$all": [current_user.id, request_doc['from_user_id']], "$size": 2},
            "is_group_chat": False
        })
        
        if not existing_conversation:
            # Create new conversation
            conversation = Conversation(
                participants=[current_user.id, request_doc['from_user_id']],
                is_group_chat=False
            )
            await db.conversations.insert_one(conversation.dict())
    
    return {"message": f"Connection request {new_status}"}

# Chat Routes
@api_router.post("/chat/conversations", response_model=Conversation)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user)
):
    # Validate that current user is in participants
    if current_user.id not in conversation_data.participants:
        conversation_data.participants.append(current_user.id)
    
    # Check if 1-on-1 conversation already exists
    if not conversation_data.is_group_chat and len(conversation_data.participants) == 2:
        existing_conversation = await db.conversations.find_one({
            "participants": {"$all": conversation_data.participants, "$size": 2},
            "is_group_chat": False
        })
        
        if existing_conversation:
            return Conversation(**{k: v for k, v in existing_conversation.items() if k != '_id'})
    
    # Create new conversation
    conversation = Conversation(
        participants=conversation_data.participants,
        is_group_chat=conversation_data.is_group_chat,
        group_name=conversation_data.group_name,
        group_description=conversation_data.group_description,
        group_admin=current_user.id if conversation_data.is_group_chat else None
    )
    
    await db.conversations.insert_one(conversation.dict())
    return conversation

@api_router.get("/chat/conversations", response_model=List[ConversationWithDetails])
async def get_user_conversations(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100)
):
    # Find conversations where user is participant
    conversations_cursor = db.conversations.find({
        "participants": current_user.id
    }).sort("updated_at", -1).limit(limit)
    
    conversations_docs = await conversations_cursor.to_list(length=limit)
    
    result = []
    for conv_doc in conversations_docs:
        conversation = Conversation(**{k: v for k, v in conv_doc.items() if k != '_id'})
        
        # Get other participant details for 1-on-1 chats
        other_participant = None
        if not conversation.is_group_chat:
            other_user_id = next((p for p in conversation.participants if p != current_user.id), None)
            if other_user_id:
                other_user_doc = await db.users.find_one({"id": other_user_id})
                if other_user_doc:
                    other_participant = {
                        "id": other_user_doc["id"],
                        "first_name": other_user_doc["first_name"],
                        "last_name": other_user_doc["last_name"],
                        "email": other_user_doc["email"],
                        "profile": other_user_doc.get("profile")
                    }
        
        # Get unread messages count
        unread_count = await db.messages.count_documents({
            "conversation_id": conversation.id,
            "sender_id": {"$ne": current_user.id},
            "read_by": {"$not": {"$in": [current_user.id]}}
        })
        
        # Get last message
        last_message = None
        if conversation.last_message_id:
            last_message_doc = await db.messages.find_one({"id": conversation.last_message_id})
            if last_message_doc:
                last_message = Message(**{k: v for k, v in last_message_doc.items() if k != '_id'})
        
        result.append(ConversationWithDetails(
            conversation=conversation,
            other_participant=other_participant,
            unread_count=unread_count,
            last_message=last_message
        ))
    
    return result

@api_router.post("/chat/messages", response_model=Message)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user)
):
    # Verify user is participant in conversation
    conversation = await db.conversations.find_one({"id": message_data.conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if current_user.id not in conversation["participants"]:
        raise HTTPException(status_code=403, detail="Not a participant in this conversation")
    
    # Create message
    message = Message(
        conversation_id=message_data.conversation_id,
        sender_id=current_user.id,
        message_type=message_data.message_type,
        content=message_data.content,
        file_attachment=message_data.file_attachment,
        voice_message=message_data.voice_message,
        reply_to_id=message_data.reply_to_id
    )
    
    # Save message
    await db.messages.insert_one(message.dict())
    
    # Update conversation's last message
    await db.conversations.update_one(
        {"id": message_data.conversation_id},
        {
            "$set": {
                "last_message_id": message.id,
                "last_message_timestamp": message.timestamp,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return message

@api_router.get("/chat/messages/{conversation_id}", response_model=List[Message])
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    before_timestamp: Optional[datetime] = Query(None)
):
    # Verify user is participant in conversation
    conversation = await db.conversations.find_one({"id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if current_user.id not in conversation["participants"]:
        raise HTTPException(status_code=403, detail="Not a participant in this conversation")
    
    # Build query
    query = {"conversation_id": conversation_id, "is_deleted": False}
    if before_timestamp:
        query["timestamp"] = {"$lt": before_timestamp}
    
    # Get messages
    messages_cursor = db.messages.find(query).sort("timestamp", -1).limit(limit)
    messages_docs = await messages_cursor.to_list(length=limit)
    
    # Convert to Message objects and reverse order (oldest first)
    messages = []
    for msg_doc in reversed(messages_docs):
        message = Message(**{k: v for k, v in msg_doc.items() if k != '_id'})
        messages.append(message)
    
    return messages

@api_router.post("/chat/messages/{message_id}/read")
async def mark_message_as_read(
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    # Update message read status
    result = await db.messages.update_one(
        {
            "id": message_id,
            "read_by": {"$not": {"$in": [current_user.id]}}
        },
        {
            "$addToSet": {"read_by": current_user.id},
            "$set": {"status": MessageStatus.READ}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found or already read")
    
    return {"message": "Message marked as read"}

# Socket.IO Handlers
active_connections: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
user_sessions: Dict[str, str] = {}  # session_id -> user_id
typing_users: Dict[str, Dict[str, datetime]] = {}  # conversation_id -> {user_id: timestamp}

@sio.event
async def connect(sid, environ, auth):
    print(f"Socket connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Socket disconnected: {sid}")
    
    if sid in user_sessions:
        user_id = user_sessions[sid]
        
        # Remove session from active connections
        if user_id in active_connections:
            active_connections[user_id].discard(sid)
            if not active_connections[user_id]:
                del active_connections[user_id]
        
        del user_sessions[sid]

@sio.event
async def authenticate(sid, data):
    try:
        user_id = data.get('user_id')
        token = data.get('token')
        
        if not user_id or not token:
            await sio.emit('auth_error', {'message': 'Missing user_id or token'}, to=sid)
            return
        
        # Add to active connections
        if user_id not in active_connections:
            active_connections[user_id] = set()
        active_connections[user_id].add(sid)
        user_sessions[sid] = user_id
        
        await sio.emit('authenticated', {'user_id': user_id}, to=sid)
        print(f"User {user_id} authenticated with session {sid}")
        
    except Exception as e:
        print(f"Authentication error: {e}")
        await sio.emit('auth_error', {'message': 'Authentication failed'}, to=sid)

@sio.event
async def join_conversation(sid, data):
    try:
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return
        
        await sio.enter_room(sid, f"conversation_{conversation_id}")
        await sio.emit('joined_conversation', {
            'conversation_id': conversation_id
        }, to=sid)
        
        print(f"Session {sid} joined conversation {conversation_id}")
        
    except Exception as e:
        print(f"Error joining conversation: {e}")

@sio.event
async def send_message(sid, data):
    try:
        conversation_id = data.get('conversation_id')
        message_data = data.get('message')
        
        if not conversation_id or not message_data:
            return
        
        user_id = user_sessions.get(sid)
        if not user_id:
            return
        
        # Broadcast message to all participants in conversation
        await sio.emit('new_message', {
            'conversation_id': conversation_id,
            'message': message_data,
            'sender_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"conversation_{conversation_id}")
        
    except Exception as e:
        print(f"Error handling send_message: {e}")

@sio.event
async def typing_start(sid, data):
    try:
        conversation_id = data.get('conversation_id')
        user_id = user_sessions.get(sid)
        
        if not conversation_id or not user_id:
            return
        
        # Track typing user
        if conversation_id not in typing_users:
            typing_users[conversation_id] = {}
        typing_users[conversation_id][user_id] = datetime.utcnow()
        
        # Broadcast typing indicator to other participants
        await sio.emit('typing_start', {
            'conversation_id': conversation_id,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"conversation_{conversation_id}", skip_sid=sid)
        
    except Exception as e:
        print(f"Error handling typing_start: {e}")

@sio.event
async def typing_stop(sid, data):
    try:
        conversation_id = data.get('conversation_id')
        user_id = data.get('user_id') or user_sessions.get(sid)
        
        if not conversation_id or not user_id:
            return
        
        # Remove from typing users
        if conversation_id in typing_users and user_id in typing_users[conversation_id]:
            del typing_users[conversation_id][user_id]
            
            if not typing_users[conversation_id]:
                del typing_users[conversation_id]
        
        # Broadcast typing stop to other participants
        await sio.emit('typing_stop', {
            'conversation_id': conversation_id,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"conversation_{conversation_id}", skip_sid=sid)
        
    except Exception as e:
        print(f"Error handling typing_stop: {e}")

@sio.event
async def message_read(sid, data):
    try:
        message_id = data.get('message_id')
        conversation_id = data.get('conversation_id')
        user_id = user_sessions.get(sid)
        
        if not message_id or not conversation_id or not user_id:
            return
        
        # Broadcast read receipt to other participants
        await sio.emit('message_read', {
            'message_id': message_id,
            'conversation_id': conversation_id,
            'user_id': user_id,
            'read_at': datetime.utcnow().isoformat()
        }, room=f"conversation_{conversation_id}", skip_sid=sid)
        
    except Exception as e:
        print(f"Error handling message_read: {e}")

# Include routers
app.include_router(api_router)

# Import and include posts router
from posts_routes import posts_router
app.include_router(posts_router)

# Mount Socket.IO
app.mount("/socket.io", socketio.ASGIApp(sio))

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()