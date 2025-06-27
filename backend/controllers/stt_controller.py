from fastapi import UploadFile, File, HTTPException
from llm_models.STT.whisper import transcribe_audio

# This is now just a regular function containing your business logic.
# It does not know it's being used by an API.
def handle_transcription(file: UploadFile = File(...)):
    """
    Takes an audio file and returns the transcribed text.
    """
    try:
        text = transcribe_audio(file)
        return {"text": text}
    except Exception as e:
        print(f"Error during transcription: {e}")
        raise HTTPException(status_code=500, detail="Audio transcription failed.")