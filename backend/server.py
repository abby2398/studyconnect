from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Form, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
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

# Import chat system
from .chat_models import *
from .chat_routes import chat_router
from .socket_handlers import ChatSocketHandler

# Initialize chat handler
chat_handler = ChatSocketHandler(sio)

# Models (existing models remain the same)
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

# Utility Functions (remain the same)
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

# Authentication Routes (remain the same)
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

# User Profile Routes (remain the same)
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

# Search and Discovery Routes (remain the same)
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

# Connection Routes (remain the same)
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
        from chat_models import ConversationCreate, Conversation
        
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

# Include chat router
app.include_router(api_router)
app.include_router(chat_router)

# Mount Socket.IO
app.mount("/socket.io", socketio.ASGIApp(sio))

# Start cleanup task
@app.on_event("startup")
async def startup_event():
    from socket_handlers import cleanup_typing_indicators
    asyncio.create_task(cleanup_typing_indicators())

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