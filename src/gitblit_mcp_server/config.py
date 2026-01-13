"""Configuration management for Gitblit MCP Server."""

import os
from urllib.parse import urlparse

from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""

    pass


class Config:
    """Configuration for Gitblit MCP Server."""

    def __init__(self) -> None:
        """Initialize configuration from environment variables."""
        # Load .env file if present
        load_dotenv()

        # Read and validate GITBLIT_URL
        gitblit_url = os.getenv("GITBLIT_URL")
        if not gitblit_url:
            raise ConfigurationError(
                "GITBLIT_URL environment variable is required. "
                "Please set it in your environment or .env file."
            )

        # Validate URL format
        parsed = urlparse(gitblit_url)
        if parsed.scheme not in ("http", "https"):
            raise ConfigurationError(
                f"Invalid GITBLIT_URL format: must be http:// or https://, got {gitblit_url}"
            )

        # Store base URL without trailing slash
        self.gitblit_url = gitblit_url.rstrip("/")

        # MCP server port (default 8000)
        port_str = os.getenv("MCP_PORT", "8000")
        try:
            self.mcp_port = int(port_str)
        except ValueError as e:
            raise ConfigurationError(
                f"Invalid MCP_PORT: must be a number, got {port_str}"
            ) from e

        # MCP server host (default 0.0.0.0)
        self.mcp_host = os.getenv("MCP_HOST", "0.0.0.0")

    @property
    def api_base_url(self) -> str:
        """Return the base URL for API endpoints."""
        return f"{self.gitblit_url}/api/mcp-server"


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
