from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user
from db.connection import get_db


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_me(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    user_id = current_user["id"]
    # Si no existe, respondemos 404 para mantener el skeleton explícito.
    sql = text("SELECT id, email, plan, created_at FROM users WHERE id = :id")
    row = (await db.execute(sql, {"id": str(UUID(str(user_id)))})).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)

