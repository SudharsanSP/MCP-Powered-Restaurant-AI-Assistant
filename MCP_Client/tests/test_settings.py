"""
Tests for MCP_Client/src/settings.py
"""
import os
from unittest.mock import patch
import pytest

from settings import Config, get_config


class TestClientSettings:
    def test_config_dataclass(self):
        cfg = Config(
            google_api_key="key123",
            gemini_model="gemini-2.5-flash",
            max_token=500,
            temperature=0.1,
            db_port="5432",
            db_host="localhost",
            db_name="db",
            db_username="postgres",
            db_password="pwd",
            port=8080,
            host="0.0.0.0",
            log_level="INFO",
            mcp_url="http://localhost:8081",
            jwt_secret="secret",
            jwt_algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
            allowed_origins=["http://localhost:3000"],
        )
        assert cfg.google_api_key == "key123"
        assert cfg.max_token == 500
        assert cfg.temperature == 0.1
        assert cfg.allowed_origins == ["http://localhost:3000"]

    def test_get_config_with_defaults(self):
        env = {
            "GOOGLE_API_KEY": "dummy_key",
            "DB_NAME": "test_db",
            "DB_PASSWORD": "secret_password",
            "MCP_SERVER_URL": "http://localhost:8081",
            "JWT_SECRET": "test_jwt_secret",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = get_config()
            assert cfg.google_api_key == "dummy_key"
            assert cfg.gemini_model == "gemini-2.5-flash"
            assert cfg.temperature == 0.1
            assert cfg.max_token == 500
            assert cfg.db_port == "5432"
            assert cfg.db_host == "localhost"
            assert cfg.port == 8080
            assert cfg.access_token_expire_minutes == 30
            assert cfg.refresh_token_expire_days == 7

    def test_get_config_with_custom_values(self):
        env = {
            "GOOGLE_API_KEY": "custom_key",
            "GEMINI_MODEL": "gemini-1.5-pro",
            "TEMPERATURE": "0.5",
            "MAX_TOKEN": "1000",
            "DB_PORT": "5433",
            "DB_HOST": "192.168.1.1",
            "DB_NAME": "custom_db",
            "DB_USERNAME": "custom_user",
            "DB_PASSWORD": "custom_password",
            "PORT": "9000",
            "HOST": "127.0.0.1",
            "LOG_LEVEL": "DEBUG",
            "MCP_SERVER_URL": "http://127.0.0.1:8081",
            "JWT_SECRET": "custom_jwt_secret",
            "JWT_ALGORITHM": "RS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
            "REFRESH_TOKEN_EXPIRE_DAYS": "14",
            "ALLOWED_ORIGINS": "http://localhost:3000, http://example.com",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = get_config()
            assert cfg.google_api_key == "custom_key"
            assert cfg.gemini_model == "gemini-1.5-pro"
            assert cfg.temperature == 0.5
            assert cfg.max_token == 1000
            assert cfg.db_port == "5433"
            assert cfg.db_host == "192.168.1.1"
            assert cfg.port == 9000
            assert cfg.host == "127.0.0.1"
            assert cfg.log_level == "DEBUG"
            assert cfg.jwt_algorithm == "RS256"
            assert cfg.access_token_expire_minutes == 60
            assert cfg.refresh_token_expire_days == 14
            assert cfg.allowed_origins == ["http://localhost:3000", "http://example.com"]
