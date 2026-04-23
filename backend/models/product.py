from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Product(BaseModel):
    id: UUID
    name: str
    brand: str
    model_code: str
    category: str
    image_url: Optional[str] = None
    created_at: datetime


class ProductCreate(BaseModel):
    name: str
    brand: str
    model_code: str
    category: str
    image_url: Optional[str] = None


class ProductResponse(Product):
    pass

