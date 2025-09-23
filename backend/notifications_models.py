"""
Notification System Models for International Student Networking App
Handles push notifications, in-app notifications, and email notifications
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class NotificationType(str, Enum):
    CONNECTION_REQUEST = "connection_request"
    CONNECTION_ACCEPTED = "connection_accepted"
    MESSAGE_RECEIVED = "message_received"
    EVENT_INVITATION = "event_invitation"
    EVENT_REMINDER = "event_reminder"
    EVENT_UPDATE = "event_update"
    EVENT_JOINED = "event_joined"
    POST_LIKED = "post_liked"
    POST_COMMENTED = "post_commented"
    POST_SHARED = "post_shared"
    MENTION = "mention"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    WELCOME = "welcome"
    VERIFICATION_REMINDER = "verification_reminder"

class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationChannel(str, Enum):
    PUSH = "push"
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class NotificationCreate(BaseModel):
    recipient_id: str
    sender_id: Optional[str] = None
    type: NotificationType
    title: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=500)
    data: Optional[Dict[str, Any]] = None  # Additional data for deep linking
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: List[NotificationChannel] = Field(default=[NotificationChannel.IN_APP])
    scheduled_at: Optional[datetime] = None  # For delayed notifications
    expires_at: Optional[datetime] = None  # Auto-delete after this time

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    recipient_id: str
    sender_id: Optional[str] = None
    type: NotificationType
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: List[NotificationChannel] = Field(default=[NotificationChannel.IN_APP])
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None

class NotificationPreferences(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    # Push notification preferences
    push_enabled: bool = True
    push_connection_requests: bool = True
    push_messages: bool = True
    push_events: bool = True
    push_posts: bool = True
    push_system: bool = True
    # Email notification preferences  
    email_enabled: bool = True
    email_connection_requests: bool = True
    email_events: bool = True
    email_system: bool = True
    email_digest: bool = True  # Daily/weekly digest
    # Quiet hours
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None  # Format: "22:00"
    quiet_hours_end: Optional[str] = None    # Format: "08:00"
    # Timezone
    timezone: str = "UTC"
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationPreferencesUpdate(BaseModel):
    push_enabled: Optional[bool] = None
    push_connection_requests: Optional[bool] = None
    push_messages: Optional[bool] = None
    push_events: Optional[bool] = None
    push_posts: Optional[bool] = None
    push_system: Optional[bool] = None
    email_enabled: Optional[bool] = None
    email_connection_requests: Optional[bool] = None
    email_events: Optional[bool] = None
    email_system: Optional[bool] = None
    email_digest: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: Optional[str] = None

class PushToken(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    token: str
    device_type: str  # "ios", "android", "web"
    device_id: Optional[str] = None
    app_version: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None

class PushTokenCreate(BaseModel):
    token: str
    device_type: str
    device_id: Optional[str] = None
    app_version: Optional[str] = None

class NotificationStats(BaseModel):
    user_id: str
    total_notifications: int
    unread_count: int
    notifications_by_type: Dict[str, int]
    notifications_by_status: Dict[str, int]
    last_notification: Optional[datetime] = None

class NotificationBatch(BaseModel):
    """For sending bulk notifications"""
    recipient_ids: List[str]
    type: NotificationType
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: List[NotificationChannel] = Field(default=[NotificationChannel.IN_APP])
    scheduled_at: Optional[datetime] = None

class EmailTemplate(BaseModel):
    """Email notification templates"""
    template_id: str
    type: NotificationType
    subject: str
    html_content: str
    text_content: str
    variables: List[str] = Field(default_factory=list)  # Template variables

# Predefined notification templates
NOTIFICATION_TEMPLATES = {
    NotificationType.CONNECTION_REQUEST: {
        "title": "New Connection Request",
        "message": "{sender_name} wants to connect with you",
        "email_subject": "You have a new connection request on StudyConnect",
        "push_body": "{sender_name} sent you a connection request"
    },
    NotificationType.CONNECTION_ACCEPTED: {
        "title": "Connection Accepted",
        "message": "{sender_name} accepted your connection request",
        "email_subject": "Your connection request was accepted",
        "push_body": "{sender_name} is now connected with you"
    },
    NotificationType.MESSAGE_RECEIVED: {
        "title": "New Message",
        "message": "{sender_name}: {message_preview}",
        "email_subject": "You have a new message on StudyConnect",
        "push_body": "{sender_name} sent you a message"
    },
    NotificationType.EVENT_INVITATION: {
        "title": "Event Invitation",
        "message": "You're invited to '{event_title}'",
        "email_subject": "You're invited to an event on StudyConnect",
        "push_body": "New event invitation: {event_title}"
    },
    NotificationType.EVENT_REMINDER: {
        "title": "Event Reminder",
        "message": "'{event_title}' starts in {time_until}",
        "email_subject": "Event Reminder: {event_title}",
        "push_body": "{event_title} starts soon"
    },
    NotificationType.EVENT_JOINED: {
        "title": "Event Update",
        "message": "{sender_name} joined '{event_title}'",
        "email_subject": "Someone joined your event",
        "push_body": "{sender_name} joined your event"
    },
    NotificationType.POST_LIKED: {
        "title": "Post Liked",
        "message": "{sender_name} liked your post",
        "email_subject": "Your post received a new like",
        "push_body": "{sender_name} liked your post"
    },
    NotificationType.POST_COMMENTED: {
        "title": "New Comment",
        "message": "{sender_name} commented on your post",
        "email_subject": "New comment on your post",
        "push_body": "{sender_name} commented on your post"
    },
    NotificationType.WELCOME: {
        "title": "Welcome to StudyConnect!",
        "message": "Complete your profile to start connecting with fellow students",
        "email_subject": "Welcome to StudyConnect - Complete Your Profile",
        "push_body": "Welcome! Let's complete your profile"
    },
    NotificationType.SYSTEM_ANNOUNCEMENT: {
        "title": "StudyConnect Update",
        "message": "{announcement_text}",
        "email_subject": "Important Update from StudyConnect",
        "push_body": "StudyConnect Announcement"
    }
}