"""
Password Reset API Routes for StudyConnect
Handles forgot password and reset password endpoints
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from password_reset_models import (
    PasswordResetRequest, PasswordResetConfirm, PasswordResetResponse
)
from password_reset_service import password_reset_service

password_router = APIRouter(prefix="/api/auth", tags=["password-reset"])

@password_router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(
    request: Request,
    background_tasks: BackgroundTasks,
    reset_request: PasswordResetRequest
):
    """
    Initiate password reset process by sending reset email
    """
    try:
        # Get client information for rate limiting and security
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "Unknown")
        
        # Process password reset request
        result = await password_reset_service.initiate_password_reset(
            email=reset_request.email,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if result["success"]:
            # Schedule cleanup of expired tokens in background
            background_tasks.add_task(password_reset_service.cleanup_expired_tokens)
            
            response_data = {
                "message": result["message"],
                "reset_token_id": result.get("token_id")
            }
            
            # Include reset token in mock mode for testing
            if result.get("mock_mode"):
                response_data["mock_mode"] = True
                response_data["reset_token"] = result.get("reset_token")
            
            return response_data
        else:
            raise HTTPException(
                status_code=400 if "Too many" in result["message"] or "wait" in result["message"] else 500,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in forgot_password endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request. Please try again later."
        )

@password_router.get("/verify-reset-token/{token}")
async def verify_reset_token(token: str):
    """
    Verify if a password reset token is valid
    """
    try:
        result = await password_reset_service.verify_reset_token(token)
        
        if result["valid"]:
            return {
                "valid": True,
                "email": result["email"],
                "expires_at": result["expires_at"]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in verify_reset_token endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error verifying token"
        )

@password_router.post("/reset-password")
async def reset_password(
    background_tasks: BackgroundTasks,
    reset_data: PasswordResetConfirm
):
    """
    Reset password using valid reset token
    """
    try:
        result = await password_reset_service.reset_password(
            token=reset_data.token,
            new_password=reset_data.new_password
        )
        
        if result["success"]:
            # Schedule cleanup of expired tokens in background
            background_tasks.add_task(password_reset_service.cleanup_expired_tokens)
            
            return {"message": result["message"]}
        else:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in reset_password endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while resetting your password. Please try again."
        )

@password_router.post("/cleanup-expired-tokens")
async def cleanup_expired_tokens(background_tasks: BackgroundTasks):
    """
    Manually trigger cleanup of expired reset tokens (admin endpoint)
    """
    try:
        background_tasks.add_task(password_reset_service.cleanup_expired_tokens)
        return {"message": "Cleanup task scheduled"}
        
    except Exception as e:
        print(f"Error scheduling cleanup: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to schedule cleanup"
        )