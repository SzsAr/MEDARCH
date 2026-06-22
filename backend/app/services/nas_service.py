import shutil
import os
import subprocess
from pathlib import Path
from typing import Tuple

from fastapi import HTTPException, status

from app.core.config import settings


class NasStorageService:
    def __init__(self) -> None:
        self.root_path = Path(settings.NAS_ROOT_PATH)

    def build_processed_path(
        self,
        tipo_codigo: str,
        numero_documento: str,
        fecha_iso: str,
        consecutivo: int,
    ) -> Path:
        file_name = f"{tipo_codigo}_{numero_documento}_{fecha_iso}_{consecutivo:03d}.pdf"
        destination = self.root_path / numero_documento / tipo_codigo / file_name
        self._ensure_within_root(destination)
        return destination

    def resolve_destination_path(
        self,
        requested_path: str,
        expected_file_name: str,
        default_path: Path,
    ) -> Path:
        destination = Path(requested_path.strip()) if requested_path.strip() else default_path

        if not destination.is_absolute():
            destination = self.root_path / destination

        if destination.name.lower() != expected_file_name.lower():
            destination = destination.with_name(expected_file_name)

        self._ensure_within_root(destination)
        return destination

    def copy_verify_delete(self, source_path: str, destination_path: Path) -> Tuple[int, int]:
        self._ensure_share_connection()
        source = Path(source_path)

        try:
            source_exists = source.exists()
        except OSError as exc:
            self._raise_storage_unavailable(f"No fue posible acceder al archivo fuente: {source}", exc)

        if not source_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El archivo fuente no existe en la NAS",
            )

        try:
            source_is_file = source.is_file()
        except OSError as exc:
            self._raise_storage_unavailable(f"No fue posible validar el archivo fuente: {source}", exc)

        if not source_is_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La ruta fuente no corresponde a un archivo valido",
            )

        try:
            source_size = source.stat().st_size
        except OSError as exc:
            self._raise_storage_unavailable(f"No fue posible leer el archivo fuente: {source}", exc)

        if source_size <= 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El archivo fuente esta vacio",
            )

        try:
            destination_exists = destination_path.exists()
        except OSError as exc:
            self._raise_storage_unavailable(f"No fue posible acceder a la ruta destino: {destination_path}", exc)

        if destination_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El archivo final ya existe en la NAS",
            )

        self._ensure_destination_directory(destination_path.parent)

        try:
            shutil.copy2(source, destination_path)
        except OSError as exc:
            self._raise_storage_unavailable(f"No fue posible copiar el archivo a NAS: {destination_path}", exc)

        try:
            destination_size = destination_path.stat().st_size
        except OSError as exc:
            self._raise_storage_unavailable(f"No fue posible validar la copia en NAS: {destination_path}", exc)

        if destination_size <= 0 or destination_size != source_size:
            try:
                destination_path.unlink()
            except FileNotFoundError:
                pass

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La copia en la NAS no coincide con el tamano del archivo original",
            )

        return source_size, destination_size

    def get_existing_file(self, file_path: str | Path) -> Path:
        path = Path(file_path)
        self._ensure_share_connection()

        try:
            path_exists = path.exists()
        except OSError as exc:
            self._raise_storage_unavailable(
                f"No fue posible acceder al archivo final en NAS: {path}",
                exc,
            )

        if not path_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El archivo final no existe en la ruta registrada: {path}",
            )

        try:
            path_is_file = path.is_file()
        except OSError as exc:
            self._raise_storage_unavailable(
                f"No fue posible validar el archivo final en NAS: {path}",
                exc,
            )

        if not path_is_file:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"La ruta registrada no corresponde a un archivo: {path}",
            )

        return path

    def _raise_storage_unavailable(self, message: str, exc: OSError) -> None:
        hint = "Verifica que la NAS este encendida, compartida y accesible desde este equipo."
        if getattr(exc, "winerror", None) == 1326:
            hint = (
                "Windows rechazo las credenciales para acceder a la NAS. "
                "Verifica el usuario/contrasena del recurso compartido o elimina sesiones SMB previas con credenciales incorrectas."
            )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"{message}. {hint} Raiz configurada: {self.root_path}. Detalle: {exc}"
            ),
        ) from exc

    def _ensure_share_connection(self) -> None:
        if os.name != "nt":
            return

        if not settings.NAS_SHARE_USER or not settings.NAS_SHARE_PASSWORD:
            return

        share_path = self._get_share_path()
        if not share_path:
            return

        try:
            result = subprocess.run(
                [
                    "net",
                    "use",
                    share_path,
                    f"/user:{settings.NAS_SHARE_USER}",
                    settings.NAS_SHARE_PASSWORD,
                    "/persistent:no",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No fue posible autenticar la NAS en {share_path}: {exc}",
            ) from exc

        if result.returncode == 0:
            return

        output = " ".join(
            part.strip()
            for part in [result.stdout, result.stderr]
            if part and part.strip()
        )
        if "1219" in output:
            output = (
                f"{output}. Windows ya tiene una conexion activa a la NAS con otras credenciales. "
                f"Ejecuta: net use {share_path} /delete"
            )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No fue posible autenticar la NAS en {share_path}. Detalle: {output or result.returncode}",
        )

    def _get_share_path(self) -> str:
        raw_path = str(self.root_path)
        if not raw_path.startswith("\\\\"):
            return ""

        parts = raw_path.lstrip("\\").split("\\")
        if len(parts) < 2:
            return ""

        return f"\\\\{parts[0]}\\{parts[1]}"

    def _ensure_destination_directory(self, directory: Path) -> None:
        try:
            directory_exists = directory.exists()
        except OSError as exc:
            self._raise_storage_unavailable(
                f"No fue posible acceder a la carpeta destino en NAS: {directory}",
                exc,
            )

        if directory_exists:
            try:
                directory_is_dir = directory.is_dir()
            except OSError as exc:
                self._raise_storage_unavailable(
                    f"No fue posible validar la carpeta destino en NAS: {directory}",
                    exc,
                )

            if not directory_is_dir:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"La ruta destino existe pero no es una carpeta: {directory}",
                )

            return

        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._raise_storage_unavailable(
                f"No fue posible crear la carpeta destino en NAS: {directory}",
                exc,
            )

    def _ensure_within_root(self, destination: Path) -> None:
        try:
            destination.relative_to(self.root_path)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La ruta destino debe permanecer dentro de la raiz NAS configurada",
            ) from exc


nas_storage_service = NasStorageService()
