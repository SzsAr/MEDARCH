from contextlib import contextmanager
from typing import Generator

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