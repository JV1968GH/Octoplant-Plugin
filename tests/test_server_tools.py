"""Focused MCP registration tests that do not require Octoplant configuration."""

import asyncio
import importlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.client import OctoplantClient, OctoplantConfigError


class ServerInitializationTests(unittest.TestCase):
    def tearDown(self) -> None:
        sys.modules.pop("server", None)

    def _load_server(self, client_constructor):
        sys.modules.pop("server", None)
        with patch("src.client.OctoplantClient", client_constructor):
            return importlib.import_module("server")

    def test_registers_operational_tools_when_runtime_is_available(self) -> None:
        server = self._load_server(type("Client", (), {}))

        tool_names = {tool.name for tool in asyncio.run(server.mcp.list_tools())}

        self.assertSetEqual(
            tool_names,
            {"authenticate", "checkout_all", "checkout_component", "resolve_project"},
        )

    def test_starts_with_configuration_tool_when_runtime_is_missing(self) -> None:
        server = self._load_server(
            lambda: (_ for _ in ()).throw(OctoplantConfigError("missing runtime"))
        )

        tool_names = {tool.name for tool in asyncio.run(server.mcp.list_tools())}

        self.assertSetEqual(tool_names, {"configuratie_ontbreekt"})


class WorkspaceResolutionTests(unittest.TestCase):
    @patch.dict("src.client.os.environ", {}, clear=True)
    def test_uses_explicit_client_workspace_outside_copilot(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            self.assertEqual(
                OctoplantClient._resolve_workspace_path(workspace),
                Path(workspace).resolve(),
            )

    @patch.dict("src.client.os.environ", {}, clear=True)
    def test_rejects_missing_client_workspace(self) -> None:
        with self.assertRaises(OctoplantConfigError):
            OctoplantClient._resolve_workspace_path(r"C:\does-not-exist")

    def test_uses_active_copilot_session_workspace(self) -> None:
        session_id = "12345678-1234-1234-1234-123456789abc"
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            project_workspace = root_path / "OT-Engineer"
            metadata_path = (
                root_path
                / ".copilot"
                / "session-state"
                / session_id
                / "workspace.yaml"
            )
            project_workspace.mkdir()
            metadata_path.parent.mkdir(parents=True)
            metadata_path.write_text(
                f"cwd: {project_workspace}\n",
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "src.client.os.environ",
                    {"COPILOT_AGENT_SESSION_ID": session_id},
                    clear=True,
                ),
                patch("src.client.Path.home", return_value=root_path),
            ):
                self.assertEqual(
                    OctoplantClient._resolve_workspace_path(
                        r"C:\temporary-artifacts\octoplant"
                    ),
                    project_workspace.resolve(),
                )

    @patch.dict("src.client.os.environ", {}, clear=True)
    def test_checkout_mirrors_to_the_supplied_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            client = OctoplantClient()
            resolved_workspace = Path(workspace).resolve()

            with patch(
                "src.client.subprocess.run",
                return_value=subprocess.CompletedProcess(args=[], returncode=0),
            ) as run:
                result = asyncio.run(
                    client.checkout_component(
                        workspace,
                        component_path=r"\{root}\{installation}\{plc-project}",
                    )
                )

            command = run.call_args.args[0]
            self.assertEqual(
                command[:4],
                [
                    client._vdogcheckout_exe,
                    "checkout",
                    "--workspace",
                    str(resolved_workspace),
                ],
            )
            self.assertEqual(run.call_args.kwargs["cwd"], client.runtime_path)
            self.assertEqual(
                Path(result["checkout_path"]),
                resolved_workspace / "octoPlantCheckouts",
            )
            self.assertNotEqual(
                Path(result["checkout_path"]).parent,
                Path(__file__).resolve().parents[1],
            )


if __name__ == "__main__":
    unittest.main()
