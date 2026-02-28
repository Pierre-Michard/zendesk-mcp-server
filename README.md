# Zendesk MCP Server

![ci](https://github.com/reminia/zendesk-mcp-server/actions/workflows/ci.yml/badge.svg)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A Model Context Protocol server for Zendesk.

This server provides a comprehensive integration with Zendesk. It offers:

- Tools for retrieving and managing tickets, comments, views, users, fields, and webhooks
- Specialized prompts for ticket analysis and response drafting
- Full access to the Zendesk Help Center articles as a knowledge base

![demo](https://res.cloudinary.com/leecy-me/image/upload/v1736410626/open/zendesk_yunczu.gif)

## Setup

- Build: `uv venv && uv pip install -e .` or `uv sync` in short.
- Set up Zendesk credentials in a `.env` file, refer to [.env.example](.env.example).
- Configure in Claude Desktop:

```json
{
  "mcpServers": {
    "zendesk": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/zendesk-mcp-server",
        "run",
        "zendesk"
      ]
    }
  }
}
```

### Docker

You can containerize the server if you prefer an isolated runtime:

1. Copy `.env.example` to `.env` and fill in your Zendesk credentials. Keep this file outside version control.
2. Build the image:

   ```bash
   docker build -t zendesk-mcp-server .
   ```

3. Run the server, providing the environment file:

   ```bash
   docker run --rm --env-file /path/to/.env zendesk-mcp-server
   ```

   Add `-i` when wiring the container to MCP clients over STDIN/STDOUT (Claude Code uses this mode).

The image installs dependencies from `requirements.lock`, drops privileges to a non-root user, and expects configuration exclusively via environment variables.

#### Claude MCP Integration

To use the Dockerized server from Claude Code/Desktop, add an entry to `settings.json`:

```json
{
  "mcpServers": {
    "zendesk": {
      "command": "/usr/local/bin/docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env-file",
        "/path/to/zendesk-mcp-server/.env",
        "zendesk-mcp-server"
      ]
    }
  }
}
```

Adjust the paths to match your environment. After saving the file, restart Claude for the new MCP server to be detected.

## Project Structure

```
src/zendesk_mcp_server/
├── server.py              # MCP server wiring (prompts, resources, tool dispatch)
├── client/
│   ├── base.py            # Auth setup and shared HTTP helper
│   ├── tickets.py         # Ticket API methods
│   ├── views.py           # Views API methods
│   ├── users.py           # Users API methods
│   ├── fields.py          # Ticket/user/organization field methods
│   ├── knowledge_base.py  # Help Center article methods
│   └── webhooks.py        # Webhook API methods
└── tools/
    ├── tickets.py         # Ticket tool definitions and handlers
    ├── views.py           # Views tool definitions and handlers
    ├── users.py           # Users tool definitions and handlers
    ├── fields.py          # Fields tool definitions and handlers
    └── webhooks.py        # Webhook tool definitions and handlers
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

Add a comment to an existing ticket.

- `ticket_id` (integer, required)
- `comment` (string, required)
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

#### list_user_fields

List all custom user fields with their options.

#### list_organization_fields

List all custom organization fields with their options.

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
