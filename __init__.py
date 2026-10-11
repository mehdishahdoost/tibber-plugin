"""Hermes adapter: prompt via plugin.yaml, configure from portable mcp.json."""

from pathlib import Path


def register(ctx):
    from agent.secret_scope import get_secret
    from hermes_cli.agent_plugins import load_agent_plugin
    from hermes_cli.config import load_config, save_config

    token = get_secret("TIBBER_ACCESS_TOKEN")
    if not token or not token.strip():
        raise RuntimeError(
            "TIBBER_ACCESS_TOKEN is required. Provide it through the Hermes "
            "plugin installation prompt or the active profile's .env."
        )

    root = Path(__file__).resolve().parent
    # Parse and validate the portable package using Hermes's own adapter. It
    # translates stdio config and discovers skills without launching anything.
    package = load_agent_plugin(root, root)
    if package.diagnostics:
        raise RuntimeError("Invalid Tibber package: " + "; ".join(
            diagnostic.message for diagnostic in package.diagnostics
        ))
    server = dict(package.mcp_servers["tibber"])
    config = load_config()
    servers = config.get("mcp_servers")
    if servers is None:
        servers = {}
    if not isinstance(servers, dict):
        raise RuntimeError("Hermes mcp_servers configuration must be a mapping.")

    existing = servers.get("tibber")
    if existing is not None and not isinstance(existing, dict):
        raise RuntimeError("Hermes mcp_servers.tibber configuration must be a mapping.")
    # Native user configuration takes precedence, just as it does when Hermes
    # loads portable MCP entries. It may use another version, launcher, or env
    # source; none of those differences should hide the bundled skill.
    if existing is None:
        # Keep the env reference literal; Hermes resolves it at connection time.
        # Merge through Hermes so unrelated user configuration is preserved.
        save_config({"mcp_servers": {"tibber": server}}, merge_existing=True)
        if load_config().get("mcp_servers", {}).get("tibber") != server:
            raise RuntimeError("Hermes could not save the Tibber MCP configuration.")

    for skill in package.skills:
        ctx.register_skill(skill.name, skill.skill_md, skill.description, skill.frontmatter)
