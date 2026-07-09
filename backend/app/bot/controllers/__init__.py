"""Bot Controller"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.bot.services import BotConfigurationService
from app.bot.repositories import BotScenarioRepository, BotKeywordRepository
from app.bot.models import BotType
from app.auth.dependencies import get_current_active_user, get_current_company_id
from app.users.models import User


router = APIRouter(prefix="/bot", tags=["Bot"])


# Request/Response Schemas
class BotConfigurationResponse(BaseModel):
    """Bot configuration response schema"""
    id: str
    company_id: str
    bot_type: str
    name: str
    welcome_message: Optional[str]
    away_message: Optional[str]
    closing_message: Optional[str]
    unknown_message: Optional[str]
    language: str
    timezone: str
    avatar_url: Optional[str]
    native_rules: Optional[dict]
    business_hours: Optional[dict]
    ml_enabled: Optional[bool]
    ml_provider: Optional[str]
    ml_model: Optional[str]
    ml_temperature: Optional[str]
    ml_max_tokens: Optional[int]
    fallback_strategy: Optional[str]
    confidence_threshold: Optional[str]
    created_at: str
    updated_at: str


class BotConfigurationCreateRequest(BaseModel):
    """Bot configuration create request schema"""
    bot_type: BotType = BotType.NATIVE
    name: str = Field(..., min_length=1, max_length=255)
    welcome_message: Optional[str] = None
    away_message: Optional[str] = None
    closing_message: Optional[str] = None
    unknown_message: Optional[str] = None
    language: str = Field(default="en", min_length=2, max_length=10)
    timezone: str = Field(default="UTC", max_length=50)
    avatar_url: Optional[str] = None
    native_rules: Optional[dict] = None
    business_hours: Optional[dict] = None
    ml_enabled: Optional[bool] = False
    ml_provider: Optional[str] = None
    ml_model: Optional[str] = None
    ml_temperature: Optional[str] = None
    ml_max_tokens: Optional[int] = None
    fallback_strategy: Optional[str] = None
    confidence_threshold: Optional[str] = None


class BotConfigurationUpdateRequest(BaseModel):
    """Bot configuration update request schema"""
    bot_type: Optional[BotType] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    welcome_message: Optional[str] = None
    away_message: Optional[str] = None
    closing_message: Optional[str] = None
    unknown_message: Optional[str] = None
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = None
    native_rules: Optional[dict] = None
    business_hours: Optional[dict] = None
    ml_enabled: Optional[bool] = None
    ml_provider: Optional[str] = None
    ml_model: Optional[str] = None
    ml_temperature: Optional[str] = None
    ml_max_tokens: Optional[int] = None
    fallback_strategy: Optional[str] = None
    confidence_threshold: Optional[str] = None


class BotScenarioResponse(BaseModel):
    """Bot scenario response schema"""
    id: str
    bot_configuration_id: str
    name: str
    trigger_keyword: str
    steps: list
    is_active: bool
    created_at: str
    updated_at: str


class BotScenarioCreateRequest(BaseModel):
    """Bot scenario create request schema"""
    name: str = Field(..., min_length=1, max_length=255)
    trigger_keyword: str = Field(..., min_length=1, max_length=255)
    steps: list = Field(..., min_items=1)
    is_active: bool = True


class BotScenarioUpdateRequest(BaseModel):
    """Bot scenario update request schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    trigger_keyword: Optional[str] = Field(None, min_length=1, max_length=255)
    steps: Optional[list] = None
    is_active: Optional[bool] = None


class BotKeywordResponse(BaseModel):
    """Bot keyword response schema"""
    id: str
    bot_configuration_id: str
    keyword: str
    response: str
    category: Optional[str]
    created_at: str
    updated_at: str


class BotKeywordCreateRequest(BaseModel):
    """Bot keyword create request schema"""
    keyword: str = Field(..., min_length=1, max_length=255)
    response: str = Field(..., min_length=1, max_length=5000)
    category: Optional[str] = Field(None, max_length=100)


class BotKeywordUpdateRequest(BaseModel):
    """Bot keyword update request schema"""
    keyword: Optional[str] = Field(None, min_length=1, max_length=255)
    response: Optional[str] = Field(None, min_length=1, max_length=5000)
    category: Optional[str] = Field(None, max_length=100)


# Bot Configuration endpoints
@router.get("/config")
async def get_bot_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get bot configuration for the current user's company"""
    bot_service = BotConfigurationService(db)
    config = await bot_service.get_active_configuration(company_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot configuration not found"
        )
    
    return {
        "id": str(config.id),
        "company_id": str(config.company_id),
        "bot_type": config.bot_type.value,
        "name": config.name,
        "welcome_message": config.welcome_message,
        "away_message": config.away_message,
        "closing_message": config.closing_message,
        "unknown_message": config.unknown_message,
        "language": config.language,
        "timezone": config.timezone,
        "avatar_url": config.avatar_url,
        "native_rules": config.native_rules,
        "business_hours": config.business_hours,
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat()
    }


@router.post("/config", status_code=status.HTTP_201_CREATED)
async def create_bot_config(
    request: BotConfigurationCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Create a new bot configuration"""
    bot_service = BotConfigurationService(db)
    
    config = await bot_service.create_configuration(
        company_id=company_id,
        bot_type=request.bot_type,
        name=request.name,
        welcome_message=request.welcome_message,
        away_message=request.away_message,
        closing_message=request.closing_message,
        unknown_message=request.unknown_message,
        language=request.language,
        timezone=request.timezone,
        avatar_url=request.avatar_url,
        native_rules=request.native_rules
    )
    # Save business_hours directly
    if request.business_hours is not None:
        config.business_hours = request.business_hours
        from app.bot.repositories import BotConfigurationRepository
        repo = BotConfigurationRepository(db)
        config = await repo.update(config)
    
    return {
        "id": str(config.id),
        "company_id": str(config.company_id),
        "bot_type": config.bot_type.value,
        "name": config.name,
        "welcome_message": config.welcome_message,
        "away_message": config.away_message,
        "closing_message": config.closing_message,
        "unknown_message": config.unknown_message,
        "language": config.language,
        "timezone": config.timezone,
        "avatar_url": config.avatar_url,
        "native_rules": config.native_rules,
        "business_hours": config.business_hours,
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat()
    }


@router.put("/config")
async def update_bot_config(
    request: BotConfigurationUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Update bot configuration"""
    bot_service = BotConfigurationService(db)
    config = await bot_service.get_active_configuration(company_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot configuration not found"
        )
    
    updated_config = await bot_service.update_configuration(
        config.id,
        name=request.name,
        welcome_message=request.welcome_message,
        away_message=request.away_message,
        closing_message=request.closing_message,
        unknown_message=request.unknown_message,
        language=request.language,
        timezone=request.timezone,
        avatar_url=request.avatar_url,
        native_rules=request.native_rules,
        bot_type=request.bot_type
    )
    # Save business_hours directly
    if request.business_hours is not None:
        updated_config.business_hours = request.business_hours
        from app.bot.repositories import BotConfigurationRepository
        repo = BotConfigurationRepository(db)
        updated_config = await repo.update(updated_config)
    
    return {
        "id": str(updated_config.id),
        "company_id": str(updated_config.company_id),
        "bot_type": updated_config.bot_type.value,
        "name": updated_config.name,
        "welcome_message": updated_config.welcome_message,
        "away_message": updated_config.away_message,
        "closing_message": updated_config.closing_message,
        "unknown_message": updated_config.unknown_message,
        "language": updated_config.language,
        "timezone": updated_config.timezone,
        "avatar_url": updated_config.avatar_url,
        "native_rules": updated_config.native_rules,
        "business_hours": updated_config.business_hours,
        "created_at": updated_config.created_at.isoformat(),
        "updated_at": updated_config.updated_at.isoformat()
    }


# Bot Scenario endpoints
@router.get("/scenarios")
async def get_scenarios(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get bot scenarios for the current user's company"""
    bot_service = BotConfigurationService(db)
    config = await bot_service.get_active_configuration(company_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot configuration not found"
        )
    
    scenario_repository = BotScenarioRepository(db)
    scenarios = await scenario_repository.get_by_bot_configuration_id(config.id)
    
    return [
        {
            "id": str(s.id),
            "bot_configuration_id": str(s.bot_configuration_id),
            "name": s.name,
            "trigger_keyword": s.trigger_keyword,
            "steps": s.steps,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat()
        }
        for s in scenarios
    ]


@router.post("/scenarios", status_code=status.HTTP_201_CREATED)
async def create_scenario(
    request: BotScenarioCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Create a new bot scenario"""
    bot_service = BotConfigurationService(db)
    config = await bot_service.get_active_configuration(company_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot configuration not found"
        )
    
    from app.bot.models import BotScenario
    scenario = BotScenario(
        bot_configuration_id=config.id,
        name=request.name,
        trigger_keyword=request.trigger_keyword,
        steps=request.steps,
        is_active=request.is_active
    )
    
    scenario_repository = BotScenarioRepository(db)
    created_scenario = await scenario_repository.create(scenario)
    
    return {
        "id": str(created_scenario.id),
        "bot_configuration_id": str(created_scenario.bot_configuration_id),
        "name": created_scenario.name,
        "trigger_keyword": created_scenario.trigger_keyword,
        "steps": created_scenario.steps,
        "is_active": created_scenario.is_active,
        "created_at": created_scenario.created_at.isoformat(),
        "updated_at": created_scenario.updated_at.isoformat()
    }


@router.put("/scenarios/{scenario_id}")
async def update_scenario(
    scenario_id: str,
    request: BotScenarioUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Update bot scenario"""
    scenario_repository = BotScenarioRepository(db)
    scenario = await scenario_repository.get_by_id(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    
    # Multi-tenant check
    bot_service = BotConfigurationService(db)
    config = await bot_service.get_by_id(scenario.bot_configuration_id)
    if not config or str(config.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if request.name is not None:
        scenario.name = request.name
    if request.trigger_keyword is not None:
        scenario.trigger_keyword = request.trigger_keyword
    if request.steps is not None:
        scenario.steps = request.steps
    if request.is_active is not None:
        scenario.is_active = request.is_active
    
    updated_scenario = await scenario_repository.update(scenario)
    
    return {
        "id": str(updated_scenario.id),
        "bot_configuration_id": str(updated_scenario.bot_configuration_id),
        "name": updated_scenario.name,
        "trigger_keyword": updated_scenario.trigger_keyword,
        "steps": updated_scenario.steps,
        "is_active": updated_scenario.is_active,
        "created_at": updated_scenario.created_at.isoformat(),
        "updated_at": updated_scenario.updated_at.isoformat()
    }


@router.delete("/scenarios/{scenario_id}")
async def delete_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Delete bot scenario"""
    scenario_repository = BotScenarioRepository(db)
    scenario = await scenario_repository.get_by_id(scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    
    # Multi-tenant check
    bot_service = BotConfigurationService(db)
    config = await bot_service.get_by_id(scenario.bot_configuration_id)
    if not config or str(config.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await scenario_repository.delete(scenario_id)
    
    return {"message": "Scenario deleted successfully"}


# Bot Keyword endpoints
@router.get("/keywords")
async def get_keywords(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get bot keywords for the current user's company"""
    bot_service = BotConfigurationService(db)
    config = await bot_service.get_active_configuration(company_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot configuration not found"
        )
    
    keyword_repository = BotKeywordRepository(db)
    keywords = await keyword_repository.get_by_bot_configuration_id(config.id)
    
    return [
        {
            "id": str(k.id),
            "bot_configuration_id": str(k.bot_configuration_id),
            "keyword": k.keyword,
            "response": k.response,
            "category": k.category,
            "created_at": k.created_at.isoformat(),
            "updated_at": k.updated_at.isoformat()
        }
        for k in keywords
    ]


@router.post("/keywords", status_code=status.HTTP_201_CREATED)
async def create_keyword(
    request: BotKeywordCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Create a new bot keyword"""
    bot_service = BotConfigurationService(db)
    config = await bot_service.get_active_configuration(company_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot configuration not found"
        )
    
    from app.bot.models import BotKeyword
    keyword = BotKeyword(
        bot_configuration_id=config.id,
        keyword=request.keyword,
        response=request.response,
        category=request.category
    )
    
    keyword_repository = BotKeywordRepository(db)
    created_keyword = await keyword_repository.create(keyword)
    
    return {
        "id": str(created_keyword.id),
        "bot_configuration_id": str(created_keyword.bot_configuration_id),
        "keyword": created_keyword.keyword,
        "response": created_keyword.response,
        "category": created_keyword.category,
        "created_at": created_keyword.created_at.isoformat(),
        "updated_at": created_keyword.updated_at.isoformat()
    }


@router.put("/keywords/{keyword_id}")
async def update_keyword(
    keyword_id: str,
    request: BotKeywordUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Update bot keyword"""
    keyword_repository = BotKeywordRepository(db)
    keyword = await keyword_repository.get_by_id(keyword_id)
    
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword not found"
        )
    
    # Multi-tenant check
    bot_service = BotConfigurationService(db)
    config = await bot_service.get_by_id(keyword.bot_configuration_id)
    if not config or str(config.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if request.keyword is not None:
        keyword.keyword = request.keyword
    if request.response is not None:
        keyword.response = request.response
    if request.category is not None:
        keyword.category = request.category
    
    updated_keyword = await keyword_repository.update(keyword)
    
    return {
        "id": str(updated_keyword.id),
        "bot_configuration_id": str(updated_keyword.bot_configuration_id),
        "keyword": updated_keyword.keyword,
        "response": updated_keyword.response,
        "category": updated_keyword.category,
        "created_at": updated_keyword.created_at.isoformat(),
        "updated_at": updated_keyword.updated_at.isoformat()
    }


@router.delete("/keywords/{keyword_id}")
async def delete_keyword(
    keyword_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Delete bot keyword"""
    keyword_repository = BotKeywordRepository(db)
    keyword = await keyword_repository.get_by_id(keyword_id)
    
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword not found"
        )
    
    # Multi-tenant check
    bot_service = BotConfigurationService(db)
    config = await bot_service.get_by_id(keyword.bot_configuration_id)
    if not config or str(config.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await keyword_repository.delete(keyword_id)
    
    return {"message": "Keyword deleted successfully"}
