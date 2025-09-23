"""
Notification Service for StudyConnect
Handles push notifications, email notifications, and in-app notifications
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from notifications_models import (
    Notification, NotificationCreate, NotificationType, NotificationChannel,
    NotificationStatus, NotificationPreferences, PushToken, NOTIFICATION_TEMPLATES
)
from server import db
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.expo_access_token = os.getenv('EXPO_ACCESS_TOKEN')
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@studyconnect.com')
        self.app_name = "StudyConnect"
        
    async def create_notification(self, notification_data: NotificationCreate) -> Notification:
        """Create and send a notification"""
        try:
            # Get user preferences
            preferences = await self.get_user_preferences(notification_data.recipient_id)
            
            # Filter channels based on preferences
            allowed_channels = self._filter_channels_by_preferences(
                notification_data.channels, 
                notification_data.type, 
                preferences
            )
            
            if not allowed_channels:
                logger.info(f"No allowed channels for notification to user {notification_data.recipient_id}")
                return None
            
            # Create notification record
            notification = Notification(
                **notification_data.dict(),
                channels=allowed_channels
            )
            
            # Store in database
            await db.notifications.insert_one(notification.dict())
            
            # Send through requested channels
            await self._send_notification(notification, preferences)
            
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            raise e
    
    async def send_bulk_notifications(self, recipient_ids: List[str], notification_data: NotificationCreate) -> List[Notification]:
        """Send notifications to multiple users"""
        notifications = []
        
        for recipient_id in recipient_ids:
            try:
                individual_notification = NotificationCreate(
                    **{**notification_data.dict(), "recipient_id": recipient_id}
                )
                notification = await self.create_notification(individual_notification)
                if notification:
                    notifications.append(notification)
            except Exception as e:
                logger.error(f"Error sending notification to {recipient_id}: {str(e)}")
                continue
        
        return notifications
    
    async def _send_notification(self, notification: Notification, preferences: NotificationPreferences):
        """Send notification through specified channels"""
        tasks = []
        
        for channel in notification.channels:
            if channel == NotificationChannel.PUSH:
                tasks.append(self._send_push_notification(notification))
            elif channel == NotificationChannel.EMAIL:
                tasks.append(self._send_email_notification(notification, preferences))
            elif channel == NotificationChannel.IN_APP:
                # In-app notifications are already stored in database
                pass
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_push_notification(self, notification: Notification):
        """Send push notification via Expo Push API"""
        try:
            # Get user's push tokens
            tokens_cursor = db.push_tokens.find({
                "user_id": notification.recipient_id,
                "is_active": True
            })
            tokens_docs = await tokens_cursor.to_list(10)
            
            if not tokens_docs:
                logger.info(f"No push tokens found for user {notification.recipient_id}")
                return
            
            # Prepare push messages
            messages = []
            template = NOTIFICATION_TEMPLATES.get(notification.type, {})
            
            for token_doc in tokens_docs:
                message = {
                    "to": token_doc["token"],
                    "title": notification.title,
                    "body": template.get("push_body", notification.message),
                    "data": notification.data or {},
                    "priority": "high" if notification.priority.value in ["high", "urgent"] else "normal",
                    "sound": "default",
                    "badge": await self._get_unread_count(notification.recipient_id)
                }
                messages.append(message)
            
            # Send via Expo Push API
            if self.expo_access_token and messages:
                await self._send_expo_push_messages(messages)
                
                # Update notification status
                await db.notifications.update_one(
                    {"id": notification.id},
                    {
                        "$set": {
                            "sent_at": datetime.utcnow(),
                            "status": NotificationStatus.SENT
                        }
                    }
                )
            
        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
            await db.notifications.update_one(
                {"id": notification.id},
                {
                    "$set": {
                        "status": NotificationStatus.FAILED,
                        "error_message": str(e)
                    }
                }
            )
    
    async def _send_expo_push_messages(self, messages: List[Dict]):
        """Send messages via Expo Push API"""
        try:
            url = "https://exp.host/--/api/v2/push/send"
            headers = {
                "Authorization": f"Bearer {self.expo_access_token}",
                "Content-Type": "application/json",
            }
            
            # Send in chunks of 100 (Expo limit)
            chunk_size = 100
            for i in range(0, len(messages), chunk_size):
                chunk = messages[i:i + chunk_size]
                
                response = requests.post(
                    url,
                    headers=headers,
                    json=chunk,
                    timeout=10
                )
                
                if response.status_code != 200:
                    logger.error(f"Expo push API error: {response.text}")
                else:
                    logger.info(f"Sent {len(chunk)} push notifications successfully")
                    
        except Exception as e:
            logger.error(f"Error with Expo Push API: {str(e)}")
            raise e
    
    async def _send_email_notification(self, notification: Notification, preferences: NotificationPreferences):
        """Send email notification via SendGrid"""
        try:
            if not self.sendgrid_api_key:
                logger.warning("SendGrid API key not configured")
                return
            
            # Get recipient user data
            user_doc = await db.users.find_one({"id": notification.recipient_id})
            if not user_doc:
                logger.error(f"User not found: {notification.recipient_id}")
                return
            
            # Get sender data if applicable
            sender_name = "StudyConnect"
            if notification.sender_id:
                sender_doc = await db.users.find_one({"id": notification.sender_id})
                if sender_doc:
                    sender_name = f"{sender_doc['first_name']} {sender_doc['last_name']}"
            
            # Prepare email content
            template = NOTIFICATION_TEMPLATES.get(notification.type, {})
            subject = template.get("email_subject", notification.title)
            
            # Format subject and message with dynamic data
            if notification.data:
                subject = subject.format(**notification.data, sender_name=sender_name)
                message = notification.message.format(**notification.data, sender_name=sender_name)
            else:
                subject = subject.replace("{sender_name}", sender_name)
                message = notification.message.replace("{sender_name}", sender_name)
            
            # Create email content
            html_content = self._generate_email_html(
                user_name=f"{user_doc['first_name']} {user_doc['last_name']}",
                title=notification.title,
                message=message,
                notification_type=notification.type,
                data=notification.data
            )
            
            text_content = f"""
            Hi {user_doc['first_name']},
            
            {message}
            
            ---
            StudyConnect Team
            
            Manage your notification preferences: https://studyconnect.com/settings/notifications
            """
            
            # Send email
            sg = SendGridAPIClient(api_key=self.sendgrid_api_key)
            mail = Mail(
                from_email=Email(self.from_email, self.app_name),
                to_emails=To(user_doc['email']),
                subject=subject,
                html_content=Content("text/html", html_content),
                plain_text_content=Content("text/plain", text_content)
            )
            
            response = sg.send(mail)
            
            if response.status_code in [200, 202]:
                logger.info(f"Email sent successfully to {user_doc['email']}")
                await db.notifications.update_one(
                    {"id": notification.id},
                    {
                        "$set": {
                            "sent_at": datetime.utcnow(),
                            "status": NotificationStatus.SENT
                        }
                    }
                )
            else:
                logger.error(f"SendGrid error: {response.body}")
                
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            await db.notifications.update_one(
                {"id": notification.id},
                {
                    "$set": {
                        "status": NotificationStatus.FAILED,
                        "error_message": str(e)
                    }
                }
            )
    
    def _generate_email_html(self, user_name: str, title: str, message: str, 
                           notification_type: NotificationType, data: Dict = None) -> str:
        """Generate HTML email template"""
        
        # Get action button based on notification type
        action_button = ""
        if notification_type == NotificationType.CONNECTION_REQUEST:
            action_button = '<a href="https://studyconnect.com/connections" style="background-color: #6c5ce7; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin-top: 20px;">View Connection Requests</a>'
        elif notification_type in [NotificationType.EVENT_INVITATION, NotificationType.EVENT_REMINDER]:
            event_id = data.get("event_id") if data else ""
            action_button = f'<a href="https://studyconnect.com/events/{event_id}" style="background-color: #00b894; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin-top: 20px;">View Event</a>'
        elif notification_type == NotificationType.MESSAGE_RECEIVED:
            action_button = '<a href="https://studyconnect.com/chat" style="background-color: #fd79a8; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin-top: 20px;">View Messages</a>'
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 40px 30px;">
                <div style="text-align: center; margin-bottom: 40px;">
                    <div style="background-color: #6c5ce7; color: white; width: 60px; height: 60px; border-radius: 30px; display: inline-flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold;">S</div>
                    <h1 style="color: #1a1a2e; margin-top: 20px; margin-bottom: 10px;">StudyConnect</h1>
                    <p style="color: #666; margin: 0;">Connect. Study. Succeed.</p>
                </div>
                
                <div style="background-color: #f8f9ff; padding: 30px; border-radius: 12px; border-left: 4px solid #6c5ce7;">
                    <h2 style="color: #1a1a2e; margin-top: 0; margin-bottom: 20px;">{title}</h2>
                    <p style="color: #333; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
                        Hi {user_name},
                    </p>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">
                        {message}
                    </p>
                    {action_button}
                </div>
                
                <div style="margin-top: 40px; padding-top: 30px; border-top: 1px solid #eee; text-align: center;">
                    <p style="color: #666; font-size: 14px; margin-bottom: 10px;">
                        You're receiving this email because you're part of the StudyConnect community.
                    </p>
                    <p style="color: #666; font-size: 14px;">
                        <a href="https://studyconnect.com/settings/notifications" style="color: #6c5ce7; text-decoration: none;">Manage notification preferences</a> | 
                        <a href="https://studyconnect.com/unsubscribe" style="color: #6c5ce7; text-decoration: none;">Unsubscribe</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    async def get_user_preferences(self, user_id: str) -> NotificationPreferences:
        """Get user notification preferences"""
        try:
            prefs_doc = await db.notification_preferences.find_one({"user_id": user_id})
            if prefs_doc:
                return NotificationPreferences(**{k: v for k, v in prefs_doc.items() if k != '_id'})
            else:
                # Create default preferences
                default_prefs = NotificationPreferences(user_id=user_id)
                await db.notification_preferences.insert_one(default_prefs.dict())
                return default_prefs
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return NotificationPreferences(user_id=user_id)  # Return defaults
    
    def _filter_channels_by_preferences(self, requested_channels: List[NotificationChannel], 
                                      notification_type: NotificationType, 
                                      preferences: NotificationPreferences) -> List[NotificationChannel]:
        """Filter channels based on user preferences"""
        allowed_channels = []
        
        for channel in requested_channels:
            if channel == NotificationChannel.PUSH:
                if preferences.push_enabled and self._is_push_type_allowed(notification_type, preferences):
                    allowed_channels.append(channel)
            elif channel == NotificationChannel.EMAIL:
                if preferences.email_enabled and self._is_email_type_allowed(notification_type, preferences):
                    allowed_channels.append(channel)
            elif channel == NotificationChannel.IN_APP:
                # In-app notifications are always allowed
                allowed_channels.append(channel)
        
        return allowed_channels
    
    def _is_push_type_allowed(self, notification_type: NotificationType, preferences: NotificationPreferences) -> bool:
        """Check if push notifications are allowed for this type"""
        type_mapping = {
            NotificationType.CONNECTION_REQUEST: preferences.push_connection_requests,
            NotificationType.CONNECTION_ACCEPTED: preferences.push_connection_requests,
            NotificationType.MESSAGE_RECEIVED: preferences.push_messages,
            NotificationType.EVENT_INVITATION: preferences.push_events,
            NotificationType.EVENT_REMINDER: preferences.push_events,
            NotificationType.EVENT_UPDATE: preferences.push_events,
            NotificationType.EVENT_JOINED: preferences.push_events,
            NotificationType.POST_LIKED: preferences.push_posts,
            NotificationType.POST_COMMENTED: preferences.push_posts,
            NotificationType.POST_SHARED: preferences.push_posts,
            NotificationType.SYSTEM_ANNOUNCEMENT: preferences.push_system,
            NotificationType.WELCOME: preferences.push_system,
        }
        return type_mapping.get(notification_type, True)
    
    def _is_email_type_allowed(self, notification_type: NotificationType, preferences: NotificationPreferences) -> bool:
        """Check if email notifications are allowed for this type"""
        type_mapping = {
            NotificationType.CONNECTION_REQUEST: preferences.email_connection_requests,
            NotificationType.CONNECTION_ACCEPTED: preferences.email_connection_requests,
            NotificationType.EVENT_INVITATION: preferences.email_events,
            NotificationType.EVENT_REMINDER: preferences.email_events,
            NotificationType.EVENT_UPDATE: preferences.email_events,
            NotificationType.SYSTEM_ANNOUNCEMENT: preferences.email_system,
            NotificationType.WELCOME: preferences.email_system,
        }
        return type_mapping.get(notification_type, False)  # Default to False for email
    
    async def _get_unread_count(self, user_id: str) -> int:
        """Get unread notification count for badge"""
        try:
            count = await db.notifications.count_documents({
                "recipient_id": user_id,
                "read_at": None,
                "status": {"$ne": NotificationStatus.FAILED}
            })
            return count
        except Exception:
            return 0
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read"""
        try:
            result = await db.notifications.update_one(
                {"id": notification_id, "recipient_id": user_id, "read_at": None},
                {"$set": {"read_at": datetime.utcnow(), "status": NotificationStatus.READ}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return False
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        try:
            result = await db.notifications.update_many(
                {"recipient_id": user_id, "read_at": None},
                {"$set": {"read_at": datetime.utcnow(), "status": NotificationStatus.READ}}
            )
            return result.modified_count
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            return 0


# Helper functions for creating specific notification types

async def send_connection_request_notification(sender_id: str, recipient_id: str):
    """Send connection request notification"""
    service = NotificationService()
    
    # Get sender info
    sender_doc = await db.users.find_one({"id": sender_id})
    sender_name = f"{sender_doc['first_name']} {sender_doc['last_name']}" if sender_doc else "Someone"
    
    notification = NotificationCreate(
        recipient_id=recipient_id,
        sender_id=sender_id,
        type=NotificationType.CONNECTION_REQUEST,
        title="New Connection Request",
        message=f"{sender_name} wants to connect with you",
        data={"sender_id": sender_id, "sender_name": sender_name},
        channels=[NotificationChannel.PUSH, NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    )
    
    return await service.create_notification(notification)

async def send_connection_accepted_notification(sender_id: str, recipient_id: str):
    """Send connection accepted notification"""
    service = NotificationService()
    
    sender_doc = await db.users.find_one({"id": sender_id})
    sender_name = f"{sender_doc['first_name']} {sender_doc['last_name']}" if sender_doc else "Someone"
    
    notification = NotificationCreate(
        recipient_id=recipient_id,
        sender_id=sender_id,
        type=NotificationType.CONNECTION_ACCEPTED,
        title="Connection Accepted",
        message=f"{sender_name} accepted your connection request",
        data={"sender_id": sender_id, "sender_name": sender_name},
        channels=[NotificationChannel.PUSH, NotificationChannel.IN_APP]
    )
    
    return await service.create_notification(notification)

async def send_message_notification(sender_id: str, recipient_id: str, message_preview: str):
    """Send new message notification"""
    service = NotificationService()
    
    sender_doc = await db.users.find_one({"id": sender_id})
    sender_name = f"{sender_doc['first_name']} {sender_doc['last_name']}" if sender_doc else "Someone"
    
    notification = NotificationCreate(
        recipient_id=recipient_id,
        sender_id=sender_id,
        type=NotificationType.MESSAGE_RECEIVED,
        title="New Message",
        message=f"{sender_name}: {message_preview[:50]}{'...' if len(message_preview) > 50 else ''}",
        data={"sender_id": sender_id, "sender_name": sender_name, "message_preview": message_preview},
        channels=[NotificationChannel.PUSH, NotificationChannel.IN_APP]
    )
    
    return await service.create_notification(notification)

async def send_event_notification(event_id: str, recipient_ids: List[str], notification_type: NotificationType):
    """Send event-related notifications"""
    service = NotificationService()
    
    # Get event info
    event_doc = await db.events.find_one({"id": event_id})
    if not event_doc:
        return
    
    event_title = event_doc.get("title", "Event")
    
    # Determine message based on type
    if notification_type == NotificationType.EVENT_INVITATION:
        title = "Event Invitation"
        message = f"You're invited to '{event_title}'"
    elif notification_type == NotificationType.EVENT_REMINDER:
        title = "Event Reminder"
        message = f"'{event_title}' starts soon"
    elif notification_type == NotificationType.EVENT_UPDATE:
        title = "Event Update"
        message = f"'{event_title}' has been updated"
    else:
        title = "Event Notification"
        message = f"Update about '{event_title}'"
    
    notification_data = NotificationCreate(
        recipient_id="", # Will be set individually
        type=notification_type,
        title=title,
        message=message,
        data={"event_id": event_id, "event_title": event_title},
        channels=[NotificationChannel.PUSH, NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    )
    
    return await service.send_bulk_notifications(recipient_ids, notification_data)

async def send_post_notification(post_id: str, sender_id: str, recipient_id: str, notification_type: NotificationType):
    """Send post-related notifications"""
    service = NotificationService()
    
    sender_doc = await db.users.find_one({"id": sender_id})
    sender_name = f"{sender_doc['first_name']} {sender_doc['last_name']}" if sender_doc else "Someone"
    
    # Determine message based on type
    if notification_type == NotificationType.POST_LIKED:
        title = "Post Liked"
        message = f"{sender_name} liked your post"
    elif notification_type == NotificationType.POST_COMMENTED:
        title = "New Comment"
        message = f"{sender_name} commented on your post"
    elif notification_type == NotificationType.POST_SHARED:
        title = "Post Shared"
        message = f"{sender_name} shared your post"
    else:
        title = "Post Update"
        message = f"Update on your post"
    
    notification = NotificationCreate(
        recipient_id=recipient_id,
        sender_id=sender_id,
        type=notification_type,
        title=title,
        message=message,
        data={"post_id": post_id, "sender_id": sender_id, "sender_name": sender_name},
        channels=[NotificationChannel.PUSH, NotificationChannel.IN_APP]
    )
    
    return await service.create_notification(notification)

async def send_welcome_notification(user_id: str):
    """Send welcome notification to new users"""
    service = NotificationService()
    
    notification = NotificationCreate(
        recipient_id=user_id,
        type=NotificationType.WELCOME,
        title="Welcome to StudyConnect! 🎓",
        message="Complete your profile to start connecting with fellow international students",
        data={"action": "complete_profile"},
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    )
    
    return await service.create_notification(notification)