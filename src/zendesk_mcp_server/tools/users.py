import json
from typing import Any

import mcp.types as types

TOOLS = [
    types.Tool(
        name="list_users",
        description="List Zendesk users with optional role filter. Use role='agent' or role='admin' to list team members.",
        inputSchema={
            "type": "object",
            "properties": {
                "role": {"type": "string", "description": "Filter by role: agent, admin, or end-user"},
                "page": {"type": ["integer", "string"], "description": "Page number", "default": 1},
                "per_page": {"type": ["integer", "string"], "description": "Number of users per page (max 100)", "default": 25},
            },
            "required": [],
        },
    ),
]


def handle(name: str, arguments: dict[str, Any] | None, client) -> list[types.TextContent] | None:
    if name == "list_users":
        role = arguments.get("role") if arguments else None
        page = int(arguments.get("page", 1)) if arguments else 1
        per_page = int(arguments.get("per_page", 25)) if arguments else 25
        return [types.TextContent(type="text", text=json.dumps(client.get_users(role=role, page=page, per_page=per_page), indent=2))]

    return None
