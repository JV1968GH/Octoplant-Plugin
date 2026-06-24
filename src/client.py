"""OctoplantClient -- centrale client voor alle OctoPlant/versiondog API-aanroepen.

Verantwoordelijk voor:
- Bearer-token ophalen via VDogCheckOut.exe (credentials intern in de exe)
- REST API-aanroepen (Export API via httpx)
- CLI subprocess-aanroepen (VDogCheckOut.exe checkout, VDogAutoExport.exe)

SCOPE: uitsluitend lees- en exportbewerkingen. Geen check-in, geen maintenance mode.

Credentials zijn NOOIT zichtbaar in deze module. Ze worden intern beheerd door
VDogCheckOut.exe via een externe access-rights database.
"""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

import httpx


_PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Pad naar de VDogCheckOut.exe wrapper (credentials intern afgehandeld)
_VDOGCHECKOUT_DEFAULT = (
    _PROJECT_ROOT / "binaryTools" / "VDogCheckOut" / "publish" / "VDogCheckOut.exe"
)


_CHECKOUT_RETURN_CODES: dict[int, str] = {
    0: "OK -- ten minste een component uitgecheckt",
    1: "Fout -- geen check-out mogelijk of minimaal een mislukt",
    2: "Geen componenten gevonden (onvoldoende rechten?)",
    1000: "Login-fout -- controleer gebruikersnaam en wachtwoord",
}

_VDOG_CLIENT_CANDIDATES = (
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "vdogClient",
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "vdogClient",
    Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "vdogClient",
)


class OctoplantConfigError(RuntimeError):
    """Wordt gegooid wanneer verplichte configuratie ontbreekt."""


class OctoplantApiError(RuntimeError):
    """HTTP-fout van de OctoPlant API — gesanitiseerd, geen server-URL of body."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"OctoPlant API-fout (HTTP {status_code})")
        self.status_code = status_code


def _raise_sanitised(resp: httpx.Response) -> None:
    """Gooi OctoplantApiError als de response niet succesvol is.
    Vervangt raise_for_status() om te voorkomen dat server-URL of response-body
    in de exception-message lekt naar de LLM.
    """
    if not resp.is_success:
        raise OctoplantApiError(resp.status_code)





class OctoplantClient:
    """Client voor OctoPlant/versiondog -- alleen lezen en exporteren."""

    def __init__(self) -> None:
        missing = []
        for var in ("OCTOPLANT_SERVER", "OCTOPLANT_ARCHIVE_PATH"):
            if not os.environ.get(var):
                missing.append(var)
        if missing:
            raise OctoplantConfigError(
                f"Ontbrekende omgevingsvariabelen: {', '.join(missing)}. "
                "Controleer het .env bestand."
            )

        self.server: str = os.environ["OCTOPLANT_SERVER"].rstrip("/")
        self.archive_path: str = os.environ["OCTOPLANT_ARCHIVE_PATH"]
        self.vdog_client_path: str = ""
        self.ssl_verify: bool = (
            os.environ.get("OCTOPLANT_SSL_VERIFY", "true").lower() != "false"
        )
        self.export_path: str = os.environ.get("OCTOPLANT_EXPORT_PATH", "")

        _default_checkout = str(_PROJECT_ROOT / "octoPlantCheckouts")
        self.checkout_path: str = (
            os.environ.get("OCTOPLANT_CHECKOUT_PATH") or _default_checkout
        )

        # VDogCheckOut.exe: env override of auto-discover naast project
        _exe_override = os.environ.get("VDOGCHECKOUT_EXE", "")
        self._vdogcheckout_exe: str = str(
            self._resolve_existing_file(
                _exe_override if _exe_override else str(_VDOGCHECKOUT_DEFAULT),
                _PROJECT_ROOT,
            )
        )
        if not Path(self._vdogcheckout_exe).exists():
            raise OctoplantConfigError(
                f"VDogCheckOut.exe niet gevonden: {self._vdogcheckout_exe}\n"
                "Bouw het project of stel VDOGCHECKOUT_EXE in .env in."
            )

        self.vdog_client_path = str(
            self._resolve_vdog_client_path(os.environ.get("OCTOPLANT_VDOG_CLIENT_PATH", ""))
        )

        self._token: Optional[str] = None

    # ------------------------------------------------------------------
    # Authenticatie -- token via VDogCheckOut.exe
    # ------------------------------------------------------------------

    async def get_token(self) -> str:
        """Haal een Bearer-token op via VDogCheckOut.exe. Gecached tot invalidatie."""
        if self._token:
            return self._token

        result = await asyncio.to_thread(
            subprocess.run,
            [self._vdogcheckout_exe, "token"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 1000:
            raise OctoplantConfigError(
                "Authenticatie mislukt. "
                "Controleer de credentials en test met: VDogCheckOut.exe login"
            )
        if result.returncode != 0:
            raise OctoplantConfigError(
                "VDogCheckOut.exe token gaf een fout. "
                f"Returncode: {result.returncode}."
            )

        token = result.stdout.strip()
        if not token:
            raise OctoplantConfigError(
                "Geen token ontvangen van VDogCheckOut.exe. "
                "Controleer de server-verbinding."
            )

        self._token = token
        return self._token

    def invalidate_token(self) -> None:
        """Verwijder de gecachede token (bijv. na een 401-fout)."""
        self._token = None

    def _auth_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    @staticmethod
    def _resolve_existing_file(path_value: str, base_dir: Path) -> Path:
        candidate = Path(os.path.expandvars(path_value.strip())).expanduser()
        if not candidate.is_absolute():
            candidate = (base_dir / candidate).resolve()
        return candidate

    def _resolve_vdog_client_path(self, configured: str) -> Path:
        if configured.strip():
            candidate = Path(os.path.expandvars(configured.strip())).expanduser()
            if not candidate.is_absolute():
                candidate = (_PROJECT_ROOT / candidate).resolve()
            if (candidate / "VDogAutoExport.exe").exists():
                return candidate
            raise OctoplantConfigError(
                "VDogAutoExport.exe niet gevonden in OCTOPLANT_VDOG_CLIENT_PATH."
            )

        checkout_exe_dir = Path(self._vdogcheckout_exe).resolve().parent
        if (checkout_exe_dir / "VDogAutoExport.exe").exists():
            return checkout_exe_dir

        for candidate in _VDOG_CLIENT_CANDIDATES:
            if (candidate / "VDogAutoExport.exe").exists():
                return candidate

        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        for path_dir in path_dirs:
            if not path_dir:
                continue
            candidate = Path(path_dir).expanduser()
            if (candidate / "VDogAutoExport.exe").exists():
                return candidate

        raise OctoplantConfigError(
            "VDogAutoExport.exe niet gevonden via auto-discover. "
            "Stel OCTOPLANT_VDOG_CLIENT_PATH in .env in."
        )

    # ------------------------------------------------------------------
    # Check-Out (via VDogCheckOut.exe)
    # ------------------------------------------------------------------

    async def checkout_component(
        self,
        component_path: Optional[str] = None,
        component_id: Optional[str] = None,
        with_backups: bool = False,
        number_of_archives: int = 0,
        version: Optional[int] = None,
        with_std_libs: bool = False,
        comment: Optional[str] = None,
    ) -> dict[str, Any]:
        """Check een component of map uit via VDogCheckOut.exe.

        Credentials worden intern door de exe afgehandeld.
        Na een succesvolle checkout wordt het archief gespiegeld naar
        OCTOPLANT_CHECKOUT_PATH via robocopy /MIR.

        Args:
            component_path:     Relatief pad van het component.
                                Laat None voor alle componenten.
            component_id:       Component-ID als alternatief voor component_path.
            with_backups:       Ook backups uitchecken.
            number_of_archives: Aantal te checken archives (0 = alle).
            version:            Specifiek versienummer (standaard = huidig).
            with_std_libs:      Gekoppelde standaardbibliotheken meechecken.
            comment:            Opmerking zichtbaar in het CheckIn-CheckOut-Log.

        Returns:
            Dict met returncode, status, checkout_path, stdout en stderr.
        """
        args: list[str] = [self._vdogcheckout_exe, "checkout"]

        if component_id:
            args += ["--id", component_id]
        elif component_path is not None:
            args.append(component_path)
        else:
            args.append("--all")

        if with_backups:
            args.append("--backups")
        if number_of_archives:
            args += ["--archives", str(number_of_archives)]
        if with_std_libs:
            args.append("--std-libs")
        if version is not None:
            args += ["--version", str(version)]
        if comment:
            args += ["--comment", comment]

        result = await asyncio.to_thread(
            subprocess.run, args, capture_output=True, text=True
        )

        return {
            "returncode": result.returncode,
            "status": _CHECKOUT_RETURN_CODES.get(
                result.returncode, f"Onbekende code ({result.returncode})"
            ),
            "checkout_path": self.checkout_path,
            "stdout": "",
            "stderr": "",
            "binary_output_suppressed": True,
        }

    # ------------------------------------------------------------------
    # Export REST API
    # ------------------------------------------------------------------

    async def start_export(self, export_contents: dict[str, Any]) -> dict[str, Any]:
        """Dien een export-order in via POST /v1/order."""
        token = await self.get_token()
        async with httpx.AsyncClient(verify=self.ssl_verify) as http:
            resp = await http.post(
                f"{self.server}/v1/order",
                json={"exportContents": export_contents},
                headers=self._auth_headers(token),
            )
            if resp.status_code == 401:
                self.invalidate_token()
            _raise_sanitised(resp)
            return resp.json()

    async def get_export_status(self, order_name: str) -> dict[str, Any]:
        """Vraag de status van een export-order op via GET /v1/order/{name}."""
        token = await self.get_token()
        async with httpx.AsyncClient(verify=self.ssl_verify) as http:
            resp = await http.get(
                f"{self.server}/v1/order/{order_name}",
                headers=self._auth_headers(token),
            )
            if resp.status_code == 401:
                self.invalidate_token()
            _raise_sanitised(resp)
            return resp.json()

    async def download_export(self, order_name: str, output_path: str) -> str:
        """Download een afgeronde export als ZIP via GET /v1/order/{name}/download."""
        token = await self.get_token()
        async with httpx.AsyncClient(verify=self.ssl_verify, timeout=120.0) as http:
            resp = await http.get(
                f"{self.server}/v1/order/{order_name}/download",
                headers={
                    **self._auth_headers(token),
                    "Accept": "application/octet-stream",
                },
            )
            if resp.status_code == 401:
                self.invalidate_token()
            _raise_sanitised(resp)

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.content)

        return os.path.abspath(output_path)

    async def cancel_export(self, order_name: str) -> dict[str, Any]:
        """Annuleer een lopende export-order via POST /v1/order/{name}/cancel."""
        token = await self.get_token()
        async with httpx.AsyncClient(verify=self.ssl_verify) as http:
            resp = await http.post(
                f"{self.server}/v1/order/{order_name}/cancel",
                headers=self._auth_headers(token),
            )
            if resp.status_code == 401:
                self.invalidate_token()
            _raise_sanitised(resp)
            return resp.json()

    # ------------------------------------------------------------------
    # Export via CLI (VDogAutoExport.exe)
    # ------------------------------------------------------------------

    async def export_via_cli(
        self,
        ini_file_path: str,
    ) -> dict[str, Any]:
        """Voer een export uit via VDogAutoExport.exe met een INI-parameterbestand.

        Het Bearer-token wordt via VDogCheckOut.exe opgehaald en doorgegeven
        aan VDogAutoExport.exe via /token:. Credentials zijn niet zichtbaar.
        """
        exe = os.path.join(self.vdog_client_path, "VDogAutoExport.exe")
        token = await self.get_token()

        args: list[str] = [
            exe,
            f"/rd:{self.archive_path}",
            f"/CFile:{ini_file_path}",
            f"/token:{token}",
        ]

        result = await asyncio.to_thread(subprocess.run, args, capture_output=True, text=True)

        return {
            "returncode": result.returncode,
            "success": result.returncode == 0,
            "stdout": "",
            "stderr": "",
            "binary_output_suppressed": True,
        }