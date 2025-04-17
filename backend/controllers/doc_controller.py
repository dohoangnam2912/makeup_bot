import logging
import os
import shutil
import uuid

from fastapi import Body, FastAPI, File, HTTPException, UploadFile

from backend.models.entities import DeleteFileRequest, Document, QueryInput, QueryResponse
from utils.langchain_utils import get_rag_chain
from utils.mongo_utils import (
    get_all_documents,
    insert_document_record,
    delete_document_record,
)
from utils.qdrant_utils import delete_document_from_qdrant, index_document_to_qdrant

logger = logging.getLogger("app.doc_controller")

def handle_upload_and_index_document(file: UploadFile = File(...)):
    """
    Upload and index a document to the RAG system.
    
    Args:
        file: The uploaded file object
        
    Returns:
        dict: Status message and file ID
        
    Raises:
        HTTPException: If file type is not supported or indexing fails
    """
    allowed_extension = [".docx", ".pdf", ".html"]
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extension:
        allowed_types = ', '.join(allowed_extension)
        logger.warning(f"Unsupported file type. Allowed types are {allowed_types}")
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed types are {allowed_types}"
        )
    
    safe_file_path = os.path.basename(file.filename)
    temp_file_path = f"/tmp/{safe_file_path}"

    try:
        # Save the uploaded file to a temporary file
        with open(temp_file_path, "wb") as buffer:  
            shutil.copyfileobj(file.file, buffer)
        
        file_id = insert_document_record(file.filename)
        qdrant_index_success = index_document_to_qdrant(temp_file_path, file_id)
        
        if qdrant_index_success:
            return {
                "message": f"File {file.filename} has been successfully uploaded and indexed.",
                "file_id": file_id
            }
        else:
            delete_document_record(file_id)
            logger.error(f"Failed to index file: {file.filename}.")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to index file: {file.filename}."
            )
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def handle_list_documents():
    """
    List all documents in the system.
    
    Returns:
        list[Document]: List of document records
    """
    logger.info("Getting list of documents.")
    return get_all_documents() 


def handle_delete_document(request: DeleteFileRequest = Body(...)):
    """
    Delete a document from the system.
    
    Args:
        request: The delete request containing the file ID
        
    Returns:
        dict: Status message
    """
    logger.info(f"Deleting documents with file_id {request.file_id}.")
    qdrant_delete_success = delete_document_from_qdrant(request.file_id)

    if qdrant_delete_success:
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {
                "message": f"Successfully deleted document with {request.file_id} from the system."
            }
        else:
            logger.warning(
                f"Deleted from Qdrant but failed to delete document with file_id "
                f"{request.file_id} from the database."
            )
            return {
                "error": f"Deleted from Qdrant but failed to delete document with file_id "
                         f"{request.file_id} from the database."
            }
    else:
        logger.warning(f"Failed to delete document with file_id {request.file_id} from Qdrant.")
        return {
            "error": f"Failed to delete document with file_id {request.file_id} from Qdrant."
        }