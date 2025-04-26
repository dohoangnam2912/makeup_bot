"""
FastAPI application for document-based RAG system with Qdrant and MongoDB.
"""
import logging
from fastapi import FastAPI
from routes import chat_routes, doc_routes, audio_routes, tts_routes
from fastapi.middleware.cors import CORSMiddleware


# Set up logging
logger = logging.getLogger('app')
logger.setLevel('DEBUG')
file_handler = logging.FileHandler('/home/yosakoi/Work/chatbot/logs/app.log')
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Initialize fastapi
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_routes.router, prefix="/routes")
app.include_router(doc_routes.router, prefix="/routes")
app.include_router(audio_routes.router, prefix="/routes")
app.include_router(tts_routes.router, prefix="/routes")