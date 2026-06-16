# 🧠 CONTEXTO WATCHER - MEDARCH

---

# 📌 OBJETIVO

El watcher es un servicio en Python encargado de detectar archivos PDF nuevos en una carpeta local, extraer texto embebido cuando esté disponible, y registrar el documento con metadatos pre-completados en la base de datos.

---

# 📂 RUTA A MONITOREAR

Sistema operativo: Windows

Ruta:
```
C:\Escaneos\PENDIENTES\
```

---

# 🧠 FUNCIONALIDAD

El watcher debe:

1. Detectar archivos nuevos en la carpeta PENDIENTES
2. Validar que sean archivos PDF
3. **Extraer texto del PDF (OCR por imagen es opcional)**
4. **Detectar automáticamente:**
   - Número de documento (cédula, pasaporte, etc.)
   - Tipo de documento (historia clínica, receta, etc.)
5. **Auto-crear paciente si el número de documento es nuevo**
6. Registrar el archivo en la base de datos con metadatos pre-completados

---

# 🗄️ BASE DE DATOS

Motor: PostgreSQL
Esquema: gesdoc
Tablas: documentos, pacientes, tipos_documento

---

# 📊 CAMPOS A INSERTAR

Cuando se detecta un archivo nuevo:

- `ruta_temporal` → ruta completa del archivo
- `nombre_archivo_original` → nombre del archivo
- `estado` → 'PENDIENTE'
- `id_paciente` → auto-detectado por OCR o NULL
- `id_tipo` → auto-detectado por OCR o NULL
- `fecha_carga` → timestamp automático

---

# 🔤 PROCESO DE EXTRACCIÓN DE TEXTO

1. **Extracción de texto embebido**: Usa `pdfplumber` para extraer texto del PDF
2. **OCR por imagen (opcional)**: Si el PDF no tiene texto embebido se puede usar
   Tesseract OCR, pero esta funcionalidad es opcional y está deshabilitada por
   defecto en la distribución principal.
3. **Detección de número de documento**: Busca patrones de cédula, pasaporte, etc.
4. **Detección de tipo de documento**: Busca palabras clave para clasificar

### Patrones detectados:

- **Historia clínica**: Palabras clave "historia", "historial", "anamnesis", "diagnóstico", "tratamiento"
- **Consentimiento informado**: Palabras clave "consentimiento", "consentido", "autorización", "acepto"
- **Receta/Fórmula**: Palabras clave "receta", "prescripción", "medicamento", "fármaco"
- **Certificado**: Palabras clave "certificado", "diagnóstico certificado", "incapacidad", "alta"
- **Examen de laboratorio**: Palabras clave "examen", "laboratorio", "resultado", "análisis"
- **Radiografía**: Palabras clave "radiografía", "radiography", "rayos x"
- **Carné de vacunación**: Palabras clave "vacuna", "vaccination", "inmunización"

---

# ⚙️ INSTALACIÓN

## Requisitos previos (Windows)

### 1. Python 3.8+
```powershell
python --version
```

### 2. Tesseract OCR (requerido para OCR en PDFs sin texto embebido)

**Descarga e instalación:**
1. Descargar instalador: https://github.com/UB-Mannheim/tesseract/wiki
2. Ejecutar instalador (versión recomendada: 5.x o superior)
3. Instalar en ruta predeterminada: `C:\Program Files\Tesseract-OCR`

**Configurar variable de entorno (opcional, si se instala en ruta no estándar):**
```powershell
# En PowerShell como administrador:
[System.Environment]::SetEnvironmentVariable("TESSERACT_CMD", "C:\Program Files\Tesseract-OCR\tesseract.exe", "User")
```

### 3. Dependencias Python

```powershell
cd C:\MEDARCH\watcher
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. Variables de entorno (archivo .env o en sistema)

```
MEDARCH_WATCH_PATH=C:\Escaneos\PENDIENTES
MEDARCH_WATCH_RECURSIVE=true
MEDARCH_DB_HOST=localhost
MEDARCH_DB_PORT=5432
MEDARCH_DB_NAME=medarch_db
MEDARCH_DB_USER=medarch_user
MEDARCH_DB_PASSWORD=Medarch123*
```

---

# 🚀 EJECUCIÓN

```powershell
cd C:\MEDARCH\watcher
python watcher.py
```

---

# ⚠️ REGLAS IMPORTANTES

- **OCR es asistivo**: Los datos detectados son sugerencias, no definitivos
- **Validación humana**: Todo documento pasa por revisión en frontend antes de procesarse
- **Auto-creación de pacientes**: Si se detecta un número de documento nuevo, se crea el paciente automáticamente
- **NO mover archivos**: Solo registrar en BD
- **NO modificar archivos**: El watcher es solo lectura

---

# 🚫 VALIDACIONES

- Ignorar archivos que no sean PDF
- Evitar duplicados (por ruta_temporal)
- No insertar si ya existe documento con esa ruta
- Continuar procesamiento incluso si OCR falla

---

# 🧠 MANEJO DE ERRORES

- Si falla OCR → continuar (dejar NULL id_paciente e id_tipo)
- Si falla conexión BD → reintentar cada N segundos
- Si falla lectura PDF → log en consola, continuar
- No detener watcher

---

# ⚙️ TECNOLOGÍA

Lenguaje: Python 3.8+

Librerías:
- `watchdog` (monitoreo de archivos)
- `psycopg2` (PostgreSQL)
- `pdfplumber` (extracción de texto embebido)

---

# 📊 LOGS ESPERADOS

```
[INFO] Watcher iniciado en: C:\Escaneos\PENDIENTES
[INFO] Archivo detectado: C:\Escaneos\PENDIENTES\scan_001.pdf
[INFO] Número de documento detectado: 1234567890
[INFO] Tipo de documento detectado: 7 (historia clínica)
[INFO] Paciente creado: 1234567890 (ID: 42)
[INFO] Documento registrado: C:\Escaneos\PENDIENTES\scan_001.pdf (ID paciente: 42, ID tipo: 7)
```

---

# 🧠 COMPORTAMIENTO

- Debe correr continuamente
- Debe detectar múltiples archivos
- Debe ser estable ante errores
- Debe registrar todo en logs
- Debe permitir revisión humana de OCR en frontend

---

# 📌 EJEMPLO DE FLUJO

**Archivo detectado:**
```
C:\Escaneos\PENDIENTES\cedula_202404.pdf
```

**Procesamiento:**
1. Extraer texto → "Cédula de ciudadanía 1234567890..."
2. Detectar número → "1234567890"
3. Detectar tipo → "cedula" → id_tipo=1 (si existe en BD)
4. Buscar/crear paciente → id_paciente=42 (nuevo)
5. Registrar en BD → PENDIENTE, id_paciente=42, id_tipo=1

**Resultado en frontend:**
- Documento en bandeja PENDIENTES
- Número y tipo pre-completados
- Operador revisa y valida
- Si es correcto → Procesar
- Si es incorrecto → Editar y procesar

---

ruta_temporal = C:\Escaneos\PENDIENTES\scan_001.pdf
nombre_archivo_original = scan_001.pdf
estado = PENDIENTE

---

# 🎯 RESULTADO

El watcher convierte archivos físicos en registros controlados en base de datos.

---

# FIN
