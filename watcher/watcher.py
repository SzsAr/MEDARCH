import logging
import os
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Optional

import psycopg2
from psycopg2 import OperationalError
from psycopg2.pool import SimpleConnectionPool
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


# ============================================
# 🧠 CONFIGURACIÓN
# ============================================

@dataclass(frozen=True)
class Settings:
    watch_path: str = os.getenv("MEDARCH_WATCH_PATH", r"C:\Escaneos\PENDIENTES")
    recursive: bool = os.getenv("MEDARCH_WATCH_RECURSIVE", "true").lower() == "true"

    db_host: str = os.getenv("MEDARCH_DB_HOST", "localhost")
    db_port: int = int(os.getenv("MEDARCH_DB_PORT", "5432"))
    db_name: str = os.getenv("MEDARCH_DB_NAME", "medarch_db")
    db_user: str = os.getenv("MEDARCH_DB_USER", "medarch_user")
    db_password: str = os.getenv("MEDARCH_DB_PASSWORD", "Medarch123*")

    db_min_conn: int = int(os.getenv("MEDARCH_DB_MIN_CONN", "1"))
    db_max_conn: int = int(os.getenv("MEDARCH_DB_MAX_CONN", "5"))

    reconnect_wait_seconds: int = int(os.getenv("MEDARCH_RECONNECT_WAIT", "5"))


# ============================================
# 🧠 UTILIDAD: ESPERAR ARCHIVO COMPLETO
# ============================================

def wait_until_file_is_ready(path: str, timeout: int = 10) -> bool:
    """
    Espera hasta que el archivo deje de crecer en tamaño.
    Evita procesar archivos incompletos.
    """
    try:
        previous_size = -1

        for _ in range(timeout):
            if not os.path.exists(path):
                return False

            current_size = os.path.getsize(path)

            if current_size == previous_size:
                return True

            previous_size = current_size
            time.sleep(1)

        return False
    except Exception as e:
        logging.warning("No se pudo validar tamaño del archivo %s: %s", path, e)
        return False


# ============================================
# 🗄️ BASE DE DATOS
# ============================================

class DatabaseClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.pool: Optional[SimpleConnectionPool] = None

    def connect(self) -> None:
        if self.pool is not None:
            return

        self.pool = SimpleConnectionPool(
            minconn=self.settings.db_min_conn,
            maxconn=self.settings.db_max_conn,
            host=self.settings.db_host,
            port=self.settings.db_port,
            dbname=self.settings.db_name,
            user=self.settings.db_user,
            password=self.settings.db_password,
            connect_timeout=10,
        )
        logging.info("Conexion a PostgreSQL inicializada")

    def close(self) -> None:
        if self.pool is not None:
            self.pool.closeall()
            self.pool = None
            logging.info("Pool de conexiones PostgreSQL cerrado")

    def ensure_connection(self) -> None:
        while True:
            try:
                self.connect()
                return
            except Exception as exc:
                logging.exception("Error conectando a PostgreSQL: %s", exc)
                time.sleep(self.settings.reconnect_wait_seconds)

    def insert_pending_document(self, full_path: str, file_name: str) -> bool:
        if self.pool is None:
            raise RuntimeError("Pool de conexiones no inicializado")

        conn = None
        try:
            conn = self.pool.getconn()
            conn.autocommit = False

            with conn.cursor() as cursor:
                # Evitar duplicados
                cursor.execute(
                    """
                    SELECT 1
                    FROM gesdoc.documentos
                    WHERE ruta_temporal = %s
                    LIMIT 1;
                    """,
                    (full_path,),
                )
                already_exists = cursor.fetchone() is not None

                if already_exists:
                    conn.rollback()
                    logging.info("Registro duplicado omitido: %s", full_path)
                    return False

                # Insertar documento
                cursor.execute(
                    """
                    INSERT INTO gesdoc.documentos (
                        ruta_temporal,
                        nombre_archivo_original,
                        estado
                    ) VALUES (%s, %s, 'PENDIENTE');
                    """,
                    (full_path, file_name),
                )
                conn.commit()
                logging.info("Documento registrado: %s", full_path)
                return True

        except OperationalError as exc:
            if conn:
                conn.rollback()
            logging.exception("Error operacional BD para %s: %s", full_path, exc)
            self.close()
            self.ensure_connection()
            return False
        except Exception as exc:
            if conn:
                conn.rollback()
            logging.exception("Error insertando %s: %s", full_path, exc)
            return False
        finally:
            if conn and self.pool:
                self.pool.putconn(conn)


# ============================================
# 👀 WATCHER EVENTO
# ============================================

class PDFCreatedEventHandler(FileSystemEventHandler):
    def __init__(self, database_client: DatabaseClient) -> None:
        super().__init__()
        self.database_client = database_client

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return

        full_path = str(Path(event.src_path).resolve())
        extension = Path(full_path).suffix.lower()

        if extension != ".pdf":
            logging.debug("Archivo ignorado (no es PDF): %s", full_path)
            return

        logging.info("Archivo detectado: %s", full_path)

        # 🔥 Esperar a que el archivo esté completamente copiado
        is_ready = wait_until_file_is_ready(full_path)

        if not is_ready:
            logging.warning("Archivo no listo o incompleto: %s", full_path)
            return

        file_name = Path(full_path).name

        try:
            self.database_client.insert_pending_document(
                full_path=full_path,
                file_name=file_name,
            )
        except Exception as exc:
            logging.exception("Error procesando archivo %s: %s", full_path, exc)


# ============================================
# 🚀 SERVICIO WATCHER
# ============================================

class WatcherService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.stop_event = Event()
        self.observer = Observer()
        self.database_client = DatabaseClient(settings=settings)

    def _validate_watch_folder(self) -> None:
        watch_folder = Path(self.settings.watch_path)
        if not watch_folder.exists() or not watch_folder.is_dir():
            raise FileNotFoundError(
                f"La carpeta no existe: {self.settings.watch_path}"
            )

    def _register_signal_handlers(self) -> None:
        def _handle_signal(sig: int, _frame: object) -> None:
            logging.info("Cerrando watcher...")
            self.stop_event.set()

        signal.signal(signal.SIGINT, _handle_signal)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, _handle_signal)

    def start(self) -> None:
        self._validate_watch_folder()
        self._register_signal_handlers()

        self.database_client.ensure_connection()

        event_handler = PDFCreatedEventHandler(self.database_client)

        self.observer.schedule(
            event_handler,
            path=self.settings.watch_path,
            recursive=self.settings.recursive,
        )

        self.observer.start()
        logging.info("Watcher iniciado en: %s", self.settings.watch_path)

        try:
            while not self.stop_event.is_set():
                time.sleep(1)
        finally:
            self.stop()

    def stop(self) -> None:
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join(timeout=5)

        self.database_client.close()
        logging.info("Watcher detenido")


# ============================================
# 🧠 MAIN
# ============================================

def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def main() -> int:
    configure_logging()
    settings = Settings()

    try:
        service = WatcherService(settings)
        service.start()
        return 0
    except FileNotFoundError as exc:
        logging.error(str(exc))
        return 1
    except KeyboardInterrupt:
        logging.info("Interrupcion manual")
        return 0
    except Exception as exc:
        logging.exception("Error fatal: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())