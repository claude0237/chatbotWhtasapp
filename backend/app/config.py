"""Application Configuration"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "WhatsApp SaaS Platform"
    app_env: str = "development"
    app_debug: bool = True
    app_version: str = "0.1.0"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # Database
    database_url: str
    database_sync_url: str
    
    # Redis
    redis_url: str
    redis_cache_url: str
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Password Hashing
    password_hash_algorithm: str = "argon2"
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # Credential encryption (Fernet key — generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    credential_encryption_key: str = ""

    # WhatsApp / Meta
    whatsapp_webhook_verify_token: str = ""
    whatsapp_api_version: str = "v18.0"
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_business_id: str = ""
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-opus-20240229"
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""
    
    # Celery
    celery_broker_url: str
    celery_result_backend: str
    
    # Storage
    storage_type: str = "local"
    s3_bucket: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = ""
    s3_endpoint: str = ""
    
    # Monitoring
    sentry_dsn: str = ""
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
