from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from chat_models import *
from server import db, get_current_user, User
import asyncio
from datetime import datetime

chat_router = APIRouter(prefix="/api/chat")

# Conversation Management
@chat_router.post("/conversations", response_model=Conversation)
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

@chat_router.get("/conversations", response_model=List[ConversationWithDetails])
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

# Message Management
@chat_router.post("/messages", response_model=Message)
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

@chat_router.get("/messages/{conversation_id}", response_model=List[Message])
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

@chat_router.post("/messages/{message_id}/read")
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

@chat_router.post("/messages/{message_id}/edit")
async def edit_message(
    message_id: str,
    new_content: str,
    current_user: User = Depends(get_current_user)
):
    # Verify message ownership and update
    result = await db.messages.update_one(
        {
            "id": message_id,
            "sender_id": current_user.id,
            "is_deleted": False
        },
        {
            "$set": {
                "content": new_content,
                "edited_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found or cannot be edited")
    
    return {"message": "Message updated successfully"}

@chat_router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    # Soft delete message (mark as deleted)
    result = await db.messages.update_one(
        {
            "id": message_id,
            "sender_id": current_user.id
        },
        {
            "$set": {
                "is_deleted": True,
                "content": "This message was deleted"
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found or cannot be deleted")
    
    return {"message": "Message deleted successfully"}

# Search Messages
@chat_router.get("/search", response_model=List[Message])
async def search_messages(
    query: str = Query(..., min_length=1),
    conversation_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=50)
):
    # Build search query
    search_query = {
        "content": {"$regex": query, "$options": "i"},
        "is_deleted": False
    }
    
    if conversation_id:
        # Verify user is participant in specific conversation
        conversation = await db.conversations.find_one({"id": conversation_id})
        if not conversation or current_user.id not in conversation["participants"]:
            raise HTTPException(status_code=403, detail="Access denied to conversation")
        
        search_query["conversation_id"] = conversation_id
    else:
        # Search only in user's conversations
        user_conversations = await db.conversations.find({
            "participants": current_user.id
        }).to_list(1000)
        
        conversation_ids = [conv["id"] for conv in user_conversations]
        search_query["conversation_id"] = {"$in": conversation_ids}
    
    # Execute search
    messages_cursor = db.messages.find(search_query).sort("timestamp", -1).limit(limit)
    messages_docs = await messages_cursor.to_list(length=limit)
    
    messages = []
    for msg_doc in messages_docs:
        message = Message(**{k: v for k, v in msg_doc.items() if k != '_id'})
        messages.append(message)
    
    return messages