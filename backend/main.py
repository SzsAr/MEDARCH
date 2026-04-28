from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.core.security import get_current_user


app = FastAPI(title="MEDARCH API", version="1.0.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"http://127.0.0.1:5500",
		"http://localhost:5500",
		"http://127.0.0.1:8000",
		"http://localhost:8000",
	],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Auth endpoint - sin autenticación
app.include_router(auth_router)

# POST /users - sin autenticación (crear usuario)
# Solo POST es público, el resto requiere autenticación
app.include_router(users_router, tags=["Users"])

# Otros endpoints de usuarios - requieren autenticación SUPERADMIN
protected_router = APIRouter(dependencies=[Depends(get_current_user)])

# Las rutas GET, PUT, PATCH, DELETE ya están protegidas en users.py con require_role("SUPERADMIN")


@protected_router.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
	return {"status": "ok"}


app.include_router(protected_router)
