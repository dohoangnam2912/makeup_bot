import uuid
import logging
from backend.models.entities import QueryInput, QueryResponse
from backend.utils.langchain_utils import get_rag_chain
from backend.utils.mongo_utils import (
    get_chat_history,
    insert_application_logs
)

logger = logging.getLogger("app.chat_controller")

def handle_chat(query_input: QueryInput) -> QueryResponse:
    """
    Process a chat query using the RAG system.
    
    Args:
        query_input: The query input including question and model preferences
        
    Returns:
        QueryResponse: The AI response and session information
    """
    session_id = query_input.session_id or str(uuid.uuid4())
    logger.info(
        f"Session ID: {session_id}, User Query: {query_input.question}, "
        f"Model: {query_input.model}"
    )
    
    chat_history = get_chat_history(session_id)
    logger.info(f"Chat history: {chat_history}")
    rag_chain = get_rag_chain(query_input.model.value)
    response = rag_chain.invoke({
        "input": query_input.question,
        "chat_history": chat_history
    })
    logger.info("Sucessfully invoke rag_chain")
    insert_application_logs(
        session_id, 
        query_input.question, 
        response["answer"], 
        query_input.model
    )
    logger.info(f"Session ID: {session_id}, AI response: {response}")
    
    return QueryResponse(
        response=response["answer"],
        session_id=session_id,
        model=query_input.model
    )