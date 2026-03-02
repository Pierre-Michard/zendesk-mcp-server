import json
import logging
from contextvars import ContextVar
from typing import Any, Dict

import uvicorn
from mcp.server import InitializationOptions, NotificationOptions, Server, types
from mcp.server.sse import SseServerTransport
from pydantic import AnyUrl
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from zendesk_mcp_server.client import ZendeskClient
from zendesk_mcp_server.tools import ALL_TOOLS, dispatch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("zendesk-mcp-server")
logger.info("zendesk mcp server started")

# Per-session client, set in the SSE handler and inherited by all tool call coroutines
_current_client: ContextVar[ZendeskClient] = ContextVar("current_client")

TICKET_ANALYSIS_TEMPLATE = """
You are a helpful Zendesk support analyst. You've been asked to analyze ticket #{ticket_id}.

Please fetch the ticket info and comments to analyze it and provide:
1. A summary of the issue
2. The current status and timeline
3. Key points of interaction

Remember to be professional and focus on actionable insights.
"""

COMMENT_DRAFT_TEMPLATE = """
You are a helpful Zendesk support agent. You need to draft a response to ticket #{ticket_id}.

Please fetch the ticket info, comments and knowledge base to draft a professional and helpful response that:
1. Acknowledges the customer's concern
2. Addresses the specific issues raised
3. Provides clear next steps or ask for specific details need to proceed
4. Maintains a friendly and professional tone
5. Ask for confirmation before commenting on the ticket

The response should be formatted well and ready to be posted as a comment.
"""

server = Server("Zendesk Server")


@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="analyze-ticket",
            description="Analyze a Zendesk ticket and provide insights",
            arguments=[
                types.PromptArgument(name="ticket_id", description="The ID of the ticket to analyze", required=True)
            ],
        ),
        types.Prompt(
            name="draft-ticket-response",
            description="Draft a professional response to a Zendesk ticket",
            arguments=[
                types.PromptArgument(name="ticket_id", description="The ID of the ticket to respond to", required=True)
            ],
        ),
    ]


@server.get_prompt()
async def handle_get_prompt(name: str, arguments: Dict[str, str] | None) -> types.GetPromptResult:
    if not arguments or "ticket_id" not in arguments:
        raise ValueError("Missing required argument: ticket_id")
    ticket_id = int(arguments["ticket_id"])
    try:
        if name == "analyze-ticket":
            prompt = TICKET_ANALYSIS_TEMPLATE.format(ticket_id=ticket_id)
            description = f"Analysis prompt for ticket #{ticket_id}"
        elif name == "draft-ticket-response":
            prompt = COMMENT_DRAFT_TEMPLATE.format(ticket_id=ticket_id)
            description = f"Response draft prompt for ticket #{ticket_id}"
        else:
            raise ValueError(f"Unknown prompt: {name}")
        return types.GetPromptResult(
            description=description,
            messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=prompt.strip()))],
        )
    except Exception as e:
        logger.error(f"Error generating prompt: {e}")
        raise


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return ALL_TOOLS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    try:
        client = _current_client.get()
        return dispatch(name, arguments, client)
    except LookupError:
        return [types.TextContent(type="text", text="Error: no authenticated session found")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri=AnyUrl("zendesk://knowledge-base"),
            name="Zendesk Knowledge Base",
            description="Access to Zendesk Help Center articles and sections",
            mimeType="application/json",
        )
    ]


@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    if uri.scheme != "zendesk":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")
    path = str(uri).replace("zendesk://", "")
    if path != "knowledge-base":
        raise ValueError(f"Unknown resource path: {path}")
    try:
        client = _current_client.get()
        kb_data = client.get_all_articles()
        return json.dumps(
            {
                "knowledge_base": kb_data,
                "metadata": {
                    "sections": len(kb_data),
                    "total_articles": sum(len(s["articles"]) for s in kb_data.values()),
                },
            },
            indent=2,
        )
    except Exception as e:
        logger.error(f"Error fetching knowledge base: {e}")
        raise


# ── HTTP endpoints ────────────────────────────────────────────────────────────

sse_transport = SseServerTransport("/messages")


async def sse_endpoint(request: Request) -> Response:
    subdomain = request.headers.get("X-Zendesk-Subdomain")
    email = request.headers.get("X-Zendesk-Email")
    api_key = request.headers.get("X-Zendesk-Token")

    if not all([subdomain, email, api_key]):
        return Response(
            "Unauthorized: X-Zendesk-Subdomain, X-Zendesk-Email, and X-Zendesk-Token headers are required",
            status_code=401,
        )

    try:
        client = ZendeskClient(subdomain=subdomain, email=email, token=api_key)
        client.test_connection()
    except Exception as e:
        return Response(f"Unauthorized: {str(e)}", status_code=401)

    logger.info(f"New session established for subdomain={subdomain} email={email}")
    _current_client.set(client)

    async with sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
        await server.run(
            streams[0],
            streams[1],
            InitializationOptions(
                server_name="Zendesk",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


async def messages_endpoint(request: Request) -> Response:
    await sse_transport.handle_post_message(request.scope, request.receive, request._send)


starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=sse_endpoint),
        Route("/messages", endpoint=messages_endpoint, methods=["POST"]),
    ]
)


def main():
    uvicorn.run(starlette_app, host="0.0.0.0", port=8000)