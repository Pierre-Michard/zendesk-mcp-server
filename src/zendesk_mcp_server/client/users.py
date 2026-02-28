from typing import Any, Dict


class UsersMixin:
    def get_users(
        self, role: str | None = None, page: int = 1, per_page: int = 25
    ) -> Dict[str, Any]:
        try:
            per_page = min(per_page, 100)
            params: Dict[str, str] = {"page": str(page), "per_page": str(per_page)}
            if role:
                params["role"] = role
            data = self._request("users.json", params=params)
            user_list = [
                {
                    "id": u.get("id"),
                    "name": u.get("name"),
                    "email": u.get("email"),
                    "role": u.get("role"),
                    "active": u.get("active"),
                    "created_at": u.get("created_at"),
                    "updated_at": u.get("updated_at"),
                }
                for u in data.get("users", [])
            ]
            return {
                "users": user_list,
                "page": page,
                "per_page": per_page,
                "count": len(user_list),
                "role_filter": role,
                "has_more": data.get("next_page") is not None,
                "next_page": page + 1 if data.get("next_page") else None,
                "previous_page": page - 1 if data.get("previous_page") and page > 1 else None,
            }
        except Exception as e:
            raise Exception(f"Failed to get users: {str(e)}")