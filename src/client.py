"""Read-only OctoPlant/versiondog navigation and checkout client."""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from src.navigation import ServerArchiveNavigator


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_VDOGCHECKOUT_DEFAULT = (
    _PROJECT_ROOT / "binaryTools" / "VDogCheckOut" / "publish" / "VDogCheckOut.exe"
)

_CHECKOUT_RETURN_CODES: dict[int, str] = {
    0: "OK -- ten minste een component uitgecheckt",
    1: "Fout -- geen check-out mogelijk of minimaal een mislukt",
    2: "Geen componenten gevonden (onvoldoende rechten?)",
    10: "Configuratiefout -- controleer de lokale Octoplant-pluginruntime",
    1000: "Login-fout -- controleer gebruikersnaam en wachtwoord",
}


class OctoplantConfigError(RuntimeError):
    """Raised when required local configuration is unavailable."""


class OctoplantClient:
    """Client for read-only shared-archive navigation and component checkout."""

    def __init__(self) -> None:
        self.workspace_path = Path.cwd().resolve()
        self.export_path = str(self.workspace_path / "octoPlantCheckouts")
        self._vdogcheckout_exe = str(
            self._resolve_existing_file(
                str(_VDOGCHECKOUT_DEFAULT),
                _PROJECT_ROOT,
            )
        )
        if not Path(self._vdogcheckout_exe).exists():
            raise OctoplantConfigError(
                f"VDogCheckOut.exe niet gevonden: {self._vdogcheckout_exe}\n"
                "Installeer de plugin opnieuw; de meegeleverde runtime-artifacts ontbreken."
            )

        self._navigator = ServerArchiveNavigator()

    def resolve_project(
        self,
        installation_name: Optional[str] = None,
        cost_center: Optional[str] = None,
        plc_name: Optional[str] = None,
    ) -> dict[str, str]:
        """Resolve a PLC project by reading the shared server archive."""
        return self._navigator.resolve(
            installation_name=installation_name,
            cost_center=cost_center,
            plc_name=plc_name,
        ).as_dict()

    @staticmethod
    def _resolve_existing_file(path_value: str, base_dir: Path) -> Path:
        candidate = Path(os.path.expandvars(path_value.strip())).expanduser()
        if not candidate.is_absolute():
            candidate = (base_dir / candidate).resolve()
        return candidate

    async def checkout_component(
        self,
        component_path: Optional[str] = None,
        component_id: Optional[str] = None,
        with_backups: bool = False,
        number_of_archives: int = 1,
        version: Optional[int] = None,
        with_std_libs: bool = False,
        comment: Optional[str] = None,
    ) -> dict[str, Any]:
        """Check out a component or folder through the native versiondog CLI."""
        args: list[str] = [
            self._vdogcheckout_exe,
            "checkout",
        ]

        if component_id:
            args += ["--id", component_id]
        elif component_path is not None:
            args.append(component_path)
        else:
            args.append("--all")

        if with_backups:
            args.append("--backups")
        args += ["--archives", str(number_of_archives)]
        if with_std_libs:
            args.append("--std-libs")
        if version is not None:
            args += ["--version", str(version)]
        if comment:
            args += ["--comment", comment]

        result = await asyncio.to_thread(
            subprocess.run,
            args,
            capture_output=True,
            text=True,
            cwd=self.workspace_path,
        )

        return {
            "returncode": result.returncode,
            "status": _CHECKOUT_RETURN_CODES.get(
                result.returncode, f"Onbekende code ({result.returncode})"
            ),
            "checkout_path": self.export_path,
            "stdout": "",
            "stderr": "",
            "binary_output_suppressed": True,
        }
