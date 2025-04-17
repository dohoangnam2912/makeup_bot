import sqlite3
import logging
from datetime import datetime

DB_NAME = "rag_app.db"

LOOKUP_FUNCTION = [
    "get_db_connection",
    "create_application_logs",
    "insert_application_logs",
    "insert_document_record", 
    "delete_document_record", 
    "get_all_documents", 
    "get_chat_history"
]


logger = logging.getLogger('app.db')

def get_db_connection():
    logger.info("Connecting to db.")
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    try:
        yield conn
    finally:
        conn.close()

def create_application_logs():
    logger.info("Creating application logs.")
    try:
        with sqlite3.connect(DB_NAME) as conn: 
            conn.row_factory = sqlite3.Row
            conn.execute("""
                CREATE TABLE IF NOT EXISTS application_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    user_query TEXT,
                    response TEXT,
                    model TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """) 
    except sqlite3.Error as e:
        logger.error(e) 

def create_document_store():
    logger.info("Creating documents store.")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_store (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_name TEXT,
                        upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    except sqlite3.Error as e:
        logger.error(e) 

def insert_application_logs(session_id, user_query, response, model):
    logger.info("Inserting application logs.")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("""
                INSERT INTO application_logs (session_id, user_query, response, model) VALUES (?, ?, ?, ?)
            """, (session_id, user_query, response, model))
    except sqlite3.Error as e:
        logger.error(f"Insert application error {e}") 

def insert_document_record(file_name):
    logger.info("Inserting document record.")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor() 
            cursor.execute("""
                INSERT INTO document_store (file_name) VALUES (?)
            """, (file_name,))
            file_id = cursor.lastrowid
        return file_id
    except sqlite3.Error as e:
        logger.error(e)
        return None 
    

# TODO: Need improvement because can't insert all the messages into chat
# Right now we add only 10 chat
def get_chat_history(session_id):
    logger.info("Getting chat history.")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT user_query, response FROM application_logs WHERE session_id=? LIMIT 10 ORDER BY created_at DESC", (session_id,))
            messages = []
            for row in cursor.fetchall():
                messages.extend([
                    {"role": "human", "content": row['user_query']},
                    {"role": "ai", "content": row["response"]}
                ])
            logger.info(f"Returning chat {messages}")
            return messages
    except sqlite3.Error as e:
        logger.error(e) 

def delete_document_record(file_id):
    logger.info(f"DELETE in SQL database with {file_id}")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("""
                DELETE FROM document_store WHERE id = ?
            """, (file_id,))
        return True
    except sqlite3.Error as e:
        logger.error(e) 
        return False
    
def get_all_documents():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, file_name, upload_timestamp FROM document_store ORDER BY upload_timestamp DESC")
            documents = cursor.fetchall()
        return [dict(doc) for doc in documents]
    except sqlite3.Error as e:
        logger.error(e)
        return None



create_application_logs()
create_document_store()
