"""
Entities for systems.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import List, Union

class GenerationModelName(str, Enum):
    """Model names for text generation"""
    # API models
    GEMINI_2_FLASH = "gemini-2.0-flash"

    # Huggingface models
    LLAMA_3_1_8B = "meta-llama/Llama-3.1-8B-Instruct"
    GPT_2 = "openai-community/gpt2"

class QueryRewritingModel(str, Enum):
    """Model names for query rewriting"""
    # API models
    GEMINI_2_FLASH = "gemini-2.0-flash"

class SpeechToTextModel(str, Enum):
    PHO_WHISPER = "vinai/PhoWhisper-medium"

class IntentClassificationModel(str, Enum):
    # Huggingface models
    BERT_BASE_FINETUNED = "/home/yosakoi/Work/chatbot/models/LLM/intent_classification"

class EmbeddingModelName(str, Enum):
    TEXT_EMBEDDING_004 = "models/text-embedding-004"
    VIETNAMSE_EMBEDDING = "dangvantuan/vietnamese-embedding"

class QueryInput(BaseModel):
    question: str
    session_id: str = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now())

class QueryResponse(BaseModel):
    response: Union[str, List[str]]
    session_id: str
    query: str
    conversation_id:str
    type: str

class Document(BaseModel):
    id: int
    file_name: str
    upload_timestamp: datetime

class DeleteFileRequest(BaseModel):
    file_id: int