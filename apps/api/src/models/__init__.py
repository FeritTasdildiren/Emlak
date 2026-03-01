"""
Emlak Teknoloji Platformu - SQLAlchemy Models

Tüm entity modelleri buradan export edilir.
Alembic autogenerate için tüm modellerin import edilmesi zorunludur.
"""

from src.models.area_analysis import AreaAnalysis
from src.models.bank_rate import BankRate
from src.models.base import BaseModel, SoftDeleteMixin, TenantMixin
from src.models.customer import Customer
from src.models.customer_note import CustomerNote
from src.models.deprem_risk import DepremRisk
from src.models.inbox_event import InboxEvent
from src.models.match import PropertyCustomerMatch
from src.models.message import Conversation, Message
from src.models.model_registry import ModelRegistry
from src.models.notification import Notification
from src.models.office import Office
from src.models.outbox_event import OutboxEvent
from src.models.payment import Payment
from src.models.prediction_log import PredictionLog
from src.models.price_history import PriceHistory
from src.models.property import Property
from src.models.scraped_listing import ScrapedListing
from src.models.showcase import Showcase
from src.models.subscription import Subscription
from src.models.user import User
from src.models.valuation import PropertyValuation
from src.modules.valuations.models.usage_quota import UsageQuota

__all__ = [
    "AreaAnalysis",
    "BankRate",
    "BaseModel",
    "Conversation",
    "Customer",
    "CustomerNote",
    "DepremRisk",
    "InboxEvent",
    "Message",
    "ModelRegistry",
    "Notification",
    "Office",
    "OutboxEvent",
    "Payment",
    "PredictionLog",
    "PriceHistory",
    "Property",
    "PropertyCustomerMatch",
    "PropertyValuation",
    "ScrapedListing",
    "Showcase",
    "SoftDeleteMixin",
    "Subscription",
    "TenantMixin",
    "UsageQuota",
    "User",
]
