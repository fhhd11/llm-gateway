from fastapi import HTTPException

class InsufficientFundsError(HTTPException):
    def __init__(self, detail: str = "Insufficient funds"):
        super().__init__(status_code=402, detail=detail)

class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail)

class AuthorizationError(HTTPException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=403, detail=detail)

class ValidationError(HTTPException):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=422, detail=detail)

class ServiceUnavailableError(HTTPException):
    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(status_code=503, detail=detail)

class LLMServiceError(HTTPException):
    def __init__(self, detail: str = "LLM service error"):
        super().__init__(status_code=503, detail=detail)