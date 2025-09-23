import socketio
from typing import Dict, Set
import json
from datetime import datetime
import asyncio
from chat_models import TypingIndicator, OnlineStatus, Message
from server import db

# Store active connections
active_connections: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
user_sessions: Dict[str, str] = {}  # session_id -> user_id
typing_users: Dict[str, Dict[str, datetime]] = {}  # conversation_id -> {user_id: timestamp}

class ChatSocketHandler:
    def __init__(self, sio: socketio.AsyncServer):
        self.sio = sio
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.sio.event
        async def connect(sid, environ, auth):
            print(f"Socket connected: {sid}")
            
        @self.sio.event
        async def disconnect(sid):
            await self.handle_disconnect(sid)
            
        @self.sio.event
        async def authenticate(sid, data):
            await self.handle_authenticate(sid, data)
            
        @self.sio.event
        async def join_conversation(sid, data):
            await self.handle_join_conversation(sid, data)
            
        @self.sio.event
        async def leave_conversation(sid, data):
            await self.handle_leave_conversation(sid, data)
            
        @self.sio.event
        async def send_message(sid, data):
            await self.handle_send_message(sid, data)
            
        @self.sio.event
        async def typing_start(sid, data):
            await self.handle_typing_start(sid, data)
            
        @self.sio.event
        async def typing_stop(sid, data):
            await self.handle_typing_stop(sid, data)
            
        @self.sio.event
        async def message_read(sid, data):
            await self.handle_message_read(sid, data)
            
        @self.sio.event
        async def get_online_users(sid, data):
            await self.handle_get_online_users(sid, data)
    
    async def handle_disconnect(self, sid):
        print(f"Socket disconnected: {sid}")
        
        if sid in user_sessions:
            user_id = user_sessions[sid]
            
            # Remove session from active connections
            if user_id in active_connections:
                active_connections[user_id].discard(sid)
                if not active_connections[user_id]:
                    del active_connections[user_id]
                    
                    # Update user's offline status
                    await self.update_user_online_status(user_id, False)
            
            del user_sessions[sid]
    
    async def handle_authenticate(self, sid, data):
        try:
            user_id = data.get('user_id')
            token = data.get('token')
            
            if not user_id or not token:
                await self.sio.emit('auth_error', {'message': 'Missing user_id or token'}, to=sid)
                return
            
            # TODO: Verify JWT token here
            # For now, we'll trust the user_id from client
            
            # Add to active connections
            if user_id not in active_connections:
                active_connections[user_id] = set()
            active_connections[user_id].add(sid)
            user_sessions[sid] = user_id
            
            # Update user's online status
            await self.update_user_online_status(user_id, True)
            
            await self.sio.emit('authenticated', {'user_id': user_id}, to=sid)
            print(f"User {user_id} authenticated with session {sid}")
            
        except Exception as e:
            print(f"Authentication error: {e}")
            await self.sio.emit('auth_error', {'message': 'Authentication failed'}, to=sid)
    
    async def handle_join_conversation(self, sid, data):
        try:
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                return
            
            await self.sio.enter_room(sid, f"conversation_{conversation_id}")
            await self.sio.emit('joined_conversation', {
                'conversation_id': conversation_id
            }, to=sid)
            
            print(f"Session {sid} joined conversation {conversation_id}")
            
        except Exception as e:
            print(f"Error joining conversation: {e}")
    
    async def handle_leave_conversation(self, sid, data):
        try:
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                return
            
            await self.sio.leave_room(sid, f"conversation_{conversation_id}")
            
            # Stop typing indicator
            if sid in user_sessions:
                user_id = user_sessions[sid]
                await self.handle_typing_stop(sid, {
                    'conversation_id': conversation_id,
                    'user_id': user_id
                })
            
            print(f"Session {sid} left conversation {conversation_id}")
            
        except Exception as e:
            print(f"Error leaving conversation: {e}")
    
    async def handle_send_message(self, sid, data):
        try:
            conversation_id = data.get('conversation_id')
            message_data = data.get('message')
            
            if not conversation_id or not message_data:
                return
            
            user_id = user_sessions.get(sid)
            if not user_id:
                return
            
            # Broadcast message to all participants in conversation
            await self.sio.emit('new_message', {
                'conversation_id': conversation_id,
                'message': message_data,
                'sender_id': user_id,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"conversation_{conversation_id}")
            
            # Stop typing indicator for sender
            await self.handle_typing_stop(sid, {
                'conversation_id': conversation_id,
                'user_id': user_id
            })
            
        except Exception as e:
            print(f"Error handling send_message: {e}")
    
    async def handle_typing_start(self, sid, data):
        try:
            conversation_id = data.get('conversation_id')
            user_id = user_sessions.get(sid)
            
            if not conversation_id or not user_id:
                return
            
            # Track typing user
            if conversation_id not in typing_users:
                typing_users[conversation_id] = {}
            typing_users[conversation_id][user_id] = datetime.utcnow()
            
            # Broadcast typing indicator to other participants
            await self.sio.emit('typing_start', {
                'conversation_id': conversation_id,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"conversation_{conversation_id}", skip_sid=sid)
            
        except Exception as e:
            print(f"Error handling typing_start: {e}")
    
    async def handle_typing_stop(self, sid, data):
        try:
            conversation_id = data.get('conversation_id')
            user_id = data.get('user_id') or user_sessions.get(sid)
            
            if not conversation_id or not user_id:
                return
            
            # Remove from typing users
            if conversation_id in typing_users and user_id in typing_users[conversation_id]:
                del typing_users[conversation_id][user_id]
                
                if not typing_users[conversation_id]:
                    del typing_users[conversation_id]
            
            # Broadcast typing stop to other participants
            await self.sio.emit('typing_stop', {
                'conversation_id': conversation_id,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"conversation_{conversation_id}", skip_sid=sid)
            
        except Exception as e:
            print(f"Error handling typing_stop: {e}")
    
    async def handle_message_read(self, sid, data):
        try:
            message_id = data.get('message_id')
            conversation_id = data.get('conversation_id')
            user_id = user_sessions.get(sid)
            
            if not message_id or not conversation_id or not user_id:
                return
            
            # Broadcast read receipt to other participants
            await self.sio.emit('message_read', {
                'message_id': message_id,
                'conversation_id': conversation_id,
                'user_id': user_id,
                'read_at': datetime.utcnow().isoformat()
            }, room=f"conversation_{conversation_id}", skip_sid=sid)
            
        except Exception as e:
            print(f"Error handling message_read: {e}")
    
    async def handle_get_online_users(self, sid, data):
        try:
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                return
            
            # Get conversation participants
            conversation = await db.conversations.find_one({"id": conversation_id})
            if not conversation:
                return
            
            # Check which participants are online
            online_users = []
            for participant_id in conversation['participants']:
                if participant_id in active_connections:
                    online_users.append(participant_id)
            
            await self.sio.emit('online_users', {
                'conversation_id': conversation_id,
                'online_users': online_users
            }, to=sid)
            
        except Exception as e:
            print(f"Error handling get_online_users: {e}")
    
    async def update_user_online_status(self, user_id: str, is_online: bool):
        try:
            # Update user's online status in database
            await db.online_status.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "is_online": is_online,
                        "last_seen": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            # Notify relevant users about status change
            # Get user's conversations
            conversations = await db.conversations.find({
                "participants": user_id
            }).to_list(1000)
            
            for conv in conversations:
                # Emit status change to all participants in each conversation
                await self.sio.emit('user_status_change', {
                    'user_id': user_id,
                    'is_online': is_online,
                    'last_seen': datetime.utcnow().isoformat()
                }, room=f"conversation_{conv['id']}")
            
        except Exception as e:
            print(f"Error updating user online status: {e}")

# Clean up typing indicators periodically
async def cleanup_typing_indicators():
    while True:
        try:
            current_time = datetime.utcnow()
            conversations_to_remove = []
            
            for conversation_id, users in typing_users.items():
                users_to_remove = []
                for user_id, timestamp in users.items():
                    # Remove typing indicators older than 10 seconds
                    if (current_time - timestamp).total_seconds() > 10:
                        users_to_remove.append(user_id)
                
                for user_id in users_to_remove:
                    del users[user_id]
                
                if not users:
                    conversations_to_remove.append(conversation_id)
            
            for conversation_id in conversations_to_remove:
                del typing_users[conversation_id]
            
            await asyncio.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            print(f"Error in cleanup_typing_indicators: {e}")
            await asyncio.sleep(5)