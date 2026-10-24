"""
agent_router.py
---------------
FastAPI router for the autonomous manager agent.

Endpoints
---------
  POST /coffee_shop_bot/api/v1/agent
      Accept a natural language business request, run the autonomous agent,
      and return the task list + summary + generated .docx filename.
      Requires: Admin JWT.

  GET /coffee_shop_bot/api/v1/agent/documents/{filename}
      Download a previously generated .docx document.
      Requires: Admin JWT.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Body, Depends, Path as FPath, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse

from models.APIresponse import APIResponse
from models.model import AgentRequest
from services.autonomous_service import AutonomousAgentService
from services.dependency import get_autonomous_service
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/coffee_shop_bot/api/v1")

_DOCUMENTS_DIR = Path(__file__).resolve().parents[2] / "documents"

@router.post("/agent")
async def run_agent(
    http_request: Request,
    request: AgentRequest = Body(...),
    service: AutonomousAgentService = Depends(get_autonomous_service),
):

    try:
        logger.info("Agent endpoint: request received")
        result = await service.run(request)
        data = APIResponse(
            data=result.model_dump(),
            code=HttpStatusCode.OK,
            message="Agent completed successfully.",
            request_id=http_request.state.request_id,
        )
        return JSONResponse(
            content=jsonable_encoder(data.to_dict()),
            status_code=data.code,
        )
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Unhandled error in /agent endpoint")
        raise Custom_Exception(
            "The agent request could not be completed.",
            ErrorCode.INTERNAL_SERVER_ERROR,
            HttpStatusCode.INTERNAL_SERVER_ERROR,
        )


@router.get("/agent/documents/{filename}")
async def download_document(
    http_request: Request,
    filename: str = FPath(..., description="Name of the generated .docx file."),
    service: AutonomousAgentService = Depends(get_autonomous_service),
):
    """
    Download a generated Word document by filename.

    The filename is returned in the response of POST /agent.
    """
    try:
        logger.info("Document download requested: %s", filename)

        # Basic path-traversal guard
        if "/" in filename or "\\" in filename or ".." in filename:
            raise Custom_Exception(
                "Invalid document filename.",
                ErrorCode.VALIDATION_ERROR,
                HttpStatusCode.BAD_REQUEST,
            )
        if not filename.endswith(".docx"):
            raise Custom_Exception(
                "Only .docx documents can be downloaded.",
                ErrorCode.VALIDATION_ERROR,
                HttpStatusCode.BAD_REQUEST,
            )

        file_path = _DOCUMENTS_DIR / filename
        if not file_path.exists():
            raise Custom_Exception(
                f"Document '{filename}' was not found.",
                ErrorCode.DATA_NOT_FOUND,
                HttpStatusCode.NOT_FOUND,
            )

        return FileResponse(
            path=str(file_path),
            media_type=(
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            ),
            filename=filename,
        )
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Unhandled error in document download")
        raise Custom_Exception(
            "The document could not be downloaded.",
            ErrorCode.INTERNAL_SERVER_ERROR,
            HttpStatusCode.INTERNAL_SERVER_ERROR,
        )
