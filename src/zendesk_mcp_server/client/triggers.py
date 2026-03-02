from typing import Any, Dict, List


class TriggersMixin:
    def list_triggers(self, active: bool | None = None, page: int = 1, per_page: int = 25) -> Dict[str, Any]:
        try:
            per_page = min(per_page, 100)
            params: Dict[str, str] = {"page": str(page), "per_page": str(per_page)}
            if active is not None:
                params["active"] = "true" if active else "false"
            data = self._request("triggers", params=params)
            trigger_list = [
                {
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "active": t.get("active"),
                    "position": t.get("position"),
                    "conditions": t.get("conditions"),
                    "actions": t.get("actions"),
                    "created_at": t.get("created_at"),
                    "updated_at": t.get("updated_at"),
                }
                for t in data.get("triggers", [])
            ]
            return {
                "triggers": trigger_list,
                "count": data.get("count", len(trigger_list)),
                "next_page": data.get("next_page"),
                "previous_page": data.get("previous_page"),
            }
        except Exception as e:
            raise Exception(f"Failed to list triggers: {str(e)}")

    def get_trigger(self, trigger_id: int) -> Dict[str, Any]:
        try:
            data = self._request(f"triggers/{trigger_id}")
            t = data.get("trigger", {})
            return {
                "id": t.get("id"),
                "title": t.get("title"),
                "active": t.get("active"),
                "position": t.get("position"),
                "conditions": t.get("conditions"),
                "actions": t.get("actions"),
                "created_at": t.get("created_at"),
                "updated_at": t.get("updated_at"),
            }
        except Exception as e:
            raise Exception(f"Failed to get trigger {trigger_id}: {str(e)}")

    def test_trigger(self, trigger_id: int, ticket_id: int) -> Dict[str, Any]:
        """Check whether a trigger's conditions match a given ticket."""
        try:
            trigger = self.get_trigger(trigger_id)
            ticket_data = self._request(f"tickets/{ticket_id}")
            ticket = ticket_data.get("ticket", {})
            conditions = trigger.get("conditions", {})
            return {
                "trigger_id": trigger_id,
                "trigger_title": trigger.get("title"),
                "ticket_id": ticket_id,
                "ticket_subject": ticket.get("subject"),
                "ticket_status": ticket.get("status"),
                "conditions": conditions,
                "actions": trigger.get("actions"),
                "note": (
                    "Zendesk does not expose a server-side trigger test endpoint. "
                    "This response contains the trigger conditions and ticket details "
                    "so you can manually verify if the trigger would fire."
                ),
            }
        except Exception as e:
            raise Exception(f"Failed to test trigger {trigger_id} against ticket {ticket_id}: {str(e)}")