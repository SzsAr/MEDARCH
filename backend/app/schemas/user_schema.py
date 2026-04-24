from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class UserCreateRequest(BaseModel):
	usuario: str = Field(..., min_length=3, max_length=50)
	nombre: str = Field(..., min_length=2, max_length=150)
	password: str = Field(..., min_length=8, max_length=128)
	rol: Literal["CONSULTA", "ARCHIVO", "SUPERADMIN"]


class UserUpdateRequest(BaseModel):
	nombre: str = Field(..., min_length=2, max_length=150)
	rol: Literal["CONSULTA", "ARCHIVO", "SUPERADMIN"]
	activo: bool


class UserPasswordChangeRequest(BaseModel):
	nueva_password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
	id_usuario: int
	usuario: str
	nombre: str
	rol: str
	activo: bool
	fecha_creacion: datetime
