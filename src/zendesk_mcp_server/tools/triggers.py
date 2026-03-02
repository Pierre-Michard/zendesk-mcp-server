import json
from typing import Any

from mcp.server import types

TOOLS = [
    types.Tool(
        name="list_triggers",
        description="List Zendesk triggers with optional filtering by active status",
        inputSchema={
            "type": "object",
            "properties": {
                "active": {"type": "boolean", "description": "Filter by active (true) or inactive (false) triggers. Omit to return all."},
                "page": {"type": "integer", "description": "Page number", "default": 1},
                "per_page": {"type": "integer", "description": "Number of triggers per page (max 100)", "default": 25},
            },
            "required": [],
        },
    ),
    types.Tool(
        name="get_trigger",
        description="Get a Zendesk trigger by ID, including its conditions and actions",
        inputSchema={
            "type": "object",
            "properties": {
                "trigger_id": {"type": "integer", "description": "The ID of the trigger to retrieve"},
            },
            "required": ["trigger_id"],
        },
    ),
    types.Tool(
        name="test_trigger",
        description=(
            "Test whether a trigger's conditions would match a given ticket. "
            "Returns the trigger conditions, actions, and ticket details side-by-side "
            "so you can verify whether the trigger would fire."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "trigger_id": {"type": "integer", "description": "The ID of the trigger to test"},
                "ticket_id": {"type": "integer", "description": "The ID of the ticket to test against"},
            },
            "required": ["trigger_id", "ticket_id"],
        },
    ),
]


def handle(name: str, arguments: dict[str, Any] | None, client) -> list[types.TextContent] | None:
    if name == "list_triggers":
        active = arguments.get("active") if arguments else None
        page = arguments.get("page", 1) if arguments else 1
        per_page = arguments.get("per_page", 25) if arguments else 25
        return [types.TextContent(type="text", text=json.dumps(client.list_triggers(active=active, page=page, per_page=per_page), indent=2))]

    if name == "get_trigger":
        if not arguments:
            raise ValueError("Missing arguments")
        return [types.TextContent(type="text", text=json.dumps(client.get_trigger(trigger_id=arguments["trigger_id"]), indent=2))]

    if name == "test_trigger":
        if not arguments:
            raise ValueError("Missing arguments")
        result = client.test_trigger(trigger_id=arguments["trigger_id"], ticket_id=arguments["ticket_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    return None