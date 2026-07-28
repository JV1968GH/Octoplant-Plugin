"""Octoplant — MCP Server voor OctoPlant/versiondog.

Entry point: python server.py (stdio transport voor GitHub Copilot Desktop).

Laadt configuratie uit .env in dezelfde map.
SCOPE: uitsluitend navigatie en check-out — geen check-in, geen maintenance mode.
"""

import os
import pathlib
import sys

# Voeg projectmap toe aan Python-pad zodat 'src' importeerbaar is
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Laad .env uit dezelfde map als dit script
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from mcp.server.fastmcp import FastMCP

from src.client import OctoplantClient, OctoplantConfigError
from src.tools.checkout import register_checkout_tools
from src.tools.navigation import register_navigation_tools

# Bouw het server-icoon als file:-URI voor stdio-transport.
# FastMCP >= ~1.20 ondersteunt de icons-parameter; bij oudere versies wordt
# het genegeerd via de try/except hieronder.
_icons = None
try:
    from mcp.types import Icon as _Icon
    import inspect as _inspect

    if "icons" in _inspect.signature(FastMCP.__init__).parameters:
        _icon_file = pathlib.Path(__file__).parent.resolve() / "assets" / "Octoplant.png"
        if _icon_file.exists():
            _icons = [_Icon(src=_icon_file.as_uri(), mime_type="image/png")]
except Exception:
    pass

mcp = FastMCP(
    "MCP_OP",
    instructions=(
        "MCP server voor OctoPlant/versiondog. "
        "Biedt read-only toegang: navigatie en check-out van componenten. "
        "Check-in en maintenance mode zijn uitdrukkelijk NIET beschikbaar."
    ),
    **({"icons": _icons} if _icons is not None else {}),
)

try:
    client = OctoplantClient()
    register_checkout_tools(mcp, client)
    register_navigation_tools(mcp, client)

    @mcp.tool()
    async def authenticate() -> dict:
        """Test de verbinding en authenticatie met de OctoPlant server.

        Voert VDogCheckOut.exe login uit en retourneert uitsluitend de exit code.
        Gebruik dit om te controleren of de plugin correct geconfigureerd is
        voordat je checkout-tools aanroept.

        Returns:
            Dict met 'success' (bool) en 'returncode':
            - 0    = verbinding en authenticatie geslaagd
            - 1    = verbindingsfout
            - 10   = configuratiefout
            - 1000 = authenticatie mislukt
        """
        import asyncio
        import subprocess
        result = await asyncio.to_thread(
            subprocess.run,
            [
                client._vdogcheckout_exe,
                "--env",
                str(client._env_file),
                "login",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=client.workspace_path,
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
        }

except OctoplantConfigError:
    # Server start wel op maar tools geven een configuratiefout terug
    # zodat de MCP-client de server niet afwijst bij ontbrekende .env
    import sys

    print("[Octoplant] Waarschuwing: lokale configuratie is onvolledig.", file=sys.stderr)

    @mcp.tool()
    def configuratie_ontbreekt() -> str:
        """Geeft aan dat de .env configuratie ontbreekt of onvolledig is."""
        return (
            "Octoplant MCP is niet geconfigureerd.\n"
            "Maak een lokale .env-configuratie volgens .env.example."
        )


if __name__ == "__main__":
    mcp.run()
