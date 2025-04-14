import logging
import uuid
import os

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from pydantic import BaseModel

from ..core.storage import upload_file_to_s3
from admin_app.core.auth import get_current_user
# We will add authentication dependency later
# from ..core.security import get_current_username

logger = logging.getLogger(__name__)
router = APIRouter()

class ImageUploadResponse(BaseModel):
    filename: str
    url: str

@router.post(
    "/images",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image",
    description="Uploads an image file to the S3 storage and returns its filename and URL."
)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    user = Depends(get_current_user)
):
    """Handles image uploads."""
    # Generate a unique filename to avoid conflicts
    _, extension = os.path.splitext(file.filename)
    unique_filename = f"{uuid.uuid4()}{extension}"

    logger.info(f"Attempting to upload image '{file.filename}' as '{unique_filename}'")

    # Upload the file using the storage utility
    success = upload_file_to_s3(file=file, object_name=unique_filename)

    if not success:
        logger.error(f"Failed to upload image '{file.filename}'")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not upload image to storage.",
        )

    # Construct the URL - simple relative path for now
    # Assumes Caddy proxies /images/ directly to the bucket root
    image_url = f"/images/{unique_filename}"
    logger.info(f"Image '{unique_filename}' uploaded successfully. URL: {image_url}")

    return ImageUploadResponse(filename=unique_filename, url=image_url) 