import json
from typing import Any

from mcp.server import types

TOOLS = [
    types.Tool(
        name="list_ticket_fields",
        description="List all ticket fields (system and custom) with their options",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    types.Tool(
        name="list_user_fields",
        description="List all custom user fields with their options",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    types.Tool(
        name="list_organization_fields",
        description="List all custom organization fields with their options",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]


def handle(name: str, arguments: dict[str, Any] | None, client) -> list[types.TextContent] | None:
    if name == "list_ticket_fields":
        return [types.TextContent(type="text", text=json.dumps(client.get_ticket_fields(), indent=2))]

    if name == "list_user_fields":
        return [types.TextContent(type="text", text=json.dumps(client.get_user_fields(), indent=2))]

    if name == "list_organization_fields":
        return [types.TextContent(type="text", text=json.dumps(client.get_organization_fields(), indent=2))]

    return None
