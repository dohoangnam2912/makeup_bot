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
    GPT4_O = "gpt-4o"
    GPT4_O_MINI = "gpt-4o-mini"
    GEMINI_2_FLASH = "gemini-2.0-flash"

class EmbeddingModelName(str, Enum):
    TEXT_EMBEDDING_004 = "models/text-embedding-004"

class QueryInput(BaseModel):
    question: str
    session_id: str = Field(default=None)
    model: GenerationModelName = Field(default=GenerationModelName.GEMINI_2_FLASH)
    timestampt: datetime = Field(default=datetime.now())

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