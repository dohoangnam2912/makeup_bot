# backend/controllers/intent_controller.py

from fastapi import APIRouter
from pydantic import BaseModel
from utils.intent_classifier import IntentClassifier

class IntentRequest(BaseModel):
    text: str

router = APIRouter()
classifier = IntentClassifier()

@router.post("/classify")
def classify_intent(request: IntentRequest):
    intent = classifier.classify(request.text)
    return {"intent": intent}