import logging
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from .config import settings

logger = logging.getLogger(__name__)

s3_client = None

def get_s3_client():
    """Initializes and returns the Boto3 S3 client."""
    global s3_client
    if s3_client is None:
        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.MINIO_ENDPOINT_URL,
                aws_access_key_id=settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=settings.MINIO_SECRET_KEY,
                config=boto3.session.Config(signature_version='s3v4'), # Recommended for MinIO
                region_name='us-east-1' # Default region, usually ignored by MinIO but can be required by boto3
            )
            # Optional: Check connection by listing buckets (requires permissions)
            # s3_client.list_buckets()
            logger.info("S3 client initialized successfully.")
        except ClientError as e:
            logger.error(f"Failed to initialize S3 client: {e}", exc_info=True)
            raise RuntimeError("Could not connect to S3 storage.") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during S3 client initialization: {e}", exc_info=True)
            raise RuntimeError("Could not connect to S3 storage due to an unexpected error.") from e

    return s3_client

def upload_file_to_s3(file: UploadFile, object_name: str) -> bool:
    """
    Uploads a file object to the configured S3 bucket.

    Args:
        file: The FastAPI UploadFile object.
        object_name: The desired name for the object in the S3 bucket.

    Returns:
        True if upload was successful, False otherwise.
    """
    s3 = get_s3_client()
    if not s3:
        return False # Client failed to initialize

    try:
        s3.upload_fileobj(
            file.file, # The file-like object
            settings.MINIO_BUCKET_NAME,
            object_name,
            ExtraArgs={
                'ContentType': file.content_type
            }
        )
        logger.info(f"Successfully uploaded '{file.filename}' as '{object_name}' to bucket '{settings.MINIO_BUCKET_NAME}'.")
        return True
    except ClientError as e:
        logger.error(
            f"Failed to upload '{file.filename}' as '{object_name}' to bucket '{settings.MINIO_BUCKET_NAME}': {e}",
            exc_info=True
        )
        return False
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during S3 upload of '{file.filename}': {e}",
            exc_info=True
        )
        return False 