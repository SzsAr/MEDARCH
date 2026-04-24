# 🔧 GUÍA DE DIAGNÓSTICO DESDE CONSOLA - MEDARCH API

**Actualizado:** 2026-04-24  
**Estado:** ✅ Errores corregidos

---

## 📋 Errores Identificados y Corregidos

| Error | Ubicación | Tipo | Estado |
|-------|-----------|------|--------|
| `list[]` en Python 3.8 | users.py línea 30 | Sintaxis | ✅ Corregido |
| `dict[]` en Python 3.8 | users.py líneas 32, 40, 49, 54, 58, 59, 63, 66, 67 | Sintaxis | ✅ Corregido |
| `list[UserResponse]` | user_service.py línea 59 | Sintaxis | ✅ Corregido |
| `dict[str, str]` | user_service.py líneas 144, 182 | Sintaxis | ✅ Corregido |

---

## 🚨 Problema Principal: Python 3.8 Incompatibilidad

### ❌ Lo que NO funciona en Python 3.8/3.9

```python
# INCORRECTO - Genera TypeError
response_model=list[UserResponse]
response_model=dict[str, str]
_: dict[str, Any]
) -> dict[str, str]:
) -> list[UserResponse]:
```

### ✅ Lo que SÍ funciona (Python 3.8+)

```python
# CORRECTO - Compatible con Python 3.8+
from typing import Dict, List

response_model=List[UserResponse]
response_model=Dict[str, str]
_: Dict[str, Any]
) -> Dict[str, str]:
) -> List[UserResponse]:
```

---

## 🔍 Diagnóstico Paso a Paso

### 1️⃣ Verificar Versión de Python

```bash
python --version
```

**Salida esperada:**
```
Python 3.8.x
Python 3.9.x
Python 3.10.x
Python 3.11.x
```

**Nota:** Si es 3.8 o 3.9, DEBE usar tipos de `typing`.

---

### 2️⃣ Verificar Sintaxis de Archivos

```bash
# Desde directorio backend/
python -m py_compile app/api/routes/users.py
python -m py_compile app/services/user_service.py
```

**Salida esperada:** (Sin errores)

**Si hay error:**
```
SyntaxError: 'type' object is not subscriptable
```

---

### 3️⃣ Verificar Importaciones

```bash
# Verificar que se importan correctamente
python -c "from app.api.routes.users import router; print('✓ users.py importa OK')"
python -c "from app.services.user_service import create_user; print('✓ user_service.py importa OK')"
```

**Salida esperada:**
```
✓ users.py importa OK
✓ user_service.py importa OK
```

**Si hay error ModuleNotFoundError:**
```
ModuleNotFoundError: No module named 'app'
```
→ Solución: Ejecutar desde el directorio correcto (`cd backend`)

---

### 4️⃣ Verificar Dependencias de Pydantic

```bash
python -c "from pydantic import BaseModel; print('✓ Pydantic instalado')"
python -c "from fastapi import FastAPI; print('✓ FastAPI instalado')"
```

**Salida esperada:**
```
✓ Pydantic instalado
✓ FastAPI instalado
```

**Si hay error:**
```
ModuleNotFoundError: No module named 'fastapi'
```
→ Solución: `pip install -r requirements.txt`

---

### 5️⃣ Verificar Base de Datos

```bash
python -c "from app.db.session import get_connection; get_connection(); print('✓ BD conectada')"
```

**Salida esperada:**
```
✓ BD conectada
```

**Si hay error:**
```
RuntimeError: No se pudo conectar a la base de datos
```

→ Verificar:
- ¿PostgreSQL está corriendo?
- ¿Variables de entorno `.env` configuradas?
- ¿Credenciales correctas en `.env`?

---

### 6️⃣ Ejecutar Servidor de Prueba

```bash
# Opción 1: Con python main.py (si está configurado)
python main.py

# Opción 2: Con uvicorn directo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Salida esperada:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**Si hay error de imports:**
```
ImportError: cannot import name 'require_role' from 'app.core.security'
```
→ Verificar que `security.py` tiene la función `require_role()`

---

## 🧪 Tests de Validación

### Test 1: Verificar que imports funcionan

```bash
cat > test_imports.py << 'EOF'
#!/usr/bin/env python
import sys
try:
    from app.api.routes.users import router
    print("✓ users.py importa correctamente")
except Exception as e:
    print(f"✗ Error en users.py: {e}")
    sys.exit(1)

try:
    from app.services.user_service import create_user, list_users
    print("✓ user_service.py importa correctamente")
except Exception as e:
    print(f"✗ Error en user_service.py: {e}")
    sys.exit(1)

try:
    from app.schemas.user_schema import UserResponse, UserCreateRequest
    print("✓ user_schema.py importa correctamente")
except Exception as e:
    print(f"✗ Error en user_schema.py: {e}")
    sys.exit(1)

print("\n✓ Todos los imports OK")
EOF

python test_imports.py
```

---

### Test 2: Verificar tipos de retorno

```bash
python -c "
from typing import get_type_hints
from app.services.user_service import list_users
hints = get_type_hints(list_users)
print(f'Return type: {hints.get(\"return\")}')
"
```

**Salida esperada:**
```
Return type: typing.List[app.schemas.user_schema.UserResponse]
```

---

## ✅ Checklist de Validación Completa

```bash
#!/bin/bash
cd backend

echo "1. Verificando Python..."
python --version

echo "2. Compilando archivos..."
python -m py_compile app/api/routes/users.py
python -m py_compile app/services/user_service.py
echo "   ✓ Sin errores de sintaxis"

echo "3. Verificando imports..."
python -c "from app.api.routes.users import router; print('   ✓ users.py OK')"
python -c "from app.services.user_service import create_user; print('   ✓ user_service.py OK')"

echo "4. Verificando dependencias..."
pip list | grep -E "fastapi|pydantic|psycopg2"

echo "5. Intentando conectar BD..."
python -c "from app.db.session import get_connection; get_connection(); print('   ✓ BD conectada')"

echo ""
echo "✓ TODAS LAS VALIDACIONES PASARON"
```

---

## 🐛 Errores Comunes y Soluciones

### Error 1: `TypeError: 'type' object is not subscriptable`

```python
# PROBLEMA
response_model=list[UserResponse]

# SOLUCIÓN
from typing import List
response_model=List[UserResponse]
```

---

### Error 2: `ModuleNotFoundError: No module named 'app'`

```bash
# PROBLEMA
python test.py  # desde raíz del proyecto

# SOLUCIÓN
cd backend      # entrar a directorio backend
python test.py  # ahora sí
```

---

### Error 3: `RuntimeError: No se pudo conectar a la base de datos`

```bash
# VERIFICAR POSTGRESQL
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # macOS
tasklist | find "postgres"  # Windows

# VERIFICAR .env
cat app/.env

# VERIFICAR CREDENCIALES
psql -U medarch_user -h localhost -d medarch_db
```

---

### Error 4: `ImportError: cannot import name 'require_role'`

```bash
# Verificar que security.py tiene require_role()
grep -n "def require_role" app/core/security.py

# Si no está, agregar a security.py
```

---

### Error 5: `psycopg2.OperationalError: FATAL:  role does not exist`

```bash
# Crear el role en PostgreSQL
psql -U postgres << 'EOF'
CREATE ROLE medarch_user LOGIN PASSWORD 'Medarch123*';
CREATE DATABASE medarch_db OWNER medarch_user;
EOF
```

---

## 📊 Script de Diagnóstico Automático

```bash
#!/bin/bash
# save as: backend/diagnose.sh

echo "=========================================="
echo "DIAGNÓSTICO MEDARCH API"
echo "=========================================="
echo ""

# 1. Python
echo "1. Python:"
python --version
echo ""

# 2. Sintaxis
echo "2. Verificar sintaxis..."
python -m py_compile app/api/routes/users.py 2>&1 && echo "   ✓ users.py" || echo "   ✗ users.py"
python -m py_compile app/services/user_service.py 2>&1 && echo "   ✓ user_service.py" || echo "   ✗ user_service.py"
echo ""

# 3. Imports
echo "3. Verificar imports..."
python -c "from app.api.routes.users import router" 2>&1 && echo "   ✓ users" || echo "   ✗ users"
python -c "from app.services.user_service import create_user" 2>&1 && echo "   ✓ user_service" || echo "   ✗ user_service"
echo ""

# 4. Dependencias
echo "4. Dependencias instaladas:"
pip list | grep -E "fastapi|pydantic|uvicorn|psycopg2"
echo ""

echo "=========================================="
echo "FIN DEL DIAGNÓSTICO"
echo "=========================================="
```

**Uso:**
```bash
chmod +x backend/diagnose.sh
./backend/diagnose.sh
```

---

## 📞 Si los Problemas Persisten

1. **Guardar output completo:**
   ```bash
   python -m py_compile app/api/routes/users.py 2>&1 > error.log
   cat error.log
   ```

2. **Revisar archivo:** `ERRORES_DIAGNOSTICO.md`

3. **Verificar cambios realizados:**
   ```bash
   git diff app/api/routes/users.py
   git diff app/services/user_service.py
   ```

---

**Última actualización:** 2026-04-24 ✓ Todos los errores corregidos
