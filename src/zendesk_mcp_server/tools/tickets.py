import json
from typing import Any

from mcp.server import types

TOOLS = [
    types.Tool(
        name="get_ticket",
        description="Retrieve a Zendesk ticket by its ID",
        inputSchema={
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer", "description": "The ID of the ticket to retrieve"}
            },
            "required": ["ticket_id"],
        },
    ),
    types.Tool(
        name="get_tickets",
        description="Fetch the latest tickets with pagination support. Optionally filter by a specific view or status.",
        inputSchema={
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "Page number", "default": 1},
                "per_page": {"type": "integer", "description": "Number of tickets per page (max 100)", "default": 25},
                "sort_by": {"type": "string", "description": "Field to sort by (created_at, updated_at, priority, status)", "default": "created_at"},
                "sort_order": {"type": "string", "description": "Sort order (asc or desc)", "default": "desc"},
                "view_id": {"type": "integer", "description": "Optional view ID to filter tickets by a specific view"},
                "status": {"type": "string", "description": "Optional status filter (new, open, pending, hold, solved, closed)"},
            },
            "required": [],
        },
    ),
    types.Tool(
        name="create_ticket",
        description="Create a new Zendesk ticket",
        inputSchema={
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Ticket subject"},
                "description": {"type": "string", "description": "Ticket description"},
                "requester_id": {"type": "integer"},
                "assignee_id": {"type": "integer"},
                "priority": {"type": "string", "description": "low, normal, high, urgent"},
                "type": {"type": "string", "description": "problem, incident, question, task"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "custom_fields": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["subject", "description"],
        },
    ),
    types.Tool(
        name="update_ticket",
        description="Update fields on an existing Zendesk ticket (e.g., status, priority, assignee_id)",
        inputSchema={
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer", "description": "The ID of the ticket to update"},
                "subject": {"type": "string"},
                "status": {"type": "string", "description": "new, open, pending, on-hold, solved, closed"},
                "priority": {"type": "string", "description": "low, normal, high, urgent"},
                "type": {"type": "string"},
                "assignee_id": {"type": "integer"},
                "requester_id": {"type": "integer"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "custom_fields": {"type": "array", "items": {"type": "object"}},
                "due_at": {"type": "string", "description": "ISO8601 datetime"},
            },
            "required": ["ticket_id"],
        },
    ),
    types.Tool(
        name="update_tickets_batch",
        description="Update multiple Zendesk tickets in a single API call. Efficient for bulk operations like closing multiple tickets or reassigning tickets.",
        inputSchema={
            "type": "object",
            "properties": {
                "tickets": {
                    "type": "array",
                    "description": "Array of ticket objects to update. Each must have 'id' and fields to update.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer", "description": "The ticket ID (required)"},
                            "subject": {"type": "string"},
                            "status": {"type": "string", "description": "new, open, pending, on-hold, solved, closed"},
                            "priority": {"type": "string", "description": "low, normal, high, urgent"},
                            "type": {"type": "string"},
                            "assignee_id": {"type": "integer"},
                            "requester_id": {"type": "integer"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "custom_fields": {"type": "array", "items": {"type": "object"}},
                            "due_at": {"type": "string", "description": "ISO8601 datetime"},
                        },
                        "required": ["id"],
                    },
                }
            },
            "required": ["tickets"],
        },
    ),
    types.Tool(
        name="get_ticket_comments",
        description="Retrieve all comments for a Zendesk ticket by its ID",
        inputSchema={
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer", "description": "The ID of the ticket to get comments for"}
            },
            "required": ["ticket_id"],
        },
    ),
    types.Tool(
        name="create_ticket_comment",
        description="Create a new comment on an existing Zendesk ticket",
        inputSchema={
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer", "description": "The ID of the ticket to comment on"},
                "comment": {
                    "type": "string",
                    "description": (
                        "The comment content to add. Must be formatted as HTML. "
                        "Use HTML tags for formatting: <br> for line breaks, <p> for paragraphs, "
                        "<b> for bold, <i> for italic, <ul>/<li> for lists, etc. "
                        "Example: 'Hello,<br>Thank you for reaching out.<br><br>Best regards'"
                    ),
                },
                "public": {"type": "boolean", "description": "Whether the comment should be public", "default": True},
            },
            "required": ["ticket_id", "comment"],
        },
    ),
]


def handle(name: str, arguments: dict[str, Any] | None, client) -> list[types.TextContent] | None:
    if name == "get_ticket":
        if not arguments:
            raise ValueError("Missing arguments")
        return [types.TextContent(type="text", text=json.dumps(client.get_ticket(arguments["ticket_id"])))]

    if name == "get_tickets":
        page = arguments.get("page", 1) if arguments else 1
        per_page = arguments.get("per_page", 25) if arguments else 25
        sort_by = arguments.get("sort_by", "created_at") if arguments else "created_at"
        sort_order = arguments.get("sort_order", "desc") if arguments else "desc"
        view_id = arguments.get("view_id") if arguments else None
        status = arguments.get("status") if arguments else None
        result = client.get_tickets(page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order, view_id=view_id, status=status)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    if name == "create_ticket":
        if not arguments:
            raise ValueError("Missing arguments")
        created = client.create_ticket(
            subject=arguments.get("subject"),
            description=arguments.get("description"),
            requester_id=arguments.get("requester_id"),
            assignee_id=arguments.get("assignee_id"),
            priority=arguments.get("priority"),
            type=arguments.get("type"),
            tags=arguments.get("tags"),
            custom_fields=arguments.get("custom_fields"),
        )
        return [types.TextContent(type="text", text=json.dumps({"message": "Ticket created successfully", "ticket": created}, indent=2))]

    if name == "update_ticket":
        if not arguments:
            raise ValueError("Missing arguments")
        ticket_id = arguments.get("ticket_id")
        if ticket_id is None:
            raise ValueError("ticket_id is required")
        update_fields = {k: v for k, v in arguments.items() if k != "ticket_id"}
        updated = client.update_ticket(ticket_id=int(ticket_id), **update_fields)
        return [types.TextContent(type="text", text=json.dumps({"message": "Ticket updated successfully", "ticket": updated}, indent=2))]

    if name == "update_tickets_batch":
        if not arguments:
            raise ValueError("Missing arguments")
        tickets = arguments.get("tickets")
        if not tickets:
            raise ValueError("tickets array is required")
        result = client.update_tickets_batch(tickets=tickets)
        return [types.TextContent(type="text", text=json.dumps({"message": f"Batch update initiated for {result['tickets_count']} tickets", "result": result}, indent=2))]

    if name == "get_ticket_comments":
        if not arguments:
            raise ValueError("Missing arguments")
        comments = client.get_ticket_comments(arguments["ticket_id"])
        return [types.TextContent(type="text", text=json.dumps(comments))]

    if name == "create_ticket_comment":
        if not arguments:
            raise ValueError("Missing arguments")
        result = client.post_comment(
            ticket_id=arguments["ticket_id"],
            comment=arguments["comment"],
            public=arguments.get("public", True),
        )
        return [types.TextContent(type="text", text=f"Comment created successfully: {result}")]

    return None