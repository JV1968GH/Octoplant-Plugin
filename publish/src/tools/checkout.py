"""MCP-tools voor de gecontroleerde OctoPlant/versiondog checkoutlifecycle.

Registreer tools via register_checkout_tools(mcp, client).
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from src.client import OctoplantClient


def register_checkout_tools(mcp: FastMCP, client: OctoplantClient) -> None:
    """Registreer alle checkout-gerelateerde MCP-tools op de gegeven FastMCP instantie."""

    @mcp.tool()
    async def checkout_component(
        workspace_path: Optional[str] = None,
        installation_name: Optional[str] = None,
        cost_center: Optional[str] = None,
        component_path: Optional[str] = None,
        with_backups: bool = False,
        number_of_archives: int = 1,
        version: Optional[int] = None,
        with_std_libs: bool = False,
        comment: Optional[str] = None,
    ) -> dict:
        """Check een component of project uit vanuit OctoPlant/versiondog.

        Geef installatiegegevens uit de handoff en component_path uit
        resolve_project op. Een ontbrekend project geeft status not_found;
        er is geen checkout-all fallback.

        Args:
            workspace_path:     Optionele absolute directe checkout-root, die
                                indien nodig wordt aangemaakt. Zonder dit pad
                                wordt de lokale clientarchive gebruikt.
            installation_name:  Installatienaam uit de handoff.
            cost_center:        Kostenplaats uit de handoff.
            component_path:     Relatief pad binnen de archive met verplichte leading backslash,
                                bijv. "\\{hoofdmap}\\{installatiemap}\\{PLC-project}".
            with_backups:       True = backups ook uitchecken (standaard False).
            number_of_archives: Aantal te checken archives (0 = alle, standaard 1).
            version:            Versienummer om te checken; standaard = huidige versie.
            with_std_libs:      True = gekoppelde standaardbibliotheken meechecken.
            comment:            Opmerking in het CheckIn-CheckOut-Log.

        Returns:
            Dict met returncode, status (not_found bij code 2), checkout_path,
            artifact_path en een indicatie dat binaire output onderdrukt werd.
        """
        return await client.checkout_component(
            workspace_path=workspace_path,
            installation_name=installation_name,
            cost_center=cost_center,
            component_path=component_path,
            with_backups=with_backups,
            number_of_archives=number_of_archives,
            version=version,
            with_std_libs=with_std_libs,
            comment=comment,
        )

    @mcp.tool()
    async def checkin_unchanged_component(
        component_path: str,
    ) -> dict:
        """Geef precies een onveranderde lokale checkout vrij zonder nieuwe versie.

        Gebruik uitsluitend het component_path uit resolve_project. De tool maakt
        nooit een nieuwe versie en accepteert geen brede paden.
        """
        return await client.checkin_unchanged_component(component_path)

    @mcp.tool()
    async def checkout_copy_and_release_component(
        workspace_path: str,
        component_path: str,
        installation_name: Optional[str] = None,
        cost_center: Optional[str] = None,
        with_backups: bool = False,
        number_of_archives: int = 1,
        version: Optional[int] = None,
        with_std_libs: bool = False,
        comment: Optional[str] = None,
    ) -> dict:
        """Check out, mirror, and release one component as one lifecycle.

        Use component_path from resolve_project. The plugin releases the native
        checkout only after the checkout and artifact mirror have succeeded.
        """
        return await client.checkout_copy_and_release_component(
            workspace_path=workspace_path,
            installation_name=installation_name,
            cost_center=cost_center,
            component_path=component_path,
            with_backups=with_backups,
            number_of_archives=number_of_archives,
            version=version,
            with_std_libs=with_std_libs,
            comment=comment,
        )
