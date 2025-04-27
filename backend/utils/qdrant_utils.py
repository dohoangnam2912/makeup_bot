"""Vector store utilities using Qdrant with Redis caching for embeddings."""

import logging
import os
from typing import List, Optional

from dotenv import load_dotenv
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    UnstructuredHTMLLoader,
)
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, Filter, PointIdsList

from models.entities import EmbeddingModelName
from .redis_utils import test_redis_connection
from .langchain_redis import get_redis_cached_embeddings

# Configure logging
logger = logging.getLogger("app.qdrant_utils")

# Load environment variables
load_dotenv()

# Set Google API key if not already in environment
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# Check if Redis is available
USE_REDIS_CACHE = test_redis_connection()

# Constants
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
COLLECTION_NAME = "document_collection"
VECTOR_DIMENSION = 768  # Default dimension for embeddings
RETRIEVER_K = 3


def initialize_text_splitter():
    """Initialize and return the text splitter with configured parameters."""
    logger.info("Initializing text splitter")
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )



def initialize_embedding_function(model_name: str = None):
    """
    Initialize and return the embedding function.
    
    Args:
        model_name: Name of the embedding model to use
        
    Returns:
        Embeddings: Initialized embedding function
    """
    # Use the specified model or default from environment variable or entity
    model_name = model_name or os.getenv("EMBEDDING_MODEL", EmbeddingModelName.TEXT_EMBEDDING_004)
    print(f"Embedding model name: {model_name}")
    # Check if the model is a Google model or a Hugging Face model
    if model_name.startswith("models/text-embedding") or model_name.startswith("embedding"):
        logger.info(f"Using Google embedding model: {model_name}")
        base_embeddings = GoogleGenerativeAIEmbeddings(model=model_name)
    else:
        # Assuming any other model name is a Hugging Face model
        logger.info(f"Using Hugging Face embedding model: {model_name}")
        model_path = os.getenv("EMBEDDING_MODEL_PATH", model_name)
        base_embeddings = HuggingFaceEmbeddings(
            model_name=model_path,
            model_kwargs={"device": "cuda" if os.getenv("USE_GPU", "false").lower() == "true" else "cpu"}
        )
    
    # Wrap with Redis caching if available
    if USE_REDIS_CACHE:
        logger.info("Using Redis cache for embeddings")
        return get_redis_cached_embeddings(base_embeddings)
    else:
        return base_embeddings


def initialize_qdrant_client():
    """Initialize and return the Qdrant client."""
    qdrant_url = os.getenv("QDRANT_URL")
    
    if qdrant_url:
        logger.info(f"Connecting to Qdrant at {qdrant_url}")
        return QdrantClient(url=qdrant_url)
    else:
        logger.info("Using local Qdrant database")
        return QdrantClient(path="./qdrant_db")


def get_vector_dimension(embedding_function: Embeddings) -> int:
    """
    Get the vector dimension for the specified embedding function.
    
    Args:
        embedding_function: Initialized embedding function
        
    Returns:
        int: Vector dimension
    """
    # For Google models, dimension is fixed
    logger.info(f"Getting vector dimension for embedding model: {embedding_function}")
    if isinstance(embedding_function, GoogleGenerativeAIEmbeddings):
        if "004" in embedding_function.model:
            return 768
        elif "003" in embedding_function.model:
            return 768
        else:
            return 768  # Default
            
    # For Hugging Face models, we need to compute it
    try:
        # Embed a simple text to get the dimension
        test_embedding = embedding_function.embed_query("test")
        return len(test_embedding)
    except Exception as e:
        logger.warning(f"Error determining vector dimension: {e}. Using default: {VECTOR_DIMENSION}")
        return VECTOR_DIMENSION


def ensure_collection_exists(client, embedding_function):
    """
    Ensure that the Qdrant collection exists, creating it if necessary.
    
    Args:
        client: Initialized Qdrant client
        embedding_function: Initialized embedding function
        
    Returns:
        bool: True if collection exists or was created successfully
    """
    try:
        collections = client.get_collections()
        collection_names = [collection.name for collection in collections.collections]
        
        # Get vector dimension for the embedding model
        dimension = get_vector_dimension(embedding_function)
        
        if COLLECTION_NAME not in collection_names:
            logger.info(f"Creating new Qdrant collection: {COLLECTION_NAME} with dimension {dimension}")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={
                    "size": dimension,
                    "distance": Distance.COSINE,
                },
            )
            logger.info("Collection created successfully")
        else:
            # Verify dimension matches
            collection_info = client.get_collection(COLLECTION_NAME)
            actual_dimension = collection_info.config.params.vectors.size
            
            if actual_dimension != dimension:
                logger.warning(
                    f"Collection dimension mismatch: collection={actual_dimension}, model={dimension}. "
                    f"Using existing collection, but this may cause issues."
                )
            
            logger.info(f"Collection {COLLECTION_NAME} already exists with dimension {actual_dimension}")
        
        return True
    except Exception as e:
        logger.error(f"Error ensuring collection exists: {e}")
        return False


def initialize_vectorstore(client, embedding_function):
    """
    Initialize and return the Qdrant vector store.
    
    Args:
        client: Initialized Qdrant client
        embedding_function: Initialized embedding function
        
    Returns:
        Qdrant: Initialized vector store
    """
    return Qdrant(
        client=client,
        collection_name=COLLECTION_NAME,
        embeddings=embedding_function,
        metadata_payload_key="metadata",
    )


def load_and_split_document(file_path: str, text_splitter) -> List[Document]:
    """
    Load document from file path and split into chunks.
    
    Args:
        file_path: Path to the document file
        text_splitter: Initialized text splitter
        
    Returns:
        List[Document]: List of document chunks
        
    Raises:
        ValueError: If file type is not supported
    """
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
    logger.info(f"Finished loading with {len(documents)} documents.")
    
    split_documents = text_splitter.split_documents(documents=documents)
    logger.info(f"Split into {len(split_documents)} chunks.")
    
    return split_documents


def index_document_to_qdrant(vectorstore, file_path: str, file_id: int) -> bool:
    logger.info(f"Indexing to Qdrant with {file_path} - {file_id}")
    
    try:
        text_splitter = initialize_text_splitter()
        splits = load_and_split_document(file_path, text_splitter)

        # Add metadata to each split
        for split in splits:
            split.metadata['file_id'] = file_id
        
        logger.info(f"Adding {len(splits)} document chunks to Qdrant")
        vectorstore.add_documents(splits)
        logger.info("Successfully added documents to Qdrant")
        
        return True
    
    except Exception as e:
        logger.error(f"Error indexing document: {e}")
        return False


def delete_document_from_qdrant(client, file_id: int) -> bool:
    """
    Delete document chunks from Qdrant by file_id.
    
    Args:
        client: Initialized Qdrant client
        file_id: File ID to delete
        
    Returns:
        bool: True if deletion was successful
    """
    try:
        # Create filter for the specific file_id
        file_filter = Filter(
            must=[
                {"key": "metadata.file_id", "match": {"value": file_id}}
            ]
        )
        
        # Get the points with the specified file_id
        search_result = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=file_filter,
            limit=10000,  # Adjust based on expected maximum chunks per document
        )
        
        point_ids = [point.id for point in search_result[0]]
        logger.info(f"Found {len(point_ids)} document chunks for file_id {file_id}")
        
        if point_ids:
            # Delete the points with the specified IDs
            client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=PointIdsList(points=point_ids),
            )
            logger.info(f"Deleted {len(point_ids)} document chunks for file_id {file_id}")
        else:
            logger.warning(f"No documents found for file_id {file_id}")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to delete documents with file_id {file_id}: {e}")
        return False


def create_retriever(vectorstore, k=RETRIEVER_K):
    """
    Create a retriever from the vector store.
    
    Args:
        vectorstore: Initialized vector store
        k: Number of results to retrieve
        
    Returns:
        Retriever: Configured retriever
    """
    return vectorstore.as_retriever(search_kwargs={"k": k})


def get_embedding_model_name():
    """Get the current embedding model name from environment or default."""
    return os.getenv("EMBEDDING_MODEL", EmbeddingModelName.TEXT_EMBEDDING_004)


# Initialize components for direct import
text_splitter = initialize_text_splitter()
embedding_function = initialize_embedding_function()
client = initialize_qdrant_client()
ensure_collection_exists(client, embedding_function)
vectorstore = initialize_vectorstore(client, embedding_function)
retriever = create_retriever(vectorstore)


# For direct usage in other modules
def index_document(file_path: str, file_id: int) -> bool:
    """Public function to index a document."""
    return index_document_to_qdrant(vectorstore, file_path, file_id)


def delete_document(file_id: int) -> bool:
    """Public function to delete a document."""
    return delete_document_from_qdrant(client, file_id)


def reinitialize_with_embedding_model(model_name: str) -> None:
    """
    Reinitialize the vector store with a different embedding model.
    
    Args:
        model_name: Name of the embedding model to use
    """
    global embedding_function, vectorstore, retriever
    
    logger.info(f"Reinitializing vector store with embedding model: {model_name}")
    embedding_function = initialize_embedding_function(model_name)
    
    # Ensure collection exists with proper dimensions
    ensure_collection_exists(client, embedding_function)
    
    # Reinitialize the vector store and retriever
    vectorstore = initialize_vectorstore(client, embedding_function)
    retriever = create_retriever(vectorstore)
    
    logger.info("Vector store reinitialized successfully")