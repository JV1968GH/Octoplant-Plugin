"""Read-only OctoPlant/versiondog navigation and checkout client."""

import asyncio
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Literal, Optional

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
    def _component_parts(component_path: Optional[str]) -> tuple[str, ...]:
        """Validate and split one relative component path returned by resolution."""
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
            or any(
                part in {".", ".."}
                or ":" in part
                or Path(part).name != part
                for part in component_parts
            )
        ):
            raise OctoplantConfigError(
                "component_path must be a relative Octoplant component path."
            )
        return component_parts

    @staticmethod
    def _resolve_artifact_path(
        checkout_root: Path, component_parts: tuple[str, ...]
    ) -> Path:
        """Return the one local directory a targeted checkout may occupy."""
        return checkout_root.joinpath(*component_parts)

    @staticmethod
    def _path_exists(path: Path) -> bool:
        """Treat a broken link as an existing unsafe checkout collision."""
        return os.path.lexists(path)

    @classmethod
    def _checkout_destination(
        cls,
        workspace_path: Optional[str],
        installation_name: Optional[str],
        cost_center: Optional[str],
        component_path: Optional[str],
    ) -> tuple[Optional[Path], tuple[str, ...], Optional[Path]]:
        checkout_root = cls._resolve_checkout_root(
            workspace_path, installation_name, cost_center
        )
        component_parts = cls._component_parts(component_path)
        artifact_path = (
            cls._resolve_artifact_path(checkout_root, component_parts)
            if checkout_root is not None
            else None
        )
        return checkout_root, component_parts, artifact_path

    @staticmethod
    def _destination_response(
        status: str, checkout_root: Optional[Path], artifact_path: Optional[Path]
    ) -> dict[str, Any]:
        response: dict[str, Any] = {
            "status": status,
            "binary_output_suppressed": True,
        }
        if checkout_root is not None:
            response["checkout_path"] = str(checkout_root)
        if artifact_path is not None:
            response["artifact_path"] = str(artifact_path)
        return response

    def inspect_checkout_destination(
        self,
        workspace_path: Optional[str] = None,
        installation_name: Optional[str] = None,
        cost_center: Optional[str] = None,
        component_path: Optional[str] = None,
    ) -> dict[str, Any]:
        """Inspect the exact local target without creating or changing anything."""
        checkout_root, _, artifact_path = self._checkout_destination(
            workspace_path, installation_name, cost_center, component_path
        )
        if checkout_root is None or artifact_path is None:
            return self._destination_response(
                "checkout_destination_undetermined", checkout_root, artifact_path
            )
        if not self._path_exists(artifact_path):
            return self._destination_response(
                "checkout_destination_available", checkout_root, artifact_path
            )
        if artifact_path.is_symlink() or not artifact_path.is_dir():
            return self._destination_response(
                "checkout_destination_unsafe", checkout_root, artifact_path
            )
        response = self._destination_response(
            "existing_checkout_detected", checkout_root, artifact_path
        )
        response["available_actions"] = ["replace", "reuse", "stop"]
        return response

    @staticmethod
    def _remove_exact_artifact(checkout_root: Path, artifact_path: Path) -> None:
        """Remove only a verified, non-link artifact directory below its checkout root."""
        if (
            artifact_path == checkout_root
            or checkout_root.is_symlink()
            or artifact_path.is_symlink()
            or not artifact_path.is_dir()
        ):
            raise OctoplantConfigError(
                "The existing checkout target is not a safe directory to replace."
            )
        try:
            artifact_path.relative_to(checkout_root)
        except ValueError as exception:
            raise OctoplantConfigError(
                "The existing checkout target is outside the installation checkout root."
            ) from exception
        resolved_root = checkout_root.resolve()
        resolved_artifact = artifact_path.resolve()
        if resolved_artifact == resolved_root:
            raise OctoplantConfigError(
                "The existing checkout target resolves to the installation checkout root."
            )
        try:
            resolved_artifact.relative_to(resolved_root)
        except ValueError as exception:
            raise OctoplantConfigError(
                "The existing checkout target resolves outside the installation checkout root."
            ) from exception
        shutil.rmtree(resolved_artifact)

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
        collision_action: Optional[Literal["replace", "reuse", "stop"]] = None,
    ) -> dict[str, Any]:
        """Check out a component or folder through the native versiondog CLI."""
        checkout_root, component_parts, artifact_path = self._checkout_destination(
            workspace_path, installation_name, cost_center, component_path
        )
        if artifact_path is not None and self._path_exists(artifact_path):
            if artifact_path.is_symlink() or not artifact_path.is_dir():
                return self._destination_response(
                    "checkout_destination_unsafe", checkout_root, artifact_path
                )
            if collision_action is None:
                response = self._destination_response(
                    "existing_checkout_requires_choice", checkout_root, artifact_path
                )
                response["available_actions"] = ["replace", "reuse", "stop"]
                return response
            if collision_action == "reuse":
                response = self._destination_response(
                    "existing_checkout_reused", checkout_root, artifact_path
                )
                response["returncode"] = 0
                response["outcome"] = "reused_existing_checkout"
                return response
            if collision_action == "stop":
                response = self._destination_response(
                    "existing_checkout_stopped", checkout_root, artifact_path
                )
                response["returncode"] = None
                response["outcome"] = "stopped_existing_checkout"
                return response
            if collision_action == "replace":
                self._remove_exact_artifact(checkout_root, artifact_path)
            else:
                raise OctoplantConfigError(
                    "collision_action must be one of: replace, reuse, stop."
                )
        elif collision_action is not None:
            raise OctoplantConfigError(
                "collision_action is only valid after an existing checkout is detected."
            )
        args: list[str] = [
            self._vdogcheckout_exe,
            "checkout",
            "--json",
        ]
        if checkout_root is not None:
            args += ["--workspace", str(checkout_root)]
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

        response: dict[str, Any] = {
            "returncode": result.returncode,
            "status": _CHECKOUT_RETURN_CODES.get(result.returncode, f"Onbekende code ({result.returncode})"),
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
            response["status"] = "checked_out"
            response["native_status"] = native_result.get("status")
            response["outcome"] = "fresh_checkout"
            response["checkout_path"] = checkout_path
            response["artifact_path"] = str(
                Path(checkout_path).joinpath(*component_parts)
            )
            if collision_action == "replace":
                response["collision_action"] = "replace"
        elif result.returncode == 2:
            response["status"] = "not_found"
        return response
