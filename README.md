# Tibber Agent Plugin

[Tibber MCP server](https://github.com/mehdishahdoost/tibber-mcp-server) and the [electricity summary skill](https://github.com/mehdishahdoost/tibber-electricity-summary) bundled for Hermes and Agent Plugins clients.

## Install in Hermes

Run in an interactive terminal:

```sh
hermes plugins install mehdishahdoost/tibber-plugin --enable
```

For an existing installation, reinstall the updated package:

```sh
hermes plugins install mehdishahdoost/tibber-plugin --force --enable
```

Hermes reads the native plugin.yaml adapter and asks for a missing **TIBBER_ACCESS_TOKEN** using masked input. Get your token at https://developer.tibber.com/. Hermes saves it in the active profile's .env. An existing token is reused. If the token is skipped or empty, the adapter refuses to load.

Enable the plugin when prompted (or use --enable), then restart Hermes. The adapter validates mcp.json and installs its Tibber entry into native MCP configuration automatically. No separate MCP setup prompt is needed. The first server launch downloads tibber-mcp-server@0.2.2 using npx. Requires Node.js 18+, npx on PATH, and Hermes with MCP and portable-package parsing support.

Use skills_list to find tibber:tibber-electricity-summary. Ask Hermes to list your Tibber homes; the MCP tool names start with mcp__tibber__.

## Package layout

- plugin.json: Agent Plugins 1.0.0 manifest.
- mcp.json: sole source of the MCP server configuration.
- skills/tibber-electricity-summary/SKILL.md: active summary skill.
- plugin.yaml and __init__.py: Hermes adapter for credential prompting, configuration, and skill registration. Hermes prefers this native manifest over plugin.json.

Agent Plugins 1.0.0 leaves authentication to clients. Hermes does not prompt for requires_env in a pure portable manifest, which is why the adapter is necessary. Other clients can load plugin.json and mcp.json without executing it. The ${TIBBER_ACCESS_TOKEN} reference is Hermes-specific; other clients need equivalent client-managed credential resolution. Never replace it with a real token in committed files.

The exact upstream skill is preserved in skills/tibber-electricity-summary/references/upstream-SKILL.md at upstream commit 1f41ecdb53b247392791534c5ff4b1271074924d. The active skill changes only metadata.hermes to a JSON string for portable metadata compatibility; its body is unchanged.

## Existing configurations and removal

A differing mcp_servers.tibber entry is preserved and reported as a conflict. Review/remove that entry and restart Hermes to let the adapter configure it from mcp.json. Other configuration is preserved. The credential stays in .env; config.yaml contains its reference only.

Because the adapter installs a native MCP entry, removing/disabling this plugin also requires removing mcp_servers.tibber from the active profile's config.yaml and restarting Hermes. Remove TIBBER_ACCESS_TOKEN from that profile's .env when no longer needed.
