# dtos/custom_app_exception.py
import uuid
from typing import List, Optional
from models.APIresponse import APIResponse, Error

"""
Custom application exception designed to standardize error handling across the API layer.

This exception supports both single and multiple structured errors via the `Error` model,
and can generate a consistent `APIResponse` object for HTTP responses. Each instance
includes a unique request ID for tracing, standardized error codes, and proper HTTP status mapping.

It is used throughout the application to:
- Centralize error formatting
- Support rich error payloads (e.g., validation errors)
- Generate traceable logs via `request_id`
- Seamlessly convert exceptions into API responses using `to_api_response()`

Example:
    raise CustomAppException(
        message="User not found",
        code="USER_NOT_FOUND",
        status_code=404,
        error_code_id="USR_001"
    )

Or from multiple errors:
    CustomAppException.from_errors([error1, error2], 400)
"""
class Custom_Exception(Exception):
    """
    Custom application exception supporting multiple structured errors.
    Produces a standardized API response.
    """
    def __init__(
        self,
        message: str,
        code: str,
        status_code: int,
        errors: Optional[List[Error]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.errors = errors or [
            Error(code=code, message=message)
        ]
        self.request_id = str(uuid.uuid4())

    def to_api_response(self) -> APIResponse:
        return APIResponse(
            data=None,           # No data on error
            errors=self.errors,
            code=self.status_code
        )

    def __str__(self):
        first_err = self.errors[0]
        return f"[{self.request_id}] {first_err.message} (Code: {first_err.code}, HTTP: {self.status_code})"

    @classmethod
    def from_errors(cls, errors: List[Error], status_code: int):
        """
        Create exception from multiple errors.
        Uses the first error for top-level message/code/error_code_id.
        """
        if not errors:
            return cls(
                message="Unknown error occurred",
                code="UNKNOWN_ERROR",
                status_code=status_code
            )

        first_error = errors[0]
        return cls(
            message=first_error.message,
            code=first_error.code,
            status_code=status_code,
            errors=errors
        )   