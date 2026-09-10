from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    google_api_key: str
    gemini_model: str
    max_token: int
    temperature: int
    db_port: str
    db_host: str
    db_name: str
    db_username: str
    db_password: str
    port: int
    host: str
    log_level: str
    mcp_url:str
    jwt_secret: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    allowed_origins: list[str]

def get_config():
    return Config(
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        gemini_model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
        temperature=float(os.getenv('TEMPERATURE', '0.1')),
        max_token=int(os.getenv('MAX_TOKEN', '500')),
        db_port=os.getenv('DB_PORT', '5432'),
        db_host=os.getenv('DB_HOST', 'localhost'),
        db_name=os.getenv('DB_NAME'),
        db_username=os.getenv('DB_USERNAME', 'postgres'),
        db_password=os.getenv('DB_PASSWORD'),
        port=int(os.getenv('PORT', '8080')),
        host=os.getenv('HOST', '0.0.0.0'),
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
        mcp_url=os.getenv('MCP_SERVER_URL'),
        jwt_secret=os.getenv('JWT_SECRET', ''),
        jwt_algorithm=os.getenv('JWT_ALGORITHM', 'HS256'),
        access_token_expire_minutes=int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30')),
        refresh_token_expire_days=int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7')),
        allowed_origins=[origin.strip() for origin in os.getenv('ALLOWED_ORIGINS', '').split(',') if origin.strip()],
    )
config= get_config()
