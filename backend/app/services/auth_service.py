from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.db.session import get_db_cursor
from app.schemas.auth_schema import LoginRequest, TokenResponse


def login(payload: LoginRequest) -> TokenResponse:
	invalid_credentials = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Credenciales inválidas",
	)

	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			cur.execute(
				"""
				SELECT id_usuario, usuario, nombre, rol, activo, password_hash
				FROM gesdoc.usuarios
				WHERE LOWER(usuario) = LOWER(%s)
				""",
				(payload.usuario,),
			)
			user = cur.fetchone()
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al validar credenciales",
		) from exc

	if not user:
		raise invalid_credentials

	if not user["activo"]:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Usuario inactivo",
		)

	if not verify_password(payload.password, user["password_hash"]):
		raise invalid_credentials

	token = create_access_token(
		{
			"id_usuario": user["id_usuario"],
			"usuario": user["usuario"],
			"rol": user["rol"],
		}
	)

	return TokenResponse(
		access_token=token,
		token_type="bearer",
		expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
	)
