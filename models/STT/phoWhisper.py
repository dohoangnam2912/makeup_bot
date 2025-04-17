from transformers import pipeline

transcriber = pipeline("automatic-speech-recognition", model="vinai/PhoWhisper-tiny")
output = transcriber('/home/yosakoi/Work/chatbot/model/STT/Whisper_CODE/sample4.wav')['text']

print(output)