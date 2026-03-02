# Zendesk MCP Server

![ci](https://github.com/reminia/zendesk-mcp-server/actions/workflows/ci.yml/badge.svg)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A Model Context Protocol server for Zendesk.

This server provides a comprehensive integration with Zendesk. It offers:

- Tools for retrieving and managing tickets, comments, views, users, fields, webhooks, and triggers
- Specialized prompts for ticket analysis and response drafting
- Full access to the Zendesk Help Center articles as a knowledge base

![demo](https://res.cloudinary.com/leecy-me/image/upload/v1736410626/open/zendesk_yunczu.gif)

## Authentication

The server uses an HTTP/SSE transport with a token-based authentication layer. Zendesk credentials are **never stored in environment variables or config files** — they are supplied at runtime by each client.

### Auth flow

1. **Obtain a session token** by posting your Zendesk credentials:

   ```bash
   curl -X POST http://localhost:8000/auth \
     -H "Content-Type: application/json" \
     -d '{"subdomain": "your-subdomain", "email": "you@example.com", "api_key": "your-api-token"}'
   # → {"token": "<uuid>"}
   ```

2. **Connect your MCP client** to the SSE endpoint, passing the token as a Bearer header:

   ```
   GET http://localhost:8000/sse
   Authorization: Bearer <token>
   ```

3. **Tool calls** are sent as normal MCP messages:

   ```
   POST http://localhost:8000/messages?session_id=<session-id>
   ```

Each session gets its own isolated `ZendeskClient`. Sessions are held in memory for the lifetime of the server process.

## Setup

### Local

```bash
uv sync
uv run zendesk
```

The server starts on `http://0.0.0.0:8000`.

### Docker

Build the image:

```bash
docker build -t zendesk-mcp-server .
```

Run it:

```bash
docker run --rm -p 8000:8000 zendesk-mcp-server
```

Then authenticate via `POST /auth` as shown above.

## Project Structure

```
src/zendesk_mcp_server/
├── server.py              # HTTP/SSE server, auth endpoint, session management
├── client/
│   ├── __init__.py        # Composes all mixins into ZendeskClient
│   ├── base.py            # Auth setup and shared HTTP helper
│   ├── tickets.py         # Ticket API methods
│   ├── views.py           # Views API methods
│   ├── users.py           # Users API methods
│   ├── fields.py          # Ticket/user/organization field methods
│   ├── knowledge_base.py  # Help Center article methods
│   ├── webhooks.py        # Webhook API methods
│   └── triggers.py        # Trigger API methods
└── tools/
    ├── __init__.py        # Tool registration and dispatch
    ├── tickets.py         # Ticket tool definitions and handlers
    ├── views.py           # Views tool definitions and handlers
    ├── users.py           # Users tool definitions and handlers
    ├── fields.py          # Fields tool definitions and handlers
    ├── webhooks.py        # Webhook tool definitions and handlers
    └── triggers.py        # Trigger tool definitions and handlers
```

To add a new domain, create a mixin in `client/` and a module in `tools/`, then register both in their respective `__init__.py`.

## Resources

### zendesk://knowledge-base

Returns all Help Center sections and their articles.

## Prompts

### analyze-ticket

Fetches ticket info and comments, then provides a summary, timeline, and key interaction points.

- Arguments: `ticket_id` (required)

### draft-ticket-response

Fetches ticket info, comments, and knowledge base to draft a professional reply ready to post.

- Arguments: `ticket_id` (required)

## Tools

### Tickets

#### get_tickets

Fetch tickets with pagination, optional view filter, and optional status filter.

- `page` (integer, optional, default 1)
- `per_page` (integer, optional, default 25, max 100)
- `sort_by` (string, optional): `created_at`, `updated_at`, `priority`, `status`
- `sort_order` (string, optional): `asc` or `desc`
- `view_id` (integer, optional): filter by view
- `status` (string, optional): `new`, `open`, `pending`, `hold`, `solved`, `closed`

#### get_ticket

Retrieve a single ticket by ID.

- `ticket_id` (integer, required)

#### create_ticket

Create a new ticket.

- `subject` (string, required)
- `description` (string, required)
- `requester_id` (integer, optional)
- `assignee_id` (integer, optional)
- `priority` (string, optional): `low`, `normal`, `high`, `urgent`
- `type` (string, optional): `problem`, `incident`, `question`, `task`
- `tags` (array[string], optional)
- `custom_fields` (array[object], optional)

#### update_ticket

Update fields on an existing ticket.

- `ticket_id` (integer, required)
- `subject` (string, optional)
- `status` (string, optional): `new`, `open`, `pending`, `on-hold`, `solved`, `closed`
- `priority` (string, optional): `low`, `normal`, `high`, `urgent`
- `type` (string, optional)
- `assignee_id` (integer, optional)
- `requester_id` (integer, optional)
- `tags` (array[string], optional)
- `custom_fields` (array[object], optional)
- `due_at` (string, optional): ISO8601 datetime

#### update_tickets_batch

Update multiple tickets in a single call.

- `tickets` (array[object], required): each item must have `id` plus any updatable fields

#### get_ticket_comments

Retrieve all comments for a ticket.

- `ticket_id` (integer, required)

#### create_ticket_comment

Add a comment to an existing ticket. **Content must be formatted as HTML** — use `<br>` for line breaks, `<p>` for paragraphs, `<b>` / `<i>` for emphasis, `<ul>` / `<li>` for lists, etc.

- `ticket_id` (integer, required)
- `comment` (string, required): HTML-formatted content
- `public` (boolean, optional, default true)

### Views

#### list_views

List all views with pagination.

- `page` (integer, optional, default 1)
- `per_page` (integer, optional, default 25, max 100)

### Users

#### list_users

List users with optional role filter.

- `role` (string, optional): `agent`, `admin`, `end-user`
- `page` (integer, optional, default 1)
- `per_page` (integer, optional, default 25, max 100)

### Fields

#### list_ticket_fields

List all ticket fields (system and custom) with their options.

#### create_ticket_field

Create a new custom ticket field.

- `type` (string, required): `text`, `textarea`, `checkbox`, `date`, `integer`, `decimal`, `regexp`, `tagger`, `lookup`
- `title` (string, required)
- `description` (string, optional)
- `required` (boolean, optional)
- `active` (boolean, optional)
- `custom_field_options` (array[object], optional): `[{"name": "Label", "value": "key"}]` for dropdown fields

#### update_ticket_field

Update an existing custom ticket field.

- `field_id` (integer, required)
- `title` (string, optional)
- `description` (string, optional)
- `required` (boolean, optional)
- `active` (boolean, optional)
- `custom_field_options` (array[object], optional)

#### list_user_fields

List all custom user fields with their options.

#### create_user_field

Create a new custom user field.

- `key` (string, required): unique snake_case identifier, cannot be changed after creation
- `type` (string, required): same options as ticket fields
- `title` (string, required)
- `description` (string, optional)
- `active` (boolean, optional)
- `custom_field_options` (array[object], optional)

#### update_user_field

Update an existing custom user field.

- `field_id` (integer, required)
- `title` (string, optional)
- `description` (string, optional)
- `active` (boolean, optional)
- `custom_field_options` (array[object], optional)

#### list_organization_fields

List all custom organization fields with their options.

#### create_organization_field

Create a new custom organization field.

- `key` (string, required): unique snake_case identifier, cannot be changed after creation
- `type` (string, required): same options as ticket fields
- `title` (string, required)
- `description` (string, optional)
- `active` (boolean, optional)
- `custom_field_options` (array[object], optional)

#### update_organization_field

Update an existing custom organization field.

- `field_id` (integer, required)
- `title` (string, optional)
- `description` (string, optional)
- `active` (boolean, optional)
- `custom_field_options` (array[object], optional)

### Webhooks

#### list_webhooks

List all webhooks with pagination.

- `page` (integer, optional, default 1)
- `per_page` (integer, optional, default 25, max 100)

#### create_webhook

Create a new webhook.

- `name` (string, required)
- `endpoint` (string, required): destination URL
- `http_method` (string, required): `GET`, `POST`, `PUT`, `PATCH`, or `DELETE` — must be `POST` to subscribe to events
- `request_format` (string, required): `json`, `xml`, or `form_encoded` — must be `json` to subscribe to events
- `status` (string, required): `active` or `inactive`
- `description` (string, optional)
- `subscriptions` (array[string], optional): e.g. `["conditional_ticket_events"]`
- `authentication` (object, optional)
- `custom_headers` (object, optional)

#### delete_webhook

Delete a webhook by ID.

- `webhook_id` (string, required)

### Triggers

#### list_triggers

List triggers with optional active/inactive filter and pagination.

- `active` (boolean, optional): `true` for active only, `false` for inactive only, omit for all
- `page` (integer, optional, default 1)
- `per_page` (integer, optional, default 25, max 100)

#### get_trigger

Fetch a single trigger by ID, including its full conditions and actions.

- `trigger_id` (integer, required)

#### create_trigger

Create a new trigger.

- `title` (string, required)
- `conditions` (object, required): `all` (AND) and/or `any` (OR) arrays; each condition has `field`, `operator`, `value`
- `actions` (array[object], required): each action has `field` and `value`
- `active` (boolean, optional, default true)
- `position` (integer, optional): execution order — lower value runs first

Example:
```json
{
  "title": "Escalate urgent tickets",
  "conditions": {
    "all": [{"field": "priority", "operator": "is", "value": "urgent"}]
  },
  "actions": [
    {"field": "status", "value": "open"},
    {"field": "assignee_id", "value": "12345"}
  ]
}
```

#### test_trigger

Fetch a trigger and a ticket side-by-side so you can verify whether the trigger conditions would match.

- `trigger_id` (integer, required)
- `ticket_id` (integer, required)