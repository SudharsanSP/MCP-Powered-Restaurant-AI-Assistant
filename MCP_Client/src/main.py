import sys
import asyncio
import uvicorn
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routers.router import router as agent_router
from routers.default_router import router as default_router
from routers.auth_router import router as auth_router
from routers.user_router import router as user_router
from models.APIresponse import APIResponse, Error
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from migration.migration import Migration
from settings import config
from services.dependency import lifespan_dependencies
from utilities.logger import get_logger
from middleware.auth import AuthMiddleware
from middleware.context import ContextMiddleware
from repositories.database import Database

logger = get_logger(__name__)

async def lifespan(app: FastAPI):
    logger.info("Starting application lifespan")
    try:
        async for dependencies in lifespan_dependencies():
            app.state.dependencies = dependencies
            logger.info("Application startup completed")
            yield
    finally:
        await Database().close()
        logger.info("Application shutdown completed")

# FASTAPI  INITIALIZATION
app = FastAPI(
    title="MCP-Powered Restaurant AI Assistant",
    description="Chatbot assistant",
    version="1.0.0",
    lifespan=lifespan
)

# MIDDLEWARE CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(AuthMiddleware)
app.add_middleware(ContextMiddleware)

app.include_router(default_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(agent_router)

# EXCEPTION HANDLERS 
@app.exception_handler(Custom_Exception)
async def custom_exception_handler(request: Request, exc: Custom_Exception):
    exc.request_id = request.state.request_id
    logger.error(
        "Application error while handling request",
        extra={
            "request_id": request.state.request_id,
            "exception": str(exc),
        },
    )
    api_response = exc.to_api_response()
    return JSONResponse(
        status_code=exc.status_code,
        content=api_response.to_dict()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        "Request validation failed",
        extra={"request_id": request_id},
    )
    errors = []
    for error in exc.errors():
        errors.append(Error(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"{error['loc'][-1]}: {error['msg']}"
        ))
    
    api_response = APIResponse(
        data=None,
        errors=errors,
        code=HttpStatusCode.UNPROCESSABLE_ENTITY,
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=HttpStatusCode.UNPROCESSABLE_ENTITY,
        content=api_response.to_dict()
    )

if __name__ == "__main__":
   
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        loop=asyncio.SelectorEventLoop if sys.platform == "win32" else "auto",
        reload=False,
        log_level= config.log_level.lower()
    )
