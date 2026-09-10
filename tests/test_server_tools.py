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

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from src.client import OctoplantClient, OctoplantConfigError


class PluginPackageTests(unittest.TestCase):
    _root = Path(__file__).resolve().parents[1]
    _profile_path = Path("agents") / "octoplant-specialist.agent.md"
    _fixtures_path = Path("tests") / "fixtures"
    _work_result_fields = {
        "schema_version",
        "correlation_id",
        "step_id",
        "status",
        "summary",
        "output_artifacts",
        "octoplant_checkout",
        "evidence",
        "risks",
    }

    def _load_fixture(self, name: str) -> dict:
        return json.loads((self._root / self._fixtures_path / name).read_text())

    def _profile_example(self, heading: str) -> dict:
        profile = (self._root / self._profile_path).read_text()
        _, separator, remaining = profile.partition(heading)
        self.assertTrue(separator)
        return json.loads(remaining.split("```json", 1)[1].split("```", 1)[0])

    def _validate_work_result(self, result: dict) -> None:
        schema = json.loads(
            (self._root / "contracts" / "work-result.schema.json").read_text()
        )
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(result)

    def _assert_exact_work_result_root(self, result: dict) -> None:
        self.assertSetEqual(set(result), self._work_result_fields | ({"errors"} if "errors" in result else set()))
        self.assertNotIn("type", result)
        self.assertNotIn("result", result)
        self.assertNotIn("skipped", result)
        self.assertEqual(result["schema_version"], "1.2")
        UUID(result["correlation_id"])
        self.assertTrue(result["step_id"])
        self.assertTrue(result["evidence"])
        self.assertTrue(result["risks"])

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
        self.assertIn("exactly one `octoplant.*` work_request", source_profile)
        self.assertIn("Enabled=N", source_profile)
        self.assertIn("WithoutComparison=Y", source_profile)
        self.assertIn("For every checkout request", source_profile)
        self.assertIn("checkout_copy_and_release_component", source_profile)
        self.assertIn("octoplant.resolve_project_context", source_profile)
        self.assertIn("octoplant.checkout_copy_release", source_profile)
        self.assertIn("do not substitute", source_profile)
        self.assertIn("correlation_id", source_profile)
        self.assertIn("step_id", source_profile)
        self.assertIn("before this child becomes idle", source_profile)
        self.assertIn("The one JSON object is the entire final response", source_profile)
        self.assertIn("`type`, `result`, or `skipped` fields", source_profile)
        self.assertIn("`captured_at` timestamp", source_profile)
        self.assertIn("resolved_identity` is the canonical structured identity", source_profile)

    def test_publishes_the_same_work_result_contract(self) -> None:
        source_contract = (
            self._root / "contracts" / "work-result.schema.json"
        ).read_text()
        package_contract = (
            self._root / "publish" / "contracts" / "work-result.schema.json"
        ).read_text()

        self.assertEqual(source_contract, package_contract)

    def test_publishes_the_same_work_result_workflow_docs(self) -> None:
        for path in (
            Path("skills") / "Octoplant" / "SKILL.md",
            Path("skills") / "Octoplant" / "references" / "checkout.md",
        ):
            self.assertEqual(
                (self._root / path).read_text(),
                (self._root / "publish" / path).read_text(),
                path,
            )

    def test_documents_a_complete_generic_result_for_checkout_returncode_one(self) -> None:
        result = self._profile_example("### Terminal targeted-checkout failure")
        self.assertEqual(
            result, self._load_fixture("checkout-failed.work-result.json")
        )
        self._validate_work_result(result)
        self._assert_exact_work_result_root(result)

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
        for evidence in result["evidence"]:
            self.assertTrue(evidence["type"])
            datetime.fromisoformat(evidence["captured_at"])
        self.assertSetEqual(set(result["risks"][0]), {"code", "description"})
        self.assertNotIn("stdout", json.dumps(result))
        self.assertNotIn("stderr", json.dumps(result))
        self.assertNotIn("traceback", json.dumps(result).lower())

    def test_requires_generic_handling_for_every_terminal_checkout_error(self) -> None:
        profile = (self._root / self._profile_path).read_text()

        self.assertIn("Return code `1` or unknown non-zero code", profile)
        self.assertIn("Return code `10`", profile)
        self.assertIn("Return code `1000`", profile)
        self.assertIn("Tool invocation error without a return code", profile)
        self.assertIn("Authentication failed.", profile)
        self.assertIn("Preserve the input\n`correlation_id` and `step_id` exactly.", profile)
        for status in (
            "completed",
            "blocked",
            "failed",
            "ambiguous",
            "needs_input",
            "unsafe",
        ):
            self.assertIn(f"`{status}`", profile)
        self.assertIn(
            "each entry must contain exactly\n`ref`, `kind`, and `local_path`",
            profile,
        )

    def test_documents_schema_valid_successful_targeted_checkout_result(self) -> None:
        result = self._profile_example("### Successful targeted checkout")
        self.assertEqual(
            result, self._load_fixture("checkout-success.work-result.json")
        )

        self._validate_work_result(result)
        self._assert_exact_work_result_root(result)

        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["output_artifacts"])
        for artifact in result["output_artifacts"]:
            self.assertSetEqual(set(artifact), {"ref", "kind", "local_path"})
            self.assertTrue(artifact["ref"])
            self.assertTrue(artifact["kind"])
            self.assertTrue(artifact["local_path"])
        self.assertEqual(
            result["octoplant_checkout"]["local_checkout_ref"],
            result["output_artifacts"][0]["ref"],
        )
        self.assertIsInstance(result["octoplant_checkout"]["resolved_identity"], dict)
        self.assertNotIn("resolved_project_identity", result["octoplant_checkout"])
        self.assertIn(
            "octoplant_unchanged_release_completed",
            {evidence["type"] for evidence in result["evidence"]},
        )

    def test_documents_schema_valid_completed_not_found_result(self) -> None:
        result = self._profile_example("### Completed targeted checkout not found")
        self.assertEqual(
            result, self._load_fixture("checkout-not-found.work-result.json")
        )

        self._validate_work_result(result)
        self._assert_exact_work_result_root(result)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["output_artifacts"], [])
        self.assertIsNone(result["octoplant_checkout"]["local_checkout_ref"])
        self.assertNotIn(
            "octoplant_unchanged_release_completed",
            {evidence["type"] for evidence in result["evidence"]},
        )

    def test_requires_complete_work_result_fields(self) -> None:
        schema = json.loads(
            (self._root / "contracts" / "work-result.schema.json").read_text()
        )

        self.assertTrue(
            {
                "schema_version",
                "correlation_id",
                "step_id",
                "status",
                "output_artifacts",
                "evidence",
                "risks",
            }.issubset(schema["required"])
        )
        self.assertEqual(schema["properties"]["evidence"]["minItems"], 1)
        self.assertEqual(schema["properties"]["risks"]["minItems"], 1)
        self.assertSetEqual(
            set(schema["properties"]["status"]["enum"]),
            {"completed", "blocked", "needs_input", "failed", "unsafe", "ambiguous"},
        )
        self.assertIn(
            "captured_at", schema["$defs"]["evidence"]["required"]
        )
        self.assertSetEqual(
            set(schema["$defs"]["artifact"]["required"]),
            {"ref", "kind", "local_path"},
        )
        checkout = schema["$defs"]["octoplantCheckout"]["properties"]
        self.assertEqual(checkout["resolved_identity"]["$ref"], "#/$defs/projectIdentity")
        self.assertEqual(checkout["resolved_project_identity"]["type"], "string")

        valid_result = self._load_fixture("checkout-success.work-result.json")
        valid_result["octoplant_checkout"]["resolved_project_identity"] = (
            "Dendermonde PLC 2"
        )
        self._validate_work_result(valid_result)

        for forbidden_key in ("type", "result", "skipped"):
            invalid_result = self._load_fixture("checkout-success.work-result.json")
            invalid_result[forbidden_key] = "invalid-wrapper"
            with self.assertRaises(ValidationError):
                self._validate_work_result(invalid_result)

        invalid_identity = self._load_fixture("checkout-success.work-result.json")
        invalid_identity["octoplant_checkout"]["resolved_identity"] = (
            "Dendermonde PLC 2"
        )
        with self.assertRaises(ValidationError):
            self._validate_work_result(invalid_identity)

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
        self.assertIn(
            "checkout_copy_and_release_component",
            source_skill,
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
        self.assertEqual(result["status"], "Fout -- geen check-out mogelijk of minimaal een mislukt")
        self.assertTrue(result["binary_output_suppressed"])
        self.assertEqual(result["stdout"], "")
        self.assertEqual(result["stderr"], "")
        self.assertNotIn("native failure details", json.dumps(result))
        self.assertNotIn("native error details", json.dumps(result))

    def test_checkin_requires_confirmation(self) -> None:
        client = OctoplantClient()

        with self.assertRaisesRegex(OctoplantConfigError, "Explicit confirmation"):
            asyncio.run(
                client.checkin_unchanged_component(
                    r"\{root}\{installation}\{plc-project}", False
                )
            )

    def test_checkin_uses_the_dedicated_wrapper(self) -> None:
        client = OctoplantClient()

        with patch(
            "src.client.subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0),
        ) as run:
            result = asyncio.run(
                client.checkin_unchanged_component(
                    r"\{root}\{installation}\{plc-project}", True
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
    def test_confirmed_lifecycle_mirrors_then_releases(self) -> None:
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
                side_effect=[checkout_result, subprocess.CompletedProcess(args=[], returncode=0), release_result],
            ) as run:
                result = asyncio.run(
                    client.checkout_copy_and_release_component(
                        workspace_path=workspace,
                        installation_name="Example installation",
                        cost_center="100026",
                        component_path=r"\{root}\{installation}\{plc-project}",
                        confirmed=True,
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
                        confirmed=True,
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
                        confirmed=True,
                    )
                )

        self.assertFalse(result["success"])
        self.assertFalse(result["release_executed"])
        self.assertEqual(run.call_count, 1)
        self.assertNotIn("--all", run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
