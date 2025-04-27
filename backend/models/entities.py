"""
Entities for systems.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

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

class IntentClassificationModel(str, Enum):
    # Huggingface models
    BERT_BASE_FINETUNED = "/home/yosakoi/Work/chatbot/models/LLM/intent_classification"

class EmbeddingModelName(str, Enum):
    TEXT_EMBEDDING_004 = "models/text-embedding-004"
    VIETNAMSE_EMBEDDING = "dangvantuan/vietnamese-embedding"

class QueryInput(BaseModel):
    question: str
    session_id: str = Field(default=None)
    model: GenerationModelName = Field(default=GenerationModelName.GEMINI_2_FLASH)
    timestamp: datetime = Field(default_factory=lambda: datetime.now())

class QueryResponse(BaseModel):
    response: str
    session_id: str
    model: GenerationModelName
    rewritten_question: str

class Document(BaseModel):
    id: int
    file_name: str
    upload_timestamp: datetime

class DeleteFileRequest(BaseModel):
    file_id: int