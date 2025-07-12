from fastapi import HTTPException

class InsufficientFundsError(HTTPException):
    def __init__(self, detail: str = "Insufficient funds"):
        super().__init__(status_code=402, detail=detail)