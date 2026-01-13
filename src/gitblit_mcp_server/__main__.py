"""Entry point for running Gitblit MCP Server as a Python module."""

import sys

from .config import ConfigurationError, get_config
from .server import get_server


def main() -> None:
    """Main entry point for the MCP server."""
    try:
        # Validate configuration on startup
        config = get_config()
        print("Gitblit MCP Server starting...", file=sys.stderr)
        print(f"Backend: {config.api_base_url}", file=sys.stderr)
        print(
            f"MCP server: http://{config.mcp_host}:{config.mcp_port}/sse",
            file=sys.stderr,
        )

        # Get the server instance and run with SSE transport (HTTP)
        server = get_server()
        server.run(transport="sse", host=config.mcp_host, port=config.mcp_port)

    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
