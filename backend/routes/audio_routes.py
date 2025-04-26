from fastapi import APIRouter, UploadFile, File
from controllers.audio_controller import transcribe_audio

router = APIRouter()

@router.post("/transcribe")
async def transcribe_route(audio: UploadFile = File(...)):
    transcript = transcribe_audio(audio)
    return {"transcript": transcript}
