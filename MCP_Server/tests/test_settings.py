"""
Tests for MCP_Server/src/settings.py
"""
import os
from unittest.mock import patch
import pytest

from settings import Config, get_config


class TestServerSettings:
    def test_config_dataclass_fields(self):
        conf = Config(
            db_port="5432",
            db_host="localhost",
            db_name="test_db",
            db_username="test_user",
            db_password="secret_password",
            port=8081,
            host="0.0.0.0",
            log_level="INFO",
        )
        assert conf.db_port == "5432"
        assert conf.db_host == "localhost"
        assert conf.db_name == "test_db"
        assert conf.db_username == "test_user"
        assert conf.db_password == "secret_password"
        assert conf.port == 8081
        assert conf.host == "0.0.0.0"
        assert conf.log_level == "INFO"

    def test_get_config_defaults(self):
        env = {
            "DB_PORT": "5432",
            "DB_HOST": "localhost",
            "DB_NAME": "test_coffee_shop",
            "DB_USERNAME": "postgres",
            "DB_PASSWORD": "password123",
            "MCP_PORT": "8081",
            "HOST": "0.0.0.0",
            "LOG_LEVEL": "DEBUG",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = get_config()
            assert cfg.db_port == "5432"
            assert cfg.db_host == "localhost"
            assert cfg.db_name == "test_coffee_shop"
            assert cfg.db_username == "postgres"
            assert cfg.db_password == "password123"
            assert cfg.port == 8081
            assert cfg.host == "0.0.0.0"
            assert cfg.log_level == "DEBUG"

    def test_get_config_custom_values(self):
        env = {
            "DB_PORT": "5433",
            "DB_HOST": "127.0.0.1",
            "DB_NAME": "custom_mcp_db",
            "DB_USERNAME": "admin",
            "DB_PASSWORD": "custom_pass",
            "MCP_PORT": "9090",
            "HOST": "127.0.0.1",
            "LOG_LEVEL": "WARNING",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = get_config()
            assert cfg.db_port == "5433"
            assert cfg.db_host == "127.0.0.1"
            assert cfg.db_name == "custom_mcp_db"
            assert cfg.db_username == "admin"
            assert cfg.db_password == "custom_pass"
            assert cfg.port == 9090
            assert cfg.host == "127.0.0.1"
            assert cfg.log_level == "WARNING"
