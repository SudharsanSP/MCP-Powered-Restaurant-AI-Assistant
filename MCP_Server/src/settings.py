from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:

    db_port: str
    db_host: str
    db_name: str
    db_username: str
    db_password: str
    port: int
    host: str
    log_level: str
def get_config():
    return Config(
        db_port=os.getenv('DB_PORT', '5432'),
        db_host=os.getenv('DB_HOST', 'localhost'),
        db_name=os.getenv('DB_NAME'),
        db_username=os.getenv('DB_USERNAME', 'postgres'),
        db_password=os.getenv('DB_PASSWORD'),
        port=int(os.getenv('MCP_PORT', '8081')),
        host=os.getenv('HOST', '0.0.0.0'),
        log_level=os.getenv('LOG_LEVEL', 'INFO')
    )
config= get_config()
