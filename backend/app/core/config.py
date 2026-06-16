import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)


class Settings:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "medarch_db")
    DB_USER: str = os.getenv("DB_USER", "medarch_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    NAS_ROOT_PATH: str = os.getenv("NAS_ROOT_PATH", r"\\192.168.100.4\toshiba ext\MEDARCH")
    NAS_SHARE_USER: str = os.getenv("NAS_SHARE_USER", "")
    NAS_SHARE_PASSWORD: str = os.getenv("NAS_SHARE_PASSWORD", "")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )


settings = Settings()
