"""
AI Assistant API Routes for International Student Networking App
Handles AI chat functionality and student assistance
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from ai_models import (
    AIMessage, AIMessageCreate, AIChat, AIChatWithMessages,
    AIAssistantStats, MessageRole
)
from server import get_current_user, User, db
from emergentintegrations.llm.chat import LlmChat, UserMessage

ai_router = APIRouter(prefix="/api/ai", tags=["ai"])

# AI Assistant System Message
SYSTEM_MESSAGE = """You are an AI assistant for StudyConnect, a mobile app that helps international students connect before arriving at their new institution. Your role is to help students with:

1. **Academic Questions**: Course selection, university systems, study tips, academic culture
2. **Living Abroad**: Housing, visa info, cultural adaptation, practical tips
3. **Social Connections**: Making friends, joining events, networking advice
4. **App Usage**: How to use StudyConnect features (posts, events, connections, chat)
5. **General Student Life**: Campus resources, student organizations, local information

**Guidelines**:
- Be helpful, friendly, and encouraging
- Provide practical, actionable advice
- If you don't know something specific about a university or location, suggest resources where they can find accurate information
- Encourage students to use app features to connect with others
- Be sensitive to cultural differences and challenges international students face
- Keep responses concise but informative (aim for 2-4 paragraphs)
- When relevant, suggest connecting with other students through the app

**Key StudyConnect Features to mention when relevant**:
- **Posts**: Share updates, ask questions, find study partners
- **Events**: Join or create study groups, social events, networking meetups
- **Search**: Find students from same university, country, or course
- **Connections**: Send connection requests to build your network
- **Chat**: Message other students directly

Always maintain a supportive and encouraging tone. Remember that international students may feel overwhelmed, so provide reassurance along with practical advice."""

async def get_ai_chat_instance(user_id: str) -> LlmChat:
    """Get AI chat instance for the user"""
    try:
        api_key = os.getenv("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"student_assistant_{user_id}",
            system_message=SYSTEM_MESSAGE
        )
        
        # Use GPT-4o-mini for efficiency
        chat.with_model("openai", "gpt-4o-mini")
        
        return chat
    except Exception as e:
        print(f"Error creating AI chat instance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initialize AI assistant")

async def get_user_context(user: User) -> dict:
    """Get relevant user context for AI responses"""
    context = {
        "user_name": f"{user.first_name} {user.last_name}",
        "user_id": user.id,
    }
    
    if user.profile:
        profile = user.profile
        context.update({
            "university": profile.university,
            "course": profile.course,
            "origin_country": profile.origin_country,
            "destination_country": profile.destination_country,
            "academic_year": profile.academic_year,
            "interests": profile.interests,
        })
    
    return context

@ai_router.post("/chat/send", response_model=AIMessage)
async def send_message_to_ai(
    message_data: AIMessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Send a message to the AI assistant"""
    start_time = time.time()
    
    try:
        # Get or create chat session
        session_id = f"chat_{current_user.id}"
        
        # Get AI chat instance
        ai_chat = await get_ai_chat_instance(current_user.id)
        
        # Get user context for personalized responses
        user_context = await get_user_context(current_user)
        
        # Enhance message with user context
        enhanced_message = message_data.message
        if user_context.get('university'):
            enhanced_message += f"\n\n[User Context: Student at {user_context['university']}"
            if user_context.get('course'):
                enhanced_message += f", studying {user_context['course']}"
            if user_context.get('origin_country') and user_context.get('destination_country'):
                enhanced_message += f", from {user_context['origin_country']} to {user_context['destination_country']}"
            enhanced_message += "]"
        
        # Store user message
        user_message = AIMessage(
            user_id=current_user.id,
            session_id=session_id,
            role=MessageRole.USER,
            message=message_data.message,
            context=message_data.context
        )
        await db.ai_messages.insert_one(user_message.dict())
        
        # Send message to AI
        ai_user_message = UserMessage(text=enhanced_message)
        ai_response = await ai_chat.send_message(ai_user_message)
        
        # Calculate response time
        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        # Store AI response
        ai_message = AIMessage(
            user_id=current_user.id,
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            message=ai_response,
            context=user_context,
            response_time_ms=response_time_ms,
            tokens_used=None  # Could be calculated if needed
        )
        await db.ai_messages.insert_one(ai_message.dict())
        
        # Update or create chat record
        chat_doc = await db.ai_chats.find_one({"session_id": session_id})
        if chat_doc:
            await db.ai_chats.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "updated_at": ai_message.timestamp,
                        "title": message_data.message[:50] + "..." if len(message_data.message) > 50 else message_data.message
                    },
                    "$inc": {"message_count": 2}  # User message + AI response
                }
            )
        else:
            chat = AIChat(
                user_id=current_user.id,
                session_id=session_id,
                title=message_data.message[:50] + "..." if len(message_data.message) > 50 else message_data.message,
                message_count=2
            )
            await db.ai_chats.insert_one(chat.dict())
        
        return ai_message
        
    except Exception as e:
        print(f"Error in AI chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process AI request")

@ai_router.get("/chat/history", response_model=List[AIMessage])
async def get_chat_history(
    session_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Get AI chat history for the user"""
    try:
        query = {"user_id": current_user.id}
        if session_id:
            query["session_id"] = session_id
        else:
            # Default to main chat session
            query["session_id"] = f"chat_{current_user.id}"
        
        messages_cursor = db.ai_messages.find(query).sort("timestamp", 1).skip(skip).limit(limit)
        messages_docs = await messages_cursor.to_list(length=limit)
        
        messages = []
        for msg_doc in messages_docs:
            messages.append(AIMessage(**{k: v for k, v in msg_doc.items() if k != '_id'}))
        
        return messages
        
    except Exception as e:
        print(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get chat history")

@ai_router.get("/chats", response_model=List[AIChat])
async def get_user_chats(
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Get user's AI chat sessions"""
    try:
        chats_cursor = db.ai_chats.find({"user_id": current_user.id}).sort("updated_at", -1).skip(skip).limit(limit)
        chats_docs = await chats_cursor.to_list(length=limit)
        
        chats = []
        for chat_doc in chats_docs:
            chats.append(AIChat(**{k: v for k, v in chat_doc.items() if k != '_id'}))
        
        return chats
        
    except Exception as e:
        print(f"Error getting user chats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get chats")

@ai_router.delete("/chat/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a chat session and its messages"""
    try:
        # Verify chat belongs to user
        chat_doc = await db.ai_chats.find_one({"session_id": session_id, "user_id": current_user.id})
        if not chat_doc:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Delete chat messages
        await db.ai_messages.delete_many({"session_id": session_id, "user_id": current_user.id})
        
        # Delete chat record
        await db.ai_chats.delete_one({"session_id": session_id, "user_id": current_user.id})
        
        return {"message": "Chat session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting chat session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete chat session")

@ai_router.get("/suggestions")
async def get_ai_suggestions(current_user: User = Depends(get_current_user)):
    """Get AI-powered suggestions for the user"""
    try:
        suggestions = []
        
        # Base suggestions for all users
        base_suggestions = [
            "How do I make friends as an international student?",
            "What should I know about campus culture?",
            "Help me find study partners",
            "Tips for adjusting to a new country",
            "How to use StudyConnect effectively"
        ]
        
        # Personalized suggestions based on user profile
        if current_user.profile:
            profile = current_user.profile
            
            if profile.university:
                suggestions.append(f"What should I know about {profile.university}?")
            
            if profile.course:
                suggestions.append(f"Study tips for {profile.course} students")
            
            if profile.origin_country and profile.destination_country:
                suggestions.append(f"Advice for {profile.origin_country} students in {profile.destination_country}")
            
            if profile.interests:
                suggestions.append(f"Find students with interests in {', '.join(profile.interests[:2])}")
        
        # Add base suggestions if we don't have enough personalized ones
        while len(suggestions) < 5:
            for suggestion in base_suggestions:
                if suggestion not in suggestions:
                    suggestions.append(suggestion)
                    break
            if len(suggestions) >= 5:
                break
        
        return {"suggestions": suggestions[:5]}
        
    except Exception as e:
        print(f"Error getting AI suggestions: {str(e)}")
        return {"suggestions": base_suggestions[:5]}

@ai_router.get("/stats", response_model=AIAssistantStats)
async def get_ai_stats(current_user: User = Depends(get_current_user)):
    """Get AI assistant usage statistics for the user"""
    try:
        # Get total messages
        total_messages = await db.ai_messages.count_documents({"user_id": current_user.id})
        
        # Get total chats
        total_chats = await db.ai_chats.count_documents({"user_id": current_user.id})
        
        # Get average response time
        pipeline = [
            {"$match": {"user_id": current_user.id, "role": "assistant", "response_time_ms": {"$exists": True}}},
            {"$group": {"_id": None, "avg_response_time": {"$avg": "$response_time_ms"}}}
        ]
        avg_result = await db.ai_messages.aggregate(pipeline).to_list(1)
        avg_response_time = avg_result[0]["avg_response_time"] if avg_result else 0
        
        # Get last interaction
        last_message = await db.ai_messages.find_one(
            {"user_id": current_user.id},
            sort=[("timestamp", -1)]
        )
        last_interaction = last_message["timestamp"] if last_message else None
        
        return AIAssistantStats(
            user_id=current_user.id,
            total_messages=total_messages,
            total_tokens_used=0,  # Could be implemented if needed
            total_chats=total_chats,
            average_response_time_ms=avg_response_time,
            last_interaction=last_interaction
        )
        
    except Exception as e:
        print(f"Error getting AI stats: {str(e)}")
        # Return default stats on error
        return AIAssistantStats(
            user_id=current_user.id,
            total_messages=0,
            total_tokens_used=0,
            total_chats=0,
            average_response_time_ms=0,
            last_interaction=None
        )