# backend/routes/intent_routes.py

from fastapi import APIRouter
from controllers import intent_controller

router = APIRouter()

router.include_router(intent_controller.router, prefix="/intent", tags=["intent"])