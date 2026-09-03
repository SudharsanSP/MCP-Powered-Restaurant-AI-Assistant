# models/api_response_dto.py
import uuid
from typing import List, Optional

class Error:
    def __init__(self, code: str, message: str, error_code_id: Optional[str] = None):
        self.code = code
        self.message = message

    def to_dict(self):
        return {
            "code": self.code,
            "message": self.message,
        }

class APIResponse:
    def __init__(
        self,
        data=None,
        errors: Optional[List[Error]] = None,
        code: Optional[int] = None,
        message: Optional[str] = None
    ):
        self.data = data or []
        self.errors = errors or []
        self.code = code or 200
        self.request_id = str(uuid.uuid4())

        # Use provided message, or generate one
        if message is not None:
            self.message = message
        elif not self.errors:
            self.message = "Success"
        elif len(self.errors) == 1:
            self.message = self.errors[0].message
        else:
            self.message = "Something went wrong."

    def to_dict(self):
        return {
            "data": self.data if self.data is not None else None,
            "errors": [error.to_dict() for error in self.errors] if self.errors else [],
            "status_code": self.code,
            "request_id": self.request_id,
            "message": self.message 
        }