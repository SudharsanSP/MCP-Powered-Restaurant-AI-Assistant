from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    aws_region: str
    aws_access_key: str
    aws_secret_key: str
    s3_bucket: str
    project_arn: str
    profile_arn: str
    input_s3_uri: str
    output_s3_uri: str
    blueprint_name: str
    
    model_id: str
    max_token: int
    temperature: int
    db_port: str
    db_host: str
    db_name: str
    db_username: str
    db_password: str
    memory_db_name: str
    port: int
    host: str
    log_level: str
    mcp_url:str

def get_config():
    return Config(
        aws_region=os.getenv('AWS_REGION'),
        aws_access_key=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        s3_bucket=os.getenv('S3_BUCKET'),
        project_arn=os.getenv('PROJECT_ARN'),
        profile_arn=os.getenv('PROFILE_ARN'),
        input_s3_uri=os.getenv('INPUT_S3_URI'),
        output_s3_uri=os.getenv('OUTPUT_S3_URI'),
        blueprint_name=os.getenv('BLUEPRINT_NAME'),
        model_id=os.getenv('MODEL_ARN'),
        temperature=float(os.getenv('TEMPERATURE', '0.1')),
        max_token=int(os.getenv('MAX_TOKEN', '500')),
        db_port=os.getenv('DB_PORT', '5432'),
        db_host=os.getenv('DB_HOST', 'localhost'),
        db_name=os.getenv('DB_NAME'),
        db_username=os.getenv('DB_USERNAME', 'postgres'),
        db_password=os.getenv('DB_PASSWORD'),
        memory_db_name = os.getenv('MEMORY_DB_NAME'),
        port=int(os.getenv('PORT', '8080')),
        host=os.getenv('HOST', '0.0.0.0'),
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
        mcp_url=os.getenv('MCP_SERVER_URL')
    )
config= get_config()
