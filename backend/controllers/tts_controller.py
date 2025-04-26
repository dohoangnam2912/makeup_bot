from gtts import gTTS
import uuid
import os

OUTPUT_DIR = "tmp"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def synthesize_speech(text: str) -> str:
    filename = f"gtts_{uuid.uuid4().hex[:8]}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)

    tts = gTTS(text=text, lang="vi", tld="com.vn")  # com.vn => Google tiếng Việt chuẩn
    tts.save(filepath)

    return filepath