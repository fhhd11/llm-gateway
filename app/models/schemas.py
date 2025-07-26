from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: bool = False

class ChatCompletionResponse(BaseModel):
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str
    permission: List[Dict[str, Any]] = []
    root: Optional[str] = None
    parent: Optional[str] = None

class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[ModelInfo]

class ErrorResponse(BaseModel):
    detail: str
    code: int
    error_type: Optional[str] = None