DO $$
BEGIN
IF NOT EXISTS (
SELECT FROM pg_catalog.pg_roles WHERE rolname = 'medarch_user'
) THEN
CREATE ROLE medarch_user LOGIN PASSWORD 'Medarch123*';
END IF;
END
$$;

-- ============================================
-- 2. CREAR BASE DE DATOS
-- ============================================

DO $$
BEGIN
IF NOT EXISTS (
SELECT FROM pg_database WHERE datname = 'medarch_db'
) THEN
CREATE DATABASE medarch_db OWNER medarch_user;
END IF;
END
$$;

-- ============================================
-- IMPORTANTE:
-- Después de esto debes conectarte a:
-- medarch_db
-- ============================================

-- ============================================
-- 3. CREAR ESQUEMA
-- ============================================

CREATE SCHEMA IF NOT EXISTS gesdoc AUTHORIZATION medarch_user;

SET search_path TO gesdoc;

-- ============================================
-- 3.1 PERMISOS DE APLICACION
-- ============================================

GRANT USAGE ON SCHEMA gesdoc TO medarch_user;

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA gesdoc
TO medarch_user;

GRANT USAGE, SELECT
ON ALL SEQUENCES IN SCHEMA gesdoc
TO medarch_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA gesdoc
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO medarch_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA gesdoc
GRANT USAGE, SELECT ON SEQUENCES TO medarch_user;

-- ============================================
-- 4. TABLA: PACIENTES
-- ============================================

CREATE TABLE IF NOT EXISTS pacientes (
id_paciente SERIAL PRIMARY KEY,
numero_documento VARCHAR(20) NOT NULL UNIQUE,
nombre VARCHAR(150),
fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 5. TABLA: TIPOS_DOCUMENTO
-- ============================================

CREATE TABLE IF NOT EXISTS tipos_documento (
id_tipo SERIAL PRIMARY KEY,
codigo VARCHAR(10) NOT NULL UNIQUE,
descripcion VARCHAR(100) NOT NULL,
activo BOOLEAN DEFAULT TRUE
);

-- ============================================
-- 6. TABLA: USUARIOS
-- ============================================

CREATE TABLE IF NOT EXISTS usuarios (
id_usuario SERIAL PRIMARY KEY,
usuario VARCHAR(50) NOT NULL UNIQUE,
nombre VARCHAR(150) NOT NULL,
rol VARCHAR(50) NOT NULL CHECK (rol IN ('CONSULTA','ARCHIVO','SUPERADMIN')),
activo BOOLEAN DEFAULT TRUE,
fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 7. TABLA: DOCUMENTOS (MODELO HÍBRIDO)
-- ============================================

CREATE TABLE IF NOT EXISTS documentos (
id_documento BIGSERIAL PRIMARY KEY,

-- DATOS INICIALES (WATCHER)
ruta_temporal VARCHAR(500) NOT NULL,
nombre_archivo_original VARCHAR(255) NOT NULL,
fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

-- ESTADO
estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE'
    CHECK (estado IN ('PENDIENTE','EN_REVISION','PROCESADO','ERROR')),

-- DATOS COMPLETADOS EN PROCESAMIENTO
id_paciente INT,
id_tipo INT,
fecha DATE,
consecutivo INT,

nombre_archivo VARCHAR(255),
ruta_archivo VARCHAR(500),

fecha_procesado TIMESTAMP,

-- RELACIONES
CONSTRAINT fk_doc_paciente FOREIGN KEY (id_paciente)
    REFERENCES pacientes(id_paciente),

CONSTRAINT fk_doc_tipo FOREIGN KEY (id_tipo)
    REFERENCES tipos_documento(id_tipo)

);

-- ============================================
-- 8. TABLA: LOG_AUDITORIA
-- ============================================

CREATE TABLE IF NOT EXISTS log_auditoria (
id_log BIGSERIAL PRIMARY KEY,

id_documento BIGINT,
id_usuario INT NOT NULL,

accion VARCHAR(50) NOT NULL,
detalle VARCHAR(500),

fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

CONSTRAINT fk_log_doc FOREIGN KEY (id_documento)
    REFERENCES documentos(id_documento),

CONSTRAINT fk_log_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuarios(id_usuario)

);

-- ============================================
-- 9. ÍNDICES (RENDIMIENTO)
-- ============================================

-- Búsqueda por paciente
CREATE INDEX IF NOT EXISTS ix_doc_paciente
ON documentos (id_paciente);

-- Bandeja de pendientes
CREATE INDEX IF NOT EXISTS ix_doc_estado
ON documentos (estado);

-- Búsqueda por fecha
CREATE INDEX IF NOT EXISTS ix_doc_fecha
ON documentos (fecha);

-- Logs por documento
CREATE INDEX IF NOT EXISTS ix_log_documento
ON log_auditoria (id_documento);

-- ============================================
-- 10. REGLA PARA EVITAR DUPLICADOS LÓGICOS
-- ============================================

CREATE UNIQUE INDEX IF NOT EXISTS ux_doc_unico
ON documentos (id_paciente, id_tipo, fecha, consecutivo)
WHERE estado = 'PROCESADO';

-- ============================================
-- 11. CREACION DE NUEVA COLUMNA PARA USUARIOS
-- ============================================
ALTER TABLE gesdoc.usuarios
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);