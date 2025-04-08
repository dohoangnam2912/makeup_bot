# So define the models here
# For chat bot, we have to define models for the following:
# 1. Message": So we just call it Input, in this context call it QueryInput
# So for message, we have to define the following:
# text: String
# id: String
# timestampt: Datetime
# user_id: String
# 2. Response
# So for response, we have to define the following:
# text: String
# id: String
# timestampt: Datetime
# 3. Model
# For model we may declare a class
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class GenerationModelName(str, Enum):
    GEMINI_2_FLASH = "gemini-2.0-flash"
    LLAMA_3_1_8B = "meta-llama/Llama-3.1-8B-Instruct"

class EmbeddingModelName(str, Enum):
    TEXT_EMBEDDING_004 = "models/text-embedding-004"
    VIETNAMSE_EMBEDDING = "dangvantuan/vietnamese-embedding"

class QueryInput(BaseModel):
    question: str
    session_id: str = Field(default=None)
    model: GenerationModelName = Field(default=GenerationModelName.GEMINI_2_FLASH)
    timestamp: datetime = Field(default_factory=datetime.now())

class QueryResponse(BaseModel):
    response: str
    session_id: str
    model: GenerationModelName

class Document(BaseModel):
    id: int
    file_name: str
    upload_timestamp: datetime
    # file_size: int
    # content_type: str

class DeleteFileRequest(BaseModel):
    file_id: int