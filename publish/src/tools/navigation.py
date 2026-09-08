"""MCP-tool for read-only shared-archive navigation."""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from src.client import OctoplantClient


def register_navigation_tools(mcp: FastMCP, client: OctoplantClient) -> None:
    """Register the project navigation tool."""

    @mcp.tool()
    def resolve_project(
        installation_name: Optional[str] = None,
        cost_center: Optional[str] = None,
        plc_name: Optional[str] = None,
    ) -> dict[str, str]:
        """Read the shared archive and resolve the current PLC project path.

        Call this at the beginning of every OctoPlant checkout session. It scans
        the current tree, defaults to RWZI's, and resolves the best PLC project
        below ARCHIVE. Use component_path for checkout_component;
        archive_relative_path is the shared filesystem location.
        """
        return client.resolve_project(
            installation_name=installation_name,
            cost_center=cost_center,
            plc_name=plc_name,
        )
