# 🧠 WATCHER - MEDARCH OCR

**Servicio de detección y OCR de documentos para MEDARCH**

---

## 📌 ¿QUÉ ES?

El watcher es un servicio Python que monitorea una carpeta local (`C:\Escaneos\PENDIENTES`) y automáticamente:

1. ✅ **Detecta nuevos archivos PDF**
2. 🔤 **Extrae texto embebido del PDF** (pdfplumber). OCR por imagen (Tesseract)
     es opcional y está deshabilitado por defecto.
3. 🧑 **Detecta número de documento** (cédula, pasaporte, etc.)
4. 📄 **Detecta tipo de documento** (historia clínica, receta, etc.)
5. 👤 **Auto-crea pacientes** si es la primera vez que ve ese número
6. 💾 **Registra en base de datos** con metadatos pre-completados

---

## 🚀 INICIO RÁPIDO

### Requisitos previos
- Python 3.8+
- PostgreSQL 12+
- Tesseract OCR es opcional (sólo si se habilita OCR por imagen)

### Instalación

```powershell
# Clonar o navegar al directorio
cd C:\MEDARCH\watcher

# Crear entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar watcher
python watcher.py
```

**Ver [SETUP_WINDOWS.md](./SETUP_WINDOWS.md) para instrucciones detalladas**

---

## 📊 FLUJO DE TRABAJO

```
Carpeta PENDIENTES
        ↓
   [Detectar PDF]
        ↓
   [Extraer texto OCR]
        ↓
   [Detectar número de documento]
        ↓
   [Detectar tipo de documento]
        ↓
   [Crear/obtener paciente]
        ↓
   [Registrar en BD con metadatos]
        ↓
   [Frontend muestra en bandeja PENDIENTES]
        ↓
   [Operador revisa y valida]
        ↓
   [Procesar documento]
```

---

## 🔤 CAPACIDADES OCR

### Extracción de texto

- **PDFs con texto embebido**: Lectura rápida usando `pdfplumber`
- **Archivos escaneados**: OCR por imagen es opcional y se realiza con Tesseract
     si se habilita manualmente.

### Detección de números

- Búsqueda de patrones: números de 8-15 dígitos
- Formatos: `1234567890`, `123.456.789`, `123-456-789`
- Palabras clave: "cédula", "cedula", "c.c", "cc", "identificación"

### Detección de tipos

- **Historia clínica**: "historia", "historial", "anamnesis", "diagnóstico", "tratamiento"
- **Consentimiento informado**: "consentimiento", "autorización", "acepto"
- **Receta/Fórmula**: "receta", "prescripción", "medicamento", "fármaco"
- **Certificado médico**: "certificado", "incapacidad", "alta"
- **Examen de laboratorio**: "examen", "laboratorio", "resultado", "análisis"
- **Radiografía/Imaging**: "radiografía", "rayos x"
- **Carné de vacunación**: "vacuna", "vaccination", "inmunización"

---

## 📈 FLUJO EN FRONTEND

Cuando el watcher registra un documento:

```
📥 Documento PENDIENTE en bandeja
   ├─ ID Paciente: [pre-completado o vacío]
   ├─ Tipo documento: [pre-completado o vacío]
   ├─ Número identificación: [puede cambiar]
   └─ Botones: [Revisar] [Procesar] [Error]

👁️ Operador revisa:
   ├─ Si OCR acertó → Procesar directo
   ├─ Si OCR falló → Editar y procesar
   └─ Si error grave → Marcar como ERROR

💾 Documento se mueve a estado PROCESADO
   ├─ Se genera nombre final: TIPO_CEDULA_FECHA_CONSECUTIVO.pdf
   ├─ Se guarda en NAS
   └─ Se registra auditoria
```

---

## 🛠️ CONFIGURACIÓN

### Tipos de documentos en la base de datos

**Importante**: Los tipos de documentos deben estar registrados en la tabla `gesdoc.tipos_documento` antes de ejecutar el watcher.

**Ejecutar el script de setup:**
```sql
-- Ver archivo: TIPOS_DOCUMENTOS_CLINICOS.sql
-- Conectar a medarch_db como medarch_user y ejecutar:
psql -U medarch_user -d medarch_db -f TIPOS_DOCUMENTOS_CLINICOS.sql
```

O ejecutar manualmente en pgAdmin/psql:
```sql
INSERT INTO gesdoc.tipos_documento (codigo, descripcion, activo)
VALUES 
    ('HISTORIA', 'Historia Clínica', TRUE),
    ('CONSENTIMIENTO', 'Consentimiento Informado', TRUE),
    ('RECETA', 'Receta / Fórmula Médica', TRUE),
    ('CERTIFICADO', 'Certificado Médico', TRUE),
    ('EXAMEN', 'Examen de Laboratorio', TRUE),
    ('RADIOGRAFIA', 'Radiografía / Imagen Diagnóstica', TRUE),
    ('VACUNA', 'Carné de Vacunación', TRUE),
    ('EPICRISIS', 'Epicrisis / Resumen de Alta', TRUE);
```

### Variables de entorno

```env
# Rutas
MEDARCH_WATCH_PATH=C:\Escaneos\PENDIENTES
MEDARCH_WATCH_RECURSIVE=true

# Base de datos
MEDARCH_DB_HOST=localhost
MEDARCH_DB_PORT=5432
MEDARCH_DB_NAME=medarch_db
MEDARCH_DB_USER=medarch_user
MEDARCH_DB_PASSWORD=Medarch123*

# Pool
MEDARCH_DB_MIN_CONN=1
MEDARCH_DB_MAX_CONN=5
MEDARCH_RECONNECT_WAIT=5
```

Nota: por seguridad y para evitar dependencias nativas en entornos donde
Tesseract no está instalado, OCR está deshabilitado por defecto.
Para habilitar OCR en tiempo de ejecución, exporta la variable:

```env
MEDARCH_ENABLE_OCR=true
```

---

## 📊 ESTRUCTURA DE CÓDIGO

```
watcher.py
├── Settings (configuración)
├── OCREngine (extracción OCR)
├── DocumentTypeRegistry (tipos de documento)
├── DatabaseClient (conexión BD)
├── PDFCreatedEventHandler (eventos de archivos)
└── WatcherService (servicio principal)
```

### Clases principales

| Clase | Responsabilidad |
|-------|-----------------|
| `OCREngine` | Extrae texto de PDFs |
| `DocumentTypeRegistry` | Carga tipos y detecta clasificación |
| `DatabaseClient` | Conexión y operaciones BD |
| `PDFCreatedEventHandler` | Evento de archivo nuevo |
| `WatcherService` | Orquestación del watcher |

---

## 📊 EJEMPLO DE EJECUCIÓN

```
[INFO] Conexion a PostgreSQL inicializada
[INFO] Tipos de documentos cargados: ['cedula', 'pasaporte', 'licencia', 'historia', 'receta', 'certificado']
[INFO] Watcher iniciado en: C:\Escaneos\PENDIENTES

# Usuario copia archivo
[INFO] Archivo detectado: C:\Escaneos\PENDIENTES\cedula.pdf

# OCR se ejecuta
[INFO] Número de documento detectado: 1234567890
[INFO] Tipo de documento detectado: 1
[INFO] Paciente creado: 1234567890 (ID: 42)

# Se registra en BD
[INFO] Documento registrado: C:\Escaneos\PENDIENTES\cedula.pdf (ID paciente: 42, ID tipo: 1)
```

---

## ✅ VALIDACIONES

- ✅ Solo procesa PDFs
- ✅ Evita duplicados (por ruta_temporal)
- ✅ Tolera fallos de OCR (continúa con NULL si falla)
- ✅ Auto-crea pacientes automáticamente
- ✅ Carga tipos de documentos de BD
- ✅ Registra en logs todo
 - ✅ Registra auditoría en `log_auditoria`
 - ✅ OCR deshabilitado por defecto y documentado (usar `MEDARCH_ENABLE_OCR=true` para activar)

---

# ⚠️ LIMITACIONES

- ⚠️ OCR en archivos escaneados es lento (~5-10 seg por página)
- ⚠️ OCR puede tener errores en documentos de baja calidad
- ⚠️ La detección de tipo es por palabras clave, no es 100% exacta

**→ Por eso la validación humana en frontend es crítica**

---

## 🔗 DEPENDENCIAS

```
watchdog==6.0.0          # Monitoreo de archivos
psycopg2-binary==2.9.10  # PostgreSQL driver
pdfplumber==0.10.4       # Extracción de texto PDF

```

---

## 📝 LOGS

El watcher genera logs en consola y opcionalmente en archivo. Ejemplos:

```
[INFO] Conexion a PostgreSQL inicializada
[INFO] Watcher iniciado en: C:\Escaneos\PENDIENTES
[DEBUG] Archivo ignorado (no es PDF): file.txt
[INFO] Archivo detectado: documento.pdf
[INFO] Número de documento detectado: 1234567890
[INFO] Tipo de documento detectado: 1
[INFO] Paciente creado: 1234567890 (ID: 42)
[WARNING] Error en OCR: ...
[ERROR] Error insertando documento: ...
```

---

## 🚨 TROUBLESHOOTING

| Problema | Causa | Solución |
|----------|-------|----------|
| `TesseractNotFoundError` | Tesseract no instalado | Ver SETUP_WINDOWS.md |
| `psycopg2.OperationalError` | PostgreSQL no corre | Iniciar PostgreSQL |
| `pdfplumber ImportError` | Dependencia no instalada | `pip install pdfplumber` |
| OCR muy lento | Archivos grandes escaneados | Normal, esperar o optimizar |
| No detecta número | OCR falló o formato raro | Validar manualmente en frontend |

---

## 🔒 REGLA IMPORTANTE

> **OCR es asistivo, no definitivo. Todo documento requiere validación humana en el frontend antes de procesarse.**

La detección de número y tipo es una sugerencia para acelerar el flujo, pero siempre debe ser revisada por un operador.

---

## 📞 CONTACTO

Para cambios o mejoras en:
- Patrones de detección → editar `DocumentTypeRegistry.keywords`
- Tipos de documento → modificar en `tipos_documento` en BD
- OCR → revisar `OCREngine`

---

## 📄 ARCHIVOS RELACIONADOS

- [SETUP_WINDOWS.md](./SETUP_WINDOWS.md) - Instalación paso a paso
- [WATCHER_CONTEXT.md](./WATCHER_CONTEXT.md) - Contexto técnico
- [requirements.txt](./requirements.txt) - Dependencias Python
- [watcher.py](./watcher.py) - Código principal

---

**Última actualización**: 2026-04-29  
**Versión**: 2.0 (con OCR)
