"""
Notification System API Routes for StudyConnect
Handles notification CRUD operations, preferences, and push token management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta

from notifications_models import (
    Notification, NotificationCreate, NotificationPreferences, NotificationPreferencesUpdate,
    PushToken, PushTokenCreate, NotificationStats, NotificationBatch,
    NotificationType, NotificationStatus, NotificationChannel
)
from notifications_service import (
    NotificationService, send_connection_request_notification,
    send_connection_accepted_notification, send_message_notification,
    send_event_notification, send_post_notification, send_welcome_notification
)
from server import get_current_user, User, db

notifications_router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# Notification Management Endpoints

@notifications_router.get("/", response_model=List[Notification])
async def get_notifications(
    status: Optional[NotificationStatus] = None,
    type: Optional[NotificationType] = None,
    unread_only: bool = False,
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Get user's notifications"""
    try:
        # Build query
        query = {"recipient_id": current_user.id}
        
        if status:
            query["status"] = status
        if type:
            query["type"] = type
        if unread_only:
            query["read_at"] = None
        
        # Get notifications
        notifications_cursor = db.notifications.find(query).sort("created_at", -1).skip(skip).limit(limit)
        notifications_docs = await notifications_cursor.to_list(length=limit)
        
        notifications = []
        for notif_doc in notifications_docs:
            notifications.append(Notification(**{k: v for k, v in notif_doc.items() if k != '_id'}))
        
        return notifications
        
    except Exception as e:
        print(f"Error getting notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get notifications")

@notifications_router.get("/unread/count")
async def get_unread_count(current_user: User = Depends(get_current_user)):
    """Get unread notification count"""
    try:
        count = await db.notifications.count_documents({
            "recipient_id": current_user.id,
            "read_at": None,
            "status": {"$ne": NotificationStatus.FAILED}
        })
        
        return {"unread_count": count}
        
    except Exception as e:
        print(f"Error getting unread count: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get unread count")

@notifications_router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read"""
    try:
        service = NotificationService()
        success = await service.mark_as_read(notification_id, current_user.id)
        
        if success:
            return {"message": "Notification marked as read"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found or already read")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")

@notifications_router.post("/read-all")
async def mark_all_notifications_read(current_user: User = Depends(get_current_user)):
    """Mark all notifications as read"""
    try:
        service = NotificationService()
        count = await service.mark_all_as_read(current_user.id)
        
        return {"message": f"Marked {count} notifications as read"}
        
    except Exception as e:
        print(f"Error marking all notifications as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark notifications as read")

@notifications_router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a notification"""
    try:
        result = await db.notifications.delete_one({
            "id": notification_id,
            "recipient_id": current_user.id
        })
        
        if result.deleted_count > 0:
            return {"message": "Notification deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")

# Notification Preferences Endpoints

@notifications_router.get("/preferences", response_model=NotificationPreferences)
async def get_notification_preferences(current_user: User = Depends(get_current_user)):
    """Get user's notification preferences"""
    try:
        service = NotificationService()
        preferences = await service.get_user_preferences(current_user.id)
        return preferences
        
    except Exception as e:
        print(f"Error getting notification preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get notification preferences")

@notifications_router.put("/preferences", response_model=NotificationPreferences)
async def update_notification_preferences(
    preferences_update: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user's notification preferences"""
    try:
        # Get current preferences
        prefs_doc = await db.notification_preferences.find_one({"user_id": current_user.id})
        
        if not prefs_doc:
            # Create default preferences
            default_prefs = NotificationPreferences(user_id=current_user.id)
            await db.notification_preferences.insert_one(default_prefs.dict())
            prefs_doc = default_prefs.dict()
        
        # Update preferences
        update_data = {k: v for k, v in preferences_update.dict(exclude_unset=True).items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        await db.notification_preferences.update_one(
            {"user_id": current_user.id},
            {"$set": update_data}
        )
        
        # Return updated preferences
        updated_prefs_doc = await db.notification_preferences.find_one({"user_id": current_user.id})
        return NotificationPreferences(**{k: v for k, v in updated_prefs_doc.items() if k != '_id'})
        
    except Exception as e:
        print(f"Error updating notification preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update notification preferences")

# Push Token Management Endpoints

@notifications_router.post("/push-tokens", response_model=PushToken)
async def register_push_token(
    token_data: PushTokenCreate,
    current_user: User = Depends(get_current_user)
):
    """Register a push notification token"""
    try:
        # Check if token already exists
        existing_token = await db.push_tokens.find_one({
            "user_id": current_user.id,
            "token": token_data.token
        })
        
        if existing_token:
            # Update existing token
            await db.push_tokens.update_one(
                {"user_id": current_user.id, "token": token_data.token},
                {
                    "$set": {
                        "is_active": True,
                        "updated_at": datetime.utcnow(),
                        "last_used": datetime.utcnow(),
                        "device_type": token_data.device_type,
                        "device_id": token_data.device_id,
                        "app_version": token_data.app_version,
                    }
                }
            )
            
            updated_token_doc = await db.push_tokens.find_one({
                "user_id": current_user.id,
                "token": token_data.token
            })
            return PushToken(**{k: v for k, v in updated_token_doc.items() if k != '_id'})
        else:
            # Create new token
            push_token = PushToken(
                user_id=current_user.id,
                **token_data.dict()
            )
            
            await db.push_tokens.insert_one(push_token.dict())
            return push_token
            
    except Exception as e:
        print(f"Error registering push token: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register push token")

@notifications_router.delete("/push-tokens/{token}")
async def deactivate_push_token(
    token: str,
    current_user: User = Depends(get_current_user)
):
    """Deactivate a push notification token"""
    try:
        result = await db.push_tokens.update_one(
            {"user_id": current_user.id, "token": token},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            return {"message": "Push token deactivated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Push token not found")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deactivating push token: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to deactivate push token")

@notifications_router.get("/push-tokens", response_model=List[PushToken])
async def get_user_push_tokens(current_user: User = Depends(get_current_user)):
    """Get user's push tokens"""
    try:
        tokens_cursor = db.push_tokens.find({"user_id": current_user.id})
        tokens_docs = await tokens_cursor.to_list(50)
        
        tokens = []
        for token_doc in tokens_docs:
            tokens.append(PushToken(**{k: v for k, v in token_doc.items() if k != '_id'}))
        
        return tokens
        
    except Exception as e:
        print(f"Error getting push tokens: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get push tokens")

# Notification Statistics Endpoint

@notifications_router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(current_user: User = Depends(get_current_user)):
    """Get notification statistics for the user"""
    try:
        # Total notifications
        total_notifications = await db.notifications.count_documents({"recipient_id": current_user.id})
        
        # Unread count
        unread_count = await db.notifications.count_documents({
            "recipient_id": current_user.id,
            "read_at": None,
            "status": {"$ne": NotificationStatus.FAILED}
        })
        
        # Notifications by type
        type_pipeline = [
            {"$match": {"recipient_id": current_user.id}},
            {"$group": {"_id": "$type", "count": {"$sum": 1}}}
        ]
        type_result = await db.notifications.aggregate(type_pipeline).to_list(20)
        notifications_by_type = {item["_id"]: item["count"] for item in type_result}
        
        # Notifications by status
        status_pipeline = [
            {"$match": {"recipient_id": current_user.id}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_result = await db.notifications.aggregate(status_pipeline).to_list(10)
        notifications_by_status = {item["_id"]: item["count"] for item in status_result}
        
        # Last notification
        last_notification_doc = await db.notifications.find_one(
            {"recipient_id": current_user.id},
            sort=[("created_at", -1)]
        )
        last_notification = last_notification_doc["created_at"] if last_notification_doc else None
        
        return NotificationStats(
            user_id=current_user.id,
            total_notifications=total_notifications,
            unread_count=unread_count,
            notifications_by_type=notifications_by_type,
            notifications_by_status=notifications_by_status,
            last_notification=last_notification
        )
        
    except Exception as e:
        print(f"Error getting notification stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get notification stats")

# Test Notification Endpoint (for development)

@notifications_router.post("/test")
async def send_test_notification(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Send a test notification (for development/testing)"""
    try:
        service = NotificationService()
        
        notification = NotificationCreate(
            recipient_id=current_user.id,
            type=NotificationType.SYSTEM_ANNOUNCEMENT,
            title="Test Notification 🧪",
            message="This is a test notification from StudyConnect!",
            data={"test": True, "timestamp": datetime.utcnow().isoformat()},
            channels=[NotificationChannel.PUSH, NotificationChannel.IN_APP]
        )
        
        # Send notification in background
        background_tasks.add_task(service.create_notification, notification)
        
        return {"message": "Test notification queued successfully"}
        
    except Exception as e:
        print(f"Error sending test notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send test notification")

# Bulk Operations (Admin/System use)

@notifications_router.post("/broadcast")
async def broadcast_notification(
    notification_batch: NotificationBatch,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Broadcast notification to multiple users (admin feature)"""
    try:
        # For now, allow any user to send broadcasts
        # In production, this should be restricted to admin users
        
        service = NotificationService()
        
        notification_data = NotificationCreate(
            recipient_id="", # Will be set for each recipient
            type=notification_batch.type,
            title=notification_batch.title,
            message=notification_batch.message,
            data=notification_batch.data,
            priority=notification_batch.priority,
            channels=notification_batch.channels,
            scheduled_at=notification_batch.scheduled_at
        )
        
        # Send notifications in background
        background_tasks.add_task(
            service.send_bulk_notifications,
            notification_batch.recipient_ids,
            notification_data
        )
        
        return {
            "message": f"Broadcast notification queued for {len(notification_batch.recipient_ids)} recipients"
        }
        
    except Exception as e:
        print(f"Error broadcasting notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to broadcast notification")