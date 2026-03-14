import json
from typing import Any

import mcp.types as types

TOOLS = [
    types.Tool(
        name="list_views",
        description="List all Zendesk views with pagination support",
        inputSchema={
            "type": "object",
            "properties": {
                "page": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Page number", "default": 1},
                "per_page": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Number of views per page (max 100)", "default": 25},
            },
            "required": [],
        },
    ),
]


def handle(name: str, arguments: dict[str, Any] | None, client) -> list[types.TextContent] | None:
    if name == "list_views":
        page = int(arguments.get("page", 1)) if arguments else 1
        per_page = int(arguments.get("per_page", 25)) if arguments else 25
        return [types.TextContent(type="text", text=json.dumps(client.get_views(page=page, per_page=per_page), indent=2))]

    return None