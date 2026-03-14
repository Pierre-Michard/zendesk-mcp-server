import json
from typing import Any

import mcp.types as types

TOOLS = [
    types.Tool(
        name="list_triggers",
        description="List Zendesk triggers with optional filtering by active status",
        inputSchema={
            "type": "object",
            "properties": {
                "active": {"type": "boolean", "description": "Filter by active (true) or inactive (false) triggers. Omit to return all."},
                "page": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Page number", "default": 1},
                "per_page": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Number of triggers per page (max 100)", "default": 25},
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
                "trigger_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "The ID of the trigger to retrieve"},
            },
            "required": ["trigger_id"],
        },
    ),
    types.Tool(
        name="create_trigger",
        description="Create a new Zendesk trigger with conditions and actions",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Title of the trigger"},
                "conditions": {
                    "type": "object",
                    "description": (
                        "Conditions that must be met for the trigger to fire. "
                        "Use 'all' for AND logic and 'any' for OR logic. "
                        "Each condition has 'field', 'operator', and 'value'. "
                        "Example: {\"all\": [{\"field\": \"status\", \"operator\": \"is\", \"value\": \"new\"}]}"
                    ),
                    "properties": {
                        "all": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "field": {"type": "string"},
                                    "operator": {"type": "string"},
                                    "value": {"type": "string"},
                                },
                                "required": ["field", "operator", "value"],
                            },
                        },
                        "any": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "field": {"type": "string"},
                                    "operator": {"type": "string"},
                                    "value": {"type": "string"},
                                },
                                "required": ["field", "operator", "value"],
                            },
                        },
                    },
                },
                "actions": {
                    "type": "array",
                    "description": (
                        "Actions to perform when the trigger fires. "
                        "Each action has a 'field' and 'value'. "
                        "Example: [{\"field\": \"status\", \"value\": \"pending\"}]"
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "value": {},
                        },
                        "required": ["field", "value"],
                    },
                },
                "active": {"type": "boolean", "description": "Whether the trigger is active (default true)"},
                "position": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Position of the trigger in the list (lower runs first)"},
            },
            "required": ["title", "conditions", "actions"],
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
                "trigger_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "The ID of the trigger to test"},
                "ticket_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "The ID of the ticket to test against"},
            },
            "required": ["trigger_id", "ticket_id"],
        },
    ),
]


def handle(name: str, arguments: dict[str, Any] | None, client) -> list[types.TextContent] | None:
    if name == "list_triggers":
        active = arguments.get("active") if arguments else None
        page = int(arguments.get("page", 1)) if arguments else 1
        per_page = int(arguments.get("per_page", 25)) if arguments else 25
        return [types.TextContent(type="text", text=json.dumps(client.list_triggers(active=active, page=page, per_page=per_page), indent=2))]

    if name == "get_trigger":
        if not arguments:
            raise ValueError("Missing arguments")
        return [types.TextContent(type="text", text=json.dumps(client.get_trigger(trigger_id=int(arguments["trigger_id"])), indent=2))]

    if name == "create_trigger":
        if not arguments:
            raise ValueError("Missing arguments")
        result = client.create_trigger(
            title=arguments["title"],
            conditions=arguments["conditions"],
            actions=arguments["actions"],
            active=arguments.get("active"),
            position=int(arguments["position"]) if arguments.get("position") is not None else None,
        )
        return [types.TextContent(type="text", text=json.dumps({"message": "Trigger created successfully", "trigger": result}, indent=2))]

    if name == "test_trigger":
        if not arguments:
            raise ValueError("Missing arguments")
        result = client.test_trigger(trigger_id=int(arguments["trigger_id"]), ticket_id=int(arguments["ticket_id"]))
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    return None