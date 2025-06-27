from fastapi import APIRouter, Form
from fastapi.responses import FileResponse
from controllers.tts_controller import synthesize_speech
from pydantic import BaseModel
# from models.entities import Message

router = APIRouter()

class SynthesizeRequest(BaseModel):
    message: str

# 2. Update your endpoint to expect an instance of this model.
@router.post("/synthesize")
def synthesize_endpoint(text: str = Form(...)):
    filepath = synthesize_speech(text)
    return FileResponse(filepath, media_type="audio/wav", filename=filepath.split("/")[-1])
