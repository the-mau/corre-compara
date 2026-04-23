from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class User(BaseModel):
    id: UUID
    email: str
    plan: str = "free"
    created_at: datetime


class UserResponse(User):
    pass

