"""Focused MCP registration, handoff, and checkout lifecycle tests."""

import asyncio
import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.client import OctoplantClient, OctoplantConfigError


class PluginPackageTests(unittest.TestCase):
    _root = Path(__file__).resolve().parents[1]
    _profile_path = Path("agents") / "octoplant-specialist.agent.md"
    _fixtures_path = Path("tests") / "fixtures"
    _terminal_states = (
        "✅ COMPLETED",
        "🔎 NOT_FOUND",
        "❓ NEEDS_INPUT",
        "⚠️ BLOCKED",
        "❌ FAILED",
        "🛑 UNSAFE",
    )

    def _load_fixture(self, name: str) -> str:
        return (self._root / self._fixtures_path / name).read_text(
            encoding="utf-8"
        ).strip()

    def test_registers_the_specialist_agent_in_source_and_package(self) -> None:
        source_manifest = json.loads((self._root / "plugin.json").read_text())
        package_manifest = json.loads(
            (self._root / "publish" / "plugin.json").read_text()
        )

        self.assertEqual(source_manifest["agents"], ["agents/"])
        self.assertEqual(package_manifest["agents"], ["agents/"])

    def test_publishes_the_same_shared_handoff_profile(self) -> None:
        source_profile = (self._root / self._profile_path).read_text(encoding="utf-8")
        package_profile = (
            self._root / "publish" / self._profile_path
        ).read_text(encoding="utf-8")

        self.assertEqual(source_profile, package_profile)
        self.assertIn("name: octoplant-specialist", source_profile)
        self.assertIn(self._load_fixture("octoplant-handoff.txt"), source_profile)
        self.assertIn(self._load_fixture("octoplant-completed-result.txt"), source_profile)
        self.assertIn("checkout_copy_and_release_component", source_profile)
        self.assertIn("Enabled=N", source_profile)
        self.assertIn("WithoutComparison=Y", source_profile)
        self.assertIn("ReleaseAfterCheckIn=Y", source_profile)
        self.assertIn("Do not delegate to APG, Control Expert", source_profile)

    def test_documents_only_the_approved_terminal_states(self) -> None:
        profile = (self._root / self._profile_path).read_text(encoding="utf-8")
        skill = (self._root / "skills" / "Octoplant" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        for state in self._terminal_states:
            self.assertIn(state, profile)
            self.assertIn(state, skill)

        completed_result = self._load_fixture("octoplant-completed-result.txt")
        self.assertTrue(completed_result.startswith("↩️ RESULTAAT — ✅ COMPLETED"))
        self.assertIn("Lokaal project:", completed_result)
        for forbidden in (
            "{",
            "}",
            "component_path",
            "correlation_id",
            "evidence",
            "risks",
            "work_result",
        ):
            self.assertNotIn(forbidden, completed_result)

    def test_publishes_the_same_shared_interface_docs(self) -> None:
        for path in (
            Path("skills") / "Octoplant" / "SKILL.md",
            Path("skills") / "Octoplant" / "references" / "checkout.md",
            Path("skills") / "Octoplant" / "references" / "mcp-tools.md",
            Path("skills") / "Octoplant" / "references" / "navigation.md",
            Path("skills") / "Octoplant" / "references" / "project-structure.md",
        ):
            self.assertEqual(
                (self._root / path).read_text(encoding="utf-8"),
                (self._root / "publish" / path).read_text(encoding="utf-8"),
                path,
            )

    def test_publishes_the_same_runtime_sources(self) -> None:
        for path in (
            Path("server.py"),
            Path("src") / "client.py",
            Path("src") / "tools" / "checkout.py",
        ):
            self.assertEqual(
                (self._root / path).read_text(encoding="utf-8"),
                (self._root / "publish" / path).read_text(encoding="utf-8"),
                path,
            )

    def test_keeps_all_release_version_metadata_in_sync(self) -> None:
        source_manifest = json.loads((self._root / "plugin.json").read_text())
        package_manifest = json.loads(
            (self._root / "publish" / "plugin.json").read_text()
        )
        source_project = (self._root / "pyproject.toml").read_text(encoding="utf-8")
        package_project = (
            self._root / "publish" / "pyproject.toml"
        ).read_text(encoding="utf-8")
        source_skill = (
            self._root / "skills" / "Octoplant" / "SKILL.md"
        ).read_text(encoding="utf-8")
        package_skill = (
            self._root / "publish" / "skills" / "Octoplant" / "SKILL.md"
        ).read_text(encoding="utf-8")
        version = source_manifest["version"]

        self.assertEqual(version, "3.0.0")
        self.assertEqual(package_manifest["version"], version)
        self.assertIn(f'version = "{version}"', source_project)
        self.assertIn(f'version = "{version}"', package_project)
        self.assertIn(f"version: {version}", source_skill)
        self.assertIn(f"version: {version}", package_skill)
        self.assertIn(
            f"**Release:** {version}",
            (self._root / "README.md").read_text(encoding="utf-8"),
        )

    def test_does_not_publish_the_retired_work_result_contract(self) -> None:
        self.assertFalse(
            (self._root / "contracts" / "work-result.schema.json").exists()
        )
        self.assertFalse(
            (
                self._root
                / "publish"
                / "contracts"
                / "work-result.schema.json"
            ).exists()
        )
        self.assertFalse(
            any((self._root / self._fixtures_path).glob("*.work-result.json"))
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
            {
                "authenticate",
                "checkout_component",
                "checkout_copy_and_release_component",
                "checkin_unchanged_component",
                "resolve_project",
            },
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
    def test_checkout_mirrors_to_the_handoff_installation_directory(self) -> None:
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

            command = run.call_args_list[0].args[0]
            self.assertEqual(
                command[:4],
                [
                    client._vdogcheckout_exe,
                    "checkout",
                    "--json",
                    r"\{root}\{installation}\{plc-project}",
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
            mirror_command = run.call_args_list[1].args[0]
            self.assertEqual(mirror_command[0], "robocopy")
            self.assertEqual(mirror_command[3:5], ["/MIR", "/R:1"])
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

    def test_checkout_returns_a_generic_safe_failure(self) -> None:
        client = OctoplantClient()

        with patch(
            "src.client.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout="native failure details",
                stderr="native error details",
            ),
        ):
            result = asyncio.run(
                client.checkout_component(
                    component_path=r"\{root}\{installation}\{plc-project}",
                )
            )

        self.assertEqual(result["returncode"], 1)
        self.assertEqual(
            result["status"],
            "Fout -- geen check-out mogelijk of minimaal een mislukt",
        )
        self.assertTrue(result["binary_output_suppressed"])
        self.assertEqual(result["stdout"], "")
        self.assertEqual(result["stderr"], "")
        self.assertNotIn("native failure details", json.dumps(result))
        self.assertNotIn("native error details", json.dumps(result))

    def test_checkin_uses_the_dedicated_wrapper(self) -> None:
        client = OctoplantClient()

        with patch(
            "src.client.subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0),
        ) as run:
            result = asyncio.run(
                client.checkin_unchanged_component(
                    r"\{root}\{installation}\{plc-project}"
                )
            )

        self.assertEqual(
            run.call_args.args[0],
            [
                client._vdogcheckin_exe,
                "checkin",
                "--json",
                r"\{root}\{installation}\{plc-project}",
            ],
        )
        self.assertTrue(result["success"])
        self.assertTrue(result["binary_output_suppressed"])

    @patch.dict("src.client.os.environ", {}, clear=True)
    def test_lifecycle_mirrors_then_releases(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            client = OctoplantClient()
            native_checkout = Path(workspace) / "clientarchive"

            checkout_result = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps({"checkout_path": str(native_checkout)}),
                stderr="",
            )
            release_result = subprocess.CompletedProcess(args=[], returncode=0)
            with patch(
                "src.client.subprocess.run",
                side_effect=[
                    checkout_result,
                    subprocess.CompletedProcess(args=[], returncode=0),
                    release_result,
                ],
            ) as run:
                result = asyncio.run(
                    client.checkout_copy_and_release_component(
                        workspace_path=workspace,
                        installation_name="Example installation",
                        cost_center="100026",
                        component_path=r"\{root}\{installation}\{plc-project}",
                    )
                )

        self.assertTrue(result["success"])
        self.assertTrue(result["release_executed"])
        self.assertEqual(run.call_args_list[1].args[0][0], "robocopy")
        self.assertEqual(
            run.call_args_list[2].args[0],
            [
                client._vdogcheckin_exe,
                "checkin",
                "--json",
                r"\{root}\{installation}\{plc-project}",
            ],
        )

    @patch.dict("src.client.os.environ", {}, clear=True)
    def test_lifecycle_does_not_release_after_mirror_failure(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            client = OctoplantClient()
            checkout_result = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps({"checkout_path": workspace}),
                stderr="",
            )
            mirror_failure = subprocess.CompletedProcess(args=[], returncode=8)
            with patch(
                "src.client.subprocess.run",
                side_effect=[checkout_result, mirror_failure],
            ) as run:
                result = asyncio.run(
                    client.checkout_copy_and_release_component(
                        workspace_path=workspace,
                        installation_name="Example installation",
                        cost_center="100026",
                        component_path=r"\{root}\{installation}\{plc-project}",
                    )
                )

        self.assertFalse(result["success"])
        self.assertFalse(result["release_executed"])
        self.assertEqual(run.call_count, 2)

    @patch.dict("src.client.os.environ", {}, clear=True)
    def test_lifecycle_does_not_release_after_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            client = OctoplantClient()
            with patch(
                "src.client.subprocess.run",
                return_value=subprocess.CompletedProcess(args=[], returncode=2),
            ) as run:
                result = asyncio.run(
                    client.checkout_copy_and_release_component(
                        workspace_path=workspace,
                        installation_name="Example installation",
                        cost_center="100026",
                        component_path=r"\{root}\{installation}\{missing-project}",
                    )
                )

        self.assertFalse(result["success"])
        self.assertFalse(result["release_executed"])
        self.assertEqual(run.call_count, 1)
        self.assertNotIn("--all", run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
