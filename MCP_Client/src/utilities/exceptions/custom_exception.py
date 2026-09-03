# dtos/custom_app_exception.py
from typing import List, Optional
from models.APIresponse import APIResponse, Error


class Custom_Exception(Exception):

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int,
        errors: Optional[List[Error]] = None,
        request_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.errors = errors or [
            Error(code=code, message=message)
        ]
        self.request_id = request_id

    def to_api_response(self) -> APIResponse:
        return APIResponse(
            data=None,           # No data on error
            errors=self.errors,
            code=self.status_code,
            request_id=self.request_id,
        )

    def __str__(self):
        first_err = self.errors[0]
        return f"[{self.request_id}] {first_err.message} (Code: {first_err.code}, HTTP: {self.status_code})"
