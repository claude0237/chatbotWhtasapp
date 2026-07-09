"""Storage Service for file management (S3/MinIO)"""
from typing import Optional
import os
import uuid
from app.config import settings


class StorageService:
    """Service for managing file storage (S3/MinIO or local)"""
    
    def __init__(self):
        self.use_s3 = bool(settings.s3_endpoint_url or settings.aws_access_key_id)
        self.bucket_name = settings.s3_bucket_name or "documents"
    
    async def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        content_type: Optional[str] = None,
        company_id: Optional[str] = None
    ) -> str:
        """Upload a file to storage and return the file path"""
        if self.use_s3:
            return await self._upload_to_s3(file_content, file_name, content_type, company_id)
        else:
            return await self._upload_to_local(file_content, file_name, content_type, company_id)
    
    async def _upload_to_s3(
        self,
        file_content: bytes,
        file_name: str,
        content_type: Optional[str] = None,
        company_id: Optional[str] = None
    ) -> str:
        """Upload file to S3/MinIO"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            if company_id:
                file_path = f"{company_id}/{uuid.uuid4()}_{file_name}"
            else:
                file_path = f"{uuid.uuid4()}_{file_name}"
            
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region or 'us-east-1'
            )
            
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=file_content,
                **extra_args
            )
            
            return f"s3://{self.bucket_name}/{file_path}"
        except ImportError:
            raise ImportError("boto3 library not installed for S3 storage")
        except ClientError as e:
            raise RuntimeError(f"S3 upload failed: {str(e)}")
    
    async def _upload_to_local(
        self,
        file_content: bytes,
        file_name: str,
        content_type: Optional[str] = None,
        company_id: Optional[str] = None
    ) -> str:
        """Upload file to local storage"""
        storage_dir = os.path.join(settings.storage_path or "storage", "uploads")
        if company_id:
            storage_dir = os.path.join(storage_dir, company_id)
        
        os.makedirs(storage_dir, exist_ok=True)
        file_path = os.path.join(storage_dir, f"{uuid.uuid4()}_{file_name}")
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return file_path
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage"""
        if file_path.startswith("s3://"):
            return await self._delete_from_s3(file_path)
        else:
            return await self._delete_from_local(file_path)
    
    async def _delete_from_s3(self, file_path: str) -> bool:
        """Delete file from S3/MinIO"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            path_parts = file_path.replace("s3://", "").split("/", 1)
            bucket = path_parts[0]
            key = path_parts[1] if len(path_parts) > 1 else ""
            
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region or 'us-east-1'
            )
            
            s3_client.delete_object(Bucket=bucket, Key=key)
            return True
        except ImportError:
            raise ImportError("boto3 library not installed for S3 storage")
        except ClientError as e:
            raise RuntimeError(f"S3 delete failed: {str(e)}")
    
    async def _delete_from_local(self, file_path: str) -> bool:
        """Delete file from local storage"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            raise RuntimeError(f"Local delete failed: {str(e)}")
