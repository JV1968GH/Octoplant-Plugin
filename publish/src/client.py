"""Read-only OctoPlant/versiondog navigation and checkout client."""

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from src.navigation import ServerArchiveNavigator


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_VDOGCHECKOUT_DEFAULT = (
    _PROJECT_ROOT / "binaryTools" / "VDogCheckOut" / "publish" / "VDogCheckOut.exe"
)
_VDOGCHECKIN_DEFAULT = (
    _PROJECT_ROOT / "binaryTools" / "VDogCheckIn" / "publish" / "VDogCheckIn.exe"
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
    """Client for OctoPlant/versiondog navigation and controlled lifecycle operations."""

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
        self._vdogcheckin_exe = str(
            self._resolve_existing_file(str(_VDOGCHECKIN_DEFAULT), _PROJECT_ROOT)
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
    def _resolve_workspace_path(workspace_path: Optional[str]) -> Optional[Path]:
        """Resolve the initial prompt workspace supplied by the agent handoff."""
        if workspace_path is None:
            return None
        if not isinstance(workspace_path, str):
            raise OctoplantConfigError(
                "workspace_path must reference an absolute workspace directory."
            )
        if not workspace_path.strip():
            return None

        path = Path(os.path.expandvars(workspace_path.strip())).expanduser()
        if not path.is_absolute():
            raise OctoplantConfigError(
                "workspace_path must reference an absolute workspace directory."
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
        workspace_path: Optional[str],
        installation_name: Optional[str],
        cost_center: Optional[str],
    ) -> Optional[Path]:
        """Place checkouts below the initial prompt workspace, never a child session."""
        workspace = cls._resolve_workspace_path(workspace_path)
        if workspace is None:
            return None
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
        workspace_path: Optional[str] = None,
        installation_name: Optional[str] = None,
        cost_center: Optional[str] = None,
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
        if (
            not component_path.startswith(("\\", "/"))
            or not component_parts
            or any(part in {".", ".."} for part in component_parts)
        ):
            raise OctoplantConfigError(
                "component_path must be a relative Octoplant component path."
            )
        args: list[str] = [self._vdogcheckout_exe, "checkout", "--json", component_path]

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

        response: dict[str, Any] = {
            "returncode": result.returncode,
            "status": _CHECKOUT_RETURN_CODES.get(
                result.returncode, f"Onbekende code ({result.returncode})"
            ),
            "stdout": "",
            "stderr": "",
            "binary_output_suppressed": True,
        }
        if result.returncode == 0:
            try:
                native_result = json.loads(result.stdout)
                checkout_path = native_result["checkout_path"]
            except (json.JSONDecodeError, KeyError, TypeError) as exception:
                raise RuntimeError(
                    "VDogCheckOut.exe returned no valid checkout result."
                ) from exception
            response["status"] = native_result.get("status", response["status"])
            response["checkout_path"] = checkout_path
            component_source = Path(checkout_path).joinpath(*component_parts)
            if checkout_root is None:
                response["artifact_path"] = str(component_source)
            else:
                artifact_path = checkout_root.joinpath(*component_parts)
                mirror_result = await asyncio.to_thread(
                    subprocess.run,
                    ["robocopy", str(component_source), str(artifact_path), "/MIR", "/R:1", "/W:1", "/NFL", "/NDL", "/NP"],
                    capture_output=True, text=True, cwd=self.runtime_path,
                )
                if mirror_result.returncode > 7:
                    response["status"] = "Checkout geslaagd, maar artifactmirror mislukt"
                    response["mirror_returncode"] = mirror_result.returncode
                else:
                    response["artifact_path"] = str(artifact_path)
        elif result.returncode == 2:
            response["status"] = "not_found"
        return response

    async def checkin_unchanged_component(self, component_path: str, confirmed: bool) -> dict[str, Any]:
        if confirmed is not True:
            raise OctoplantConfigError("Explicit confirmation is required before releasing a checkout.")
        component_parts = tuple(part for part in component_path.replace("/", "\\").split("\\") if part)
        if not component_path.startswith(("\\", "/")) or not component_parts or any(part in {".", ".."} for part in component_parts):
            raise OctoplantConfigError("component_path must be a relative Octoplant component path.")
        if not Path(self._vdogcheckin_exe).exists():
            raise OctoplantConfigError("VDogCheckIn.exe ontbreekt; installeer de plugin opnieuw.")
        result = await asyncio.to_thread(
            subprocess.run, [self._vdogcheckin_exe, "checkin", "--json", component_path],
            capture_output=True, text=True, cwd=self.runtime_path,
        )
        return {"returncode": result.returncode, "success": result.returncode == 0,
                "component_path": component_path, "binary_output_suppressed": True}

    async def checkout_copy_and_release_component(
        self, workspace_path: str, installation_name: Optional[str],
        cost_center: Optional[str], component_path: str, confirmed: bool,
        with_backups: bool = False, number_of_archives: int = 1,
        version: Optional[int] = None, with_std_libs: bool = False,
        comment: Optional[str] = None,
    ) -> dict[str, Any]:
        if confirmed is not True:
            raise OctoplantConfigError("Explicit confirmation is required before releasing a checkout.")
        if self._resolve_workspace_path(workspace_path) is None:
            raise OctoplantConfigError("workspace_path is required for checkout, copy, and release.")

        checkout = await self.checkout_component(
            workspace_path=workspace_path, installation_name=installation_name,
            cost_center=cost_center, component_path=component_path,
            with_backups=with_backups, number_of_archives=number_of_archives,
            version=version, with_std_libs=with_std_libs, comment=comment,
        )
        if checkout["returncode"] != 0 or "mirror_returncode" in checkout:
            return {
                "success": False, "component_path": component_path, "checkout": checkout,
                "release_executed": False, "binary_output_suppressed": True,
            }

        release = await self.checkin_unchanged_component(component_path, confirmed=True)
        return {
            "success": release["success"], "component_path": component_path,
            "checkout": checkout, "release": release, "release_executed": True,
            "binary_output_suppressed": True,
        }
