import whisper
import csv
import os

# Load the Whisper model
# Options: "tiny", "base", "small", "medium", "large"
model = whisper.load_model("medium")

# Load an audio file (WAV, MP3, or other formats supported by ffmpeg)
audio_path = "/home/yosakoi/Work/chatbot/model/STT/Whisper_CODE/sample3.wav"

# Check if the audio file exists
if not os.path.exists(audio_path):
    print(f"Error: Audio file '{audio_path}' not found.")

# Transcribe the audio
result = model.transcribe(audio_path, language="vi")  # For Vietnamese

# # Translation
# result = model.transcribe(audio_path, task="translate")

# Print the transcribed text
print("Transcription:")
print(result["text"])

# Optional: Print timestamps for each segment
print("\nTimestamps:")
for segment in result["segments"]:
    print(f"[{segment['start']:.2f}s - {segment['end']:.2f}s]: {segment['text']}")

# Save transcription to a CSV file
csv_file = "transcription_output.csv"

# Write the results to the CSV
with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    # Write the header
    writer.writerow(["Start Time (s)", "End Time (s)", "Text"])

    # Write each segment
    for segment in result["segments"]:
        writer.writerow([segment["start"], segment["end"], segment["text"]])

print(f"Transcription saved to {csv_file}")