import uuid
import logging
from models.entities import QueryInput, QueryResponse, QueryRewritingModel
from utils.langchain_utils import get_rag_chain, rewrite_prompt_with_llm
from utils.mongo_utils import (
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
    logger.info(f"User Query: {query_input.question}")
    
    # Step 1: Try to rewrite the prompt using LLM
    try:
        rewrite_model = QueryRewritingModel.GEMINI_2_FLASH
        rewritten_prompt = rewrite_prompt_with_llm(rewrite_model.value, query_input.question)
        logger.info(f"Rewritten Prompt: {rewritten_prompt}")
    except Exception as e:
        # If something goes wrong with the LLM, keep the original input
        logger.error(f"Error while rewriting prompt: {e}")
        rewritten_prompt = query_input.question  # Keep the original input in case of error
        logger.info(f"Fallback to original prompt: {rewritten_prompt}")
    
    # Step 2: Get chat history for the session
    chat_history = get_chat_history(session_id)
    
    # Step 3: Create RAG chain using the rewritten prompt
    rag_chain = get_rag_chain(query_input.model.value, rewritten_prompt)
    
    # Step 4: Get response from the RAG chain
    response = rag_chain.invoke({
        "input": rewritten_prompt,
        "chat_history": chat_history
    })

    # Step 5: Extract answer from the response
    if isinstance(response, dict):
        answer_text = response.get("answer") or response.get("text") or ""
    else:
        answer_text = response

    # Step 6: Log the successful invocation of RAG chain
    logger.info("Successfully invoked rag_chain")
    
    # Step 7: Insert application logs (store logs in DB or file)
    insert_application_logs(
        session_id, 
        rewritten_prompt, 
        answer_text, 
        query_input.model
    )

    # Step 8: Log the session and response for debugging purposes
    logger.info(f"Session ID: {session_id}, AI response: {answer_text}")
    
    # Step 9: Return response along with rewritten question
    return QueryResponse(
        response=answer_text,
        session_id=session_id,
        model=query_input.model,
        rewritten_question=rewritten_prompt  # Return the rewritten question to the frontend
    )