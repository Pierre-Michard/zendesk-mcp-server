from typing import Any, Dict


class FieldsMixin:
    def get_ticket_fields(self) -> Dict[str, Any]:
        try:
            data = self._request("ticket_fields.json")
            field_list = [
                {
                    "id": f.get("id"),
                    "type": f.get("type"),
                    "title": f.get("title"),
                    "description": f.get("description"),
                    "active": f.get("active"),
                    "required": f.get("required"),
                    "custom_field_options": f.get("custom_field_options"),
                    "system_field_options": f.get("system_field_options"),
                }
                for f in data.get("ticket_fields", [])
            ]
            return {"ticket_fields": field_list, "count": len(field_list)}
        except Exception as e:
            raise Exception(f"Failed to get ticket fields: {str(e)}")

    def get_user_fields(self) -> Dict[str, Any]:
        try:
            data = self._request("user_fields.json")
            field_list = [
                {
                    "id": f.get("id"),
                    "key": f.get("key"),
                    "type": f.get("type"),
                    "title": f.get("title"),
                    "description": f.get("description"),
                    "active": f.get("active"),
                    "custom_field_options": f.get("custom_field_options"),
                }
                for f in data.get("user_fields", [])
            ]
            return {"user_fields": field_list, "count": len(field_list)}
        except Exception as e:
            raise Exception(f"Failed to get user fields: {str(e)}")

    def get_organization_fields(self) -> Dict[str, Any]:
        try:
            data = self._request("organization_fields.json")
            field_list = [
                {
                    "id": f.get("id"),
                    "key": f.get("key"),
                    "type": f.get("type"),
                    "title": f.get("title"),
                    "description": f.get("description"),
                    "active": f.get("active"),
                    "custom_field_options": f.get("custom_field_options"),
                }
                for f in data.get("organization_fields", [])
            ]
            return {"organization_fields": field_list, "count": len(field_list)}
        except Exception as e:
            raise Exception(f"Failed to get organization fields: {str(e)}")