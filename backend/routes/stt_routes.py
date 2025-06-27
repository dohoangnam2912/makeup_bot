from fastapi import APIRouter, UploadFile, File
from controllers.stt_controller import handle_transcription

router = APIRouter()

@router.post("/transcribe")
def transcribe_endpoint(file: UploadFile = File(...)):
    return handle_transcription(file)