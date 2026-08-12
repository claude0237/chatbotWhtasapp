"""ML Routes"""
from app.ml.controllers import router as ml_router, public_router as ml_public_router

router = ml_router
public_router = ml_public_router
