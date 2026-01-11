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
from botocore.config import Config

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
        config=Config(signature_version="s3v4"),
    )


class PresignedUrlRequest(BaseModel):
    session_id: str
    content_type: str = "video/webm"


class PresignedUrlResponse(BaseModel):
    upload_url: str
    video_key: str
    expires_in: int


# =============================================================================
# Multipart Upload Models (for streaming uploads)
# =============================================================================

class StartMultipartRequest(BaseModel):
    session_id: str
    content_type: str = "video/webm"


class StartMultipartResponse(BaseModel):
    upload_id: str
    video_key: str


class GetPartUrlRequest(BaseModel):
    session_id: str
    upload_id: str
    part_number: int


class GetPartUrlResponse(BaseModel):
    upload_url: str
    part_number: int


class CompletedPart(BaseModel):
    part_number: int
    etag: str


class CompleteMultipartRequest(BaseModel):
    session_id: str
    upload_id: str
    parts: list[CompletedPart]
    is_public: bool = False


class CompleteMultipartResponse(BaseModel):
    success: bool
    video_url: str
    video_key: str


class UploadConfirmRequest(BaseModel):
    session_id: str
    video_key: str
    is_public: bool = False


class UploadConfirmResponse(BaseModel):
    success: bool
    video_url: str
    is_public: bool
    expires_in: Optional[int] = None


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
    supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_API_KEY
    if not settings.SUPABASE_URL or not supabase_key:
        return None
    try:
        from supabase import create_client
        return create_client(settings.SUPABASE_URL, supabase_key)
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

        # Generate presigned URL for viewing the video
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": request.video_key,
            },
            ExpiresIn=settings.S3_PRESIGNED_URL_EXPIRATION,
        )

        # Store video metadata in Supabase with public flag and presigned URL
        # Note: We store presigned URL for immediate use. For long-term access,
        # use the /download-url endpoint to regenerate fresh presigned URLs.
        supabase = get_supabase_client()
        if supabase:
            try:
                # Check if record already exists in videos table
                existing = supabase.table("videos").select("*").eq("uuid", request.session_id).execute()

                video_data = {
                    "link": presigned_url,
                    "public": request.is_public,
                    "video_key": request.video_key  # Store key for regenerating presigned URLs
                }

                if existing.data and len(existing.data) > 0:
                    # Update existing record with presigned URL
                    supabase.table("videos").update(video_data).eq("uuid", request.session_id).execute()
                    logger.info(f"Updated video record for session {request.session_id} (public={request.is_public})")
                else:
                    # Insert new record with presigned URL
                    video_data["uuid"] = request.session_id
                    supabase.table("videos").insert(video_data).execute()
                    logger.info(f"Created video record for session {request.session_id} (public={request.is_public})")
            except Exception as db_error:
                logger.warning(f"Failed to store video metadata in database: {db_error}")
                # Continue even if database storage fails - the video is still in S3

        logger.info(f"Confirmed upload for session {request.session_id} (public={request.is_public})")

        return UploadConfirmResponse(
            success=True,
            video_url=presigned_url,
            is_public=request.is_public,
            expires_in=settings.S3_PRESIGNED_URL_EXPIRATION,
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


# =============================================================================
# Multipart Upload Endpoints (for streaming uploads during recording)
# =============================================================================

@videos_router.post("/multipart/start", response_model=StartMultipartResponse)
async def start_multipart_upload(request: StartMultipartRequest):
    """
    Start a multipart upload for streaming video chunks.
    Call this when recording begins.
    """
    s3_client = get_s3_client()
    video_key = f"videos/{request.session_id}/recording.webm"

    try:
        response = s3_client.create_multipart_upload(
            Bucket=settings.S3_BUCKET_NAME,
            Key=video_key,
            ContentType=request.content_type,
        )

        upload_id = response["UploadId"]
        logger.info(f"Started multipart upload for session {request.session_id}: {upload_id}")

        return StartMultipartResponse(
            upload_id=upload_id,
            video_key=video_key,
        )

    except ClientError as e:
        logger.error(f"Failed to start multipart upload: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start multipart upload"
        )


@videos_router.post("/multipart/part-url", response_model=GetPartUrlResponse)
async def get_part_upload_url(request: GetPartUrlRequest):
    """
    Get a presigned URL for uploading a specific part.
    Call this for each chunk during recording.
    """
    s3_client = get_s3_client()
    video_key = f"videos/{request.session_id}/recording.webm"

    try:
        presigned_url = s3_client.generate_presigned_url(
            "upload_part",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": video_key,
                "UploadId": request.upload_id,
                "PartNumber": request.part_number,
            },
            ExpiresIn=3600,  # 1 hour
        )

        return GetPartUrlResponse(
            upload_url=presigned_url,
            part_number=request.part_number,
        )

    except ClientError as e:
        logger.error(f"Failed to generate part upload URL: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate part upload URL"
        )


@videos_router.post("/multipart/complete", response_model=CompleteMultipartResponse)
async def complete_multipart_upload(request: CompleteMultipartRequest):
    """
    Complete a multipart upload after all parts are uploaded.
    Call this when recording ends - should be instant since all data is already in S3.
    """
    s3_client = get_s3_client()
    video_key = f"videos/{request.session_id}/recording.webm"

    try:
        # Complete the multipart upload
        s3_client.complete_multipart_upload(
            Bucket=settings.S3_BUCKET_NAME,
            Key=video_key,
            UploadId=request.upload_id,
            MultipartUpload={
                "Parts": [
                    {"PartNumber": part.part_number, "ETag": part.etag}
                    for part in sorted(request.parts, key=lambda p: p.part_number)
                ]
            },
        )

        # Generate presigned URL for viewing
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": video_key,
            },
            ExpiresIn=settings.S3_PRESIGNED_URL_EXPIRATION,
        )

        # Store in Supabase
        supabase = get_supabase_client()
        if supabase:
            try:
                existing = supabase.table("videos").select("*").eq("uuid", request.session_id).execute()
                video_data = {
                    "link": presigned_url,
                    "public": request.is_public,
                    "video_key": video_key,
                }
                if existing.data and len(existing.data) > 0:
                    supabase.table("videos").update(video_data).eq("uuid", request.session_id).execute()
                else:
                    video_data["uuid"] = request.session_id
                    supabase.table("videos").insert(video_data).execute()
                logger.info(f"Stored video metadata for session {request.session_id}")
            except Exception as db_error:
                logger.warning(f"Failed to store video metadata: {db_error}")

        logger.info(f"Completed multipart upload for session {request.session_id}")

        return CompleteMultipartResponse(
            success=True,
            video_url=presigned_url,
            video_key=video_key,
        )

    except ClientError as e:
        logger.error(f"Failed to complete multipart upload: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to complete multipart upload"
        )


@videos_router.post("/multipart/abort")
async def abort_multipart_upload(session_id: str, upload_id: str):
    """
    Abort a multipart upload if something goes wrong.
    """
    s3_client = get_s3_client()
    video_key = f"videos/{session_id}/recording.webm"

    try:
        s3_client.abort_multipart_upload(
            Bucket=settings.S3_BUCKET_NAME,
            Key=video_key,
            UploadId=upload_id,
        )
        logger.info(f"Aborted multipart upload for session {session_id}")
        return {"success": True}

    except ClientError as e:
        logger.error(f"Failed to abort multipart upload: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to abort multipart upload"
        )
