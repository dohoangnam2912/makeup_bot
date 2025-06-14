from fastapi import APIRouter
from controllers.chat_controller import handle_chat
from models.entities import QueryInput, QueryResponse

router = APIRouter()

@router.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):
    print(" QUERY INPUT ",query_input)
    return handle_chat(query_input)
 