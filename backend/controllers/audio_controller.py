from fastapi import UploadFile
import logging
from transformers import pipeline
import tempfile
import torch  # Import torch

logger = logging.getLogger("app.audio_controller")

# Determine the device to use
device = "cuda:0" if torch.cuda.is_available() else "cpu" # Use GPU 0 if available, otherwise use CPU

# Load the PhoWhisper model once, and move it to the GPU if available
transcriber = pipeline(
    "automatic-speech-recognition",
    model="vinai/PhoWhisper-large",
    generate_kwargs={"language": "vi"},
    device=device  # Pass the device here
)

def transcribe_audio(file: UploadFile) -> str:
    # Create a temporary file from UploadFile in memory
    with tempfile.NamedTemporaryFile(suffix=".wav") as temp_audio:
        temp_audio.write(file.file.read())
        temp_audio.flush()  # ensure all content is written

        result = transcriber(temp_audio.name)
        logger.info(f"Speech: {result['text']}")
        return result["text"]
