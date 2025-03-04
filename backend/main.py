from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from db_utils import insert_application_logs, insert_document_record, delete_document_record, get_all_documents, get_chat_history
from langchain_core.output_parsers import StrOutputParser
from chroma_utils import index_document_to_chroma, delete_document_from_chroma
from langchain_utils import get_rag_chain
import logging
from entities import *
import uuid
import os
import shutil

# Set up logging
logger = logging.getLogger('app')
logger.setLevel('DEBUG')
file_handler = logging.FileHandler('app.log')
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Initialize fastapi
app = FastAPI()

@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):
    session_id = query_input.session_id or str(uuid.uuid4())
    logger.info(f"Session ID: {session_id}, User Query: {query_input.question}, Model: {query_input.model}")
    
    chat_history = get_chat_history(session_id)
    rag_chain = get_rag_chain(query_input.model.value)
    response = rag_chain.invoke({
        "input": query_input.question,
        "chat_history": chat_history
    })
    insert_application_logs(session_id, query_input.question, response["answer"], query_input.model)
    logger.info(f"Session ID: {session_id}, AI response: {response}")
    return QueryResponse(response=response["answer"], session_id=session_id, model=query_input.model)

@app.post("/upload-doc")
def upload_and_index_document(file: UploadFile = File(...)):
    allowed_extension = [".docx", ".pdf", ".html"]
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extension:
        logger.warning(f"Unsupported file type. Allowed types are {', '.join(allowed_extension)}")
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are {', '.join(allowed_extension)}")
    
    safe_file_path = os.path.basename(file.filename)
    temp_file_path = f"/tmp/{safe_file_path}"

    try:
        # Save the uploaded file to a temporary file
        with open(temp_file_path, "wb") as buffer:  
            shutil.copyfileobj(file.file, buffer)
        
        file_id = insert_document_record(file.filename)
        chroma_index_success = index_document_to_chroma(temp_file_path, file_id)
        if chroma_index_success:
            return {"message": f"File {file.filename} has been successfully uploaded and indexed.", "file_id": file_id}
        else:
            delete_document_record(file.filename)
            logger.error(f"Failed to index file: {file.filename}.")
            raise HTTPException(status_code=500, detail=f"Failed to index file: {file.filename}.")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/list-docs", response_model=list[Document])
def list_documents():
    logger.info("Getting list of documents.")
    return get_all_documents() 


@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest = Body(...)):
    logger.info(f"Deleting documents with file_id {request.file_id}.")
    chroma_delete_success = delete_document_from_chroma(request.file_id)

    if chroma_delete_success:
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {"message": f"Successfully deleted document with {request.file_id} from the system.", }
        else:
            logger.warning(f"Deleted from Chroma but failed to delete document with file_id {request.file_id} from the database.")
            return {"error": f"Deleted from Chroma but failed to delete document with file_id {request.file_id} from the database."}
    else:
        logger.warning(f"Failed to delete document with file_id {request.file_id} form Chroma.")
        return {"error": f"Failed to delete document with file_id {request.file_id} form Chroma."}