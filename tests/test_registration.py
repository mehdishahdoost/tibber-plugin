"""Regression checks for credential gating and existing MCP configuration."""

import copy
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tibber_plugin", ROOT / "__init__.py")
PLUGIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PLUGIN)


class RegistrationTests(unittest.TestCase):
    def run_registration(self, config, token="test-token"):
        state = copy.deepcopy(config)
        secret = ModuleType("agent.secret_scope")
        secret.get_secret = Mock(return_value=token)
        portable = ModuleType("hermes_cli.agent_plugins")
        portable.load_agent_plugin = Mock(return_value=SimpleNamespace(
            diagnostics=[],
            mcp_servers={"tibber": {
                "command": "npx",
                "args": ["-y", "tibber-mcp-server@0.2.2"],
                "env": {"TIBBER_ACCESS_TOKEN": "${TIBBER_ACCESS_TOKEN}"},
            }},
            skills=[SimpleNamespace(
                name="tibber-electricity-summary",
                skill_md=ROOT / "skills/tibber-electricity-summary/SKILL.md",
                description="Electricity summary", frontmatter={},
            )],
        ))
        settings = ModuleType("hermes_cli.config")
        settings.load_config = lambda: copy.deepcopy(state)

        def save(value, *, merge_existing=False):
            self.assertTrue(merge_existing)
            state.setdefault("mcp_servers", {}).update(value["mcp_servers"])

        settings.save_config = Mock(side_effect=save)
        context = SimpleNamespace(register_skill=Mock())
        with patch.dict(sys.modules, {
            "agent": ModuleType("agent"), "agent.secret_scope": secret,
            "hermes_cli": ModuleType("hermes_cli"),
            "hermes_cli.agent_plugins": portable, "hermes_cli.config": settings,
        }):
            PLUGIN.register(context)
            PLUGIN.register(context)
        return state, settings.save_config, context.register_skill

    def test_existing_server_does_not_hide_skill(self):
        for enabled in (True, False):
            with self.subTest(enabled=enabled):
                config = {"mcp_servers": {"tibber": {
                    "command": "custom-launcher", "args": [], "enabled": enabled,
                }}, "model": "keep-me"}
                state, save, register = self.run_registration(config)
                self.assertEqual(state, config)
                save.assert_not_called()
                self.assertEqual(register.call_count, 2)
                self.assertEqual(register.call_args.args[0], "tibber-electricity-summary")

    def test_missing_server_is_added_once_without_storing_token(self):
        state, save, register = self.run_registration({
            "mcp_servers": {"other": {"command": "other"}}, "model": "keep-me",
        })
        save.assert_called_once()
        self.assertEqual(state["mcp_servers"]["other"], {"command": "other"})
        self.assertEqual(state["model"], "keep-me")
        self.assertNotIn("test-token", repr(state))
        self.assertEqual(register.call_count, 2)

    def test_missing_token_remains_required(self):
        for token in (None, "", "  "):
            with self.subTest(token=token), self.assertRaisesRegex(RuntimeError, "required"):
                self.run_registration({}, token=token)


if __name__ == "__main__":
    unittest.main()
