import logging
import os
import shutil

from fastapi import UploadFile, HTTPException
from models.entities import DeleteFileRequest
from utils.mongo_utils import (
    get_all_documents,
    insert_document_record,
    delete_document_record,
)
from utils.qdrant_utils import delete_document_from_qdrant, index_document_to_qdrant

logger = logging.getLogger("app.doc_controller")

def handle_upload_and_index_document(file: UploadFile):
    allowed_extensions = [".docx", ".pdf", ".html"]
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in allowed_extensions:
        logger.warning(f"Unsupported file type: {ext}")
        raise HTTPException(400, f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}")

    temp_path = f"/tmp/{os.path.basename(file.filename)}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_id = insert_document_record(file.filename)
        if index_document_to_qdrant(temp_path, file_id):
            return {"message": f"File {file.filename} uploaded and indexed.", "file_id": file_id}
        else:
            delete_document_record(file_id)
            logger.error(f"Failed to index file: {file.filename}")
            raise HTTPException(500, f"Failed to index file: {file.filename}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def handle_list_documents():
    logger.info("Listing documents.")
    return get_all_documents()

def handle_delete_document(request: DeleteFileRequest):
    logger.info(f"Deleting document with file_id {request.file_id}")
    if delete_document_from_qdrant(request.file_id):
        if delete_document_record(request.file_id):
            return {"message": f"Deleted document {request.file_id}."}
        else:
            logger.warning(f"Qdrant deleted but Mongo failed for {request.file_id}")
            return {"error": "Deleted from Qdrant but not MongoDB."}
    else:
        logger.warning(f"Failed to delete {request.file_id} from Qdrant.")
        return {"error": f"Failed to delete {request.file_id} from Qdrant."}
