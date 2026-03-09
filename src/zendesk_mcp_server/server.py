import base64
import hashlib
import json
import logging
import secrets
import time
from contextvars import ContextVar
from typing import Any, Dict
from urllib.parse import urlencode

import uvicorn
import mcp.types as types
from mcp.server import InitializationOptions, NotificationOptions, Server
from mcp.server.sse import SseServerTransport
from pydantic import AnyUrl
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
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

# Temporary OAuth auth codes: code → {subdomain, email, api_key, redirect_uri, code_challenge, expires_at}
_auth_codes: dict[str, dict] = {}
_AUTH_CODE_TTL = 300  # seconds


# ── Token helpers (self-contained, survive server restarts) ───────────────────

def _make_token(subdomain: str, email: str, api_key: str) -> str:
    payload = json.dumps({"subdomain": subdomain, "email": email, "api_key": api_key})
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def _decode_token(token: str) -> dict | None:
    try:
        padded = token + "=" * (4 - len(token) % 4)
        return json.loads(base64.urlsafe_b64decode(padded))
    except Exception:
        return None


def _verify_pkce(code_verifier: str, code_challenge: str) -> bool:
    digest = hashlib.sha256(code_verifier.encode()).digest()
    computed = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return secrets.compare_digest(computed, code_challenge)


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


# ── OAuth 2.0 discovery + authorization endpoints ────────────────────────────

def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


async def oauth_protected_resource(request: Request) -> JSONResponse:
    base = _base_url(request)
    return JSONResponse({
        "resource": base,
        "authorization_servers": [base],
    })


async def oauth_authorization_server(request: Request) -> JSONResponse:
    base = _base_url(request)
    return JSONResponse({
        "issuer": base,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "registration_endpoint": f"{base}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
    })


async def register_endpoint(request: Request) -> JSONResponse:
    """Dynamic client registration — accept any client, return a static ID."""
    return JSONResponse({
        "client_id": "mcp-client",
        "client_secret": "not-used",
        "redirect_uris": [],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
    }, status_code=201)


_AUTHORIZE_FORM = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Zendesk MCP — Sign in</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 420px; margin: 80px auto; padding: 0 16px; }}
    h2 {{ margin-bottom: 24px; }}
    label {{ display: block; margin-bottom: 16px; font-size: 14px; color: #555; }}
    input {{ display: block; width: 100%; padding: 8px; margin-top: 4px; border: 1px solid #ccc;
             border-radius: 4px; font-size: 15px; box-sizing: border-box; }}
    button {{ width: 100%; padding: 10px; background: #1f73b7; color: #fff; border: none;
              border-radius: 4px; font-size: 16px; cursor: pointer; margin-top: 8px; }}
    .error {{ color: #c0392b; margin-bottom: 16px; font-size: 14px; }}
  </style>
</head>
<body>
  <h2>Zendesk MCP Server</h2>
  {error}
  <form method="post">
    <input type="hidden" name="client_id"      value="{client_id}">
    <input type="hidden" name="redirect_uri"   value="{redirect_uri}">
    <input type="hidden" name="state"          value="{state}">
    <input type="hidden" name="code_challenge" value="{code_challenge}">
    <label>Subdomain
      <input name="subdomain" placeholder="yourcompany" required autofocus>
    </label>
    <label>Email
      <input name="email" type="email" required>
    </label>
    <label>API Token
      <input name="api_key" type="password" required>
    </label>
    <button type="submit">Connect</button>
  </form>
</body>
</html>"""


async def authorize_endpoint(request: Request) -> Response:
    if request.method == "GET":
        params = request.query_params
        return HTMLResponse(_AUTHORIZE_FORM.format(
            error="",
            client_id=params.get("client_id", ""),
            redirect_uri=params.get("redirect_uri", ""),
            state=params.get("state", ""),
            code_challenge=params.get("code_challenge", ""),
        ))

    # POST — validate credentials and issue auth code
    form = await request.form()
    subdomain    = str(form.get("subdomain", "")).strip()
    email        = str(form.get("email", "")).strip()
    api_key      = str(form.get("api_key", "")).strip()
    redirect_uri = str(form.get("redirect_uri", "")).strip()
    state        = str(form.get("state", "")).strip()
    code_challenge = str(form.get("code_challenge", "")).strip()
    client_id    = str(form.get("client_id", "")).strip()

    try:
        client = ZendeskClient(subdomain=subdomain, email=email, token=api_key)
        client.test_connection()
    except Exception as e:
        return HTMLResponse(_AUTHORIZE_FORM.format(
            error=f'<p class="error">Authentication failed: {e}</p>',
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=state,
            code_challenge=code_challenge,
        ), status_code=200)

    code = secrets.token_urlsafe(32)
    _auth_codes[code] = {
        "subdomain": subdomain,
        "email": email,
        "api_key": api_key,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "expires_at": time.time() + _AUTH_CODE_TTL,
    }
    logger.info(f"Auth code issued for subdomain={subdomain} email={email}")

    qs = urlencode({"code": code, "state": state})
    return RedirectResponse(f"{redirect_uri}?{qs}", status_code=302)


async def token_endpoint(request: Request) -> JSONResponse:
    form = await request.form()
    grant_type    = str(form.get("grant_type", ""))
    code          = str(form.get("code", ""))
    code_verifier = str(form.get("code_verifier", ""))
    redirect_uri  = str(form.get("redirect_uri", ""))

    if grant_type != "authorization_code":
        return JSONResponse({"error": "unsupported_grant_type"}, status_code=400)

    entry = _auth_codes.pop(code, None)
    if not entry:
        return JSONResponse({"error": "invalid_grant", "error_description": "Unknown or expired code"}, status_code=400)

    if time.time() > entry["expires_at"]:
        return JSONResponse({"error": "invalid_grant", "error_description": "Code expired"}, status_code=400)

    if entry["redirect_uri"] and entry["redirect_uri"] != redirect_uri:
        return JSONResponse({"error": "invalid_grant", "error_description": "redirect_uri mismatch"}, status_code=400)

    if entry["code_challenge"] and code_verifier:
        if not _verify_pkce(code_verifier, entry["code_challenge"]):
            return JSONResponse({"error": "invalid_grant", "error_description": "PKCE verification failed"}, status_code=400)

    token = _make_token(entry["subdomain"], entry["email"], entry["api_key"])
    logger.info(f"Token issued for subdomain={entry['subdomain']} email={entry['email']}")
    return JSONResponse({
        "access_token": token,
        "token_type": "bearer",
    })


# ── Legacy /auth endpoint (used by setup-mcp.sh) ─────────────────────────────

async def auth_endpoint(request: Request) -> Response:
    """POST /auth  { subdomain, email, api_key } → { token }"""
    try:
        body = await request.json()
    except Exception:
        return Response("Bad Request: expected JSON body", status_code=400)

    subdomain = body.get("subdomain")
    email     = body.get("email")
    api_key   = body.get("api_key")

    if not all([subdomain, email, api_key]):
        return Response("Bad Request: subdomain, email, and api_key are required", status_code=400)

    try:
        client = ZendeskClient(subdomain=subdomain, email=email, token=api_key)
        client.test_connection()
    except Exception as e:
        return Response(f"Unauthorized: {str(e)}", status_code=401)

    token = _make_token(subdomain, email, api_key)
    logger.info(f"Token issued via /auth for subdomain={subdomain} email={email}")
    return Response(json.dumps({"token": token}), media_type="application/json")


# ── SSE transport ─────────────────────────────────────────────────────────────

sse_transport = SseServerTransport("/messages")


async def sse_endpoint(request: Request) -> Response:
    # Accept token from query param or Authorization: Bearer header
    token = request.query_params.get("token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    creds = _decode_token(token) if token else None
    if not creds:
        base = _base_url(request)
        return Response(
            "Unauthorized: authenticate via /mcp in Claude Code or run setup-mcp.sh",
            status_code=401,
            headers={"WWW-Authenticate": f'Bearer resource_metadata="{base}/.well-known/oauth-protected-resource"'},
        )

    client = ZendeskClient(subdomain=creds["subdomain"], email=creds["email"], token=creds["api_key"])
    logger.info(f"SSE session started for subdomain={creds['subdomain']} email={creds['email']}")
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


class _SentResponse:
    """No-op response returned to Starlette after handle_post_message already sent the reply."""
    async def __call__(self, scope, receive, send) -> None:
        pass


async def messages_endpoint(request: Request) -> Response:
    await sse_transport.handle_post_message(request.scope, request.receive, request._send)
    return _SentResponse()


starlette_app = Starlette(
    routes=[
        # OAuth 2.0 discovery
        Route("/.well-known/oauth-protected-resource", endpoint=oauth_protected_resource),
        Route("/.well-known/oauth-authorization-server", endpoint=oauth_authorization_server),
        # OAuth 2.0 flow
        Route("/register",  endpoint=register_endpoint,  methods=["POST"]),
        Route("/authorize", endpoint=authorize_endpoint, methods=["GET", "POST"]),
        Route("/token",     endpoint=token_endpoint,     methods=["POST"]),
        # Legacy auth (setup-mcp.sh)
        Route("/auth",     endpoint=auth_endpoint,     methods=["POST"]),
        # MCP transport
        Route("/sse",      endpoint=sse_endpoint),
        Route("/messages", endpoint=messages_endpoint, methods=["POST"]),
    ]
)


def main():
    uvicorn.run(starlette_app, host="0.0.0.0", port=8000)