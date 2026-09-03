from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from repositories.database import test_connection

router = APIRouter()


@router.get("/health/live")
async def liveness():
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness(request: Request):
    await test_connection()
    if not getattr(request.app.state, "dependencies", None):
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready"}