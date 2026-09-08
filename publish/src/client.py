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
        self.runtime_path = Path.cwd().resolve()
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
    def _resolve_workspace_path(workspace_path: str) -> Path:
        """Resolve the initial prompt workspace supplied by the agent handoff."""
        if not isinstance(workspace_path, str):
            raise OctoplantConfigError(
                "workspace_path must reference an existing absolute workspace directory."
            )

        path = Path(os.path.expandvars(workspace_path.strip())).expanduser()
        if not path.is_absolute() or not path.is_dir():
            raise OctoplantConfigError(
                "workspace_path must reference an existing absolute workspace directory."
            )

        workspace = path.resolve()
        if workspace == _PROJECT_ROOT:
            raise OctoplantConfigError(
                "workspace_path must reference the calling project workspace, not the plugin installation directory."
            )
        return workspace

    @staticmethod
    def _installation_directory_name(
        installation_name: Optional[str], cost_center: Optional[str]
    ) -> str:
        """Build a stable installation directory from explicit handoff metadata."""
        values = [
            value.strip()
            for value in (installation_name, cost_center)
            if isinstance(value, str) and value.strip()
        ]
        if not values:
            raise OctoplantConfigError(
                "installation_name or cost_center is required for the checkout destination."
            )
        if any(Path(value).name != value or value in {".", ".."} for value in values):
            raise OctoplantConfigError(
                "installation_name and cost_center must be single directory names."
            )
        return " - ".join(values)

    @classmethod
    def _resolve_checkout_root(
        cls,
        workspace_path: str,
        installation_name: Optional[str],
        cost_center: Optional[str],
    ) -> Path:
        """Place checkouts below the initial prompt workspace, never a child session."""
        workspace = cls._resolve_workspace_path(workspace_path)
        return (
            workspace
            / "PLC-projecten"
            / cls._installation_directory_name(installation_name, cost_center)
        )

    @staticmethod
    def _resolve_existing_file(path_value: str, base_dir: Path) -> Path:
        candidate = Path(os.path.expandvars(path_value.strip())).expanduser()
        if not candidate.is_absolute():
            candidate = (base_dir / candidate).resolve()
        return candidate

    async def checkout_component(
        self,
        workspace_path: str,
        installation_name: Optional[str],
        cost_center: Optional[str],
        component_path: Optional[str] = None,
        with_backups: bool = False,
        number_of_archives: int = 1,
        version: Optional[int] = None,
        with_std_libs: bool = False,
        comment: Optional[str] = None,
    ) -> dict[str, Any]:
        """Check out a component or folder through the native versiondog CLI."""
        checkout_root = self._resolve_checkout_root(
            workspace_path, installation_name, cost_center
        )
        if component_path is None:
            raise OctoplantConfigError(
                "component_path from resolve_project is required; broad checkout fallback is disabled."
            )
        component_parts = tuple(
            part for part in component_path.replace("/", "\\").split("\\") if part
        )
        if not component_parts or any(part in {".", ".."} for part in component_parts):
            raise OctoplantConfigError(
                "component_path must be a relative Octoplant component path."
            )
        artifact_path = checkout_root.joinpath(*component_parts)
        args: list[str] = [
            self._vdogcheckout_exe,
            "checkout",
            "--workspace",
            str(checkout_root),
        ]

        args.append(component_path)

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
            cwd=self.runtime_path,
        )

        response = {
            "returncode": result.returncode,
            "status": _CHECKOUT_RETURN_CODES.get(
                result.returncode, f"Onbekende code ({result.returncode})"
            ),
            "checkout_path": str(checkout_root),
            "artifact_path": str(artifact_path),
            "stdout": "",
            "stderr": "",
            "binary_output_suppressed": True,
        }
        if result.returncode == 2:
            response["status"] = "not_found"
        return response
