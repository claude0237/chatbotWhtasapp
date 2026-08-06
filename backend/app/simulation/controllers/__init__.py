"""Simulation Controller - Bot simulation for testing"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.bot.engine import BotEngine
from uuid import UUID

router = APIRouter(prefix="/simulation", tags=["Simulation"])

class SimulateRequest(BaseModel):
    company_id: str
    message: str

@router.post("/bot")
async def simulate_bot(
    request: SimulateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Simulate bot response with ML support"""
    bot_engine = BotEngine(db)
    
    response = await bot_engine.process(
        company_id=UUID(request.company_id),
        phone_number="SIMULATION",
        message_text=request.message
    )
    
    if response is None:
        return {
            "response": "Bot not configured",
            "source": "error",
            "confidence": 0.0
        }
    
    return {
        "response": response,
        "source": "bot",
        "confidence": 1.0
    }
