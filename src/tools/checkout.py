"""MCP-tools voor Check-Out van OctoPlant/versiondog componenten.

Registreer tools via register_checkout_tools(mcp, client).
Uitsluitend leesbewerkingen — check-in is expliciet uitgesloten.
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from src.client import OctoplantClient


def register_checkout_tools(mcp: FastMCP, client: OctoplantClient) -> None:
    """Registreer alle checkout-gerelateerde MCP-tools op de gegeven FastMCP instantie."""

    @mcp.tool()
    async def checkout_component(
        component_path: Optional[str] = None,
        component_id: Optional[str] = None,
        with_backups: bool = False,
        number_of_archives: int = 0,
        version: Optional[int] = None,
        with_std_libs: bool = False,
        comment: Optional[str] = None,
    ) -> dict:
        """Check een component of project uit vanuit OctoPlant/versiondog.

        Geef component_path (relatief pad) OF component_id op.
        Als geen van beide opgegeven is, worden alle toegankelijke componenten uitgecheckt.
        Bestanden worden geplaatst in de octoPlantCheckouts-map van de workspace
        (configureerbaar via OCTOPLANT_CHECKOUT_PATH in .env).

        Args:
            component_path:     Relatief pad binnen de archive met verplichte leading backslash,
                                bijv. "\\RWZI's\\100026 - Dendermonde\\100026 - Dendermonde, PLC08_CE".
                                Laat leeg (None) om alle componenten te checken.
            component_id:       Component-ID als alternatief voor component_path.
            with_backups:       True = backups ook uitchecken (standaard False).
            number_of_archives: Aantal te checken archives; 0 = alle (standaard 0).
            version:            Versienummer om te checken; standaard = huidige versie.
            with_std_libs:      True = gekoppelde standaardbibliotheken meechecken.
            comment:            Opmerking in het CheckIn-CheckOut-Log.

        Returns:
            Dict met returncode (0=OK, 1=fout, 2=niet gevonden, 1000=login-fout),
            status-omschrijving, checkout_path en een indicatie dat binaire output
            onderdrukt werd.
        """
        return await client.checkout_component(
            component_path=component_path,
            component_id=component_id,
            with_backups=with_backups,
            number_of_archives=number_of_archives,
            version=version,
            with_std_libs=with_std_libs,
            comment=comment,
        )

    @mcp.tool()
    async def checkout_all(
        with_backups: bool = False,
        number_of_archives: int = 0,
        with_std_libs: bool = False,
    ) -> dict:
        """Check alle toegankelijke componenten uit vanuit OctoPlant/versiondog.

        Handige kortweg voor checkout_component zonder padspecificatie.
        Bestanden worden geplaatst in de octoPlantCheckouts-map van de workspace
        (configureerbaar via OCTOPLANT_CHECKOUT_PATH in .env).

        Args:
            with_backups:       True = backups ook uitchecken.
            number_of_archives: Aantal te checken archives; 0 = alle.
            with_std_libs:      True = standaardbibliotheken meechecken.

        Returns:
            Dict met returncode, status-omschrijving, checkout_path en een indicatie
            dat binaire output onderdrukt werd.
        """
        return await client.checkout_component(
            component_path=None,  # lege /dirR: = alle componenten
            with_backups=with_backups,
            number_of_archives=number_of_archives,
            with_std_libs=with_std_libs,
        )
