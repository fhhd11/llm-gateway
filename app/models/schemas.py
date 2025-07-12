from pydantic import BaseModel
from typing import List, Dict, Any

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