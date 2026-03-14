import json
from typing import Any

import mcp.types as types

_FIELD_TYPE_ENUM = ["text", "textarea", "checkbox", "date", "integer", "decimal", "regexp", "tagger", "lookup"]

_CUSTOM_FIELD_OPTIONS_SCHEMA = {
    "type": "array",
    "description": "Options for dropdown (tagger) fields. Each item needs 'name' and 'value'.",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "string"},
        },
        "required": ["name", "value"],
    },
}

TOOLS = [
    # ── Ticket fields ─────────────────────────────────────────────────────────
    types.Tool(
        name="list_ticket_fields",
        description="List all ticket fields (system and custom) with their options",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    types.Tool(
        name="create_ticket_field",
        description="Create a new custom ticket field",
        inputSchema={
            "type": "object",
            "properties": {
                "type": {"type": "string", "description": "Field type", "enum": _FIELD_TYPE_ENUM},
                "title": {"type": "string", "description": "Display title of the field"},
                "description": {"type": "string", "description": "Optional description shown to agents"},
                "required": {"type": "boolean", "description": "Whether the field is required when submitting a ticket"},
                "active": {"type": "boolean", "description": "Whether the field is active (default true)"},
                "custom_field_options": _CUSTOM_FIELD_OPTIONS_SCHEMA,
            },
            "required": ["type", "title"],
        },
    ),
    types.Tool(
        name="update_ticket_field",
        description="Update an existing custom ticket field",
        inputSchema={
            "type": "object",
            "properties": {
                "field_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "ID of the ticket field to update"},
                "title": {"type": "string", "description": "New display title"},
                "description": {"type": "string", "description": "New description"},
                "required": {"type": "boolean", "description": "Whether the field is required"},
                "active": {"type": "boolean", "description": "Whether the field is active"},
                "custom_field_options": _CUSTOM_FIELD_OPTIONS_SCHEMA,
            },
            "required": ["field_id"],
        },
    ),
    # ── User fields ───────────────────────────────────────────────────────────
    types.Tool(
        name="list_user_fields",
        description="List all custom user fields with their options",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    types.Tool(
        name="create_user_field",
        description="Create a new custom user field",
        inputSchema={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Unique key for the field (snake_case, cannot be changed after creation)"},
                "type": {"type": "string", "description": "Field type", "enum": _FIELD_TYPE_ENUM},
                "title": {"type": "string", "description": "Display title of the field"},
                "description": {"type": "string", "description": "Optional description"},
                "active": {"type": "boolean", "description": "Whether the field is active"},
                "custom_field_options": _CUSTOM_FIELD_OPTIONS_SCHEMA,
            },
            "required": ["key", "type", "title"],
        },
    ),
    types.Tool(
        name="update_user_field",
        description="Update an existing custom user field",
        inputSchema={
            "type": "object",
            "properties": {
                "field_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "ID of the user field to update"},
                "title": {"type": "string", "description": "New display title"},
                "description": {"type": "string", "description": "New description"},
                "active": {"type": "boolean", "description": "Whether the field is active"},
                "custom_field_options": _CUSTOM_FIELD_OPTIONS_SCHEMA,
            },
            "required": ["field_id"],
        },
    ),
    # ── Organization fields ───────────────────────────────────────────────────
    types.Tool(
        name="list_organization_fields",
        description="List all custom organization fields with their options",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    types.Tool(
        name="create_organization_field",
        description="Create a new custom organization field",
        inputSchema={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Unique key for the field (snake_case, cannot be changed after creation)"},
                "type": {"type": "string", "description": "Field type", "enum": _FIELD_TYPE_ENUM},
                "title": {"type": "string", "description": "Display title of the field"},
                "description": {"type": "string", "description": "Optional description"},
                "active": {"type": "boolean", "description": "Whether the field is active"},
                "custom_field_options": _CUSTOM_FIELD_OPTIONS_SCHEMA,
            },
            "required": ["key", "type", "title"],
        },
    ),
    types.Tool(
        name="update_organization_field",
        description="Update an existing custom organization field",
        inputSchema={
            "type": "object",
            "properties": {
                "field_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "ID of the organization field to update"},
                "title": {"type": "string", "description": "New display title"},
                "description": {"type": "string", "description": "New description"},
                "active": {"type": "boolean", "description": "Whether the field is active"},
                "custom_field_options": _CUSTOM_FIELD_OPTIONS_SCHEMA,
            },
            "required": ["field_id"],
        },
    ),
]


def handle(name: str, arguments: dict[str, Any] | None, client) -> list[types.TextContent] | None:
    args = arguments or {}

    if name == "list_ticket_fields":
        return [types.TextContent(type="text", text=json.dumps(client.get_ticket_fields(), indent=2))]

    if name == "create_ticket_field":
        result = client.create_ticket_field(
            type=args["type"],
            title=args["title"],
            description=args.get("description"),
            required=args.get("required"),
            active=args.get("active"),
            custom_field_options=args.get("custom_field_options"),
        )
        return [types.TextContent(type="text", text=json.dumps({"message": "Ticket field created", "ticket_field": result}, indent=2))]

    if name == "update_ticket_field":
        result = client.update_ticket_field(
            field_id=int(args["field_id"]),
            title=args.get("title"),
            description=args.get("description"),
            required=args.get("required"),
            active=args.get("active"),
            custom_field_options=args.get("custom_field_options"),
        )
        return [types.TextContent(type="text", text=json.dumps({"message": "Ticket field updated", "ticket_field": result}, indent=2))]

    if name == "list_user_fields":
        return [types.TextContent(type="text", text=json.dumps(client.get_user_fields(), indent=2))]

    if name == "create_user_field":
        result = client.create_user_field(
            key=args["key"],
            type=args["type"],
            title=args["title"],
            description=args.get("description"),
            active=args.get("active"),
            custom_field_options=args.get("custom_field_options"),
        )
        return [types.TextContent(type="text", text=json.dumps({"message": "User field created", "user_field": result}, indent=2))]

    if name == "update_user_field":
        result = client.update_user_field(
            field_id=int(args["field_id"]),
            title=args.get("title"),
            description=args.get("description"),
            active=args.get("active"),
            custom_field_options=args.get("custom_field_options"),
        )
        return [types.TextContent(type="text", text=json.dumps({"message": "User field updated", "user_field": result}, indent=2))]

    if name == "list_organization_fields":
        return [types.TextContent(type="text", text=json.dumps(client.get_organization_fields(), indent=2))]

    if name == "create_organization_field":
        result = client.create_organization_field(
            key=args["key"],
            type=args["type"],
            title=args["title"],
            description=args.get("description"),
            active=args.get("active"),
            custom_field_options=args.get("custom_field_options"),
        )
        return [types.TextContent(type="text", text=json.dumps({"message": "Organization field created", "organization_field": result}, indent=2))]

    if name == "update_organization_field":
        result = client.update_organization_field(
            field_id=int(args["field_id"]),
            title=args.get("title"),
            description=args.get("description"),
            active=args.get("active"),
            custom_field_options=args.get("custom_field_options"),
        )
        return [types.TextContent(type="text", text=json.dumps({"message": "Organization field updated", "organization_field": result}, indent=2))]

    return None