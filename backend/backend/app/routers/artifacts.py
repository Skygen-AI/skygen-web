from __future__ import annotations

import uuid
import asyncio
from datetime import timedelta, datetime, timezone
from typing import Annotated
from functools import partial

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from app.deps import get_current_user
from app.models import User
from app.config import settings
from app.clients import get_s3_client
from app.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import ArtifactPresignRequest
from app.models import Task
from sqlalchemy import select


router = APIRouter()


async def run_s3_operation(func_or_partial):
    """Run S3 operation in thread pool to avoid blocking the event loop"""
    from loguru import logger
    loop = asyncio.get_event_loop()
    try:
        logger.info("Starting S3 operation")
        result = await asyncio.wait_for(
            loop.run_in_executor(None, func_or_partial),
            timeout=30.0  # 30 second timeout
        )
        logger.info("S3 operation completed successfully")
        return result
    except asyncio.TimeoutError as exc:
        logger.error("S3 operation timed out after 30 seconds")
        raise HTTPException(
            status_code=504, detail="S3 operation timed out") from exc
    except Exception as exc:
        logger.error(f"S3 operation failed: {exc}")
        raise


@router.post("/create-bucket")
async def create_bucket(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Create the artifacts bucket if it doesn't exist"""
    _ = current_user
    if settings.artifacts_bucket is None:
        raise HTTPException(
            status_code=500, detail="Artifacts bucket not configured")

    # Use internal MinIO endpoint for bucket operations
    s3 = get_s3_client()
    if s3 is None:
        raise HTTPException(
            status_code=500, detail="S3 client not available")

    # Check if bucket exists
    try:
        await run_s3_operation(partial(s3.head_bucket, Bucket=settings.artifacts_bucket))
        return {"message": f"Bucket {settings.artifacts_bucket} already exists"}
    except HTTPException:
        raise  # Re-raise timeout errors
    except Exception:
        # Bucket doesn't exist, create it
        try:
            await run_s3_operation(partial(s3.create_bucket, Bucket=settings.artifacts_bucket))
            return {"message": f"Bucket {settings.artifacts_bucket} created successfully"}
        except HTTPException:
            raise  # Re-raise timeout errors
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to create bucket: {str(e)}") from e


@router.post("/presign")
async def presign_artifact(
    request: ArtifactPresignRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    # Enforce ownership: user can presign only for their tasks
    t = (
        await db.execute(
            select(Task).where(Task.id == request.task_id,
                               Task.user_id == current_user.id)
        )
    ).scalar_one_or_none()
    if t is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if settings.artifacts_bucket is None:
        raise HTTPException(
            status_code=500, detail="Artifacts bucket not configured")

    # Use internal MinIO endpoint for bucket operations
    s3_internal = get_s3_client()
    if s3_internal is None:
        raise HTTPException(
            status_code=500, detail="S3 client not available")

    # Ensure bucket exists using internal client
    try:
        await run_s3_operation(partial(s3_internal.head_bucket, Bucket=settings.artifacts_bucket))
    except HTTPException:
        raise  # Re-raise timeout errors
    except Exception:
        # Bucket doesn't exist, create it
        try:
            await run_s3_operation(partial(s3_internal.create_bucket, Bucket=settings.artifacts_bucket))
        except HTTPException:
            raise  # Re-raise timeout errors
        except Exception:
            # Ignore if bucket already exists
            pass

    # Use external MinIO endpoint for presigned URLs if available
    if settings.minio_external_endpoint:
        # Create S3 client with external endpoint for presigned URLs
        import boto3
        from botocore.config import Config

        s3_external = boto3.client(
            's3',
            endpoint_url=settings.minio_external_endpoint,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version='s3v4')
        )
    else:
        s3_external = s3_internal

    object_key = f"tasks/{request.task_id}/{uuid.uuid4().hex}/{request.filename}"
    expires_in = 300
    url = await run_s3_operation(
        partial(
            s3_external.generate_presigned_url,
            ClientMethod="put_object",
            Params={
                "Bucket": settings.artifacts_bucket,
                "Key": object_key,
                "ContentLength": request.size,
            },
            ExpiresIn=expires_in,
        )
    )

    return {
        "upload_url": url,
        "s3_url": f"s3://{settings.artifacts_bucket}/{object_key}",
        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat(),
    }


@router.post("/upload")
async def upload_artifact(
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
    filename: str = Form(...),
    content_type: str = Form(...),
) -> dict:
    """Direct upload endpoint for artifacts like screenshots"""
    if settings.artifacts_bucket is None:
        raise HTTPException(
            status_code=500, detail="Artifacts bucket not configured")

    # Use internal MinIO endpoint for upload
    s3 = get_s3_client()
    if s3 is None:
        raise HTTPException(
            status_code=500, detail="S3 client not available")

    # Ensure bucket exists
    try:
        await run_s3_operation(partial(s3.head_bucket, Bucket=settings.artifacts_bucket))
    except HTTPException:
        raise  # Re-raise timeout errors
    except Exception:
        # Bucket doesn't exist, create it
        try:
            await run_s3_operation(partial(s3.create_bucket, Bucket=settings.artifacts_bucket))
        except HTTPException:
            raise  # Re-raise timeout errors
        except Exception:
            pass

    # Generate object key
    object_key = filename

    # Read file content
    file_content = await file.read()

    # Upload to S3
    try:
        await run_s3_operation(
            partial(
                s3.put_object,
                Bucket=settings.artifacts_bucket,
                Key=object_key,
                Body=file_content,
                ContentType=content_type
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload file: {str(e)}") from e

    # Generate public URL
    if settings.minio_external_endpoint:
        public_url = f"{settings.minio_external_endpoint.rstrip('/')}/{settings.artifacts_bucket}/{object_key}"
    else:
        public_url = f"{settings.minio_endpoint.rstrip('/')}/{settings.artifacts_bucket}/{object_key}"

    return {
        "success": True,
        "url": public_url,
        "s3_key": object_key,
        "size": len(file_content)
    }
