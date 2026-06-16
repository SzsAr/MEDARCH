from contextlib import contextmanager
import os
from pathlib import Path
from typing import Generator


def configure_postgres_dll_search_path() -> None:
    if os.name != "nt":
        return

    candidate_paths = []
    env_bin = os.getenv("MEDARCH_PG_BIN")
    if env_bin:
        candidate_paths.append(env_bin)

    candidate_paths.extend(
        [
            r"C:\Program Files\PostgreSQL\18\bin",
            r"C:\Program Files\PostgreSQL\17\bin",
            r"C:\Program Files\PostgreSQL\16\bin",
            r"C:\Program Files\PostgreSQL\15\bin",
            r"C:\Program Files\PostgreSQL\14\bin",
        ]
    )

    for candidate in candidate_paths:
        dll_path = Path(candidate) / "libpq.dll"
        if not dll_path.exists():
            continue

        os.environ["PATH"] = f"{candidate};{os.environ.get('PATH', '')}"
        try:
            os.add_dll_directory(candidate)
        except (AttributeError, FileNotFoundError, OSError):
            pass
        break


configure_postgres_dll_search_path()

import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings


def get_connection() -> psycopg2.extensions.connection:
    try:
        return psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
        )
    except psycopg2.Error as exc:
        raise RuntimeError("No se pudo conectar a la base de datos") from exc


@contextmanager
def get_db_cursor(
    dict_cursor: bool = False,
) -> Generator[
    tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor], None, None
]:
    conn = get_connection()
    cursor_factory = RealDictCursor if dict_cursor else None
    cur = conn.cursor(cursor_factory=cursor_factory)

    try:
        yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()