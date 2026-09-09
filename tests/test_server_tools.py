"""Focused MCP registration tests that do not require Octoplant configuration."""

import asyncio
import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from src.client import OctoplantClient, OctoplantConfigError


class PluginPackageTests(unittest.TestCase):
    _root = Path(__file__).resolve().parents[1]
    _profile_path = Path("agents") / "octoplant-specialist.agent.md"

    def test_registers_the_specialist_agent_in_source_and_package(self) -> None:
        source_manifest = json.loads((self._root / "plugin.json").read_text())
        package_manifest = json.loads(
            (self._root / "publish" / "plugin.json").read_text()
        )

        self.assertEqual(source_manifest["agents"], ["agents/"])
        self.assertEqual(package_manifest["agents"], ["agents/"])

    def test_publishes_the_same_specialist_agent_profile(self) -> None:
        source_profile = (self._root / self._profile_path).read_text()
        package_profile = (self._root / "publish" / self._profile_path).read_text()

        self.assertEqual(source_profile, package_profile)
        self.assertIn("name: octoplant-specialist", source_profile)
        self.assertIn("exactly one read-only `octoplant.*` work_request", source_profile)
        self.assertIn("correlation_id", source_profile)
        self.assertIn("step_id", source_profile)

    def test_documents_a_complete_generic_result_for_checkout_returncode_one(self) -> None:
        profile = (self._root / self._profile_path).read_text()
        _, separator, remaining = profile.partition(
            "### Terminal targeted-checkout failure"
        )
        self.assertTrue(separator)
        example = remaining.split("```json", 1)[1].split("```", 1)[0]
        result = json.loads(example)

        self.assertSetEqual(
            set(result),
            {
                "schema_version",
                "correlation_id",
                "step_id",
                "status",
                "summary",
                "output_artifacts",
                "octoplant_checkout",
                "evidence",
                "risks",
                "errors",
            },
        )
        self.assertEqual(result["schema_version"], "1.2")
        UUID(result["correlation_id"])
        self.assertTrue(result["step_id"])
        self.assertEqual(result["status"], "failed")
        self.assertSetEqual(
            set(result["octoplant_checkout"]),
            {
                "checkout_executed",
                "resolved_identity",
                "component_path",
                "local_checkout_ref",
                "source_version",
            },
        )
        self.assertTrue(result["octoplant_checkout"]["checkout_executed"])
        self.assertIsNone(result["octoplant_checkout"]["local_checkout_ref"])
        self.assertSetEqual(
            set(result["errors"][0]), {"code", "returncode", "message"}
        )
        self.assertEqual(result["errors"][0]["returncode"], 1)
        self.assertEqual(
            result["errors"][0]["message"],
            "The requested read-only targeted checkout could not be completed.",
        )
        self.assertTrue(result["evidence"])
        self.assertTrue(result["risks"])
        for evidence in result["evidence"]:
            self.assertTrue(evidence["type"])
            datetime.fromisoformat(evidence["captured_at"])
        self.assertSetEqual(set(result["risks"][0]), {"code", "description"})
        self.assertNotIn("stdout", json.dumps(result))
        self.assertNotIn("stderr", json.dumps(result))

    def test_requires_generic_handling_for_every_terminal_checkout_error(self) -> None:
        profile = (self._root / self._profile_path).read_text()

        self.assertIn("Return code `1` or unknown non-zero code", profile)
        self.assertIn("Return code `10`", profile)
        self.assertIn("Return code `1000`", profile)
        self.assertIn("Tool invocation error without a return code", profile)
        self.assertIn("Authentication failed.", profile)
        self.assertIn("exact input `correlation_id`", profile)
        self.assertIn("exact input `step_id`", profile)

    def test_keeps_all_release_version_metadata_in_sync(self) -> None:
        source_manifest = json.loads((self._root / "plugin.json").read_text())
        package_manifest = json.loads(
            (self._root / "publish" / "plugin.json").read_text()
        )
        source_project = (self._root / "pyproject.toml").read_text()
        package_project = (self._root / "publish" / "pyproject.toml").read_text()
        source_skill = (self._root / "skills" / "Octoplant" / "SKILL.md").read_text()
        package_skill = (
            self._root / "publish" / "skills" / "Octoplant" / "SKILL.md"
        ).read_text()
        version = source_manifest["version"]

        self.assertEqual(package_manifest["version"], version)
        self.assertIn(f'version = "{version}"', source_project)
        self.assertIn(f'version = "{version}"', package_project)
        self.assertIn(f"version: {version}", source_skill)
        self.assertIn(f"version: {version}", package_skill)
        self.assertIn(
            f"**Release:** {version}",
            (self._root / "README.md").read_text(encoding="utf-8"),
        )


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
            {"authenticate", "checkout_component", "resolve_project"},
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
    def test_allows_a_missing_direct_checkout_workspace(self) -> None:
        self.assertEqual(
            OctoplantClient._resolve_workspace_path(r"C:\does-not-exist"),
            Path(r"C:\does-not-exist"),
        )

    @patch.dict("src.client.os.environ", {}, clear=True)
    def test_checkout_writes_directly_to_the_handoff_installation_directory(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            client = OctoplantClient()
            resolved_workspace = Path(workspace).resolve()

            with patch(
                "src.client.subprocess.run",
                return_value=subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout=json.dumps(
                        {
                            "checkout_path": str(
                                resolved_workspace
                                / "PLC-projecten"
                                / "Example installation - 100026"
                            )
                        }
                    ),
                    stderr="",
                ),
            ) as run:
                result = asyncio.run(
                    client.checkout_component(
                        workspace,
                        installation_name="Example installation",
                        cost_center="100026",
                        component_path=r"\{root}\{installation}\{plc-project}",
                    )
                )

            command = run.call_args.args[0]
            self.assertEqual(
                command[:5],
                [
                    client._vdogcheckout_exe,
                    "checkout",
                    "--json",
                    "--workspace",
                    str(
                        resolved_workspace
                        / "PLC-projecten"
                        / "Example installation - 100026"
                    ),
                ],
            )
            self.assertEqual(run.call_args.kwargs["cwd"], client.runtime_path)
            self.assertEqual(
                Path(result["checkout_path"]),
                resolved_workspace
                / "PLC-projecten"
                / "Example installation - 100026",
            )
            self.assertEqual(
                Path(result["artifact_path"]),
                resolved_workspace
                / "PLC-projecten"
                / "Example installation - 100026"
                / "{root}"
                / "{installation}"
                / "{plc-project}",
            )
            self.assertNotEqual(
                Path(result["checkout_path"]).parent,
                Path(__file__).resolve().parents[1],
            )

    @patch.dict("src.client.os.environ", {}, clear=True)
    def test_checkout_without_workspace_uses_the_configured_clientarchive(self) -> None:
        client = OctoplantClient()
        clientarchive = Path(r"C:\vdClientArchive")

        with patch(
            "src.client.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps({"checkout_path": str(clientarchive)}),
                stderr="",
            ),
        ) as run:
            result = asyncio.run(
                client.checkout_component(
                    component_path=r"\{root}\{installation}\{plc-project}",
                )
            )

        self.assertNotIn("--workspace", run.call_args.args[0])
        self.assertEqual(Path(result["checkout_path"]), clientarchive)

    def test_checkout_uses_only_available_installation_identifier(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            self.assertEqual(
                OctoplantClient._resolve_checkout_root(workspace, None, "100026"),
                Path(workspace).resolve() / "PLC-projecten" / "100026",
            )

    @patch.dict("src.client.os.environ", {}, clear=True)
    def test_checkout_returns_not_found_without_broad_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            client = OctoplantClient()
            with patch(
                "src.client.subprocess.run",
                return_value=subprocess.CompletedProcess(args=[], returncode=2),
            ) as run:
                result = asyncio.run(
                    client.checkout_component(
                        workspace,
                        installation_name="Example installation",
                        cost_center=None,
                        component_path=r"\{root}\{installation}\{missing-project}",
                    )
                )

            self.assertEqual(result["status"], "not_found")
            self.assertNotIn("--all", run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
