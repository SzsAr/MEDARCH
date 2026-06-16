# 🚀 CONFIGURACIÓN DEL WATCHER EN WINDOWS

---

## 📋 REQUISITOS PREVIOS

- **Windows 10 o superior**
- **Python 3.8 o superior**
- **PostgreSQL 12 o superior** (ya configurada)
- **(Opcional)** Tesseract OCR 5.0+ (sólo si quieres habilitar OCR adicional)

---

## 🔧 PASO 1: (OPCIONAL) INSTALAR TESSERACT OCR

 El watcher ya no requiere Tesseract por defecto. Si en algún momento quieres
 habilitar OCR adicional en tu instalación, instala Tesseract manualmente y
 las bibliotecas Python necesarias en un entorno
separado. Estas instrucciones son opcionales y no son necesarios para que el
watcher registre documentos en la base de datos.

---

## 🐍 PASO 2: CONFIGURAR PYTHON Y DEPENDENCIAS

### 2.1 Crear entorno virtual

```powershell
# Navega a la carpeta del watcher
cd C:\MEDARCH\watcher

# Crea el entorno virtual
python -m venv venv

# Activa el entorno
.\venv\Scripts\Activate.ps1
```

> **Nota**: Si recibe error de políticas de ejecución:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
> .\venv\Scripts\Activate.ps1
> ```

### 2.2 Instalar dependencias

```powershell
# Asegúrate de estar en el entorno virtual (verás (venv) en el prompt)
pip install --upgrade pip

# Instala las dependencias del watcher
pip install -r requirements.txt
```

**Dependencias instaladas:**
- `watchdog` - Monitoreo de archivos
- `psycopg2-binary` - Driver PostgreSQL
- `pdfplumber` - Extracción de texto de PDFs (si necesitas extraer texto embebido)

---

## 🗄️ PASO 3: CONFIGURAR BASE DE DATOS

Asegúrate que PostgreSQL está corriendo y que el esquema `gesdoc` existe con las tablas:
- `usuarios`
- `pacientes`
- `tipos_documento`
- `documentos`

Ejecutar `bd.sql` si no lo has hecho:
```powershell
# En PowerSQL o pgAdmin:
# Conectar a medarch_db como medarch_user y ejecutar bd.sql
```

---

## 🌍 PASO 4: VARIABLES DE ENTORNO

Crear archivo `.env` en `C:\MEDARCH\watcher\` con:

```env
# Rutas y monitoreo
MEDARCH_WATCH_PATH=C:\Escaneos\PENDIENTES
MEDARCH_WATCH_RECURSIVE=true

# Base de datos
MEDARCH_DB_HOST=localhost
MEDARCH_DB_PORT=5432
MEDARCH_DB_NAME=medarch_db
MEDARCH_DB_USER=medarch_user
MEDARCH_DB_PASSWORD=Medarch123*

# Pool de conexiones
MEDARCH_DB_MIN_CONN=1
MEDARCH_DB_MAX_CONN=5
MEDARCH_RECONNECT_WAIT=5
```

> **Nota**: El código también lee de variables de entorno del sistema. Puedes usar `.env` o variables de Windows.

---

## 📁 PASO 5: CREAR CARPETA DE MONITOREO

```powershell
# Crear carpeta si no existe
New-Item -ItemType Directory -Force -Path "C:\Escaneos\PENDIENTES"

# Verificar permisos (el usuario debe tener lectura)
```

---

## ▶️ PASO 6: EJECUTAR EL WATCHER

### Con entorno virtual activado:

```powershell
cd C:\MEDARCH\watcher
.\venv\Scripts\Activate.ps1
python watcher.py
```

### Salida esperada:

```
[INFO] Conexion a PostgreSQL inicializada
[INFO] Tipos de documentos cargados: ['cedula', 'pasaporte', 'licencia', ...]
[INFO] Watcher iniciado en: C:\Escaneos\PENDIENTES
```

---

## 🧪 PASO 7: PRUEBA

1. **Copiar un PDF a la carpeta PENDIENTES**
   ```powershell
   # Por ejemplo, copiar un PDF de prueba
   Copy-Item "C:\ruta\a\documento.pdf" "C:\Escaneos\PENDIENTES\"
   ```

2. **Verificar logs en el watcher**
   - Deberías ver: "Archivo detectado:", "Número de documento detectado:", etc.

3. **Verificar en base de datos**
   ```sql
   SELECT id_documento, nombre_archivo_original, id_paciente, id_tipo, estado
   FROM gesdoc.documentos
   ORDER BY fecha_carga DESC
   LIMIT 5;
   ```

---

## 🚨 SOLUCIÓN DE PROBLEMAS

### Nota sobre OCR

El watcher está configurado para operar sin OCR por defecto. Si se habilita OCR
de forma manual, podría aparecer el error `pytesseract.TesseractNotFoundError` si
Tesseract no está instalado o no está en PATH. Estas instrucciones son sólo
relevantes si decides instalar Tesseract y las bibliotecas OCR manualmente.

### Error: `psycopg2.OperationalError: connection refused`

**Causa**: PostgreSQL no está corriendo.

**Solución**:
```powershell
# Verificar que PostgreSQL está corriendo
Get-Service PostgreSQL* | Start-Service

# O iniciar manualmente desde el Panel de Control
```

### Error: `pdfplumber` importación fallida

**Solución**:
```powershell
# Reinstalar paquete (si tienes problemas con pdfplumber)
pip uninstall pdfplumber -y
pip install pdfplumber==0.10.4
```

### Los PDFs se detectan pero OCR es lento

**Causa**: Tesseract procesa la página completa.

**Solución**: Es normal, los archivos con texto embebido son más rápidos. Los archivos escaneados sin OCR tardan más.

---

## 📦 CREAR EJECUTABLE (OPCIONAL)

Para hacer que el watcher sea un servicio de Windows automático:

```powershell
# Instalar pyinstaller
pip install pyinstaller

# Crear ejecutable
pyinstaller --onefile watcher.py

# El ejecutable estará en: dist\watcher.exe
```

---

## 📋 CHECKLIST FINAL

- [x] Python 3.8+ instalado y en PATH
 - [ ] Tesseract OCR instalado en `C:\Program Files\Tesseract-OCR` (opcional)
- [x] PostgreSQL corriendo
- [x] Entorno virtual Python creado
- [x] Dependencias instaladas: `pip install -r requirements.txt`
- [x] Carpeta `C:\Escaneos\PENDIENTES` creada
- [x] Variables de entorno configuradas (o `.env`)
- [x] Base de datos con esquema `gesdoc` creada
- [x] Watcher ejecutándose sin errores
 - [x] Watcher registra auditoría en `log_auditoria`
 - [x] OCR deshabilitado por defecto en watcher y documentado en README

---

## 📞 SOPORTE

Si hay problemas:

1. Revisar logs del watcher en consola
2. Verificar conectividad a PostgreSQL: `psql -U medarch_user -d medarch_db`
3. Verificar que Tesseract funciona: `tesseract --version`
4. Copiar el error completo y revisar en `watcher.py`

---
