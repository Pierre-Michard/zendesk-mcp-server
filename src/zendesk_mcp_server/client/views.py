from typing import Any, Dict


class ViewsMixin:
    def get_views(self, page: int = 1, per_page: int = 25) -> Dict[str, Any]:
        try:
            per_page = min(per_page, 100)
            data = self._request(
                "views.json",
                params={"page": str(page), "per_page": str(per_page)},
            )
            view_list = [
                {
                    "id": v.get("id"),
                    "title": v.get("title"),
                    "active": v.get("active"),
                    "position": v.get("position"),
                    "restriction": v.get("restriction"),
                    "created_at": v.get("created_at"),
                    "updated_at": v.get("updated_at"),
                }
                for v in data.get("views", [])
            ]
            return {
                "views": view_list,
                "page": page,
                "per_page": per_page,
                "count": len(view_list),
                "has_more": data.get("next_page") is not None,
                "next_page": page + 1 if data.get("next_page") else None,
                "previous_page": page - 1 if data.get("previous_page") and page > 1 else None,
            }
        except Exception as e:
            raise Exception(f"Failed to get views: {str(e)}")