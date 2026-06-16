import shutil
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
        source = Path(source_path)

        if not source.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El archivo fuente no existe en la NAS",
            )

        if not source.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La ruta fuente no corresponde a un archivo válido",
            )

        source_size = source.stat().st_size
        if source_size <= 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El archivo fuente está vacío",
            )

        if destination_path.exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El archivo final ya existe en la NAS",
            )

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination_path)

        destination_size = destination_path.stat().st_size
        if destination_size <= 0 or destination_size != source_size:
            try:
                destination_path.unlink()
            except FileNotFoundError:
                pass

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La copia en la NAS no coincide con el tamaño del archivo original",
            )

        return source_size, destination_size

    def _ensure_within_root(self, destination: Path) -> None:
        try:
            destination.relative_to(self.root_path)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La ruta destino debe permanecer dentro de la raíz NAS configurada",
            ) from exc


nas_storage_service = NasStorageService()
