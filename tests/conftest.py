"""Pytest configuration and fixtures for Gitblit MCP Server tests."""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from dotenv import load_dotenv
from gitblit_mcp_server import client as client_module
from gitblit_mcp_server import config as config_module
from gitblit_mcp_server import server as server_module
from gitblit_mcp_server.client import GitblitClient
from gitblit_mcp_server.config import Config


@pytest.fixture(scope="session", autouse=True)
def load_test_env() -> None:
    """Load test environment variables from .env.test file."""
    test_env_path = Path(__file__).parent / ".env.test"
    if test_env_path.exists():
        load_dotenv(test_env_path, override=True)


@pytest.fixture(autouse=True)
def reset_singletons() -> Generator[None, None, None]:
    """Reset all singletons before and after each test.

    This ensures tests that manipulate the singletons don't pollute other tests.
    """
    # Reset before test
    config_module._config = None
    client_module._shared_client = None
    server_module._mcp = None
    yield
    # Reset after test
    config_module._config = None
    client_module._shared_client = None
    server_module._mcp = None


@pytest.fixture(scope="session")
def test_config() -> Config:
    """Create test configuration instance."""
    return Config()


@pytest.fixture
def client() -> GitblitClient:
    """Create GitblitClient instance for testing."""
    return GitblitClient()


@pytest.fixture(scope="session")
def test_repo() -> str:
    """Return a known test repository name.

    This repository should exist on the test server for file/commit operations.
    Override this with an environment variable if needed.
    """
    return os.getenv("TEST_REPO", "test.git")
