from typing import Any, Dict, List


class WebhooksMixin:
    def list_webhooks(self, page: int = 1, per_page: int = 25) -> Dict[str, Any]:
        try:
            per_page = min(per_page, 100)
            data = self._request("webhooks", params={"page[size]": str(per_page)})
            webhook_list = [
                {
                    "id": w.get("id"),
                    "name": w.get("name"),
                    "endpoint": w.get("endpoint"),
                    "http_method": w.get("http_method"),
                    "request_format": w.get("request_format"),
                    "status": w.get("status"),
                    "description": w.get("description"),
                    "subscriptions": w.get("subscriptions"),
                    "created_at": w.get("created_at"),
                    "updated_at": w.get("updated_at"),
                }
                for w in data.get("webhooks", [])
            ]
            meta = data.get("meta", {})
            return {
                "webhooks": webhook_list,
                "count": len(webhook_list),
                "has_more": meta.get("has_more", False),
            }
        except Exception as e:
            raise Exception(f"Failed to list webhooks: {str(e)}")

    def create_webhook(
        self,
        name: str,
        endpoint: str,
        http_method: str,
        request_format: str,
        status: str,
        description: str | None = None,
        subscriptions: List[str] | None = None,
        authentication: Dict[str, Any] | None = None,
        custom_headers: Dict[str, str] | None = None,
    ) -> Dict[str, Any]:
        try:
            webhook: Dict[str, Any] = {
                "name": name,
                "endpoint": endpoint,
                "http_method": http_method,
                "request_format": request_format,
                "status": status,
            }
            if description is not None:
                webhook["description"] = description
            if subscriptions is not None:
                webhook["subscriptions"] = subscriptions
            if authentication is not None:
                webhook["authentication"] = authentication
            if custom_headers is not None:
                webhook["custom_headers"] = custom_headers

            data = self._request("webhooks", method="POST", body={"webhook": webhook})
            w = data.get("webhook", {})
            return {
                "id": w.get("id"),
                "name": w.get("name"),
                "endpoint": w.get("endpoint"),
                "http_method": w.get("http_method"),
                "request_format": w.get("request_format"),
                "status": w.get("status"),
                "description": w.get("description"),
                "subscriptions": w.get("subscriptions"),
                "created_at": w.get("created_at"),
                "created_by": w.get("created_by"),
                "updated_at": w.get("updated_at"),
            }
        except Exception as e:
            raise Exception(f"Failed to create webhook: {str(e)}")

    def delete_webhook(self, webhook_id: str) -> None:
        try:
            self._request(f"webhooks/{webhook_id}", method="DELETE")
        except Exception as e:
            raise Exception(f"Failed to delete webhook {webhook_id}: {str(e)}")