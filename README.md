# Tibber Agent Plugin

Agent Plugins 1.0.0 package with root `plugin.json`, root `mcp.json`, and `skills/tibber-electricity-summary/SKILL.md`.

The server runs through `npx -y tibber-mcp-server@0.2.2`. Requires Node.js 18+, npx on PATH, and Hermes with portable Agent Plugins and MCP support. The npm package downloads on first launch. There is no native Python registration entrypoint and the plugin does not write MCP entries into config.yaml.

## Install with the required token prompt

Publish this directory as a Git repository. From this checkout, run with the Python interpreter in Hermes's environment:

```sh
python scripts/install.py OWNER/REPOSITORY
```

The helper uses Hermes's own masked token prompt, saves a missing TIBBER_ACCESS_TOKEN to the active profile's .env, and invokes the normal installer with enablement requested. An existing token is reused. Skipping/cancelling the prompt or leaving the token empty prevents installation. The helper uses internal Hermes installer APIs; future changes may require updating it. Get a token at https://developer.tibber.com/.

Agent Plugins 1.0.0 leaves authentication to clients. Current Hermes does not honor requires_env in portable manifests or extensions. Direct `hermes plugins install OWNER/REPOSITORY --enable` therefore cannot be forced by this package to prompt. Use the helper to enforce the token requirement.

The `${TIBBER_ACCESS_TOKEN}` value in mcp.json is a Hermes-specific runtime secret reference. Hermes resolves it from the active profile when connecting. The portable spec defines only PLUGIN_ROOT and PLUGIN_DATA expansion; other clients must provide equivalent credential resolution. Never commit a real token.

Restart Hermes after installing. Use skills_list to discover the generated portable namespace for tibber-electricity-summary. MCP tools keep the mcp__tibber__ prefix.

## Skill provenance


Sources: https://github.com/mehdishahdoost/tibber-mcp-server and https://github.com/mehdishahdoost/tibber-electricity-summary.

## Remove or migrate

Use Hermes's normal plugin disable/remove commands and restart Hermes. No native MCP configuration is written. If you previously enabled the earlier Python version, remove its mcp_servers.tibber entry from the active profile's config.yaml; native entries take precedence over portable ones. Remove the profile's token from .env when no longer needed.
