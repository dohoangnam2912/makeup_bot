from fastapi import APIRouter, Form
from fastapi.responses import FileResponse
from controllers.tts_controller import synthesize_speech

router = APIRouter()

@router.post("/speak")
async def speak_route(text: str = Form(...)):
    filepath = synthesize_speech(text)
    return FileResponse(filepath, media_type="audio/wav", filename=filepath.split("/")[-1])
