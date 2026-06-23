"""MCP-tools voor Export van OctoPlant/versiondog data.

Ondersteunt zowel de asynchrone REST Export API als de CLI (VDogAutoExport.exe).
Registreer tools via register_export_tools(mcp, client).
"""

import asyncio
import os
import tempfile
from typing import Optional

from mcp.server.fastmcp import FastMCP

from src.client import OctoplantClient

# Beschikbare exporttypen (uit OctoPlant documentatie)
AVAILABLE_EXPORT_TYPES = [
    "projectTree",
    "jobList",
    "jobResults",
    "usersAndGroups",
    "componentTypes",
    "componentLog",
    "eventLog",
    "adminLog",
    "linkedLibraries",
    "usageInfo",
]


def _resolve_output_path(client: OctoplantClient, order_name: str) -> str:
    """Bepaal het uitvoerpad voor een export-ZIP."""
    base_dir = client.export_path or tempfile.gettempdir()
    return os.path.join(base_dir, f"octoplant_export_{order_name}.zip")


def register_export_tools(mcp: FastMCP, client: OctoplantClient) -> None:
    """Registreer alle export-gerelateerde MCP-tools op de gegeven FastMCP instantie."""

    @mcp.tool()
    async def start_export(export_types: list[str]) -> dict:
        """Start een export-order op de OctoPlant server (asynchroon).

        Geeft onmiddellijk een order-naam terug die gebruikt wordt voor
        status-polling en downloaden. Gebruik get_export_status om de
        voortgang bij te houden en download_export zodra done=true.

        Args:
            export_types: Lijst van te exporteren datatypen. Kies uit:
                          projectTree, jobList, jobResults, usersAndGroups,
                          componentTypes, componentLog, eventLog, adminLog,
                          linkedLibraries, usageInfo.

        Returns:
            OrderState JSON met 'name' (order-ID) en initiële status.
        """
        invalid = [t for t in export_types if t not in AVAILABLE_EXPORT_TYPES]
        if invalid:
            return {
                "error": f"Onbekende exporttypen: {invalid}. "
                         f"Beschikbaar: {AVAILABLE_EXPORT_TYPES}"
            }
        export_contents = {t: {} for t in export_types}
        return await client.start_export(export_contents)

    @mcp.tool()
    async def get_export_status(order_name: str) -> dict:
        """Vraag de huidige status op van een export-order.

        Args:
            order_name: Order-ID ontvangen van start_export.

        Returns:
            OrderState JSON met velden:
            - done (bool): True als de export klaar is (geslaagd of mislukt).
            - metadata.state: STATE_PENDING | STATE_RUNNING | STATE_SUCCEEDED | STATE_FAILED.
            - error: Aanwezig bij STATE_FAILED.
        """
        return await client.get_export_status(order_name)

    @mcp.tool()
    async def download_export(
        order_name: str,
        output_path: Optional[str] = None,
    ) -> str:
        """Download een afgeronde export als ZIP-bestand.

        Controleer eerst via get_export_status of done=true en
        state=STATE_SUCCEEDED voordat je deze tool aanroept.

        Args:
            order_name:  Order-ID van de afgeronde export.
            output_path: Volledig doelpad voor het ZIP-bestand.
                         Laat leeg voor automatische naamgeving in OCTOPLANT_EXPORT_PATH
                         (of de systeem temp-map).

        Returns:
            Absoluut pad naar het opgeslagen ZIP-bestand.
        """
        if not output_path:
            output_path = _resolve_output_path(client, order_name)
        return await client.download_export(order_name, output_path)

    @mcp.tool()
    async def cancel_export(order_name: str) -> dict:
        """Annuleer een wachtende of lopende export-order.

        Args:
            order_name: Order-ID van de te annuleren export.

        Returns:
            JSON-bevestiging van de server.
        """
        return await client.cancel_export(order_name)

    @mcp.tool()
    async def run_export(
        export_types: list[str],
        output_path: Optional[str] = None,
        poll_interval_seconds: float = 2.0,
        timeout_seconds: float = 300.0,
    ) -> str:
        """Start een export, wacht op voltooiing en download het resultaat in één stap.

        Combineert start_export + polling via get_export_status + download_export.
        Gebruik deze tool als je het resultaat direct nodig hebt.

        Args:
            export_types:           Zie start_export voor beschikbare typen.
            output_path:            Doelpad voor het ZIP-bestand (optioneel).
            poll_interval_seconds:  Wachttijd tussen statuscontroles (standaard 2s).
            timeout_seconds:        Maximale wachttijd in seconden (standaard 300s).

        Returns:
            Absoluut pad naar het opgeslagen ZIP-bestand.

        Raises:
            ValueError:   Als ongeldige exporttypen worden opgegeven.
            RuntimeError: Als de export mislukt op de server.
            TimeoutError: Als de export niet klaar is binnen timeout_seconds.
        """
        invalid = [t for t in export_types if t not in AVAILABLE_EXPORT_TYPES]
        if invalid:
            raise ValueError(
                f"Onbekende exporttypen: {invalid}. Beschikbaar: {AVAILABLE_EXPORT_TYPES}"
            )

        order = await client.start_export({t: {} for t in export_types})
        order_name: str = order["name"]

        elapsed = 0.0
        while elapsed < timeout_seconds:
            await asyncio.sleep(poll_interval_seconds)
            elapsed += poll_interval_seconds
            status = await client.get_export_status(order_name)
            if status.get("done"):
                state = (status.get("metadata") or {}).get("state", "")
                if state == "STATE_SUCCEEDED":
                    break
                raise RuntimeError(
                    f"Export mislukt (state={state}). Details: {status.get('error')}"
                )
        else:
            raise TimeoutError(
                f"Export niet klaar na {timeout_seconds}s (order: {order_name}). "
                "Gebruik get_export_status om handmatig te controleren."
            )

        if not output_path:
            output_path = _resolve_output_path(client, order_name)
        return await client.download_export(order_name, output_path)

    @mcp.tool()
    async def export_via_cli(ini_file_path: str) -> dict:
        """Voer een export uit via VDogAutoExport.exe met een INI-parameterbestand.

        Gebruik dit als je bestaande INI-exportconfiguraties wil hergebruiken
        of complexe exports wil uitvoeren die niet ondersteund worden door de REST API.

        Args:
            ini_file_path: Volledig pad naar het INI-parameterbestand
                           (zie OctoPlant documentatie voor de opmaak).

        Returns:
            Dict met returncode (0=OK), success (bool) en een indicatie dat
            binaire output onderdrukt werd.
        """
        return await client.export_via_cli(ini_file_path)
