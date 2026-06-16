from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from psycopg2 import IntegrityError

from app.core.config import settings
from app.db.session import get_db_cursor
from app.services.nas_service import nas_storage_service
from app.schemas.document_schema import (
	AuditLogResponse,
	DocumentErrorRequest,
	DocumentProcessRequest,
	DocumentResponse,
	DocumentReviewRequest,
	DocumentTypeCreateRequest,
	DocumentTypeUpdateRequest,
	DocumentTypeResponse,
	PatientCreateRequest,
	PatientResponse,
)


ALLOWED_PROCESS_ROLES = {"ARCHIVO", "SUPERADMIN"}


def _ensure_write_role(current_user: Dict[str, Any]) -> None:
	if current_user.get("rol") not in ALLOWED_PROCESS_ROLES:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="No tienes permisos para esta operación",
		)


def _get_document_row(cur: Any, id_documento: int) -> Optional[Dict[str, Any]]:
	cur.execute(
		"""
		SELECT
			d.id_documento,
			d.ruta_temporal,
			d.nombre_archivo_original,
			d.fecha_carga,
			d.estado,
			d.id_paciente,
			p.numero_documento AS paciente_numero_documento,
			p.nombre AS paciente_nombre,
			d.id_tipo,
			t.codigo AS tipo_codigo,
			t.descripcion AS tipo_descripcion,
			d.fecha,
			d.consecutivo,
			d.nombre_archivo,
			d.ruta_archivo,
			d.fecha_procesado
		FROM gesdoc.documentos d
		LEFT JOIN gesdoc.pacientes p ON p.id_paciente = d.id_paciente
		LEFT JOIN gesdoc.tipos_documento t ON t.id_tipo = d.id_tipo
		WHERE d.id_documento = %s
		""",
		(id_documento,),
	)
	return cur.fetchone()


def _build_document_response(row: Dict[str, Any]) -> DocumentResponse:
	return DocumentResponse(**row)


def _build_document_file_name(tipo_codigo: str, numero_documento: str, fecha: date, consecutivo: int) -> str:
	return f"{tipo_codigo}_{numero_documento}_{fecha.isoformat()}_{consecutivo:03d}.pdf"


def _log_audit(
	cur: Any,
	id_documento: Optional[int],
	id_usuario: int,
	accion: str,
	detalle: Optional[str],
) -> None:
	cur.execute(
		"""
		INSERT INTO gesdoc.log_auditoria (
			id_documento,
			id_usuario,
			accion,
			detalle
		)
		VALUES (%s, %s, %s, %s)
		""",
		(id_documento, id_usuario, accion, detalle),
	)


def _set_document_error_state(
	id_documento: int,
	id_usuario: int,
	detalle: str,
) -> DocumentResponse:
	with get_db_cursor(dict_cursor=True) as (_, cur):
		row = _get_document_row(cur, id_documento)
		if not row:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="Documento no encontrado",
			)

		cur.execute(
			"""
			UPDATE gesdoc.documentos
			SET estado = 'ERROR'
			WHERE id_documento = %s
			""",
			(id_documento,),
		)

		_log_audit(
			cur,
			id_documento,
			id_usuario,
			"DOCUMENTO_ERROR",
			detalle,
		)

		updated = _get_document_row(cur, id_documento)

	return _build_document_response(updated)


def _normalize_document_type_fields(codigo: str, descripcion: str) -> tuple[str, str]:
	normalized_codigo = codigo.strip().upper()
	normalized_descripcion = descripcion.strip()

	if not normalized_codigo:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="El código del tipo de documento es obligatorio",
		)

	if not normalized_descripcion:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="La descripción del tipo de documento es obligatoria",
		)

	return normalized_codigo, normalized_descripcion


def _upsert_review_patient(cur: Any, payload: DocumentReviewRequest) -> Dict[str, Any]:
	numero_documento = payload.numero_documento.strip()
	nombre_paciente = (payload.nombre_paciente or "").strip() or numero_documento

	if not numero_documento:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="La identificación del paciente es obligatoria",
		)

	if payload.id_paciente:
		cur.execute(
			"""
			SELECT id_paciente
			FROM gesdoc.pacientes
			WHERE id_paciente = %s
			""",
			(payload.id_paciente,),
		)
		existing_patient = cur.fetchone()
		if not existing_patient:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="Paciente no encontrado",
			)

		cur.execute(
			"""
			SELECT id_paciente
			FROM gesdoc.pacientes
			WHERE numero_documento = %s
			  AND id_paciente <> %s
			""",
			(numero_documento, payload.id_paciente),
		)
		conflicting_patient = cur.fetchone()
		if conflicting_patient:
			raise HTTPException(
				status_code=status.HTTP_409_CONFLICT,
				detail="Ya existe otro paciente con esa identificación",
			)

		cur.execute(
			"""
			UPDATE gesdoc.pacientes
			SET numero_documento = %s,
			    nombre = %s
			WHERE id_paciente = %s
			RETURNING id_paciente, numero_documento, nombre
			""",
			(numero_documento, nombre_paciente, payload.id_paciente),
		)
		patient = cur.fetchone()
		if not patient:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="Paciente no encontrado",
			)
		return patient

	cur.execute(
		"""
		SELECT id_paciente, numero_documento, nombre
		FROM gesdoc.pacientes
		WHERE numero_documento = %s
		""",
		(numero_documento,),
	)
	patient = cur.fetchone()
	if patient:
		cur.execute(
			"""
			UPDATE gesdoc.pacientes
			SET nombre = %s
			WHERE id_paciente = %s
			RETURNING id_paciente, numero_documento, nombre
			""",
			(nombre_paciente, patient["id_paciente"]),
		)
		updated_patient = cur.fetchone()
		return updated_patient or patient

	cur.execute(
		"""
		INSERT INTO gesdoc.pacientes (numero_documento, nombre)
		VALUES (%s, %s)
		RETURNING id_paciente, numero_documento, nombre
		""",
		(numero_documento, nombre_paciente),
	)
	created_patient = cur.fetchone()
	if not created_patient:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="No fue posible crear el paciente",
		)
	return created_patient


def list_documents(
	estado: Optional[str] = None,
	id_paciente: Optional[int] = None,
	id_tipo: Optional[int] = None,
	fecha_desde: Optional[date] = None,
	fecha_hasta: Optional[date] = None,
	q: Optional[str] = None,
) -> List[DocumentResponse]:
	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			query = [
				"""
				SELECT
					d.id_documento,
					d.ruta_temporal,
					d.nombre_archivo_original,
					d.fecha_carga,
					d.estado,
					d.id_paciente,
					p.numero_documento AS paciente_numero_documento,
					p.nombre AS paciente_nombre,
					d.id_tipo,
					t.codigo AS tipo_codigo,
					t.descripcion AS tipo_descripcion,
					d.fecha,
					d.consecutivo,
					d.nombre_archivo,
					d.ruta_archivo,
					d.fecha_procesado
				FROM gesdoc.documentos d
				LEFT JOIN gesdoc.pacientes p ON p.id_paciente = d.id_paciente
				LEFT JOIN gesdoc.tipos_documento t ON t.id_tipo = d.id_tipo
				WHERE 1 = 1
				"""
			]
			params: List[Any] = []

			if estado:
				query.append("AND d.estado = %s")
				params.append(estado)
			if id_paciente:
				query.append("AND d.id_paciente = %s")
				params.append(id_paciente)
			if id_tipo:
				query.append("AND d.id_tipo = %s")
				params.append(id_tipo)
			if fecha_desde:
				query.append("AND d.fecha >= %s")
				params.append(fecha_desde)
			if fecha_hasta:
				query.append("AND d.fecha <= %s")
				params.append(fecha_hasta)
			if q:
				query.append(
					"""
					AND (
						COALESCE(d.nombre_archivo_original, '') ILIKE %s OR
						COALESCE(d.ruta_temporal, '') ILIKE %s OR
						COALESCE(d.nombre_archivo, '') ILIKE %s OR
						COALESCE(p.numero_documento, '') ILIKE %s OR
						COALESCE(p.nombre, '') ILIKE %s OR
						COALESCE(t.codigo, '') ILIKE %s OR
						COALESCE(t.descripcion, '') ILIKE %s
					)
					"""
				)
				pattern = f"%{q}%"
				params.extend([pattern, pattern, pattern, pattern, pattern, pattern, pattern])

			query.append("ORDER BY d.fecha_carga DESC, d.id_documento DESC")
			cur.execute("\n".join(query), tuple(params))
			documents = cur.fetchall()
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al listar documentos",
		) from exc

	return [_build_document_response(document) for document in documents]


def get_document_by_id(id_documento: int) -> DocumentResponse:
	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			row = _get_document_row(cur, id_documento)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al consultar documento",
		) from exc

	if not row:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Documento no encontrado",
		)

	return _build_document_response(row)


def review_document(
	id_documento: int,
	payload: DocumentReviewRequest,
	current_user: Dict[str, Any],
) -> DocumentResponse:
	_ensure_write_role(current_user)

	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			row = _get_document_row(cur, id_documento)
			if not row:
				raise HTTPException(
					status_code=status.HTTP_404_NOT_FOUND,
					detail="Documento no encontrado",
				)

			if row["estado"] == "PROCESADO":
				raise HTTPException(
					status_code=status.HTTP_409_CONFLICT,
					detail="El documento ya fue procesado",
				)

			patient = _upsert_review_patient(cur, payload)

			cur.execute(
				"""
				SELECT id_tipo
				FROM gesdoc.tipos_documento
				WHERE id_tipo = %s AND activo = TRUE
				""",
				(payload.id_tipo,),
			)
			if not cur.fetchone():
				raise HTTPException(
					status_code=status.HTTP_404_NOT_FOUND,
					detail="Tipo de documento no encontrado o inactivo",
				)

			cur.execute(
				"""
				UPDATE gesdoc.documentos
				SET id_paciente = %s,
				    id_tipo = %s,
				    fecha = %s,
				    consecutivo = %s,
				    estado = 'EN_REVISION'
				WHERE id_documento = %s
				""",
				(
					patient["id_paciente"],
					payload.id_tipo,
					payload.fecha,
					payload.consecutivo,
					id_documento,
				),
			)

			_log_audit(
				cur,
				id_documento,
				int(current_user["id_usuario"]),
				"DOCUMENTO_EN_REVISION",
				"Documento validado manualmente y marcado en revisión",
			)

			updated = _get_document_row(cur, id_documento)
	except IntegrityError as exc:
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail="Ya existe un documento procesado con la misma combinación de paciente, tipo, fecha y consecutivo",
		) from exc
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al revisar documento",
		) from exc

	return _build_document_response(updated)


def process_document(
	id_documento: int,
	payload: DocumentProcessRequest,
	current_user: Dict[str, Any],
) -> DocumentResponse:
	_ensure_write_role(current_user)

	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			row = _get_document_row(cur, id_documento)
			if not row:
				raise HTTPException(
					status_code=status.HTTP_404_NOT_FOUND,
					detail="Documento no encontrado",
				)

			if row["estado"] == "PROCESADO":
				raise HTTPException(
					status_code=status.HTTP_409_CONFLICT,
					detail="El documento ya fue procesado",
				)

			cur.execute(
				"""
				SELECT id_paciente, numero_documento, nombre
				FROM gesdoc.pacientes
				WHERE id_paciente = %s
				""",
				(payload.id_paciente,),
			)
			paciente = cur.fetchone()
			if not paciente:
				raise HTTPException(
					status_code=status.HTTP_404_NOT_FOUND,
					detail="Paciente no encontrado",
				)

			cur.execute(
				"""
				SELECT id_tipo, codigo, descripcion
				FROM gesdoc.tipos_documento
				WHERE id_tipo = %s AND activo = TRUE
				""",
				(payload.id_tipo,),
			)
			tipo_documento = cur.fetchone()
			if not tipo_documento:
				raise HTTPException(
					status_code=status.HTTP_404_NOT_FOUND,
					detail="Tipo de documento no encontrado o inactivo",
				)

			nombre_archivo = _build_document_file_name(
				tipo_documento["codigo"],
				paciente["numero_documento"],
				payload.fecha,
				payload.consecutivo,
			)
			default_destination = nas_storage_service.build_processed_path(
				tipo_documento["codigo"],
				paciente["numero_documento"],
				payload.fecha.isoformat(),
				payload.consecutivo,
			)
			destination_path = default_destination

			source_path = Path(row["ruta_temporal"])
			try:
				nas_storage_service.copy_verify_delete(str(source_path), destination_path)
			except HTTPException as exc:
				_set_document_error_state(
					id_documento,
					int(current_user["id_usuario"]),
					f"Error NAS al procesar documento: {exc.detail}",
				)
				raise

			cur.execute(
				"""
				UPDATE gesdoc.documentos
				SET id_paciente = %s,
				    id_tipo = %s,
				    fecha = %s,
				    consecutivo = %s,
				    nombre_archivo = %s,
				    ruta_archivo = %s,
				    estado = 'PROCESADO',
				    fecha_procesado = CURRENT_TIMESTAMP
				WHERE id_documento = %s
				""",
				(
					payload.id_paciente,
					payload.id_tipo,
					payload.fecha,
					payload.consecutivo,
					nombre_archivo,
					str(destination_path),
					id_documento,
				),
			)

			_log_audit(
				cur,
				id_documento,
				int(current_user["id_usuario"]),
				"DOCUMENTO_PROCESADO",
				f"Documento copiado a NAS como {nombre_archivo}",
			)

			updated = _get_document_row(cur, id_documento)

		try:
			source_path.unlink()
		except FileNotFoundError:
			pass
		except Exception as exc:
			with get_db_cursor(dict_cursor=True) as (_, cur):
				_log_audit(
					cur,
					id_documento,
					int(current_user["id_usuario"]),
					"DOCUMENTO_PROCESADO_CON_ADVERTENCIA",
					f"No se pudo eliminar el original: {exc}",
				)
	except HTTPException:
		raise
	except Exception as exc:
		try:
			if destination_path.exists():
				destination_path.unlink()
		except Exception:
			pass
		try:
			_set_document_error_state(
				id_documento,
				int(current_user["id_usuario"]),
				f"Error inesperado al procesar documento: {exc}",
			)
		except Exception:
			pass
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al procesar documento",
		) from exc

	return _build_document_response(updated)


def mark_document_error(
	id_documento: int,
	payload: DocumentErrorRequest,
	current_user: Dict[str, Any],
) -> DocumentResponse:
	_ensure_write_role(current_user)

	try:
		updated = _set_document_error_state(
			id_documento,
			int(current_user["id_usuario"]),
			payload.detalle,
		)
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al marcar documento como error",
		) from exc

	return _build_document_response(updated)


def list_document_types(include_inactive: bool = False) -> List[DocumentTypeResponse]:
	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			query = [
				"""
				SELECT id_tipo, codigo, descripcion, activo
				FROM gesdoc.tipos_documento
				WHERE 1 = 1
				"""
			]
			if not include_inactive:
				query.append("AND activo = TRUE")
			query.append("ORDER BY codigo")
			cur.execute(
				"\n".join(query)
			)
			types = cur.fetchall()
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al listar tipos de documento",
		) from exc

	return [DocumentTypeResponse(**document_type) for document_type in types]


def get_document_type_by_id(id_tipo: int) -> DocumentTypeResponse:
	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			cur.execute(
				"""
				SELECT id_tipo, codigo, descripcion, activo
				FROM gesdoc.tipos_documento
				WHERE id_tipo = %s
				""",
				(id_tipo,),
			)
			tipo_documento = cur.fetchone()
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al consultar tipo de documento",
		) from exc

	if not tipo_documento:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Tipo de documento no encontrado",
		)

	return DocumentTypeResponse(**tipo_documento)


def create_document_type(
	payload: DocumentTypeCreateRequest,
	current_user: Dict[str, Any],
) -> DocumentTypeResponse:
	codigo, descripcion = _normalize_document_type_fields(payload.codigo, payload.descripcion)

	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			cur.execute(
				"""
				SELECT id_tipo
				FROM gesdoc.tipos_documento
				WHERE LOWER(codigo) = LOWER(%s)
				""",
				(codigo,),
			)
			if cur.fetchone():
				raise HTTPException(
					status_code=status.HTTP_409_CONFLICT,
					detail="Ya existe un tipo de documento con ese código",
				)

			cur.execute(
				"""
				INSERT INTO gesdoc.tipos_documento (codigo, descripcion, activo)
				VALUES (%s, %s, %s)
				RETURNING id_tipo, codigo, descripcion, activo
				""",
				(codigo, descripcion, payload.activo),
			)
			tipo_documento = cur.fetchone()
			if tipo_documento:
				_log_audit(
					cur,
					None,
					int(current_user["id_usuario"]),
					"CREAR_TIPO_DOCUMENTO",
					f"Tipo creado: {codigo} - {descripcion} (activo={payload.activo})",
				)
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al crear tipo de documento",
		) from exc

	return DocumentTypeResponse(**tipo_documento)


def update_document_type(
	id_tipo: int,
	payload: DocumentTypeUpdateRequest,
	current_user: Dict[str, Any],
) -> DocumentTypeResponse:
	codigo, descripcion = _normalize_document_type_fields(payload.codigo, payload.descripcion)

	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			cur.execute(
				"""
				SELECT id_tipo
				FROM gesdoc.tipos_documento
				WHERE id_tipo = %s
				""",
				(id_tipo,),
			)
			if not cur.fetchone():
				raise HTTPException(
					status_code=status.HTTP_404_NOT_FOUND,
					detail="Tipo de documento no encontrado",
				)

			cur.execute(
				"""
				SELECT id_tipo
				FROM gesdoc.tipos_documento
				WHERE LOWER(codigo) = LOWER(%s)
				  AND id_tipo <> %s
				""",
				(codigo, id_tipo),
			)
			if cur.fetchone():
				raise HTTPException(
					status_code=status.HTTP_409_CONFLICT,
					detail="Ya existe otro tipo de documento con ese código",
				)

			cur.execute(
				"""
				UPDATE gesdoc.tipos_documento
				SET codigo = %s,
				    descripcion = %s,
				    activo = %s
				WHERE id_tipo = %s
				RETURNING id_tipo, codigo, descripcion, activo
				""",
				(codigo, descripcion, payload.activo, id_tipo),
			)
			tipo_documento = cur.fetchone()
			if tipo_documento:
				_log_audit(
					cur,
					None,
					int(current_user["id_usuario"]),
					"ACTUALIZAR_TIPO_DOCUMENTO",
					f"Tipo actualizado: id_tipo={id_tipo}, codigo={codigo}, activo={payload.activo}",
				)
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al actualizar tipo de documento",
		) from exc

	return DocumentTypeResponse(**tipo_documento)


def toggle_document_type_status(id_tipo: int, current_user: Dict[str, Any]) -> Dict[str, str]:
	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			cur.execute(
				"""
				SELECT id_tipo, codigo, descripcion, activo
				FROM gesdoc.tipos_documento
				WHERE id_tipo = %s
				""",
				(id_tipo,),
			)
			tipo_documento = cur.fetchone()
			if not tipo_documento:
				raise HTTPException(
					status_code=status.HTTP_404_NOT_FOUND,
					detail="Tipo de documento no encontrado",
				)

			nuevo_estado = not tipo_documento["activo"]
			cur.execute(
				"""
				UPDATE gesdoc.tipos_documento
				SET activo = %s
				WHERE id_tipo = %s
				""",
				(nuevo_estado, id_tipo),
			)
			_log_audit(
				cur,
				None,
				int(current_user["id_usuario"]),
				"TOGGLE_TIPO_DOCUMENTO",
				f"Tipo {id_tipo} {'activado' if nuevo_estado else 'desactivado'}: {tipo_documento['codigo']}",
			)
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al cambiar estado del tipo de documento",
		) from exc

	return {"message": f"Tipo de documento {'activado' if nuevo_estado else 'desactivado'} correctamente"}


def list_patients(q: Optional[str] = None) -> List[PatientResponse]:
	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			query = [
				"""
				SELECT id_paciente, numero_documento, nombre, fecha_creacion
				FROM gesdoc.pacientes
				WHERE 1 = 1
				"""
			]
			params: List[Any] = []

			if q:
				query.append(
					"""
					AND (
						numero_documento ILIKE %s OR
						COALESCE(nombre, '') ILIKE %s
					)
					"""
				)
				pattern = f"%{q}%"
				params.extend([pattern, pattern])

			query.append("ORDER BY numero_documento")
			cur.execute("\n".join(query), tuple(params))
			patients = cur.fetchall()
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al listar pacientes",
		) from exc

	return [PatientResponse(**patient) for patient in patients]


def update_patient(id_paciente: int, numero_documento: str, nombre: str) -> PatientResponse:
	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			cur.execute(
				"""
				SELECT id_paciente
				FROM gesdoc.pacientes
				WHERE id_paciente = %s
				""",
				(id_paciente,),
			)
			if not cur.fetchone():
				raise HTTPException(
					status_code=status.HTTP_404_NOT_FOUND,
					detail="Paciente no encontrado",
				)

			cur.execute(
				"""
				SELECT id_paciente
				FROM gesdoc.pacientes
				WHERE numero_documento = %s
				  AND id_paciente <> %s
				""",
				(numero_documento, id_paciente),
			)
			if cur.fetchone():
				raise HTTPException(
					status_code=status.HTTP_409_CONFLICT,
					detail="Ya existe otro paciente con esa identificación",
				)

			cur.execute(
				"""
				UPDATE gesdoc.pacientes
				SET numero_documento = %s,
				    nombre = %s
				WHERE id_paciente = %s
				RETURNING id_paciente, numero_documento, nombre, fecha_creacion
				""",
				(numero_documento, nombre, id_paciente),
			)
			patient = cur.fetchone()
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al actualizar paciente",
		) from exc

	return PatientResponse(**patient)


def create_patient(payload: PatientCreateRequest) -> PatientResponse:
	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			cur.execute(
				"""
				SELECT id_paciente
				FROM gesdoc.pacientes
				WHERE numero_documento = %s
				""",
				(payload.numero_documento,),
			)
			if cur.fetchone():
				raise HTTPException(
					status_code=status.HTTP_409_CONFLICT,
					detail="El paciente ya existe",
				)

			cur.execute(
				"""
				INSERT INTO gesdoc.pacientes (numero_documento, nombre)
				VALUES (%s, %s)
				RETURNING id_paciente, numero_documento, nombre, fecha_creacion
				""",
				(payload.numero_documento, payload.nombre),
			)
			patient = cur.fetchone()
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al crear paciente",
		) from exc

	return PatientResponse(**patient)


def get_document_audit(id_documento: int) -> List[AuditLogResponse]:
	try:
		with get_db_cursor(dict_cursor=True) as (_, cur):
			cur.execute(
				"""
				SELECT
					l.id_log,
					l.id_documento,
					l.id_usuario,
					u.usuario,
					l.accion,
					l.detalle,
					l.fecha
				FROM gesdoc.log_auditoria l
				INNER JOIN gesdoc.usuarios u ON u.id_usuario = l.id_usuario
				WHERE l.id_documento = %s
				ORDER BY l.fecha DESC, l.id_log DESC
				""",
				(id_documento,),
			)
			logs = cur.fetchall()
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error al consultar auditoría del documento",
		) from exc

	return [AuditLogResponse(**log) for log in logs]
