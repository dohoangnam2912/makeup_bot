from fastapi import UploadFile
import logging
from transformers import pipeline
import tempfile

logger = logging.getLogger("app.audio_controller")

# Load the PhoWhisper model once
transcriber = pipeline(
    "automatic-speech-recognition",
    model="vinai/PhoWhisper-tiny",
    generate_kwargs={"language": "vi"}
)

def transcribe_audio(file: UploadFile) -> str:
    # Create a temporary file from UploadFile in memory
    with tempfile.NamedTemporaryFile(suffix=".wav") as temp_audio:
        temp_audio.write(file.file.read())
        temp_audio.flush()  # ensure all content is written

        result = transcriber(temp_audio.name)
        logger.info(f"Speech: {result['text']}")
        return result["text"]
