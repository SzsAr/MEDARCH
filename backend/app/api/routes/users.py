from fastapi import APIRouter, status

from app.schemas.user_schema import UserCreateRequest, UserResponse
from app.services.user_service import create_user


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(payload: UserCreateRequest) -> UserResponse:
	return create_user(payload)
