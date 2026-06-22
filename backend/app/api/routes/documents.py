from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse

from app.core.security import get_current_user, require_role
from app.schemas.document_schema import (
	AuditLogResponse,
	DocumentErrorRequest,
	DocumentProcessRequest,
	DocumentResponse,
	DocumentReviewRequest,
	DocumentTypeCreateRequest,
	DocumentTypeResponse,
	DocumentTypeUpdateRequest,
	PatientCreateRequest,
	PatientNameUpdateRequest,
	PatientResponse,
)
from app.services.document_service import (
	create_document_type,
	create_patient,
	get_document_audit,
	get_document_by_id,
	get_processed_document_file_path,
	get_document_type_by_id,
	list_documents,
	list_document_types,
	list_patients,
	mark_document_error,
	process_document,
	review_document,
	toggle_document_type_status,
	update_patient,
	update_document_type,
)


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=List[DocumentResponse])
def listar_documentos_endpoint(
	estado: Optional[str] = Query(default=None),
	id_paciente: Optional[int] = Query(default=None),
	id_tipo: Optional[int] = Query(default=None),
	fecha_desde: Optional[date] = Query(default=None),
	fecha_hasta: Optional[date] = Query(default=None),
	q: Optional[str] = Query(default=None, min_length=1),
	current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[DocumentResponse]:
	if current_user.get("rol") == "CONSULTA":
		estado = "PROCESADO"

	return list_documents(
		estado=estado,
		id_paciente=id_paciente,
		id_tipo=id_tipo,
		fecha_desde=fecha_desde,
		fecha_hasta=fecha_hasta,
		q=q,
	)


@router.get("/meta/tipos", response_model=List[DocumentTypeResponse])
def listar_tipos_documento_endpoint(
	incluir_inactivos: bool = Query(default=False),
	_: Dict[str, Any] = Depends(get_current_user),
) -> List[DocumentTypeResponse]:
	return list_document_types(include_inactive=incluir_inactivos)


@router.get("/meta/tipos/{id_tipo}", response_model=DocumentTypeResponse)
def obtener_tipo_documento_endpoint(
	id_tipo: int,
	_: Dict[str, Any] = Depends(require_role("SUPERADMIN")),
) -> DocumentTypeResponse:
	return get_document_type_by_id(id_tipo)


@router.post("/meta/tipos", response_model=DocumentTypeResponse, status_code=status.HTTP_201_CREATED)
def crear_tipo_documento_endpoint(
	payload: DocumentTypeCreateRequest,
	current_user: Dict[str, Any] = Depends(require_role("SUPERADMIN")),
) -> DocumentTypeResponse:
	return create_document_type(payload, current_user)


@router.put("/meta/tipos/{id_tipo}", response_model=DocumentTypeResponse)
def actualizar_tipo_documento_endpoint(
	id_tipo: int,
	payload: DocumentTypeUpdateRequest,
	current_user: Dict[str, Any] = Depends(require_role("SUPERADMIN")),
) -> DocumentTypeResponse:
	return update_document_type(id_tipo, payload, current_user)


@router.delete("/meta/tipos/{id_tipo}", response_model=Dict[str, str])
def toggle_tipo_documento_endpoint(
	id_tipo: int,
	current_user: Dict[str, Any] = Depends(require_role("SUPERADMIN")),
) -> Dict[str, str]:
	return toggle_document_type_status(id_tipo, current_user)


@router.get("/meta/pacientes", response_model=List[PatientResponse])
def listar_pacientes_endpoint(
	q: Optional[str] = Query(default=None, min_length=1),
	_: Dict[str, Any] = Depends(get_current_user),
) -> List[PatientResponse]:
	return list_patients(q=q)


@router.post("/meta/pacientes", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def crear_paciente_endpoint(
	payload: PatientCreateRequest,
	_: Dict[str, Any] = Depends(get_current_user),
) -> PatientResponse:
	return create_patient(payload)


@router.patch("/meta/pacientes/{id_paciente}/nombre", response_model=PatientResponse)
def actualizar_nombre_paciente_endpoint(
	id_paciente: int,
	payload: PatientNameUpdateRequest,
	current_user: Dict[str, Any] = Depends(require_role("SUPERADMIN")),
) -> PatientResponse:
	return update_patient(id_paciente, payload.nombre, current_user)


@router.get("/{id_documento}", response_model=DocumentResponse)
def obtener_documento_endpoint(
	id_documento: int,
	_: Dict[str, Any] = Depends(get_current_user),
) -> DocumentResponse:
	return get_document_by_id(id_documento)


@router.get("/{id_documento}/file")
def abrir_archivo_documento_endpoint(
	id_documento: int,
	_: Dict[str, Any] = Depends(get_current_user),
) -> FileResponse:
	file_path = get_processed_document_file_path(id_documento)
	return FileResponse(
		path=file_path,
		media_type="application/pdf",
		filename=file_path.name,
	)


@router.patch("/{id_documento}/review", response_model=DocumentResponse)
def revisar_documento_endpoint(
	id_documento: int,
	payload: DocumentReviewRequest,
	current_user: Dict[str, Any] = Depends(get_current_user),
) -> DocumentResponse:
	return review_document(id_documento, payload, current_user)


@router.patch("/{id_documento}/process", response_model=DocumentResponse)
def procesar_documento_endpoint(
	id_documento: int,
	payload: DocumentProcessRequest,
	current_user: Dict[str, Any] = Depends(get_current_user),
) -> DocumentResponse:
	return process_document(id_documento, payload, current_user)


@router.patch("/{id_documento}/error", response_model=DocumentResponse)
def marcar_documento_error_endpoint(
	id_documento: int,
	payload: DocumentErrorRequest,
	current_user: Dict[str, Any] = Depends(get_current_user),
) -> DocumentResponse:
	return mark_document_error(id_documento, payload, current_user)


@router.get("/{id_documento}/audit", response_model=List[AuditLogResponse])
def obtener_auditoria_documento_endpoint(
	id_documento: int,
	_: Dict[str, Any] = Depends(get_current_user),
) -> List[AuditLogResponse]:
	return get_document_audit(id_documento)
