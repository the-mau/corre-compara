from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class Alert(BaseModel):
    id: UUID
    user_id: UUID
    product_id: UUID
    target_price: Decimal
    size: Optional[str] = None
    active: bool = True
    triggered_at: Optional[datetime] = None
    created_at: datetime


class AlertCreate(BaseModel):
    product_id: UUID
    target_price: Decimal
    size: Optional[str] = None


class AlertResponse(Alert):
    pass

