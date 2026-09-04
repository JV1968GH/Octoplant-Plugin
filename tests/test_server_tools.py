"""Focused MCP registration tests that do not require Octoplant configuration."""

import asyncio
import importlib
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
    def test_uses_explicit_client_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            self.assertEqual(
                OctoplantClient._resolve_workspace_path(workspace),
                Path(workspace).resolve(),
            )

    def test_rejects_missing_client_workspace(self) -> None:
        with self.assertRaises(OctoplantConfigError):
            OctoplantClient._resolve_workspace_path(r"C:\does-not-exist")


if __name__ == "__main__":
    unittest.main()
