from fastapi import APIRouter, Request

from app.schemas.auth_schema import LoginRequest, TokenResponse
from app.services.auth_service import login


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login_endpoint(request: Request) -> TokenResponse:
	content_type = request.headers.get("content-type", "").lower()

	if "application/json" in content_type:
		raw_data = await request.json()
		payload_data = {
			"usuario": raw_data.get("usuario") or raw_data.get("username"),
			"password": raw_data.get("password"),
		}
	else:
		form_data = await request.form()
		payload_data = {
			"usuario": form_data.get("usuario") or form_data.get("username"),
			"password": form_data.get("password"),
		}

	payload = LoginRequest.model_validate(payload_data)
	return login(payload)
