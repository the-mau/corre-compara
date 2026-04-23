from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user
from db.connection import get_db


router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertCreateBody(BaseModel):
    product_id: UUID
    target_price: Decimal
    size: str | None = None


@router.get("")
async def list_my_alerts(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    sql = text(
        """
        SELECT
          id, user_id, product_id, target_price, size, active, triggered_at, created_at
        FROM alerts
        WHERE user_id = :user_id
          AND active = true
        ORDER BY created_at DESC
        """
    )
    rows = (await db.execute(sql, {"user_id": str(current_user["id"])})).mappings().all()
    return [dict(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_alert(
    body: AlertCreateBody,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    # Freemium: sólo premium puede tener alertas.
    plan_sql = text("SELECT plan FROM users WHERE id = :id")
    plan_row = (await db.execute(plan_sql, {"id": str(current_user["id"])})).mappings().first()
    plan = plan_row["plan"] if plan_row else "free"
    if plan != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Alertas disponibles solo para plan premium",
        )

    insert_sql = text(
        """
        INSERT INTO alerts (user_id, product_id, target_price, size, active)
        VALUES (:user_id, :product_id, :target_price, :size, true)
        RETURNING id, user_id, product_id, target_price, size, active, triggered_at, created_at
        """
    )
    row = (await db.execute(
        insert_sql,
        {
            "user_id": str(current_user["id"]),
            "product_id": str(body.product_id),
            "target_price": str(body.target_price),
            "size": body.size,
        },
    )).mappings().first()
    await db.commit()
    if not row:
        raise HTTPException(status_code=500, detail="No se pudo crear la alerta")
    return dict(row)


@router.delete("/{id}")
async def delete_alert(
    id: UUID,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    delete_sql = text(
        """
        DELETE FROM alerts
        WHERE id = :id AND user_id = :user_id
        RETURNING id
        """
    )
    row = (await db.execute(delete_sql, {"id": str(id), "user_id": str(current_user["id"])})).mappings().first()
    await db.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "deleted"}

