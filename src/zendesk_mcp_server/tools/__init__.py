from zendesk_mcp_server.tools import fields, tickets, users, views, webhooks

_DOMAIN_MODULES = [tickets, views, users, fields, webhooks]

ALL_TOOLS = [tool for mod in _DOMAIN_MODULES for tool in mod.TOOLS]


def dispatch(name: str, arguments, client):
    for mod in _DOMAIN_MODULES:
        result = mod.handle(name, arguments, client)
        if result is not None:
            return result
    raise ValueError(f"Unknown tool: {name}")


__all__ = ["ALL_TOOLS", "dispatch"]
