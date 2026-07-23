"""MCP-tools for shared-archive navigation and CLI export."""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from src.client import OctoplantClient


def register_export_tools(mcp: FastMCP, client: OctoplantClient) -> None:
    """Register project navigation and CLI export tools."""

    @mcp.tool()
    def resolve_project(
        installation_name: Optional[str] = None,
        cost_center: Optional[str] = None,
        plc_name: Optional[str] = None,
        root_name: Optional[str] = None,
    ) -> dict[str, str]:
        """Read the shared archive and resolve the current PLC project path.

        Call this at the beginning of every OctoPlant session, before CLI
        export or checkout. It scans the current tree, defaults to RWZI's,
        and resolves the best PLC project below ARCHIVE. Use component_path
        for checkout_component; archive_relative_path is the shared filesystem
        location used only when an INI explicitly needs an archive path.
        """
        return client.resolve_project(
            installation_name=installation_name,
            cost_center=cost_center,
            plc_name=plc_name,
            root_name=root_name,
        )

    @mcp.tool()
    async def export_via_cli(ini_file_path: str) -> dict:
        """Export through VDogAutoExport.exe using an existing INI file.

        First call resolve_project and use the returned path that matches the
        existing INI field's documented semantics.
        """
        return await client.export_via_cli(ini_file_path)
