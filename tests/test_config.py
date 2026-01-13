"""Tests for configuration management."""


import pytest
from gitblit_mcp_server.config import ConfigurationError


def test_config_valid_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test configuration with valid GITBLIT_URL."""
    monkeypatch.setenv("GITBLIT_URL", "http://10.1.2.3:8080")

    # Force reload of config
    from gitblit_mcp_server import config

    config._config = None

    cfg = config.get_config()
    assert cfg.gitblit_url == "http://10.1.2.3:8080"
    assert cfg.api_base_url == "http://10.1.2.3:8080/api/mcp-server"


def test_config_trailing_slash_removed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that trailing slash is removed from GITBLIT_URL."""
    monkeypatch.setenv("GITBLIT_URL", "http://10.1.2.3:8080/")

    from gitblit_mcp_server import config

    config._config = None

    cfg = config.get_config()
    assert cfg.gitblit_url == "http://10.1.2.3:8080"
    assert not cfg.gitblit_url.endswith("/")


def test_config_missing_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test configuration with missing GITBLIT_URL."""
    monkeypatch.delenv("GITBLIT_URL", raising=False)

    from gitblit_mcp_server import config

    config._config = None

    # Patch load_dotenv to prevent it from loading .env file
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("gitblit_mcp_server.config.load_dotenv", lambda: None)
        with pytest.raises(ConfigurationError) as exc_info:
            config.get_config()

    assert "GITBLIT_URL" in str(exc_info.value)
    assert "required" in str(exc_info.value).lower()


def test_config_invalid_url_scheme(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test configuration with invalid URL scheme."""
    monkeypatch.setenv("GITBLIT_URL", "ftp://10.1.2.3:8080")

    from gitblit_mcp_server import config

    config._config = None

    with pytest.raises(ConfigurationError) as exc_info:
        config.get_config()

    assert "Invalid GITBLIT_URL" in str(exc_info.value)
    assert "http" in str(exc_info.value).lower()


def test_config_https_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test configuration with HTTPS URL."""
    monkeypatch.setenv("GITBLIT_URL", "https://gitblit.example.com")

    from gitblit_mcp_server import config

    config._config = None

    cfg = config.get_config()
    assert cfg.gitblit_url == "https://gitblit.example.com"
    assert cfg.api_base_url == "https://gitblit.example.com/api/mcp-server"


def test_config_mcp_path_prefix_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test default MCP path prefix is empty."""
    monkeypatch.setenv("GITBLIT_URL", "http://10.1.2.3:8080")
    monkeypatch.delenv("MCP_PATH_PREFIX", raising=False)

    from gitblit_mcp_server import config

    config._config = None

    cfg = config.get_config()
    assert cfg.mcp_path_prefix == ""


def test_config_mcp_path_prefix_custom(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test custom MCP path prefix from environment."""
    monkeypatch.setenv("GITBLIT_URL", "http://10.1.2.3:8080")
    monkeypatch.setenv("MCP_PATH_PREFIX", "/api/mcp")

    from gitblit_mcp_server import config

    config._config = None

    cfg = config.get_config()
    assert cfg.mcp_path_prefix == "/api/mcp"


def test_config_mcp_path_prefix_adds_leading_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that leading slash is added if missing."""
    monkeypatch.setenv("GITBLIT_URL", "http://10.1.2.3:8080")
    monkeypatch.setenv("MCP_PATH_PREFIX", "api/mcp")

    from gitblit_mcp_server import config

    config._config = None

    cfg = config.get_config()
    assert cfg.mcp_path_prefix == "/api/mcp"


def test_config_mcp_path_prefix_strips_trailing_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that trailing slash is stripped from prefix."""
    monkeypatch.setenv("GITBLIT_URL", "http://10.1.2.3:8080")
    monkeypatch.setenv("MCP_PATH_PREFIX", "/api/mcp/")

    from gitblit_mcp_server import config

    config._config = None

    cfg = config.get_config()
    assert cfg.mcp_path_prefix == "/api/mcp"
