"""
Test utilities for LLM Gateway
"""
import json
from typing import Dict, Any, Optional
from fastapi.testclient import TestClient


def create_auth_headers(token: str) -> Dict[str, str]:
    """Create authorization headers with JWT token"""
    return {"Authorization": f"Bearer {token}"}


def make_chat_request(
    client: TestClient,
    messages: list,
    model: str = "gpt-4",
    stream: bool = False,
    token: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Make a chat completion request"""
    headers = {}
    if token:
        headers = create_auth_headers(token)
    
    data = {
        "model": model,
        "messages": messages,
        "stream": stream,
        **kwargs
    }
    
    response = client.post("/v1/chat/completions", json=data, headers=headers)
    return response.json() if response.status_code == 200 else {"error": response.text}


def make_models_request(
    client: TestClient,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """Make a models request"""
    headers = {}
    if token:
        headers = create_auth_headers(token)
    
    response = client.get("/v1/models", headers=headers)
    return response.json() if response.status_code == 200 else {"error": response.text}


def make_health_request(client: TestClient) -> Dict[str, Any]:
    """Make a health check request"""
    response = client.get("/health")
    return response.json() if response.status_code == 200 else {"error": response.text}


def make_metrics_request(client: TestClient) -> str:
    """Make a metrics request"""
    response = client.get("/metrics")
    return response.text if response.status_code == 200 else ""


def validate_chat_response(response: Dict[str, Any]) -> bool:
    """Validate chat completion response structure"""
    required_fields = ["id", "object", "created", "model", "choices", "usage"]
    
    for field in required_fields:
        if field not in response:
            return False
    
    if not isinstance(response["choices"], list) or len(response["choices"]) == 0:
        return False
    
    choice = response["choices"][0]
    if "message" not in choice or "content" not in choice["message"]:
        return False
    
    return True


def validate_models_response(response: Dict[str, Any]) -> bool:
    """Validate models response structure"""
    if "data" not in response:
        return False
    
    if not isinstance(response["data"], list):
        return False
    
    for model in response["data"]:
        if "id" not in model or "object" not in model:
            return False
    
    return True


def create_test_message(role: str = "user", content: str = "Hello") -> Dict[str, str]:
    """Create a test message"""
    return {"role": role, "content": content}


def create_test_conversation(messages: list) -> list:
    """Create a test conversation"""
    return [create_test_message("user", msg) if isinstance(msg, str) else msg for msg in messages] 