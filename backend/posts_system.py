# Posts & Media System Models and Routes
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from enum import Enum
import base64
import mimetypes
from PIL import Image
import io
import asyncio

# Post Models
class PostType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    MIXED = "mixed"

class MediaAttachment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_type: str  # image, video, gif
    mime_type: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None  # for videos
    thumbnail: Optional[str] = None  # base64 thumbnail for videos
    data: str  # base64 encoded media

class Post(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    author_id: str
    content: Optional[str] = None
    post_type: PostType = PostType.TEXT
    media_attachments: List[MediaAttachment] = Field(default_factory=list)
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    is_verified_only: bool = True  # Only verified students can post
    visibility: str = "public"  # public, connections, private
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = False

class PostCreate(BaseModel):
    content: Optional[str] = None
    post_type: PostType = PostType.TEXT
    media_attachments: List[MediaAttachment] = Field(default_factory=list)
    visibility: str = "public"
    location: Optional[str] = None

class PostUpdate(BaseModel):
    content: Optional[str] = None
    location: Optional[str] = None

class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    post_id: str
    author_id: str
    content: str
    parent_comment_id: Optional[str] = None  # For nested comments
    likes_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = False

class CommentCreate(BaseModel):
    content: str
    parent_comment_id: Optional[str] = None

class Like(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    post_id: Optional[str] = None
    comment_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Share(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    post_id: str
    message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PostWithDetails(BaseModel):
    post: Post
    author: Dict[str, Any]
    is_liked: bool = False
    is_shared: bool = False
    user_can_interact: bool = True

# Media Processing Functions
def compress_image(base64_data: str, max_width: int = 1200, quality: int = 80) -> str:
    """Compress and resize image while maintaining aspect ratio"""
    try:
        # Decode base64
        image_data = base64.b64decode(base64_data)
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Resize if needed
        if image.width > max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Compress
        output_buffer = io.BytesIO()
        image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
        
        # Encode back to base64
        compressed_data = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
        return compressed_data
        
    except Exception as e:
        print(f"Error compressing image: {e}")
        return base64_data  # Return original if compression fails

def generate_video_thumbnail(base64_data: str) -> Optional[str]:
    """Generate thumbnail for video (placeholder implementation)"""
    # This is a placeholder - in a real implementation, you'd use ffmpeg or similar
    # For now, return None and handle on frontend
    return None

def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from text"""
    import re
    if not text:
        return []
    hashtags = re.findall(r'#(\w+)', text)
    return [tag.lower() for tag in hashtags]

def extract_mentions(text: str) -> List[str]:
    """Extract mentions from text"""
    import re
    if not text:
        return []
    mentions = re.findall(r'@(\w+)', text)
    return mentions

def validate_media_file(file_data: bytes, file_type: str) -> Dict[str, Any]:
    """Validate and get metadata for uploaded media"""
    max_sizes = {
        'image': 10 * 1024 * 1024,  # 10MB
        'video': 100 * 1024 * 1024,  # 100MB
        'gif': 20 * 1024 * 1024,     # 20MB
    }
    
    if len(file_data) > max_sizes.get(file_type, 10 * 1024 * 1024):
        raise HTTPException(status_code=400, detail=f"File too large for {file_type}")
    
    metadata = {
        'size': len(file_data),
        'width': None,
        'height': None,
        'duration': None
    }
    
    if file_type == 'image':
        try:
            image = Image.open(io.BytesIO(file_data))
            metadata['width'] = image.width
            metadata['height'] = image.height
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file")
    
    return metadata