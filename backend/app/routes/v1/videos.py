"""
Video upload routes for S3 presigned URL generation.

This module handles:
1. Generating presigned URLs for direct browser-to-S3 uploads
2. Confirming upload completion and storing video metadata
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

videos_router = APIRouter(prefix="/videos", tags=["videos"])


def get_s3_client():
    """Create and return an S3 client using configured credentials."""
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        raise HTTPException(
            status_code=500,
            detail="AWS credentials not configured"
        )
    if not settings.S3_BUCKET_NAME:
        raise HTTPException(
            status_code=500,
            detail="S3 bucket name not configured"
        )

    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


class PresignedUrlRequest(BaseModel):
    session_id: str
    content_type: str = "video/webm"


class PresignedUrlResponse(BaseModel):
    upload_url: str
    video_key: str
    expires_in: int


class UploadConfirmRequest(BaseModel):
    session_id: str
    video_key: str
    is_public: bool = False


class UploadConfirmResponse(BaseModel):
    success: bool
    video_url: str
    is_public: bool


@videos_router.post("/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_upload_url(request: PresignedUrlRequest):
    """
    Generate a presigned URL for direct browser upload to S3.

    The frontend will use this URL to upload the video directly to S3,
    bypassing our server for the actual file transfer.
    """
    s3_client = get_s3_client()

    video_key = f"videos/{request.session_id}/recording.webm"

    try:
        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": video_key,
                "ContentType": request.content_type,
            },
            ExpiresIn=settings.S3_PRESIGNED_URL_EXPIRATION,
        )

        logger.info(f"Generated presigned URL for session {request.session_id}")

        return PresignedUrlResponse(
            upload_url=presigned_url,
            video_key=video_key,
            expires_in=settings.S3_PRESIGNED_URL_EXPIRATION,
        )

    except ClientError as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate upload URL"
        )


def get_supabase_client():
    """Initialize and return a Supabase client for video metadata storage."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    except Exception as e:
        logger.warning(f"Supabase client unavailable: {e}")
        return None


@videos_router.post("/confirm-upload", response_model=UploadConfirmResponse)
async def confirm_upload(request: UploadConfirmRequest):
    """
    Confirm that a video upload completed successfully.

    This endpoint verifies the object exists in S3, stores the video
    metadata in Supabase with the public flag, and returns the final video URL.
    """
    s3_client = get_s3_client()

    try:
        s3_client.head_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=request.video_key,
        )

        video_url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{request.video_key}"

        # Store video metadata in Supabase with public flag
        supabase = get_supabase_client()
        if supabase:
            try:
                # Check if record already exists
                existing = supabase.table("videos").select("*").eq("uuid", request.session_id).execute()

                if existing.data and len(existing.data) > 0:
                    # Update existing record
                    supabase.table("videos").update({
                        "link": video_url,
                        "public": request.is_public
                    }).eq("uuid", request.session_id).execute()
                    logger.info(f"Updated video record for session {request.session_id} (public={request.is_public})")
                else:
                    # Insert new record
                    supabase.table("videos").insert({
                        "uuid": request.session_id,
                        "link": video_url,
                        "public": request.is_public
                    }).execute()
                    logger.info(f"Created video record for session {request.session_id} (public={request.is_public})")
            except Exception as db_error:
                logger.warning(f"Failed to store video metadata in database: {db_error}")
                # Continue even if database storage fails - the video is still in S3

        logger.info(f"Confirmed upload for session {request.session_id} (public={request.is_public})")

        return UploadConfirmResponse(
            success=True,
            video_url=video_url,
            is_public=request.is_public,
        )

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "404":
            raise HTTPException(
                status_code=404,
                detail="Video not found in S3. Upload may have failed."
            )
        logger.error(f"Failed to confirm upload: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to confirm upload"
        )


@videos_router.get("/download-url/{session_id}")
async def get_download_url(session_id: str, expires_in: Optional[int] = 3600):
    """
    Generate a presigned URL for viewing/downloading a video.

    Used when users want to watch a published negotiation.
    """
    s3_client = get_s3_client()

    video_key = f"videos/{session_id}/recording.webm"

    try:
        s3_client.head_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=video_key,
        )

        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": video_key,
            },
            ExpiresIn=expires_in,
        )

        return {
            "download_url": presigned_url,
            "expires_in": expires_in,
        }

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "404":
            raise HTTPException(
                status_code=404,
                detail="Video not found"
            )
        logger.error(f"Failed to generate download URL: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate download URL"
        )
