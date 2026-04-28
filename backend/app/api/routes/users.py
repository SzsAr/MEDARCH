from typing import Any, Dict, List

from fastapi import APIRouter, Depends, status

from app.core.security import require_role
from app.schemas.user_schema import (
	UserCreateRequest,
	UserPasswordChangeRequest,
	UserResponse,
	UserUpdateRequest,
)
from app.services.user_service import (
	change_password,
	create_user,
	toggle_user_status,
	get_user_by_id,
	list_users,
	update_user,
)


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(payload: UserCreateRequest) -> UserResponse:
	return create_user(payload)


@router.get("", response_model=List[UserResponse])
def list_users_endpoint(
	_: Dict[str, Any] = Depends(require_role("SUPERADMIN")),
) -> List[UserResponse]:
	return list_users()


@router.get("/{id_usuario}", response_model=UserResponse)
def get_user_endpoint(
	id_usuario: int,
	_: Dict[str, Any] = Depends(require_role("SUPERADMIN")),
) -> UserResponse:
	return get_user_by_id(id_usuario)


@router.put("/{id_usuario}", response_model=UserResponse)
def update_user_endpoint(
	id_usuario: int,
	payload: UserUpdateRequest,
	_: Dict[str, Any] = Depends(require_role("SUPERADMIN")),
) -> UserResponse:
	return update_user(id_usuario, payload)


@router.patch("/{id_usuario}/password", response_model=Dict[str, str])
def change_password_endpoint(
	id_usuario: int,
	payload: UserPasswordChangeRequest,
	_: Dict[str, Any] = Depends(require_role("SUPERADMIN")),
) -> Dict[str, str]:
	return change_password(id_usuario, payload)


@router.delete("/{id_usuario}", response_model=Dict[str, str])
def toggle_user_status_endpoint(
	id_usuario: int,
	current_user: Dict[str, Any] = Depends(require_role("SUPERADMIN")),
) -> Dict[str, str]:
	return toggle_user_status(id_usuario, current_user)
