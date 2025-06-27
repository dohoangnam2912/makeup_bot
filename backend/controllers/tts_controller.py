import uuid
import os
import numpy as np
import soundfile as sf
from kokoro import KPipeline

# Initialize the Kokoro TTS pipeline for American English
pipeline = KPipeline(lang_code="a")  # 'a' = American English

OUTPUT_DIR = "tmp"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def synthesize_speech(text: str, voice="af_heart", speed=1.0) -> str:
    filename = f"kokoro{uuid.uuid4().hex[:8]}.wav"
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        gen = pipeline(text, voice=voice, speed=speed)
        audio_parts = [audio for _, _, audio in gen]
        audio = np.concatenate(audio_parts)
        sf.write(filepath, audio, 24000)
        return filepath
    except Exception as e:
        print(f"[TTS Error] {e}")
        return ""

# Example use
if __name__ == "__main__":
    path = synthesize_speech("Hello! This is Kokoro speaking.")
    print("Audio saved at:", path)
