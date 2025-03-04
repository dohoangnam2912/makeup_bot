# index_document_to_chroma, delete_document_from_chroma
# This modules need to process pdf, docs, html file
# What do you mean by process? Load, chunk em, then save them into chroma
# Chunking texts
# Embedding
# Indexing to chroma
# Remove them also
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from typing import List
from dotenv import load_dotenv
from entities import EmbeddingModelName
import os
import logging

logger = logging.getLogger('app.chroma_utils')
load_dotenv("../.env")
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200,length_function=len)
embedding_function = GoogleGenerativeAIEmbeddings(model=EmbeddingModelName.TEXT_EMBEDDING_004)

vectorstore = Chroma(persist_directory='./chroma_db', embedding_function=embedding_function)

def load_and_split_document(file_path: str) -> List[Document]:
    logger.info("Loading uploaded file.")
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path=file_path)
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path=file_path)
    elif file_path.endswith('.html'):
        loader = UnstructuredHTMLLoader(file_path=file_path)
    else:
        logger.warning("Loading unsupported file.")
        raise ValueError(f"Unsupported file type: {file_path}.")
    
    documents = loader.load()
    logger.info(f"Finished loading with documents.")
    return text_splitter.split_documents(documents=documents)

def index_document_to_chroma(file_path: str, file_id: int) -> bool:
    logger.info(f"Indexing to Chroma with {file_path} - {file_id}")
    try:
        splits = load_and_split_document(file_path)

        # Add metadata to each split
        for split in splits:
            split.metadata['file_id'] = file_id
        logger.info("Done splitting")
        
        vectorstore.add_documents(splits)
        return True
    
    except Exception as e:
        logger.info(f"Error indexing document with error: {e}")
        return False
    
def delete_document_from_chroma(file_id: int):
    try:
        docs = vectorstore.get(where={"file_id":file_id})
        logger.info(f"FOUND {len(docs['ids'])} document chunks for file_id {file_id}")

        vectorstore._collection.delete(where={"file_id":file_id})
        logger.info(f"DELETED {len(docs['ids'])} document chunks for file_id {file_id}")

        return True
    except Exception as e:
        logger.warning(f"FAILED to DELETE documents with {file_id}")
        return False
    
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
