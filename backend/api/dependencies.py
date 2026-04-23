import os
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt


bearer_scheme = HTTPBearer(auto_error=False)


def _get_secret() -> str:
    secret = os.getenv("SECRET_KEY")
    if not secret:
        # Fallback para dev local; en producción debe estar configurado.
        secret = "change-me"
    return secret


def _decode_jwt(token: str) -> dict[str, Any]:
    # Supabase puede emitir JWTs firmados con claves asimétricas. Para el esqueleto,
    # decodificamos con un secreto configurable (HS256) como placeholder.
    return jwt.decode(token, _get_secret(), algorithms=["HS256"])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = _decode_jwt(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # Common claims: `sub` y/o `user_id`.
    user_id = payload.get("sub") or payload.get("user_id")
    email = payload.get("email")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return {"id": user_id, "email": email, "claims": payload}

