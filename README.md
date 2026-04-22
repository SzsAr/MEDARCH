# MEDARCH

MEDARCH is a document management system for digitized clinical records. The repository is currently in the specification and database schema stage.

## What is in this repository

- `PROJECT_CONTEXT.md`: functional and architectural context for the project.
- `bd.sql`: PostgreSQL schema, tables, indexes, and initial database setup.

## Current status

- No application code has been added yet.
- There are no build or test commands defined yet.
- The database schema uses the `gesdoc` schema in PostgreSQL.

## Database setup

Apply `bd.sql` to your PostgreSQL instance to create the database objects used by the project.

Important: review the credentials in `bd.sql` before running it in any shared or production environment.

## Project rules

- The logical source of truth is the database.
- The physical source of truth is the NAS.
- OCR is only assistive; final classification is always human-validated.
- Processed documents must follow the naming format `TIPO_CEDULA_FECHA_CONSECUTIVO.pdf`.

## Reference

See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for the complete workflow, architecture, and business rules.