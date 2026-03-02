from typing import Any, Dict, List


def _ticket_field_shape(f: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": f.get("id"),
        "type": f.get("type"),
        "title": f.get("title"),
        "description": f.get("description"),
        "active": f.get("active"),
        "required": f.get("required"),
        "custom_field_options": f.get("custom_field_options"),
        "system_field_options": f.get("system_field_options"),
    }


def _user_org_field_shape(f: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": f.get("id"),
        "key": f.get("key"),
        "type": f.get("type"),
        "title": f.get("title"),
        "description": f.get("description"),
        "active": f.get("active"),
        "custom_field_options": f.get("custom_field_options"),
    }


class FieldsMixin:
    def get_ticket_fields(self) -> Dict[str, Any]:
        try:
            data = self._request("ticket_fields.json")
            field_list = [_ticket_field_shape(f) for f in data.get("ticket_fields", [])]
            return {"ticket_fields": field_list, "count": len(field_list)}
        except Exception as e:
            raise Exception(f"Failed to get ticket fields: {str(e)}")

    def create_ticket_field(
        self,
        type: str,
        title: str,
        description: str | None = None,
        required: bool | None = None,
        active: bool | None = None,
        custom_field_options: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        try:
            field: Dict[str, Any] = {"type": type, "title": title}
            if description is not None:
                field["description"] = description
            if required is not None:
                field["required"] = required
            if active is not None:
                field["active"] = active
            if custom_field_options is not None:
                field["custom_field_options"] = custom_field_options
            data = self._request("ticket_fields.json", method="POST", body={"ticket_field": field})
            return _ticket_field_shape(data.get("ticket_field", {}))
        except Exception as e:
            raise Exception(f"Failed to create ticket field: {str(e)}")

    def update_ticket_field(
        self,
        field_id: int,
        title: str | None = None,
        description: str | None = None,
        required: bool | None = None,
        active: bool | None = None,
        custom_field_options: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        try:
            field: Dict[str, Any] = {}
            if title is not None:
                field["title"] = title
            if description is not None:
                field["description"] = description
            if required is not None:
                field["required"] = required
            if active is not None:
                field["active"] = active
            if custom_field_options is not None:
                field["custom_field_options"] = custom_field_options
            data = self._request(f"ticket_fields/{field_id}.json", method="PUT", body={"ticket_field": field})
            return _ticket_field_shape(data.get("ticket_field", {}))
        except Exception as e:
            raise Exception(f"Failed to update ticket field {field_id}: {str(e)}")

    def get_user_fields(self) -> Dict[str, Any]:
        try:
            data = self._request("user_fields.json")
            field_list = [_user_org_field_shape(f) for f in data.get("user_fields", [])]
            return {"user_fields": field_list, "count": len(field_list)}
        except Exception as e:
            raise Exception(f"Failed to get user fields: {str(e)}")

    def create_user_field(
        self,
        key: str,
        type: str,
        title: str,
        description: str | None = None,
        active: bool | None = None,
        custom_field_options: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        try:
            field: Dict[str, Any] = {"key": key, "type": type, "title": title}
            if description is not None:
                field["description"] = description
            if active is not None:
                field["active"] = active
            if custom_field_options is not None:
                field["custom_field_options"] = custom_field_options
            data = self._request("user_fields.json", method="POST", body={"user_field": field})
            return _user_org_field_shape(data.get("user_field", {}))
        except Exception as e:
            raise Exception(f"Failed to create user field: {str(e)}")

    def update_user_field(
        self,
        field_id: int,
        title: str | None = None,
        description: str | None = None,
        active: bool | None = None,
        custom_field_options: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        try:
            field: Dict[str, Any] = {}
            if title is not None:
                field["title"] = title
            if description is not None:
                field["description"] = description
            if active is not None:
                field["active"] = active
            if custom_field_options is not None:
                field["custom_field_options"] = custom_field_options
            data = self._request(f"user_fields/{field_id}.json", method="PUT", body={"user_field": field})
            return _user_org_field_shape(data.get("user_field", {}))
        except Exception as e:
            raise Exception(f"Failed to update user field {field_id}: {str(e)}")

    def get_organization_fields(self) -> Dict[str, Any]:
        try:
            data = self._request("organization_fields.json")
            field_list = [_user_org_field_shape(f) for f in data.get("organization_fields", [])]
            return {"organization_fields": field_list, "count": len(field_list)}
        except Exception as e:
            raise Exception(f"Failed to get organization fields: {str(e)}")

    def create_organization_field(
        self,
        key: str,
        type: str,
        title: str,
        description: str | None = None,
        active: bool | None = None,
        custom_field_options: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        try:
            field: Dict[str, Any] = {"key": key, "type": type, "title": title}
            if description is not None:
                field["description"] = description
            if active is not None:
                field["active"] = active
            if custom_field_options is not None:
                field["custom_field_options"] = custom_field_options
            data = self._request("organization_fields.json", method="POST", body={"organization_field": field})
            return _user_org_field_shape(data.get("organization_field", {}))
        except Exception as e:
            raise Exception(f"Failed to create organization field: {str(e)}")

    def update_organization_field(
        self,
        field_id: int,
        title: str | None = None,
        description: str | None = None,
        active: bool | None = None,
        custom_field_options: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        try:
            field: Dict[str, Any] = {}
            if title is not None:
                field["title"] = title
            if description is not None:
                field["description"] = description
            if active is not None:
                field["active"] = active
            if custom_field_options is not None:
                field["custom_field_options"] = custom_field_options
            data = self._request(f"organization_fields/{field_id}.json", method="PUT", body={"organization_field": field})
            return _user_org_field_shape(data.get("organization_field", {}))
        except Exception as e:
            raise Exception(f"Failed to update organization field {field_id}: {str(e)}")