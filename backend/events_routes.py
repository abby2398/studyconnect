"""
Events System API Routes for International Student Networking App
Handles event creation, management, attendance, and discussions
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
from events_models import (
    Event, EventCreate, EventUpdate, EventWithDetails,
    EventAttendee, EventAttendeeCreate, EventAttendeeWithUser,
    EventMessage, EventMessageCreate, EventMessageWithUser,
    EventCategory, EventStatus, AttendeeStatus
)
from server import get_current_user, User, db
import json

events_router = APIRouter(prefix="/api/events", tags=["events"])

# Event Management Endpoints

@events_router.post("/", response_model=Event)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new event"""
    try:
        # Validate datetime
        if event_data.start_datetime <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Event start time must be in the future")
        
        if event_data.end_datetime <= event_data.start_datetime:
            raise HTTPException(status_code=400, detail="Event end time must be after start time")
        
        # Create event
        event = Event(
            **event_data.dict(),
            creator_id=current_user.id
        )
        
        # Store event
        await db.events.insert_one(event.dict())
        
        # Auto-join creator to the event
        attendee = EventAttendee(
            event_id=event.id,
            user_id=current_user.id,
            status=AttendeeStatus.JOINED,
            notes="Event Creator"
        )
        await db.event_attendees.insert_one(attendee.dict())
        
        # Update attendee count
        await db.events.update_one(
            {"id": event.id},
            {"$set": {"current_attendees": 1}}
        )
        
        return event
        
    except Exception as e:
        print(f"Error creating event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create event")

@events_router.get("/", response_model=List[EventWithDetails])
async def get_events(
    category: Optional[EventCategory] = None,
    city: Optional[str] = None,
    country: Optional[str] = None,
    status: EventStatus = EventStatus.UPCOMING,
    creator_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Get events with filters"""
    try:
        query = {"status": status}
        
        # Apply filters
        if category:
            query["category"] = category
        if city:
            query["location.city"] = {"$regex": city, "$options": "i"}
        if country:
            query["location.country"] = {"$regex": country, "$options": "i"}
        if creator_id:
            query["creator_id"] = creator_id
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"tags": {"$regex": search, "$options": "i"}}
            ]
        
        # Get events
        events_cursor = db.events.find(query).sort("start_datetime", 1).skip(skip).limit(limit)
        events_docs = await events_cursor.to_list(length=limit)
        
        result = []
        for event_doc in events_docs:
            event = Event(**{k: v for k, v in event_doc.items() if k != '_id'})
            
            # Get creator details
            creator_doc = await db.users.find_one({"id": event.creator_id})
            creator = {
                "id": creator_doc["id"],
                "first_name": creator_doc["first_name"],
                "last_name": creator_doc["last_name"],
                "profile": creator_doc.get("profile")
            } if creator_doc else None
            
            # Get user attendance status
            attendee_doc = await db.event_attendees.find_one({
                "event_id": event.id,
                "user_id": current_user.id
            })
            user_attendance_status = AttendeeStatus(attendee_doc["status"]) if attendee_doc else None
            
            # Check if user can join
            can_join = True
            if event.max_attendees and event.current_attendees >= event.max_attendees:
                can_join = False
            if user_attendance_status == AttendeeStatus.JOINED:
                can_join = False
            
            result.append(EventWithDetails(
                event=event,
                creator=creator,
                attendee_count=event.current_attendees,
                user_attendance_status=user_attendance_status,
                is_creator=(event.creator_id == current_user.id),
                can_join=can_join
            ))
        
        return result
        
    except Exception as e:
        print(f"Error getting events: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get events")

@events_router.get("/{event_id}", response_model=EventWithDetails)
async def get_event(
    event_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get event details"""
    try:
        # Get event
        event_doc = await db.events.find_one({"id": event_id})
        if not event_doc:
            raise HTTPException(status_code=404, detail="Event not found")
        
        event = Event(**{k: v for k, v in event_doc.items() if k != '_id'})
        
        # Get creator details
        creator_doc = await db.users.find_one({"id": event.creator_id})
        creator = {
            "id": creator_doc["id"],
            "first_name": creator_doc["first_name"],
            "last_name": creator_doc["last_name"],
            "profile": creator_doc.get("profile")
        } if creator_doc else None
        
        # Get user attendance status
        attendee_doc = await db.event_attendees.find_one({
            "event_id": event.id,
            "user_id": current_user.id
        })
        user_attendance_status = AttendeeStatus(attendee_doc["status"]) if attendee_doc else None
        
        # Check if user can join
        can_join = True
        if event.max_attendees and event.current_attendees >= event.max_attendees:
            can_join = False
        if user_attendance_status == AttendeeStatus.JOINED:
            can_join = False
        
        return EventWithDetails(
            event=event,
            creator=creator,
            attendee_count=event.current_attendees,
            user_attendance_status=user_attendance_status,
            is_creator=(event.creator_id == current_user.id),
            can_join=can_join
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get event")

@events_router.put("/{event_id}", response_model=Event)
async def update_event(
    event_id: str,
    event_update: EventUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update event (creator only)"""
    try:
        # Check if event exists and user is creator
        event_doc = await db.events.find_one({"id": event_id})
        if not event_doc:
            raise HTTPException(status_code=404, detail="Event not found")
        
        if event_doc["creator_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Only event creator can update the event")
        
        # Prepare update data
        update_data = {k: v for k, v in event_update.dict(exclude_unset=True).items() if v is not None}
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Validate datetime if provided
            if "start_datetime" in update_data or "end_datetime" in update_data:
                start_time = update_data.get("start_datetime", event_doc["start_datetime"])
                end_time = update_data.get("end_datetime", event_doc["end_datetime"])
                
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                
                if end_time <= start_time:
                    raise HTTPException(status_code=400, detail="Event end time must be after start time")
            
            await db.events.update_one({"id": event_id}, {"$set": update_data})
        
        # Get updated event
        updated_event_doc = await db.events.find_one({"id": event_id})
        return Event(**{k: v for k, v in updated_event_doc.items() if k != '_id'})
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update event")

@events_router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete event (creator only)"""
    try:
        # Check if event exists and user is creator
        event_doc = await db.events.find_one({"id": event_id})
        if not event_doc:
            raise HTTPException(status_code=404, detail="Event not found")
        
        if event_doc["creator_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Only event creator can delete the event")
        
        # Delete event and related data
        await db.events.delete_one({"id": event_id})
        await db.event_attendees.delete_many({"event_id": event_id})
        await db.event_messages.delete_many({"event_id": event_id})
        
        return {"message": "Event deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete event")

# Event Attendance Endpoints

@events_router.post("/{event_id}/join", response_model=EventAttendee)
async def join_event(
    event_id: str,
    attendee_data: EventAttendeeCreate,
    current_user: User = Depends(get_current_user)
):
    """Join an event"""
    try:
        # Check if event exists
        event_doc = await db.events.find_one({"id": event_id})
        if not event_doc:
            raise HTTPException(status_code=404, detail="Event not found")
        
        event = Event(**{k: v for k, v in event_doc.items() if k != '_id'})
        
        # Check if user already joined
        existing_attendee = await db.event_attendees.find_one({
            "event_id": event_id,
            "user_id": current_user.id
        })
        
        if existing_attendee:
            if existing_attendee["status"] == AttendeeStatus.JOINED:
                raise HTTPException(status_code=400, detail="Already joined this event")
            else:
                # Update existing status
                await db.event_attendees.update_one(
                    {"event_id": event_id, "user_id": current_user.id},
                    {"$set": {"status": attendee_data.status, "joined_at": datetime.utcnow()}}
                )
        else:
            # Check capacity
            if event.max_attendees and event.current_attendees >= event.max_attendees:
                raise HTTPException(status_code=400, detail="Event is full")
            
            # Create new attendee record
            attendee = EventAttendee(
                event_id=event_id,
                user_id=current_user.id,
                status=attendee_data.status,
                notes=attendee_data.notes
            )
            await db.event_attendees.insert_one(attendee.dict())
        
        # Update attendee count if joining
        if attendee_data.status == AttendeeStatus.JOINED:
            await db.events.update_one(
                {"id": event_id},
                {"$inc": {"current_attendees": 1}}
            )
        
        # Get updated attendee record
        attendee_doc = await db.event_attendees.find_one({
            "event_id": event_id,
            "user_id": current_user.id
        })
        return EventAttendee(**{k: v for k, v in attendee_doc.items() if k != '_id'})
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error joining event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to join event")

@events_router.delete("/{event_id}/leave")
async def leave_event(
    event_id: str,
    current_user: User = Depends(get_current_user)
):
    """Leave an event"""
    try:
        # Check if user is attendee
        attendee_doc = await db.event_attendees.find_one({
            "event_id": event_id,
            "user_id": current_user.id
        })
        
        if not attendee_doc:
            raise HTTPException(status_code=404, detail="Not attending this event")
        
        # Check if user is creator (creators can't leave their own events)
        event_doc = await db.events.find_one({"id": event_id})
        if event_doc and event_doc["creator_id"] == current_user.id:
            raise HTTPException(status_code=400, detail="Event creators cannot leave their own events")
        
        # Remove attendee and update count
        if attendee_doc["status"] == AttendeeStatus.JOINED:
            await db.events.update_one(
                {"id": event_id},
                {"$inc": {"current_attendees": -1}}
            )
        
        await db.event_attendees.delete_one({
            "event_id": event_id,
            "user_id": current_user.id
        })
        
        return {"message": "Left event successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error leaving event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to leave event")

@events_router.get("/{event_id}/attendees", response_model=List[EventAttendeeWithUser])
async def get_event_attendees(
    event_id: str,
    status: Optional[AttendeeStatus] = None,
    current_user: User = Depends(get_current_user)
):
    """Get event attendees"""
    try:
        # Check if event exists
        event_doc = await db.events.find_one({"id": event_id})
        if not event_doc:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Build query
        query = {"event_id": event_id}
        if status:
            query["status"] = status
        
        # Get attendees
        attendees_cursor = db.event_attendees.find(query).sort("joined_at", 1)
        attendees_docs = await attendees_cursor.to_list(100)
        
        result = []
        for attendee_doc in attendees_docs:
            attendee = EventAttendee(**{k: v for k, v in attendee_doc.items() if k != '_id'})
            
            # Get user details
            user_doc = await db.users.find_one({"id": attendee.user_id})
            user = {
                "id": user_doc["id"],
                "first_name": user_doc["first_name"],
                "last_name": user_doc["last_name"],
                "profile": user_doc.get("profile")
            } if user_doc else None
            
            if user:
                result.append(EventAttendeeWithUser(
                    attendee=attendee,
                    user=user
                ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting event attendees: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get event attendees")

# Event Messages/Discussion Endpoints

@events_router.post("/{event_id}/messages", response_model=EventMessage)
async def send_event_message(
    event_id: str,
    message_data: EventMessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Send message in event discussion"""
    try:
        # Check if event exists
        event_doc = await db.events.find_one({"id": event_id})
        if not event_doc:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Check if user is attendee or creator
        attendee_doc = await db.event_attendees.find_one({
            "event_id": event_id,
            "user_id": current_user.id
        })
        
        is_creator = event_doc["creator_id"] == current_user.id
        
        if not attendee_doc and not is_creator:
            raise HTTPException(status_code=403, detail="Must be an attendee to participate in discussion")
        
        # Only creators can send announcements
        if message_data.is_announcement and not is_creator:
            raise HTTPException(status_code=403, detail="Only event creators can send announcements")
        
        # Create message
        message = EventMessage(
            event_id=event_id,
            user_id=current_user.id,
            message=message_data.message,
            is_announcement=message_data.is_announcement,
            reply_to_id=message_data.reply_to_id
        )
        
        await db.event_messages.insert_one(message.dict())
        return message
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending event message: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send message")

@events_router.get("/{event_id}/messages", response_model=List[EventMessageWithUser])
async def get_event_messages(
    event_id: str,
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Get event discussion messages"""
    try:
        # Check if event exists
        event_doc = await db.events.find_one({"id": event_id})
        if not event_doc:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Check if user is attendee or creator
        attendee_doc = await db.event_attendees.find_one({
            "event_id": event_id,
            "user_id": current_user.id
        })
        
        is_creator = event_doc["creator_id"] == current_user.id
        
        if not attendee_doc and not is_creator:
            raise HTTPException(status_code=403, detail="Must be an attendee to view discussion")
        
        # Get messages
        messages_cursor = db.event_messages.find({"event_id": event_id}).sort("timestamp", 1).skip(skip).limit(limit)
        messages_docs = await messages_cursor.to_list(length=limit)
        
        result = []
        for message_doc in messages_docs:
            message = EventMessage(**{k: v for k, v in message_doc.items() if k != '_id'})
            
            # Get user details
            user_doc = await db.users.find_one({"id": message.user_id})
            user = {
                "id": user_doc["id"],
                "first_name": user_doc["first_name"],
                "last_name": user_doc["last_name"],
                "profile": user_doc.get("profile")
            } if user_doc else None
            
            if user:
                result.append(EventMessageWithUser(
                    message=message,
                    user=user
                ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting event messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get event messages")

# User's Events Endpoints

@events_router.get("/my/created", response_model=List[EventWithDetails])
async def get_my_created_events(
    status: Optional[EventStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Get events created by current user"""
    try:
        query = {"creator_id": current_user.id}
        if status:
            query["status"] = status
        
        events_cursor = db.events.find(query).sort("created_at", -1).skip(skip).limit(limit)
        events_docs = await events_cursor.to_list(length=limit)
        
        result = []
        for event_doc in events_docs:
            event = Event(**{k: v for k, v in event_doc.items() if k != '_id'})
            
            creator = {
                "id": current_user.id,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "profile": current_user.profile.dict() if current_user.profile else None
            }
            
            result.append(EventWithDetails(
                event=event,
                creator=creator,
                attendee_count=event.current_attendees,
                user_attendance_status=AttendeeStatus.JOINED,
                is_creator=True,
                can_join=False
            ))
        
        return result
        
    except Exception as e:
        print(f"Error getting created events: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get created events")

@events_router.get("/my/attending", response_model=List[EventWithDetails])
async def get_my_attending_events(
    status: Optional[AttendeeStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Get events user is attending"""
    try:
        # Get user's attendee records
        query = {"user_id": current_user.id}
        if status:
            query["status"] = status
        
        attendees_cursor = db.event_attendees.find(query).sort("joined_at", -1).skip(skip).limit(limit)
        attendees_docs = await attendees_cursor.to_list(length=limit)
        
        result = []
        for attendee_doc in attendees_docs:
            attendee = EventAttendee(**{k: v for k, v in attendee_doc.items() if k != '_id'})
            
            # Get event details
            event_doc = await db.events.find_one({"id": attendee.event_id})
            if not event_doc:
                continue
            
            event = Event(**{k: v for k, v in event_doc.items() if k != '_id'})
            
            # Get creator details
            creator_doc = await db.users.find_one({"id": event.creator_id})
            creator = {
                "id": creator_doc["id"],
                "first_name": creator_doc["first_name"],
                "last_name": creator_doc["last_name"],
                "profile": creator_doc.get("profile")
            } if creator_doc else None
            
            result.append(EventWithDetails(
                event=event,
                creator=creator,
                attendee_count=event.current_attendees,
                user_attendance_status=attendee.status,
                is_creator=(event.creator_id == current_user.id),
                can_join=False
            ))
        
        return result
        
    except Exception as e:
        print(f"Error getting attending events: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get attending events")