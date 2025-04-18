from fastapi import APIRouter, UploadFile, File, Body
from controllers.doc_controller import ( 
    handle_upload_and_index_document, 
    handle_list_documents,
    handle_delete_document
)
from models.entities import Document, DeleteFileRequest

router = APIRouter()

@router.post("/upload-doc")
def upload_and_index_document(file: UploadFile = File(...)):
    return handle_upload_and_index_document(file)

@router.get("/list-docs", response_model=list[Document])
def list_documents():
    return handle_list_documents()

@router.post("/delete-doc")
def delete_document(request: DeleteFileRequest = Body(...)):
    return handle_delete_document(request)
