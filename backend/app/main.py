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

# All routers included in protected_router are authenticated globally.
protected_router = APIRouter(dependencies=[Depends(get_current_user)])
protected_router.include_router(users_router)

app.include_router(auth_router)
app.include_router(protected_router)


@protected_router.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
