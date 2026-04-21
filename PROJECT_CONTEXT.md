# 🧠 MEDARCH - CONTEXTO COMPLETO DEL PROYECTO

---

# 1. 📌 DESCRIPCIÓN GENERAL

**MEDARCH** es un sistema de gestión documental para historias clínicas digitalizadas.

El sistema permite:

* Capturar documentos escaneados desde una carpeta local
* Clasificarlos manualmente con apoyo de OCR
* Almacenarlos estructuradamente en una NAS
* Registrar metadatos en base de datos PostgreSQL
* Mantener trazabilidad completa mediante auditoría

---

# 2. 🎯 OBJETIVO

Digitalizar archivos físicos históricos (10–20 años) y organizarlos en un sistema estructurado, consultable y auditable.

---

# 3. 🏗️ ARQUITECTURA GENERAL

## Componentes:

1. Watcher (Python)
2. Backend API (FastAPI)
3. Frontend (HTML + JS + Bootstrap)
4. Base de datos (PostgreSQL)
5. Almacenamiento (NAS)
6. OCR (Tesseract)

---

# 4. 📂 ESTRUCTURA DE CARPETAS

## 📁 Local (equipo de escaneo)

C:\Escaneos
├── PENDIENTES
├── PROCESADOS
└── ERROR\

---

## 📁 NAS (almacenamiento definitivo)

/NAS/GESDOC/{cedula}/{tipo}/{archivo}.pdf

Ejemplo:

/NAS/GESDOC/24909345/HC/HC_24909345_2014-12-01_001.pdf

---

# 5. 🔄 FLUJO OPERATIVO

## Paso 1: Escaneo

Usuario escanea documentos → llegan a carpeta local

---

## Paso 2: Validación manual

Usuario revisa:

* Legibilidad
* Integridad del documento

---

## Paso 3: Carga a carpeta PENDIENTES

Archivos se copian a:

C:\Escaneos\PENDIENTES\

---

## Paso 4: Watcher

Detecta archivos nuevos y registra en BD:

* ruta_temporal
* nombre_original
* estado = PENDIENTE
* fecha_carga

---

## Paso 5: Frontend

Muestra lista de pendientes

---

## Paso 6: OCR (apoyo)

Extrae sugerencias:

* cédula
* tipo
* fecha

Usuario valida manualmente

---

## Paso 7: Procesamiento

Usuario completa:

* paciente
* tipo_documento
* fecha

---

## Paso 8: Almacenamiento final

Sistema:

1. Genera nombre:
   TIPO_CEDULA_FECHA_CONSECUTIVO.pdf

2. Mueve archivo a NAS

3. Actualiza BD

4. Mueve archivo local a PROCESADOS

---

## Paso 9: Limpieza automática

Script elimina archivos locales con más de 7 días

---

# 6. 🧠 REGLAS DE NEGOCIO

* Un PDF = un solo tipo de documento
* Un PDF = una sola atención
* Usuario SIEMPRE valida datos (OCR es solo apoyo)
* No se permiten duplicados lógicos
* El nombre del archivo es obligatorio y estructurado
* No se puede guardar sin completar todos los datos
* Solo SUPERADMIN puede corregir documentos procesados
* Todo cambio queda registrado en auditoría

---

# 7. 🗄️ MODELO DE BASE DE DATOS

## ESQUEMA: gesdoc

---

## 🧩 TABLA: pacientes

* id_paciente (PK)
* numero_documento (UNIQUE)
* nombre
* fecha_creacion

---

## 🧩 TABLA: tipos_documento

* id_tipo (PK)
* codigo (HC, CI, etc)
* descripcion

---

## 🧩 TABLA: usuarios

* id_usuario (PK)
* usuario
* nombre
* rol (OPERARIO, ADMIN, SUPERADMIN)

---

## 🧩 TABLA: documentos

### Estado PENDIENTE:

* id_documento
* ruta_temporal
* nombre_archivo_original
* estado = PENDIENTE
* fecha_carga

---

### Estado PROCESADO:

* id_paciente
* id_tipo
* fecha
* consecutivo
* nombre_archivo
* ruta_archivo (NAS)
* fecha_procesado

---

## 🧩 TABLA: log_auditoria

* id_log
* id_documento
* id_usuario
* accion
* detalle
* fecha

---

# 8. 🔐 CONTROL DE ESTADOS

* PENDIENTE
* EN_REVISION (opcional)
* PROCESADO
* ERROR

---

# 9. ⚠️ CONTROL DE CONCURRENCIA

* Un documento no puede ser procesado por dos usuarios simultáneamente
* Se debe implementar bloqueo lógico (lock)

---

# 10. 🧠 GENERACIÓN DE NOMBRE DE ARCHIVO

Formato:

TIPO_CEDULA_FECHA_CONSECUTIVO.pdf

Ejemplo:

HC_24909345_2014-12-01_001.pdf

---

# 11. 🔁 MANEJO DE DUPLICADOS

Clave única lógica:

(paciente + tipo + fecha + consecutivo)

---

# 12. 🧹 LIMPIEZA AUTOMÁTICA

* Carpeta: PROCESADOS
* Regla: eliminar archivos > 7 días
* NAS es almacenamiento definitivo

---

# 13. ⚙️ TECNOLOGÍAS

Backend:

* Python
* FastAPI

Base de datos:

* PostgreSQL

Frontend:

* HTML
* JavaScript
* Bootstrap

OCR:

* Tesseract

Watcher:

* watchdog (Python)

---

# 14. 🚀 ESCALABILIDAD

Sistema diseñado para:

* 500.000 pacientes
* 5.000.000 documentos
* 25.000.000 logs

---

# 15. 🔍 BÚSQUEDA

* Por cédula
* Por tipo de documento
* Por fecha

---

# 16. 🧠 PRINCIPIOS DEL SISTEMA

* La BD guarda la verdad lógica
* El NAS guarda la verdad física
* El usuario valida la información
* El OCR solo asiste
* Todo es auditable

---

# 17. 📌 CONSIDERACIONES IMPORTANTES

* No eliminar archivos sin respaldo en NAS
* No confiar en OCR como fuente de verdad
* Evitar procesamiento automático sin validación humana
* Priorizar trazabilidad sobre velocidad

---

# 18. 🧭 ROADMAP DE DESARROLLO

1. Base de datos
2. Watcher
3. API (pendientes)
4. Frontend (bandeja)
5. Procesamiento
6. NAS integration
7. Auditoría
8. Limpieza automática

---

# 19. 🎯 OBJETIVO FINAL

Sistema robusto, auditable y escalable para gestión documental clínica.

---

# FIN DEL CONTEXTO
