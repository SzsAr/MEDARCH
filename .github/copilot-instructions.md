# Project Guidelines

## Code Style
- Keep implementation modular by component: watcher, API, frontend, and infrastructure scripts.
- Use clear domain names in Spanish-aligned terms already used in the project (for example: cedula, tipo_documento, estado, ruta_archivo).
- Prefer explicit validation and error handling over implicit behavior, especially in ingestion and file movement steps.
- Preserve database naming and schema conventions defined in [bd.sql](../bd.sql).

## Architecture
- Follow the target architecture documented in [PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md):
  - Watcher (Python) detects files in PENDIENTES.
  - API (FastAPI) manages state transitions and processing.
  - Frontend (HTML/JS/Bootstrap) supports manual validation.
  - PostgreSQL (schema gesdoc) stores metadata and audit history.
  - NAS stores final files as source of physical truth.
- Respect the logical/physical truth split:
  - Database is logical truth.
  - NAS is physical truth.

## Build and Test
- Current workspace is in specification/schema stage; there are no app build or test commands yet.
- For database setup, apply [bd.sql](../bd.sql) in PostgreSQL and continue work against schema gesdoc.
- When adding executable components, include runnable commands in the relevant README or docs file and keep this file updated.

## Conventions
- Keep the document lifecycle aligned with project states: PENDIENTE, EN_REVISION, PROCESADO, ERROR.
- Enforce business-critical rule: OCR is assistive only; final classification and metadata are human-validated.
- Preserve file naming contract for processed documents: TIPO_CEDULA_FECHA_CONSECUTIVO.pdf.
- Prevent logical duplicates via the key (id_paciente, id_tipo, fecha, consecutivo) for processed records.
- Ensure every significant change in document workflow records an audit event in log_auditoria.

## References
- Functional and operational rules: [PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md)
- Database schema and constraints: [bd.sql](../bd.sql)
