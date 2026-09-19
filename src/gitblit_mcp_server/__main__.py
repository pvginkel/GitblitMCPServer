"""Entry point for running Gitblit MCP Server as a Python module."""

import sys

import fastmcp  # type: ignore

from .config import ConfigurationError, get_config
from .server import get_server


def main() -> None:
    """Main entry point for the MCP server."""
    try:
        # Validate configuration on startup
        config = get_config()

        # Configure endpoint paths before starting server
        # Read defaults first, then prepend prefix
        fastmcp.settings.sse_path = config.mcp_path_prefix + fastmcp.settings.sse_path
        fastmcp.settings.message_path = config.mcp_path_prefix + fastmcp.settings.message_path
        fastmcp.settings.streamable_http_path = (
            config.mcp_path_prefix + fastmcp.settings.streamable_http_path
        )
        endpoint_path = (
            fastmcp.settings.sse_path
            if config.transport == "sse"
            else fastmcp.settings.streamable_http_path
        )

        print("Gitblit MCP Server starting...", file=sys.stderr)
        print(f"Backend: {config.api_base_url}", file=sys.stderr)
        print(
            f"MCP server: {config.transport} on "
            f"http://{config.mcp_host}:{config.mcp_port}{endpoint_path}",
            file=sys.stderr,
        )

        server = get_server()
        if config.transport == "sse":
            server.run(transport="sse", host=config.mcp_host, port=config.mcp_port)
        else:
            # Stateless: the tools keep no per-session state, so the server
            # keeps no sessions either. A restart cannot strand a client on a
            # session id it no longer knows, and sessions that clients abandon
            # without a DELETE never pile up in memory.
            server.run(
                transport="http",
                host=config.mcp_host,
                port=config.mcp_port,
                stateless_http=True,
            )

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
