import json
from typing import Any

from mcp.server import types

TOOLS = [
    types.Tool(
        name="list_webhooks",
        description="List all Zendesk webhooks with pagination",
        inputSchema={
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "Page number", "default": 1},
                "per_page": {"type": "integer", "description": "Number of webhooks per page (max 100)", "default": 25},
            },
            "required": [],
        },
    ),
    types.Tool(
        name="create_webhook",
        description="Create a new Zendesk webhook that notifies a destination URL when events occur",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Webhook name"},
                "endpoint": {"type": "string", "description": "Destination URL that the webhook notifies when Zendesk events occur"},
                "http_method": {
                    "type": "string",
                    "description": "HTTP method used for the webhook request. Must be POST to subscribe to events.",
                    "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                },
                "request_format": {
                    "type": "string",
                    "description": "Format of the outgoing request body. Must be json to subscribe to Zendesk events.",
                    "enum": ["json", "xml", "form_encoded"],
                },
                "status": {"type": "string", "description": "Webhook status", "enum": ["active", "inactive"]},
                "description": {"type": "string", "description": "Optional webhook description"},
                "subscriptions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of Zendesk event types to subscribe to (e.g. ['conditional_ticket_events'])",
                },
                "authentication": {"type": "object", "description": "Optional authentication credentials for the webhook requests"},
                "custom_headers": {
                    "type": "object",
                    "description": "Optional additional non-credential headers to include in webhook requests",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": ["name", "endpoint", "http_method", "request_format", "status"],
        },
    ),
    types.Tool(
        name="delete_webhook",
        description="Delete a Zendesk webhook by its ID",
        inputSchema={
            "type": "object",
            "properties": {
                "webhook_id": {"type": "string", "description": "The ID of the webhook to delete"}
            },
            "required": ["webhook_id"],
        },
    ),
]


def handle(name: str, arguments: dict[str, Any] | None, client) -> list[types.TextContent] | None:
    if name == "list_webhooks":
        page = arguments.get("page", 1) if arguments else 1
        per_page = arguments.get("per_page", 25) if arguments else 25
        return [types.TextContent(type="text", text=json.dumps(client.list_webhooks(page=page, per_page=per_page), indent=2))]

    if name == "create_webhook":
        if not arguments:
            raise ValueError("Missing arguments")
        webhook = client.create_webhook(
            name=arguments["name"],
            endpoint=arguments["endpoint"],
            http_method=arguments["http_method"],
            request_format=arguments["request_format"],
            status=arguments["status"],
            description=arguments.get("description"),
            subscriptions=arguments.get("subscriptions"),
            authentication=arguments.get("authentication"),
            custom_headers=arguments.get("custom_headers"),
        )
        return [types.TextContent(type="text", text=json.dumps({"message": "Webhook created successfully", "webhook": webhook}, indent=2))]

    if name == "delete_webhook":
        if not arguments:
            raise ValueError("Missing arguments")
        client.delete_webhook(webhook_id=arguments["webhook_id"])
        return [types.TextContent(type="text", text=json.dumps({"message": f"Webhook {arguments['webhook_id']} deleted successfully"}, indent=2))]

    return None
