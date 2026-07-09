"""Storage Service for file management (MinIO/S3)"""
from typing import Optional, BinaryIO
from abc import ABC, abstractmethod
import os
import uuid
from app.config import settings


class StorageProvider(ABC):
    """Base interface for storage providers"""
    
    @abstractmethod
    async def upload_file(self, file_path: str, content: BinaryIO, content_type: str) -> str:
        """Upload file and return URL"""
        pass
    
    @abstractmethod
    async def download_file(self, file_path: str) -> bytes:
        """Download file content"""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Delete file"""
        pass
    
    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        pass


class LocalStorageProvider(StorageProvider):
    """Local file system storage provider (for development)"""
    
    def __init__(self, base_path: str = "./uploads"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    async def upload_file(self, file_path: str, content: BinaryIO, content_type: str) -> str:
        """Upload file to local storage"""
        full_path = os.path.join(self.base_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'wb') as f:
            f.write(content.read())
        
        return full_path
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from local storage"""
        full_path = os.path.join(self.base_path, file_path)
        
        with open(full_path, 'rb') as f:
            return f.read()
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage"""
        full_path = os.path.join(self.base_path, file_path)
        
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in local storage"""
        full_path = os.path.join(self.base_path, file_path)
        return os.path.exists(full_path)


class S3StorageProvider(StorageProvider):
    """S3/MinIO storage provider"""
    
    def __init__(self, endpoint_url: Optional[str] = None, bucket_name: str = "documents"):
        self.endpoint_url = endpoint_url
        self.bucket_name = bucket_name
        self.client = None
    
    async def _get_client(self):
        """Get S3 client lazily"""
        if self.client is None:
            try:
                import boto3
                from botocore.client import Config as BotoConfig
                
                s3_config = BotoConfig(
                    signature_version='s3v4',
                    retries={'max_attempts': 3}
                )
                
                self.client = boto3.client(
                    's3',
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    config=s3_config
                )
                
                # Create bucket if it doesn't exist
                try:
                    self.client.head_bucket(Bucket=self.bucket_name)
                except:
                    self.client.create_bucket(Bucket=self.bucket_name)
                    
            except ImportError:
                raise ImportError("boto3 library not installed")
    
    async def upload_file(self, file_path: str, content: BinaryIO, content_type: str) -> str:
        """Upload file to S3/MinIO"""
        await self._get_client()
        
        self.client.upload_fileobj(
            content,
            self.bucket_name,
            file_path,
            ExtraArgs={'ContentType': content_type}
        )
        
        # Return URL
        if self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket_name}/{file_path}"
        else:
            return f"https://{self.bucket_name}.s3.amazonaws.com/{file_path}"
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from S3/MinIO"""
        await self._get_client()
        
        import io
        buffer = io.BytesIO()
        self.client.download_fileobj(self.bucket_name, file_path, buffer)
        return buffer.getvalue()
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from S3/MinIO"""
        await self._get_client()
        
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except Exception:
            return False
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in S3/MinIO"""
        await self._get_client()
        
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except Exception:
            return False


class StorageService:
    """Service for managing file storage"""
    
    def __init__(self, provider: Optional[StorageProvider] = None):
        if provider:
            self.provider = provider
        else:
            # Default to local storage for development
            self.provider = LocalStorageProvider()
    
    async def upload_document(
        self,
        file_content: BinaryIO,
        file_name: str,
        content_type: str,
        company_id: str
    ) -> str:
        """Upload a document and return the file path/URL"""
        # Generate unique file path
        file_extension = file_name.split('.')[-1] if '.' in file_name else ''
        unique_name = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())
        file_path = f"{company_id}/{unique_name}"
        
        return await self.provider.upload_file(file_path, file_content, content_type)
    
    async def download_document(self, file_path: str) -> bytes:
        """Download a document"""
        return await self.provider.download_file(file_path)
    
    async def delete_document(self, file_path: str) -> bool:
        """Delete a document"""
        return await self.provider.delete_file(file_path)
    
    async def document_exists(self, file_path: str) -> bool:
        """Check if document exists"""
        return await self.provider.file_exists(file_path)


# Factory function to get storage provider
def get_storage_provider() -> StorageProvider:
    """Get storage provider based on configuration"""
    if settings.s3_endpoint_url or settings.aws_access_key_id:
        return S3StorageProvider(
            endpoint_url=settings.s3_endpoint_url,
            bucket_name=settings.s3_bucket_name or "documents"
        )
    else:
        return LocalStorageProvider(base_path="./uploads")
