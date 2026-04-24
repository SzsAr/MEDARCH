from fastapi import APIRouter, Depends, FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.core.security import get_current_user


app = FastAPI(title="MEDARCH API", version="1.0.0")

# All routers included in protected_router are authenticated globally.
protected_router = APIRouter(dependencies=[Depends(get_current_user)])
protected_router.include_router(users_router)

app.include_router(auth_router)
app.include_router(protected_router)


@protected_router.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
