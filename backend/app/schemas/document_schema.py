from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentReviewRequest(BaseModel):
	id_paciente: Optional[int] = Field(default=None, gt=0)
	numero_documento: str = Field(..., min_length=3, max_length=20)
	nombre_paciente: Optional[str] = Field(default=None, min_length=2, max_length=150)
	id_tipo: int = Field(..., gt=0)
	fecha: date
	consecutivo: int = Field(..., ge=1)


class DocumentProcessRequest(BaseModel):
	id_paciente: int = Field(..., gt=0)
	id_tipo: int = Field(..., gt=0)
	fecha: date
	consecutivo: int = Field(..., ge=1)


class DocumentErrorRequest(BaseModel):
	detalle: str = Field(..., min_length=3, max_length=500)


class DocumentResponse(BaseModel):
	id_documento: int
	ruta_temporal: str
	nombre_archivo_original: str
	fecha_carga: datetime
	estado: str
	id_paciente: Optional[int] = None
	paciente_numero_documento: Optional[str] = None
	paciente_nombre: Optional[str] = None
	id_tipo: Optional[int] = None
	tipo_codigo: Optional[str] = None
	tipo_descripcion: Optional[str] = None
	fecha: Optional[date] = None
	consecutivo: Optional[int] = None
	nombre_archivo: Optional[str] = None
	ruta_archivo: Optional[str] = None
	fecha_procesado: Optional[datetime] = None


class DocumentTypeResponse(BaseModel):
	id_tipo: int
	codigo: str
	descripcion: str
	activo: bool


class DocumentTypeCreateRequest(BaseModel):
	codigo: str = Field(..., min_length=2, max_length=10)
	descripcion: str = Field(..., min_length=2, max_length=100)
	activo: bool = True


class DocumentTypeUpdateRequest(BaseModel):
	codigo: str = Field(..., min_length=2, max_length=10)
	descripcion: str = Field(..., min_length=2, max_length=100)
	activo: bool


class PatientCreateRequest(BaseModel):
	numero_documento: str = Field(..., min_length=3, max_length=20)
	nombre: str = Field(..., min_length=2, max_length=150)


class PatientUpdateRequest(BaseModel):
	numero_documento: str = Field(..., min_length=3, max_length=20)
	nombre: str = Field(..., min_length=2, max_length=150)


class PatientResponse(BaseModel):
	id_paciente: int
	numero_documento: str
	nombre: Optional[str] = None
	fecha_creacion: datetime


class AuditLogResponse(BaseModel):
	id_log: int
	id_documento: Optional[int] = None
	id_usuario: int
	usuario: Optional[str] = None
	accion: str
	detalle: Optional[str] = None
	fecha: datetime
