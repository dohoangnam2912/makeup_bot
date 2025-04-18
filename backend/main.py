"""
FastAPI application for document-based RAG system with Qdrant and MongoDB.
"""
import logging
import os


from fastapi import FastAPI
from routes import chat_routes, doc_routes

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
app.include_router(chat_routes.router, prefix="/routes")
app.include_router(doc_routes.router, prefix="/routes")
