import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict

from zenpy import Zenpy


class ZendeskBaseClient:
    def __init__(self, subdomain: str, email: str, token: str):
        self.client = Zenpy(subdomain=subdomain, email=email, token=token)
        self.subdomain = subdomain
        self.email = email
        self.token = token
        self.base_url = f"https://{subdomain}.zendesk.com/api/v2"
        credentials = f"{email}/token:{token}"
        encoded = base64.b64encode(credentials.encode()).decode("ascii")
        self.auth_header = f"Basic {encoded}"

    def _request(
        self,
        path: str,
        method: str = "GET",
        params: Dict[str, str] | None = None,
        body: Any = None,
    ) -> Any:
        """Low-level HTTP helper. Returns parsed JSON or None (for 204 No Content)."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", self.auth_header)
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req) as response:
                raw = response.read()
                return json.loads(raw.decode()) if raw else None
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else "No response body"
            raise Exception(f"HTTP {e.code} {e.reason} [{method} {path}]: {error_body}")

    def test_connection(self) -> None:
        """Validate credentials by making a lightweight API call. Raises on failure."""
        self._request("users/me.json")