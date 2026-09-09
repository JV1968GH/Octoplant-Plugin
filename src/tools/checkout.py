"""MCP-tools voor Check-Out van OctoPlant/versiondog componenten.

Registreer tools via register_checkout_tools(mcp, client).
Uitsluitend leesbewerkingen — check-in is expliciet uitgesloten.
"""

from typing import Literal, Optional

from mcp.server.fastmcp import FastMCP

from src.client import OctoplantClient


def register_checkout_tools(mcp: FastMCP, client: OctoplantClient) -> None:
    """Registreer alle checkout-gerelateerde MCP-tools op de gegeven FastMCP instantie."""

    @mcp.tool()
    async def inspect_checkout_destination(
        workspace_path: Optional[str] = None,
        installation_name: Optional[str] = None,
        cost_center: Optional[str] = None,
        component_path: Optional[str] = None,
    ) -> dict:
        """Inspecteer de exacte lokale checkoutmap zonder bestanden te wijzigen.

        Roep deze tool direct na resolve_project aan. Bij status
        existing_checkout_detected moet de gebruiker kiezen uit replace, reuse
        of stop voordat checkout_component wordt aangeroepen.
        """
        return client.inspect_checkout_destination(
            workspace_path=workspace_path,
            installation_name=installation_name,
            cost_center=cost_center,
            component_path=component_path,
        )

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
        collision_action: Optional[Literal["replace", "reuse", "stop"]] = None,
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
            collision_action:   Alleen na een bestaande lokale checkout:
                                replace verwijdert uitsluitend het exacte
                                artifactpad en voert een verse checkout uit;
                                reuse retourneert de bestaande paden zonder
                                checkout; stop beëindigt de flow zonder wijziging.

        Returns:
            Dict met checkout_path en artifact_path. Statussen onderscheiden
            checked_out, existing_checkout_reused en
            existing_checkout_stopped; zonder selectie geeft een bestaande map
            existing_checkout_requires_choice terug.
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
            collision_action=collision_action,
        )
