from typing import Any, Dict, List

from fastapi import HTTPException, status

from app.core.security import hash_password
from app.db.session import get_db_cursor
from app.schemas.user_schema import (
	UserCreateRequest,
	UserPasswordChangeRequest,
	UserResponse,
	UserUpdateRequest,
)


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
		print(f"ERROR CREAR USUARIO: {str(exc)}")  # Debug
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Error al crear el usuario: {str(exc)}",
		) from exc

	return UserResponse(**created_user)


def list_users() -> List[UserResponse]:
	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			cur.execute(
				"""
				SELECT id_usuario, usuario, nombre, rol, activo, fecha_creacion
				FROM gesdoc.usuarios
				ORDER BY usuario
				"""
			)
			users = cur.fetchall()
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al listar usuarios",
		) from exc

	return [UserResponse(**user) for user in users]


def get_user_by_id(id_usuario: int) -> UserResponse:
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
			detail="Error al consultar usuario",
		) from exc

	if not user:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Usuario no encontrado",
		)

	return UserResponse(**user)


def update_user(id_usuario: int, payload: UserUpdateRequest) -> UserResponse:
	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			cur.execute(
				"""
				SELECT id_usuario
				FROM gesdoc.usuarios
				WHERE id_usuario = %s
				""",
				(id_usuario,),
			)
			if not cur.fetchone():
				raise HTTPException(
					status_code=status.HTTP_404_NOT_FOUND,
					detail="Usuario no encontrado",
				)

			cur.execute(
				"""
				UPDATE gesdoc.usuarios
				SET nombre = %s, rol = %s, activo = %s
				WHERE id_usuario = %s
				RETURNING id_usuario, usuario, nombre, rol, activo, fecha_creacion
				""",
				(payload.nombre, payload.rol, payload.activo, id_usuario),
			)
			updated_user = cur.fetchone()
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al actualizar usuario",
		) from exc

	return UserResponse(**updated_user)


def change_password(id_usuario: int, payload: UserPasswordChangeRequest) -> Dict[str, str]:
	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			cur.execute(
				"""
				SELECT id_usuario
				FROM gesdoc.usuarios
				WHERE id_usuario = %s
				""",
				(id_usuario,),
			)
			if not cur.fetchone():
				raise HTTPException(
					status_code=status.HTTP_404_NOT_FOUND,
					detail="Usuario no encontrado",
				)

			password_hash = hash_password(payload.nueva_password)

			cur.execute(
				"""
				UPDATE gesdoc.usuarios
				SET password_hash = %s
				WHERE id_usuario = %s
				""",
				(password_hash, id_usuario),
			)
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al cambiar contraseña",
		) from exc

	return {"message": "Contraseña actualizada correctamente"}


def toggle_user_status(id_usuario: int, current_user: dict[str, Any]) -> Dict[str, str]:
	if int(current_user.get("id_usuario", 0)) == id_usuario:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="No puedes desactivar tu propio usuario",
		)

	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			# Obtener estado actual
			cur.execute(
				"""
				SELECT id_usuario, activo
				FROM gesdoc.usuarios
				WHERE id_usuario = %s
				""",
				(id_usuario,),
			)
			user = cur.fetchone()
			
			if not user:
				raise HTTPException(
					status_code=status.HTTP_404_NOT_FOUND,
					detail="Usuario no encontrado",
				)

			# Toggle: si activo=true, poner false; si false, poner true
			nuevo_estado = not user["activo"]
			
			cur.execute(
				"""
				UPDATE gesdoc.usuarios
				SET activo = %s
				WHERE id_usuario = %s
				""",
				(nuevo_estado, id_usuario),
			)
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al cambiar estado del usuario",
		) from exc

	estado_texto = "activado" if nuevo_estado else "desactivado"
	return {"message": f"Usuario {estado_texto} correctamente"}
