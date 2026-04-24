# 🔐 GESTIÓN DE USUARIOS - MEDARCH Backend

Implementación completa de autenticación y CRUD de usuarios para MEDARCH.

---

## 📖 Documentación Disponible

| Documento | Propósito |
|-----------|-----------|
| **CRUD_USUARIOS.md** | Guía técnica de endpoints con ejemplos |
| **IMPLEMENTACION_CRUD.md** | Detalles técnicos de la implementación |
| **AUTH_USERS_CONTEXT.md** | Contexto general de autenticación |

👉 **Empezar por:** CRUD_USUARIOS.md para ver todos los endpoints disponibles.

---

## 🚀 Quick Start

### 1. Configurar Variables de Entorno

Crear `.env` en `backend/app/`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=medarch_db
DB_USER=medarch_user
DB_PASSWORD=Medarch123*

SECRET_KEY=tu-clave-secreta-muy-larga-y-compleja
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 2. Crear Base de Datos

```bash
psql -U postgres -f ../database/bd.sql
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar Servidor

```bash
python main.py
```

O con uvicorn directamente:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📊 Endpoints Disponibles

### Autenticación
- `POST /auth/login` - Obtener JWT token

### Usuarios
- `POST /users` - Crear usuario (público)
- `GET /users` - Listar todos (SUPERADMIN)
- `GET /users/{id_usuario}` - Obtener por ID (SUPERADMIN)
- `PUT /users/{id_usuario}` - Actualizar (SUPERADMIN)
- `PATCH /users/{id_usuario}/password` - Cambiar contraseña (SUPERADMIN)
- `DELETE /users/{id_usuario}` - Desactivar (SUPERADMIN)

### Health Check
- `GET /health` - Estado del API

---

## 🔑 Roles del Sistema

```
CONSULTA   → Lectura de documentos
ARCHIVO    → Gestión operativa
SUPERADMIN → Control total + gestión de usuarios
```

---

## 💾 Base de Datos

### Tabla: gesdoc.usuarios

```sql
CREATE TABLE usuarios (
  id_usuario SERIAL PRIMARY KEY,
  usuario VARCHAR(50) UNIQUE NOT NULL,
  nombre VARCHAR(150) NOT NULL,
  rol VARCHAR(50) CHECK (rol IN ('CONSULTA','ARCHIVO','SUPERADMIN')),
  activo BOOLEAN DEFAULT TRUE,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  password_hash VARCHAR(255)
);
```

---

## 🔒 Seguridad

| Aspecto | Implementación |
|--------|-----------------|
| **Hash de contraseñas** | bcrypt (rounds automáticos) |
| **Autenticación** | JWT con expiración |
| **Autorización** | Control de roles por endpoint |
| **Validación** | Pydantic + SQL parametrizado |
| **Datos sensibles** | Nunca retornar password_hash |

---

## 🏗️ Estructura del Código

```
app/
├── api/
│   └── routes/
│       ├── auth.py          # POST /auth/login
│       └── users.py         # CRUD completo
├── core/
│   ├── config.py           # Variables de entorno
│   └── security.py         # JWT + bcrypt + roles
├── db/
│   └── session.py          # Conexión PostgreSQL
├── schemas/
│   ├── auth_schema.py      # LoginRequest, TokenResponse
│   └── user_schema.py      # UserCreateRequest, UserResponse, etc.
├── services/
│   ├── auth_service.py     # login()
│   └── user_service.py     # create_user, list_users, get_user_by_id, etc.
└── main.py                 # FastAPI app + routers
```

---

## 📝 Ejemplo de Uso Completo

### 1. Crear usuario SUPERADMIN

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "usuario": "admin",
    "nombre": "Administrador MEDARCH",
    "password": "Admin@123456",
    "rol": "SUPERADMIN"
  }'
```

**Respuesta:**
```json
{
  "id_usuario": 1,
  "usuario": "admin",
  "nombre": "Administrador MEDARCH",
  "rol": "SUPERADMIN",
  "activo": true,
  "fecha_creacion": "2026-04-24T13:23:22.821Z"
}
```

### 2. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "usuario": "admin",
    "password": "Admin@123456"
  }'
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 3. Usar token para acceder a endpoints SUPERADMIN

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Listar usuarios
curl -X GET http://localhost:8000/users \
  -H "Authorization: Bearer $TOKEN"

# Crear nuevo usuario
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "usuario": "jgarcia",
    "nombre": "Juan García",
    "password": "UserPass@789",
    "rol": "ARCHIVO"
  }'
```

### 4. Actualizar usuario

```bash
curl -X PUT http://localhost:8000/users/2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan García López",
    "rol": "CONSULTA",
    "activo": true
  }'
```

### 5. Cambiar contraseña

```bash
curl -X PATCH http://localhost:8000/users/2/password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nueva_password": "NewPassword@999"
  }'
```

### 6. Desactivar usuario

```bash
curl -X DELETE http://localhost:8000/users/2 \
  -H "Authorization: Bearer $TOKEN"
```

---

## ✅ Checklist de Implementación

- [x] Creación de usuario (POST /users)
- [x] Listado de usuarios (GET /users) - SUPERADMIN
- [x] Obtener usuario por ID (GET /users/{id}) - SUPERADMIN
- [x] Actualizar usuario (PUT /users/{id}) - SUPERADMIN
- [x] Cambiar contraseña (PATCH /users/{id}/password) - SUPERADMIN
- [x] Desactivar usuario (DELETE /users/{id}) - SUPERADMIN
- [x] Autenticación con JWT
- [x] Control de roles
- [x] Validación de entrada
- [x] Manejo de errores HTTP
- [x] Hash de contraseñas con bcrypt
- [x] Documentación completa

---

## 🐛 Troubleshooting

### Error: "No se pudo conectar a la base de datos"

**Solución:**
- Verificar que PostgreSQL está corriendo
- Validar credenciales en `.env`
- Confirmar que la BD `medarch_db` existe
- Verificar que el esquema `gesdoc` existe

### Error: "No tienes permisos para esta operación"

**Solución:**
- Solo usuarios con rol `SUPERADMIN` pueden acceder a endpoints CRUD
- Verificar que el usuario tiene rol SUPERADMIN en BD
- Verificar que el JWT es válido y no ha expirado

### Error: "El usuario ya existe"

**Solución:**
- El campo `usuario` es único en la BD
- Usar un nombre de usuario diferente
- O verificar que el usuario no existe ya con `GET /users`

---

## 📞 Soporte Interno

Para cambios o nuevas funcionalidades:

1. Revisar `CRUD_USUARIOS.md` para especificaciones actuales
2. Seguir el patrón de `user_service.py` para nuevas operaciones
3. Actualizar esquemas en `user_schema.py` si necesario
4. Documentar en este README

---

## 🚀 Próximas Mejoras

- [ ] Reset de contraseña por email
- [ ] Autenticación 2FA
- [ ] Cambio de contraseña propia (sin ser SUPERADMIN)
- [ ] Auditoría de acciones en `log_auditoria`
- [ ] Rate limiting
- [ ] Documentación Swagger automática
- [ ] Tests unitarios e integración

---

**API lista para producción. Revisar CRUD_USUARIOS.md para detalles técnicos.**
