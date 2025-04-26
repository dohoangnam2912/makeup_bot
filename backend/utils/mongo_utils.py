"""
MongoDB utility functions for the RAG application database operations.
"""
import logging
import os
from datetime import datetime

from pymongo import MongoClient, DESCENDING

# Set up constants
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "rag_app")

# Configure logging
logger = logging.getLogger('app.db')

# Define collection names
LOGS_COLLECTION = "application_logs"
DOCS_COLLECTION = "document_store"
SESSIONS_COLLECTION = "chat_sessions"

def get_db_connection():
    """
    Get a connection to the MongoDB database.
    
    Returns:
        tuple: MongoDB client and database objects
    """
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        logger.info("Succesfully connected to MongoDB.")
        return client, db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


def create_collections():
    """
    Initialize MongoDB collections and create indexes.
    """
    try:
        client, db = get_db_connection()
        
        # Create application_logs collection if it doesn't exist
        if LOGS_COLLECTION not in db.list_collection_names():
            logger.info("Creating application logs collection.")
            db.create_collection(LOGS_COLLECTION)
        
        # Create document_store collection if it doesn't exist
        if DOCS_COLLECTION not in db.list_collection_names():
            logger.info("Creating documents store collection.")
            db.create_collection(DOCS_COLLECTION)
        
        # Create indexes
        db[LOGS_COLLECTION].create_index("session_id")
        db[LOGS_COLLECTION].create_index("created_at")
        db[DOCS_COLLECTION].create_index("file_name")
        db[DOCS_COLLECTION].create_index("upload_timestamp")
        logger.info("Successfully inserted create collections.")
        client.close()
    except Exception as e:
        logger.error(f"Failed to create collections: {e}")


def insert_application_logs(session_id, user_query, response, model):
    """
    Insert a log entry for a chat interaction.
    
    Args:
        session_id: The unique session identifier
        user_query: The user's question
        response: The AI's response
        model: The model used for generating the response
    """
    logger.info("Inserting application logs.")
    try:
        client, db = get_db_connection()
        
        log_data = {
            "session_id": session_id,
            "user_query": user_query,
            "response": response,
            "model": model.value if hasattr(model, 'value') else str(model),
            "created_at": datetime.now()
        }
        
        db[LOGS_COLLECTION].insert_one(log_data)
        logger.info("Successfully inserted application logs.")
        client.close()
    except Exception as e:
        logger.error(f"Insert application error: {e}")


def insert_document_record(file_name):
    """
    Insert a new document record.
    
    Args:
        file_name: Name of the uploaded file
        
    Returns:
        str: Generated file_id or None on failure
    """
    try:
        client, db = get_db_connection()
        
        doc_data = {
            "file_name": file_name,
            "upload_timestamp": datetime.now()
        }
        
        result = db[DOCS_COLLECTION].insert_one(doc_data)
        file_id = str(result.inserted_id)
        
        client.close()
        logger.info("Successfully document record.")
        return file_id
    except Exception as e:
        logger.error(f"Failed to insert document record: {e}")
        return None


def get_chat_history(session_id):
    """
    Retrieve chat history for a specific session.
    
    Args:
        session_id: The unique session identifier
        
    Returns:
        list: List of message dictionaries in the format expected by LangChain
    """
    logger.info("Getting chat history.")
    try:
        client, db = get_db_connection()
        
        cursor = db[LOGS_COLLECTION].find(
            {"session_id": session_id},
            {"_id": 0, "user_query": 1, "response": 1, "created_at": 1}
        ).sort("created_at", DESCENDING).limit(10) # Limit 10 recent turns
        
        messages = []
        for row in cursor:
            messages.extend([
                ("human", row['user_query']),
                ("ai", row["response"])
            ])
        
        client.close()
        logger.info(f"Successfully retrieved {len(messages)//2} conversation turns")
        return messages
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        return []


def delete_document_record(file_id):
    """
    Delete a document record.
    
    Args:
        file_id: Unique identifier for the document
        
    Returns:
        bool: True if deletion succeeded, False otherwise
    """
    logger.info(f"Deleting document with ID {file_id} from MongoDB")
    try:
        client, db = get_db_connection()
        
        from bson.objectid import ObjectId
        result = db[DOCS_COLLECTION].delete_one({"_id": ObjectId(file_id)})
        
        client.close()
        logger.info(f"Successfully deleted document with ID {file_id} from MongoDB")
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Failed to delete document record: {e}")
        return False


def get_all_documents():
    """
    Retrieve all document records.
    
    Returns:
        list: List of document dictionaries
    """
    try:
        client, db = get_db_connection()
        
        cursor = db[DOCS_COLLECTION].find().sort("upload_timestamp", DESCENDING)
        
        # Convert ObjectId to string for JSON serialization
        documents = []
        for doc in cursor:
            doc["file_id"] = str(doc.pop("_id"))  # Replace _id with file_id as string
            documents.append(doc)
        
        client.close()
        logger.error(f"Successfully retrieved documents: {e}")
        return documents
    except Exception as e:
        logger.error(f"Failed to retrieve documents: {e}")
        return []


# Create collections and indexes on module import
create_collections()