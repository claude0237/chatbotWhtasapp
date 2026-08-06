"""Bot Models"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class BotType(str, enum.Enum):
    """Bot type"""
    NATIVE = "NATIVE"
    ML = "ML"
    HYBRID = "HYBRID"


class MLProvider(str, enum.Enum):
    """ML provider"""
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    OLLAMA = "OLLAMA"
    MISTRAL = "MISTRAL"


class FallbackStrategy(str, enum.Enum):
    """Fallback strategy for ML bot"""
    ML_TO_NATIVE = "ML_TO_NATIVE"
    NATIVE_TO_ML = "NATIVE_TO_ML"
    PARALLEL = "PARALLEL"


class MLModelType(str, enum.Enum):
    """ML model type"""
    RAG = "RAG"
    CLASSIFIER = "CLASSIFIER"
    RERANKER = "RERANKER"


class BotConfiguration(Base):
    """Bot configuration model"""
    
    __tablename__ = "bot_configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    bot_type = Column(SQLEnum(BotType), default=BotType.NATIVE, nullable=False)
    name = Column(String(255), nullable=False)
    
    # Messages
    welcome_message = Column(Text, nullable=True)
    away_message = Column(Text, nullable=True)
    closing_message = Column(Text, nullable=True)
    unknown_message = Column(Text, nullable=True)
    
    # Configuration
    language = Column(String(10), default="en", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    avatar_url = Column(String(500), nullable=True)
    
    # Native rules (JSONB)
    native_rules = Column(JSON, nullable=True)
    
    # ML Configuration
    ml_enabled = Column(Boolean, default=False, nullable=False)
    ml_provider = Column(SQLEnum(MLProvider), nullable=True)
    ml_model = Column(String(100), nullable=True)
    ml_temperature = Column(String(10), nullable=True)
    ml_max_tokens = Column(Integer, nullable=True)
    fallback_strategy = Column(SQLEnum(FallbackStrategy), default=FallbackStrategy.ML_TO_NATIVE, nullable=True)
    confidence_threshold = Column(String(10), nullable=True)
    
    # Business hours (JSONB) — schedule per day of week
    # Format: {"monday": {"open": "07:00", "close": "17:00"}, "saturday": {"open": "07:00", "close": "12:00"}, "sunday": null, ...}
    # null or missing day = closed that day
    business_hours = Column(JSON, nullable=True)

    # Follow-up / timeout configuration
    followup_timeout_minutes = Column(Integer, default=60, nullable=False)
    followup_max_retries = Column(Integer, default=3, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", backref="bot_configurations")
    scenarios = relationship("BotScenario", backref="bot_configuration", cascade="all, delete-orphan")
    keywords = relationship("BotKeyword", backref="bot_configuration", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BotConfiguration(id={self.id}, name={self.name}, bot_type={self.bot_type})>"


class BotScenario(Base):
    """Bot scenario model"""
    
    __tablename__ = "bot_scenarios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    bot_configuration_id = Column(UUID(as_uuid=True), ForeignKey("bot_configurations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    trigger_keyword = Column(String(255), nullable=False, index=True)
    
    # Steps (JSONB - flow du scénario)
    steps = Column(JSON, nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<BotScenario(id={self.id}, name={self.name}, trigger_keyword={self.trigger_keyword})>"


class BotKeyword(Base):
    """Bot keyword model"""
    
    __tablename__ = "bot_keywords"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    bot_configuration_id = Column(UUID(as_uuid=True), ForeignKey("bot_configurations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    keyword = Column(String(255), nullable=False, index=True)
    response = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<BotKeyword(id={self.id}, keyword={self.keyword}, category={self.category})>"


class BotConversationState(Base):
    """Tracks the state of an active scenario for a specific contact (phone number)"""

    __tablename__ = "bot_conversation_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    phone_number = Column(String(50), nullable=False, index=True)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("bot_scenarios.id", ondelete="CASCADE"), nullable=False)
    current_step = Column(Integer, default=0, nullable=False)
    collected_data = Column(JSON, default=dict, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    last_bot_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    scenario = relationship("BotScenario")

    def __repr__(self):
        return f"<BotConversationState(phone={self.phone_number}, scenario={self.scenario_id}, step={self.current_step})>"


class MLModel(Base):
    """ML model configuration"""
    
    __tablename__ = "ml_models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    model_type = Column(SQLEnum(MLModelType), nullable=False)
    provider = Column(SQLEnum(MLProvider), nullable=False)
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=True)
    
    # Configuration
    configuration = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", backref="ml_models")
    
    def __repr__(self):
        return f"<MLModel(id={self.id}, name={self.name}, model_type={self.model_type}, provider={self.provider})>"
