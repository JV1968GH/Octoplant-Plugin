"""Focused MCP registration tests that do not require Octoplant configuration."""

import asyncio
import importlib
import sys
import unittest
from unittest.mock import patch

from src.client import OctoplantConfigError


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


if __name__ == "__main__":
    unittest.main()
