from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from typing import List, Optional
from posts_system import *
from server import db, get_current_user, User
from datetime import datetime
import base64

posts_router = APIRouter(prefix="/api/posts")

# Post Management Routes
@posts_router.post("/", response_model=Post)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user)
):
    # Check if user can post (verified students only)
    if not current_user.is_verified:
        raise HTTPException(
            status_code=403, 
            detail="Only verified students can create posts"
        )
    
    # Process media attachments
    processed_media = []
    for media in post_data.media_attachments:
        try:
            # Validate file type
            if media.file_type not in ['image', 'video', 'gif']:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {media.file_type}")
            
            # Compress images
            if media.file_type == 'image':
                media.data = compress_image(media.data)
            
            # Generate thumbnails for videos
            elif media.file_type == 'video':
                media.thumbnail = generate_video_thumbnail(media.data)
            
            processed_media.append(media)
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing media: {str(e)}")
    
    # Extract hashtags and mentions
    hashtags = extract_hashtags(post_data.content)
    mentions = extract_mentions(post_data.content)
    
    # Determine post type
    post_type = post_data.post_type
    if processed_media:
        if len(processed_media) == 1:
            post_type = PostType(processed_media[0].file_type)
        else:
            post_type = PostType.MIXED
    
    # Create post
    post = Post(
        author_id=current_user.id,
        content=post_data.content,
        post_type=post_type,
        media_attachments=processed_media,
        visibility=post_data.visibility,
        location=post_data.location,
        hashtags=hashtags,
        mentions=mentions
    )
    
    # Save to database
    await db.posts.insert_one(post.dict())
    
    return post

@posts_router.get("/", response_model=List[PostWithDetails])
async def get_posts(
    limit: int = Query(20, ge=1, le=50),
    skip: int = Query(0, ge=0),
    author_id: Optional[str] = Query(None),
    hashtag: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    # Build query
    query = {"is_deleted": False}
    
    if author_id:
        query["author_id"] = author_id
    
    if hashtag:
        query["hashtags"] = {"$in": [hashtag.lower()]}
    
    # Get posts with filtering for visibility
    # For now, we'll show all public posts and posts from connections
    posts_cursor = db.posts.find(query).sort("created_at", -1).skip(skip).limit(limit)
    posts_docs = await posts_cursor.to_list(length=limit)
    
    result = []
    for post_doc in posts_docs:
        post = Post(**{k: v for k, v in post_doc.items() if k != '_id'})
        
        # Get author details
        author_doc = await db.users.find_one({"id": post.author_id})
        if not author_doc:
            continue
            
        author = {
            "id": author_doc["id"],
            "first_name": author_doc["first_name"],
            "last_name": author_doc["last_name"],
            "profile": author_doc.get("profile", {})
        }
        
        # Check if current user has liked this post
        like_doc = await db.likes.find_one({
            "user_id": current_user.id,
            "post_id": post.id
        })
        is_liked = bool(like_doc)
        
        # Check if current user has shared this post
        share_doc = await db.shares.find_one({
            "user_id": current_user.id,
            "post_id": post.id
        })
        is_shared = bool(share_doc)
        
        # Determine if user can interact (based on visibility and connections)
        user_can_interact = True  # For now, all verified users can interact
        
        result.append(PostWithDetails(
            post=post,
            author=author,
            is_liked=is_liked,
            is_shared=is_shared,
            user_can_interact=user_can_interact
        ))
    
    return result

@posts_router.get("/{post_id}", response_model=PostWithDetails)
async def get_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    # Find post
    post_doc = await db.posts.find_one({"id": post_id, "is_deleted": False})
    if not post_doc:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post = Post(**{k: v for k, v in post_doc.items() if k != '_id'})
    
    # Get author details
    author_doc = await db.users.find_one({"id": post.author_id})
    if not author_doc:
        raise HTTPException(status_code=404, detail="Author not found")
    
    author = {
        "id": author_doc["id"],
        "first_name": author_doc["first_name"],
        "last_name": author_doc["last_name"],
        "profile": author_doc.get("profile", {})
    }
    
    # Check interactions
    like_doc = await db.likes.find_one({"user_id": current_user.id, "post_id": post.id})
    is_liked = bool(like_doc)
    
    share_doc = await db.shares.find_one({"user_id": current_user.id, "post_id": post.id})
    is_shared = bool(share_doc)
    
    return PostWithDetails(
        post=post,
        author=author,
        is_liked=is_liked,
        is_shared=is_shared,
        user_can_interact=True
    )

@posts_router.put("/{post_id}")
async def update_post(
    post_id: str,
    post_update: PostUpdate,
    current_user: User = Depends(get_current_user)
):
    # Find post and verify ownership
    post_doc = await db.posts.find_one({
        "id": post_id,
        "author_id": current_user.id,
        "is_deleted": False
    })
    
    if not post_doc:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    
    # Update fields
    update_data = {"updated_at": datetime.utcnow()}
    
    if post_update.content is not None:
        update_data["content"] = post_update.content
        update_data["hashtags"] = extract_hashtags(post_update.content)
        update_data["mentions"] = extract_mentions(post_update.content)
    
    if post_update.location is not None:
        update_data["location"] = post_update.location
    
    # Update in database
    await db.posts.update_one(
        {"id": post_id},
        {"$set": update_data}
    )
    
    return {"message": "Post updated successfully"}

@posts_router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    # Find post and verify ownership
    result = await db.posts.update_one(
        {
            "id": post_id,
            "author_id": current_user.id,
            "is_deleted": False
        },
        {
            "$set": {
                "is_deleted": True,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    
    return {"message": "Post deleted successfully"}

# Like/Unlike Routes
@posts_router.post("/{post_id}/like")
async def like_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    # Check if post exists
    post_doc = await db.posts.find_one({"id": post_id, "is_deleted": False})
    if not post_doc:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if already liked
    existing_like = await db.likes.find_one({
        "user_id": current_user.id,
        "post_id": post_id
    })
    
    if existing_like:
        raise HTTPException(status_code=400, detail="Post already liked")
    
    # Create like
    like = Like(user_id=current_user.id, post_id=post_id)
    await db.likes.insert_one(like.dict())
    
    # Update post likes count
    await db.posts.update_one(
        {"id": post_id},
        {"$inc": {"likes_count": 1}}
    )
    
    return {"message": "Post liked successfully"}

@posts_router.delete("/{post_id}/like")
async def unlike_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    # Remove like
    result = await db.likes.delete_one({
        "user_id": current_user.id,
        "post_id": post_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Like not found")
    
    # Update post likes count
    await db.posts.update_one(
        {"id": post_id},
        {"$inc": {"likes_count": -1}}
    )
    
    return {"message": "Post unliked successfully"}

# Comment Routes
@posts_router.post("/{post_id}/comments", response_model=Comment)
async def create_comment(
    post_id: str,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user)
):
    # Check if post exists
    post_doc = await db.posts.find_one({"id": post_id, "is_deleted": False})
    if not post_doc:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Create comment
    comment = Comment(
        post_id=post_id,
        author_id=current_user.id,
        content=comment_data.content,
        parent_comment_id=comment_data.parent_comment_id
    )
    
    # Save comment
    await db.comments.insert_one(comment.dict())
    
    # Update post comments count
    await db.posts.update_one(
        {"id": post_id},
        {"$inc": {"comments_count": 1}}
    )
    
    return comment

@posts_router.get("/{post_id}/comments")
async def get_post_comments(
    post_id: str,
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    # Get comments for post
    comments_cursor = db.comments.find({
        "post_id": post_id,
        "is_deleted": False
    }).sort("created_at", 1).skip(skip).limit(limit)
    
    comments_docs = await comments_cursor.to_list(length=limit)
    
    result = []
    for comment_doc in comments_docs:
        comment = Comment(**{k: v for k, v in comment_doc.items() if k != '_id'})
        
        # Get comment author details
        author_doc = await db.users.find_one({"id": comment.author_id})
        if author_doc:
            comment_with_author = {
                **comment.dict(),
                "author": {
                    "id": author_doc["id"],
                    "first_name": author_doc["first_name"],
                    "last_name": author_doc["last_name"],
                    "profile": author_doc.get("profile", {})
                }
            }
            result.append(comment_with_author)
    
    return result

# Share Routes
@posts_router.post("/{post_id}/share")
async def share_post(
    post_id: str,
    message: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    # Check if post exists
    post_doc = await db.posts.find_one({"id": post_id, "is_deleted": False})
    if not post_doc:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if already shared
    existing_share = await db.shares.find_one({
        "user_id": current_user.id,
        "post_id": post_id
    })
    
    if existing_share:
        raise HTTPException(status_code=400, detail="Post already shared")
    
    # Create share
    share = Share(
        user_id=current_user.id,
        post_id=post_id,
        message=message
    )
    await db.shares.insert_one(share.dict())
    
    # Update post shares count
    await db.posts.update_one(
        {"id": post_id},
        {"$inc": {"shares_count": 1}}
    )
    
    return {"message": "Post shared successfully"}

# Search Routes
@posts_router.get("/search/hashtags")
async def search_by_hashtag(
    hashtag: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    # Search posts by hashtag
    posts_cursor = db.posts.find({
        "hashtags": {"$in": [hashtag.lower()]},
        "is_deleted": False
    }).sort("created_at", -1).skip(skip).limit(limit)
    
    posts_docs = await posts_cursor.to_list(length=limit)
    
    result = []
    for post_doc in posts_docs:
        post = Post(**{k: v for k, v in post_doc.items() if k != '_id'})
        
        # Get author details
        author_doc = await db.users.find_one({"id": post.author_id})
        if author_doc:
            author = {
                "id": author_doc["id"],
                "first_name": author_doc["first_name"],
                "last_name": author_doc["last_name"]
            }
            
            result.append({
                **post.dict(),
                "author": author
            })
    
    return result

@posts_router.get("/search/content")
async def search_posts(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    # Search posts by content
    posts_cursor = db.posts.find({
        "content": {"$regex": query, "$options": "i"},
        "is_deleted": False
    }).sort("created_at", -1).skip(skip).limit(limit)
    
    posts_docs = await posts_cursor.to_list(length=limit)
    
    result = []
    for post_doc in posts_docs:
        post = Post(**{k: v for k, v in post_doc.items() if k != '_id'})
        
        # Get author details
        author_doc = await db.users.find_one({"id": post.author_id})
        if author_doc:
            author = {
                "id": author_doc["id"],
                "first_name": author_doc["first_name"],
                "last_name": author_doc["last_name"]
            }
            
            result.append({
                **post.dict(),
                "author": author
            })
    
    return result