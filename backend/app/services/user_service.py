from fastapi import HTTPException, status

from app.core.security import hash_password
from app.db.session import get_db_cursor
from app.schemas.user_schema import UserCreateRequest, UserResponse


def create_user(payload: UserCreateRequest) -> UserResponse:
	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			cur.execute(
				"""
				SELECT id_usuario
				FROM gesdoc.usuarios
				WHERE LOWER(usuario) = LOWER(%s)
				""",
				(payload.usuario,),
			)
			existing = cur.fetchone()

			if existing:
				raise HTTPException(
					status_code=status.HTTP_409_CONFLICT,
					detail="El usuario ya existe",
				)

			password_hash = hash_password(payload.password)

			cur.execute(
				"""
				INSERT INTO gesdoc.usuarios (usuario, nombre, rol, activo, password_hash)
				VALUES (%s, %s, %s, TRUE, %s)
				RETURNING id_usuario, usuario, nombre, rol, activo, fecha_creacion
				""",
				(
					payload.usuario,
					payload.nombre,
					payload.rol,
					password_hash,
				),
			)
			created_user = cur.fetchone()
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al crear el usuario",
		) from exc

	return UserResponse(**created_user)
