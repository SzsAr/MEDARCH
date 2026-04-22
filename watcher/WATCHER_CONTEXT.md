# 🧠 CONTEXTO WATCHER - MEDARCH

---

# 📌 OBJETIVO

El watcher es un servicio en Python encargado de detectar archivos PDF nuevos en una carpeta local y registrar su existencia en la base de datos.

---

# 📂 RUTA A MONITOREAR

Sistema operativo: Windows

Ruta:

C:\Escaneos\PENDIENTES\

---

# 🧠 FUNCIONALIDAD

El watcher debe:

1. Detectar archivos nuevos en la carpeta PENDIENTES
2. Validar que sean archivos PDF
3. Registrar el archivo en la base de datos PostgreSQL

---

# 🗄️ BASE DE DATOS

Motor: PostgreSQL
Esquema: gesdoc
Tabla: documentos

---

# 📊 CAMPOS A INSERTAR

Cuando se detecta un archivo nuevo:

* ruta_temporal → ruta completa del archivo
* nombre_archivo_original → nombre del archivo
* estado → 'PENDIENTE'
* fecha_carga → timestamp automático

---

# ⚠️ REGLAS IMPORTANTES

* NO procesar OCR
* NO mover archivos
* NO modificar archivos
* SOLO registrar en BD

---

# 🚫 VALIDACIONES

* Ignorar archivos que no sean PDF
* Evitar duplicados (por ruta_temporal o nombre)
* No insertar si ya existe

---

# 🧠 MANEJO DE ERRORES

* Si falla inserción → log en consola
* No detener watcher
* Continuar monitoreo

---

# ⚙️ TECNOLOGÍA

Lenguaje: Python
Librerías:

* watchdog (monitoreo de archivos)
* psycopg2 o asyncpg (PostgreSQL)

---

# 🧠 COMPORTAMIENTO

* Debe correr continuamente
* Debe detectar múltiples archivos
* Debe ser estable ante errores

---

# 📌 EJEMPLO

Archivo detectado:

C:\Escaneos\PENDIENTES\scan_001.pdf

Registro esperado en BD:

ruta_temporal = C:\Escaneos\PENDIENTES\scan_001.pdf
nombre_archivo_original = scan_001.pdf
estado = PENDIENTE

---

# 🎯 RESULTADO

El watcher convierte archivos físicos en registros controlados en base de datos.

---

# FIN
