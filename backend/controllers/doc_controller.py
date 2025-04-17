import logging
import os
import shutil
import uuid

from fastapi import Body, FastAPI, File, HTTPException, UploadFile

from entities import DeleteFileRequest, Document, QueryInput, QueryResponse
from langchain_utils import get_rag_chain
from mongo_utils import (
    get_all_documents,
    get_chat_history,
    insert_application_logs,
    insert_document_record,
    delete_document_record,
)
from qdrant_utils import delete_document_from_qdrant, index_document_to_qdrant