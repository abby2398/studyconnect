from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from enum import Enum

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

class TypingIndicator(BaseModel):
    conversation_id: str
    user_id: str
    is_typing: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class OnlineStatus(BaseModel):
    user_id: str
    is_online: bool = True
    last_seen: datetime = Field(default_factory=datetime.utcnow)

class MessageReadReceipt(BaseModel):
    message_id: str
    user_id: str
    read_at: datetime = Field(default_factory=datetime.utcnow)

class ConversationWithDetails(BaseModel):
    conversation: Conversation
    other_participant: Optional[Dict[str, Any]] = None  # Other user details for 1-on-1 chats
    unread_count: int = 0
    last_message: Optional[Message] = None