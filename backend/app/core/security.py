from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.db.session import get_db_cursor


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        id_usuario = payload.get("id_usuario")
        usuario = payload.get("usuario")
        rol = payload.get("rol")

        if id_usuario is None or usuario is None or rol is None:
            raise credentials_exception

        return payload
    except JWTError as exc:
        raise credentials_exception from exc


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    payload = decode_token(token)
    id_usuario = payload.get("id_usuario")

    try:
        with get_db_cursor(dict_cursor=True) as (_, cur):
            cur.execute(
                """
                SELECT id_usuario, usuario, nombre, rol, activo, fecha_creacion
                FROM gesdoc.usuarios
                WHERE id_usuario = %s
                """,
                (id_usuario,),
            )
            user = cur.fetchone()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error consultando usuario autenticado",
        ) from exc

    if not user or not user["activo"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inválido o inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return dict(user)


def require_role(rol: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def dependency(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if current_user.get("rol") != rol:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para esta operación",
            )
        return current_user

    return dependency