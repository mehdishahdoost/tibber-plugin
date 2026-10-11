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

Hermes reads the native plugin.yaml adapter and asks for a missing **TIBBER_ACCESS_TOKEN** using masked input. Get your token at https://developer.tibber.com/. Hermes saves it in the active profile's .env. An existing token is reused. If the token is skipped or empty, the skill stays visible, but the adapter logs a setup warning and does not configure a new MCP server. Supply the token through Hermes and restart to complete setup.

Enable the plugin when prompted (or use --enable), then restart Hermes. The adapter validates mcp.json and installs its Tibber entry into native MCP configuration automatically. No separate MCP setup prompt is needed. The first server launch downloads tibber-mcp-server@0.2.2 using npx. Requires Node.js 18+, npx on PATH, and Hermes >=0.21.6 with MCP support. No additional Python dependencies are declared.

In Hermes CLI, TUI, or Desktop, run `/reload-skills` and invoke `/tibber:tibber-electricity-summary`. You can also ask Hermes to load `tibber:tibber-electricity-summary` with `skill_view`. Ask Hermes to list your Tibber homes; the MCP tool names start with mcp__tibber__.

## Package layout

- plugin.json: Agent Plugins 1.0.0 manifest.
- mcp.json: sole source of the MCP server configuration.
- skills/tibber-electricity-summary/SKILL.md: active summary skill.
- plugin.yaml and __init__.py: Hermes adapter for credential prompting, configuration, and skill registration. Hermes prefers this native manifest over plugin.json.

Agent Plugins 1.0.0 leaves authentication to clients. Hermes does not prompt for requires_env in a pure portable manifest, which is why the adapter is necessary. Other clients can load plugin.json and mcp.json without executing it. The ${TIBBER_ACCESS_TOKEN} reference is Hermes-specific; other clients need equivalent client-managed credential resolution. Never replace it with a real token in committed files.

The exact upstream skill is preserved in skills/tibber-electricity-summary/references/upstream-SKILL.md at upstream commit 1f41ecdb53b247392791534c5ff4b1271074924d. The active skill changes only metadata.hermes to a JSON string for portable metadata compatibility; its body is unchanged.

## Existing configurations and removal

An existing mcp_servers.tibber entry takes precedence and is reused unchanged, including its command, environment, and enabled setting. The skill still registers. When there is no existing entry, the adapter configures it from mcp.json. Other configuration is preserved. The adapter stores only the credential reference in config.yaml.

If the adapter created the native MCP entry, remove mcp_servers.tibber from the active profile's config.yaml when uninstalling and restart Hermes. If you already had a Tibber MCP entry, keep it if you still use it independently. Remove TIBBER_ACCESS_TOKEN from that profile's .env when no longer needed.

## Data access and execution

This is an independent community integration, not an official Tibber product.

- Hermes launches the pinned npm package `tibber-mcp-server@0.2.2` through `npx` as a local stdio subprocess. npm may download it and its dependencies from the npm registry. Node.js must already be installed. The subprocess stays running while Hermes uses the MCP connection.
- The server makes authenticated HTTPS requests to Tibber's GraphQL API at `https://api.tibber.com/v1-beta/gql`. It reads account details, home addresses, prices, consumption, and production history. It does not implement account changes or live WebSocket subscriptions.
- The adapter reads credentials only through Hermes's profile-aware `get_secret` API. Hermes owns credential prompting and storage; the adapter does not read credential files directly or log the token. The token is passed to the MCP subprocess through its environment.
- On first configuration, the adapter uses Hermes's configuration API to add the server to the active profile's `config.yaml`. Existing Tibber and unrelated settings are preserved. The MCP entry contains a token reference, not the credential.
- When invoked, the skill instructs Hermes to read/write `~/.hera/tibber.data` outside the plugin directory. This JSON cache contains home addresses, IDs, timestamps, costs, consumption, and prices, but no credentials. It asks Hermes to use Python through its ordinary tools for calculations and atomic, permission-restricted cache updates; normal tool approvals still apply.
- The bundled upstream workflow includes a default Amsterdam home. If it cannot uniquely match that home in the account, it asks the user to select one. Reports use the home's timezone and API currency.
- The plugin has no telemetry, self-updater, scheduled jobs, or custom UI. The server version is pinned; npm resolves its published dependency graph. Catalog plugin updates require review of a new commit pin.

## Development checks

```sh
python3 -m unittest discover -s tests -v
hermes plugins validate /path/to/tibber-plugin --install-deps
```

Tests use synthetic credentials and configuration. Catalog validation can run without a Tibber token; a live authenticated account check is a separate step.
