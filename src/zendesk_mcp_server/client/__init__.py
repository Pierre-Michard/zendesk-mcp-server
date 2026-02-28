from zendesk_mcp_server.client.base import ZendeskBaseClient
from zendesk_mcp_server.client.fields import FieldsMixin
from zendesk_mcp_server.client.knowledge_base import KnowledgeBaseMixin
from zendesk_mcp_server.client.tickets import TicketsMixin
from zendesk_mcp_server.client.users import UsersMixin
from zendesk_mcp_server.client.views import ViewsMixin
from zendesk_mcp_server.client.webhooks import WebhooksMixin


class ZendeskClient(
    TicketsMixin,
    ViewsMixin,
    UsersMixin,
    FieldsMixin,
    KnowledgeBaseMixin,
    WebhooksMixin,
    ZendeskBaseClient,
):
    """Composed Zendesk client. Domain logic lives in mixins; ZendeskBaseClient last in MRO."""
    pass


__all__ = ["ZendeskClient"]