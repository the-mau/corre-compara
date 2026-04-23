from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class PriceHistory(BaseModel):
    id: UUID
    product_id: UUID
    store_id: Optional[UUID] = None

    # Campos enriquecidos (pueden venir nulos si es agregado).
    store_name: Optional[str] = None

    price: Decimal
    currency: str = "MXN"
    url: Optional[str] = None
    in_stock: bool = False
    size_available: List[str] = []
    scraped_at: datetime


class PriceCreate(BaseModel):
    product_id: UUID
    store_id: UUID
    price: Decimal
    currency: str = "MXN"
    url: Optional[str] = None
    in_stock: bool = False
    size_available: List[str] = []


class PriceResponse(PriceHistory):
    pass


class PriceComparison(BaseModel):
    """
    Agrupa precios del mismo producto en distintas tiendas.
    """

    product_id: UUID
    prices: List[PriceHistory]

