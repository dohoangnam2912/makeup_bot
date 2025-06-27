"""
FastAPI application for document-based RAG system with Qdrant and MongoDB.
"""
import logging
from fastapi import FastAPI
from routes import chat_routes, tts_routes, intent_routes, stt_routes
from fastapi.middleware.cors import CORSMiddleware


# Set up logging
logger = logging.getLogger('app')
logger.setLevel('DEBUG')
file_handler = logging.FileHandler('/Users/yosakoi/Documents/Work/Makeup/logs/app.log')
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Initialize fastapi
app = FastAPI()

# Define the exact origins that are allowed to connect.
origins = [
    "http://localhost:5173", # The origin of your React frontend
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Use the explicit list of origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_routes.router, prefix="/routes")
app.include_router(tts_routes.router, prefix="/routes")
app.include_router(intent_routes.router, prefix="/routes", tags=["intent"])
app.include_router(stt_routes.router, prefix="/routes", tags=["stt"])