from typing import Any, Dict, List

from zenpy.lib.api_objects import Comment
from zenpy.lib.api_objects import Ticket as ZenpyTicket


class TicketsMixin:
    def get_ticket(self, ticket_id: int) -> Dict[str, Any]:
        try:
            ticket = self.client.tickets(id=ticket_id)
            return {
                "id": ticket.id,
                "subject": ticket.subject,
                "description": ticket.description,
                "status": ticket.status,
                "priority": ticket.priority,
                "created_at": str(ticket.created_at),
                "updated_at": str(ticket.updated_at),
                "requester_id": ticket.requester_id,
                "assignee_id": ticket.assignee_id,
                "organization_id": ticket.organization_id,
            }
        except Exception as e:
            raise Exception(f"Failed to get ticket {ticket_id}: {str(e)}")

    def get_ticket_comments(self, ticket_id: int) -> List[Dict[str, Any]]:
        try:
            comments = self.client.tickets.comments(ticket=ticket_id)
            return [
                {
                    "id": comment.id,
                    "author_id": comment.author_id,
                    "body": comment.body,
                    "html_body": comment.html_body,
                    "public": comment.public,
                    "created_at": str(comment.created_at),
                }
                for comment in comments
            ]
        except Exception as e:
            raise Exception(f"Failed to get comments for ticket {ticket_id}: {str(e)}")

    def post_comment(self, ticket_id: int, comment: str, public: bool = True) -> str:
        try:
            ticket = self.client.tickets(id=ticket_id)
            ticket.comment = Comment(html_body=comment, public=public)
            self.client.tickets.update(ticket)
            return comment
        except Exception as e:
            raise Exception(f"Failed to post comment on ticket {ticket_id}: {str(e)}")

    def _search_tickets_by_status(
        self,
        status: str,
        page: int = 1,
        per_page: int = 25,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        data = self._request(
            "search.json",
            params={
                "query": f"type:ticket status:{status}",
                "page": str(page),
                "per_page": str(per_page),
                "sort_by": sort_by,
                "sort_order": sort_order,
            },
        )
        results = data.get("results", [])
        ticket_list = [
            {
                "id": t.get("id"),
                "subject": t.get("subject"),
                "status": t.get("status"),
                "priority": t.get("priority"),
                "description": t.get("description"),
                "created_at": t.get("created_at"),
                "updated_at": t.get("updated_at"),
                "requester_id": t.get("requester_id"),
                "assignee_id": t.get("assignee_id"),
            }
            for t in results
        ]
        return {
            "tickets": ticket_list,
            "page": page,
            "per_page": per_page,
            "count": len(ticket_list),
            "total_count": data.get("count", len(ticket_list)),
            "status_filter": status,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "has_more": data.get("next_page") is not None,
            "next_page": page + 1 if data.get("next_page") else None,
            "previous_page": page - 1 if data.get("previous_page") and page > 1 else None,
        }

    def get_tickets(
        self,
        page: int = 1,
        per_page: int = 25,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        view_id: int | None = None,
        status: str | None = None,
    ) -> Dict[str, Any]:
        try:
            per_page = min(per_page, 100)
            if status and not view_id:
                return self._search_tickets_by_status(
                    status=status,
                    page=page,
                    per_page=per_page,
                    sort_by=sort_by,
                    sort_order=sort_order,
                )
            params = {
                "page": str(page),
                "per_page": str(per_page),
                "sort_by": sort_by,
                "sort_order": sort_order,
            }
            path = f"views/{view_id}/tickets.json" if view_id else "tickets.json"
            data = self._request(path, params=params)
            ticket_list = [
                {
                    "id": t.get("id"),
                    "subject": t.get("subject"),
                    "status": t.get("status"),
                    "priority": t.get("priority"),
                    "description": t.get("description"),
                    "created_at": t.get("created_at"),
                    "updated_at": t.get("updated_at"),
                    "requester_id": t.get("requester_id"),
                    "assignee_id": t.get("assignee_id"),
                }
                for t in data.get("tickets", [])
            ]
            return {
                "tickets": ticket_list,
                "page": page,
                "per_page": per_page,
                "count": len(ticket_list),
                "sort_by": sort_by,
                "sort_order": sort_order,
                "has_more": data.get("next_page") is not None,
                "next_page": page + 1 if data.get("next_page") else None,
                "previous_page": page - 1 if data.get("previous_page") and page > 1 else None,
            }
        except Exception as e:
            raise Exception(f"Failed to get tickets: {str(e)}")

    def create_ticket(
        self,
        subject: str,
        description: str,
        requester_id: int | None = None,
        assignee_id: int | None = None,
        priority: str | None = None,
        type: str | None = None,
        tags: List[str] | None = None,
        custom_fields: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        try:
            ticket = ZenpyTicket(
                subject=subject,
                description=description,
                requester_id=requester_id,
                assignee_id=assignee_id,
                priority=priority,
                type=type,
                tags=tags,
                custom_fields=custom_fields,
            )
            created_audit = self.client.tickets.create(ticket)
            created_ticket_id = getattr(getattr(created_audit, "ticket", None), "id", None)
            if created_ticket_id is None:
                created_ticket_id = getattr(created_audit, "id", None)
            created = self.client.tickets(id=created_ticket_id) if created_ticket_id else None
            return {
                "id": getattr(created, "id", created_ticket_id),
                "subject": getattr(created, "subject", subject),
                "description": getattr(created, "description", description),
                "status": getattr(created, "status", "new"),
                "priority": getattr(created, "priority", priority),
                "type": getattr(created, "type", type),
                "created_at": str(getattr(created, "created_at", "")),
                "updated_at": str(getattr(created, "updated_at", "")),
                "requester_id": getattr(created, "requester_id", requester_id),
                "assignee_id": getattr(created, "assignee_id", assignee_id),
                "organization_id": getattr(created, "organization_id", None),
                "tags": list(getattr(created, "tags", tags or []) or []),
            }
        except Exception as e:
            raise Exception(f"Failed to create ticket: {str(e)}")

    def update_ticket(self, ticket_id: int, **fields: Any) -> Dict[str, Any]:
        try:
            ticket = self.client.tickets(id=ticket_id)
            for key, value in fields.items():
                if value is None:
                    continue
                setattr(ticket, key, value)
            self.client.tickets.update(ticket)
            refreshed = self.client.tickets(id=ticket_id)
            return {
                "id": refreshed.id,
                "subject": refreshed.subject,
                "description": refreshed.description,
                "status": refreshed.status,
                "priority": refreshed.priority,
                "type": getattr(refreshed, "type", None),
                "created_at": str(refreshed.created_at),
                "updated_at": str(refreshed.updated_at),
                "requester_id": refreshed.requester_id,
                "assignee_id": refreshed.assignee_id,
                "organization_id": refreshed.organization_id,
                "tags": list(getattr(refreshed, "tags", []) or []),
            }
        except Exception as e:
            raise Exception(f"Failed to update ticket {ticket_id}: {str(e)}")

    def update_tickets_batch(self, tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not tickets:
            raise ValueError("tickets list cannot be empty")
        for ticket in tickets:
            if "id" not in ticket:
                raise ValueError("Each ticket must have an 'id' field")
        try:
            data = self._request("tickets/update_many.json", method="PUT", body={"tickets": tickets})
            job_status = data.get("job_status", {})
            return {
                "job_status": {
                    "id": job_status.get("id"),
                    "url": job_status.get("url"),
                    "status": job_status.get("status"),
                    "total": job_status.get("total"),
                    "progress": job_status.get("progress"),
                    "message": job_status.get("message"),
                },
                "tickets_count": len(tickets),
            }
        except Exception as e:
            raise Exception(f"Failed to batch update tickets: {str(e)}")