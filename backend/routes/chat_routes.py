from fastapi import APIRouter, Response, Cookie, Depends
from controllers.chat_controller import handle_chat
from models.entities import QueryInput, QueryResponse
import logging

router = APIRouter()
logger = logging.getLogger("app.chat_routes")

def get_conversation_id(conversation_id: str | None = Cookie(default=None)) -> str | None:
    logger.info(f"Retrieved conversation_id from cookie: {conversation_id}")
    return conversation_id

@router.post("/chat", response_model=QueryResponse)
def chat(
    query_input: QueryInput,
    response: Response,
    conversation_id: str | None = Depends(get_conversation_id),
):
    logger.info(f"Chat endpoint called with conversation_id: {conversation_id}")
    
    # Pass the existing conversation_id (from cookie) to the chat handler
    qr: QueryResponse = handle_chat(query_input, conversation_id=conversation_id)
    
    logger.info(f"Chat handler returned conversation_id: {qr.conversation_id}")

    if qr.conversation_id and (not conversation_id or qr.conversation_id != conversation_id):
        logger.info(f"Setting conversation_id cookie: {qr.conversation_id}")
        response.set_cookie(
            key="conversation_id",
            value=qr.conversation_id,
            httponly=True,
            secure=False,      # Keep False for HTTP (localhost) development
            samesite="Lax",    # 'Lax' is fine for dev now that CORS is handled
            path="/"           # <-- Add this! Explicitly set the path to the root
        )
    else:
        logger.info(f"Not setting cookie - conversation_id unchanged or missing")

    return qr

    return qr