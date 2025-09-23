"""
Events System Models for International Student Networking App
Handles events, attendees, and event discussions
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class EventCategory(str, Enum):
    STUDY_GROUP = "study_group"
    SOCIAL = "social"
    NETWORKING = "networking"
    WORKSHOP = "workshop"
    SPORTS = "sports"
    CULTURAL = "cultural"
    CAREER = "career"
    OTHER = "other"

class EventStatus(str, Enum):
    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class AttendeeStatus(str, Enum):
    JOINED = "joined"
    INTERESTED = "interested"
    DECLINED = "declined"

class EventLocation(BaseModel):
    address: Optional[str] = None
    city: str
    country: str
    venue_name: Optional[str] = None
    is_online: bool = False
    online_link: Optional[str] = None

class EventCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    category: EventCategory
    start_datetime: datetime
    end_datetime: datetime
    location: EventLocation
    max_attendees: Optional[int] = None
    tags: List[str] = Field(default_factory=list, max_items=10)
    is_private: bool = False
    registration_required: bool = False

class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    category: EventCategory
    creator_id: str
    start_datetime: datetime
    end_datetime: datetime
    location: EventLocation
    max_attendees: Optional[int] = None
    current_attendees: int = 0
    tags: List[str] = Field(default_factory=list)
    is_private: bool = False
    registration_required: bool = False
    status: EventStatus = EventStatus.UPCOMING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[EventCategory] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    location: Optional[EventLocation] = None
    max_attendees: Optional[int] = None
    tags: Optional[List[str]] = None
    is_private: Optional[bool] = None
    registration_required: Optional[bool] = None
    status: Optional[EventStatus] = None

class EventAttendee(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    user_id: str
    status: AttendeeStatus
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None  # Optional notes when joining

class EventAttendeeCreate(BaseModel):
    status: AttendeeStatus = AttendeeStatus.JOINED
    notes: Optional[str] = None

class EventMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    user_id: str
    message: str = Field(min_length=1, max_length=1000)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_announcement: bool = False  # For event creator announcements
    reply_to_id: Optional[str] = None  # For replies

class EventMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    is_announcement: bool = False
    reply_to_id: Optional[str] = None

class EventWithDetails(BaseModel):
    event: Event
    creator: Dict[str, Any]  # Creator user details
    attendee_count: int
    user_attendance_status: Optional[AttendeeStatus] = None
    is_creator: bool = False
    can_join: bool = True

class EventAttendeeWithUser(BaseModel):
    attendee: EventAttendee
    user: Dict[str, Any]  # User details

class EventMessageWithUser(BaseModel):
    message: EventMessage
    user: Dict[str, Any]  # User details