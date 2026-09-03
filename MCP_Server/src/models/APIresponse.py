# models/api_response_dto.py
import uuid
from typing import List, Optional

"""
Defines standardized data transfer objects (DTOs) for API responses and error handling.
Ensures consistent structure across all controller responses, including:
- Success payloads with data and metadata
- Structured error reporting
- Request tracing via unique request_id
- Interoperability with error mappers and middleware

Used throughout the application to format HTTP responses uniformly.
"""
class Error:
    def __init__(self, code: str, message: str, error_code_id: Optional[str] = None):
        self.code = code
        self.message = message

    def to_dict(self):
        return {
            "code": self.code,
            "message": self.message,
        }

"""
Encapsulates a standardized API response structure for both success and error scenarios.
Automatically generates appropriate messages based on content and supports request tracing.

Attributes:
    data: Payload data (typically a list or dict); defaults to empty list
    errors: List of Error objects; if present, indicates a failed response
    code: HTTP status code (e.g., 200, 400, 500); defaults to 200
    message: User-friendly summary; auto-generated if not provided
    request_id: Unique UUID to trace requests across logs and services

Generates consistent JSON output via `to_dict()` for use in HTTP responses.

Message Logic:
    - If custom message is given → use it
    - If no errors → "Success"
    - If one error → use that error’s message
    - If multiple errors → "Something went wrong."
"""

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