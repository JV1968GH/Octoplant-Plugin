"""Octoplant — MCP Server voor OctoPlant/versiondog.

Entry point: python server.py (stdio transport voor GitHub Copilot Desktop).

De wrapper leest configuratie veilig uit CredentialsManager.
SCOPE: navigatie, gerichte checkout en gecontroleerde checkoutvrijgave;
geen maintenance mode of andere mutaties.
"""

import os
import pathlib
import sys

# Voeg projectmap toe aan Python-pad zodat 'src' importeerbaar is
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    "MCP_Octoplant",
    instructions=(
        "MCP server voor OctoPlant/versiondog. "
        "Biedt navigatie, gerichte checkout en gecontroleerde checkoutvrijgave. "
        "De Octoplant Specialist verwerkt een zichtbare "
        "'⬇️✋ HANDOFF — OctoPlant' en sluit af met één "
        "'↩️ RESULTAAT — <terminal state>' bericht. "
        "Een check-in maakt nooit een versie en vereist expliciete bevestiging. "
        "Maintenance mode en andere mutaties zijn niet beschikbaar."
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
                "login",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=client.runtime_path,
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
        }

except OctoplantConfigError:
    # Server start wel op maar tools geven een configuratiefout terug
    # zodat de MCP-client de server niet afwijst bij een ontbrekende runtime.
    import sys

    print("[Octoplant] Waarschuwing: lokale configuratie is onvolledig.", file=sys.stderr)

    @mcp.tool()
    def configuratie_ontbreekt() -> str:
        """Geeft aan dat de Octoplant-runtime niet beschikbaar is."""
        return (
            "Octoplant MCP is niet geconfigureerd.\n"
            "Installeer de plugin-runtime opnieuw."
        )


if __name__ == "__main__":
    mcp.run()
