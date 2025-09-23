"""
AI Assistant Models for International Student Networking App
Handles AI chat messages, history, and assistant functionality
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class AIMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    context: Optional[Dict[str, Any]] = None  # Additional context for the AI

class AIMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: str
    role: MessageRole
    message: str
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tokens_used: Optional[int] = None
    response_time_ms: Optional[int] = None

class AIChat(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: str
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0

class AIChatWithMessages(BaseModel):
    chat: AIChat
    messages: List[AIMessage]

class AIAssistantStats(BaseModel):
    user_id: str
    total_messages: int
    total_tokens_used: int
    total_chats: int
    average_response_time_ms: float
    last_interaction: datetime