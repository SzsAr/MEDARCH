# 📋 CRUD DE USUARIOS - MEDARCH API

Documentación completa de los endpoints para gestionar usuarios en MEDARCH.

---

## 🔐 Requisitos Previos

- Autenticación JWT mediante `/auth/login`
- Token debe incluir rol SUPERADMIN para operaciones CRUD (excepto POST /users)
- Todas las operaciones están tipadas con Pydantic
- Las contraseñas se hashean con bcrypt

---

## 1️⃣ CREAR USUARIO

**Endpoint:** `POST /users`

**Autenticación:** ❌ No requerida (endpoint público)

**Request Body:**
```json
{
  "usuario": "jgarcia",
  "nombre": "Juan García López",
  "password": "SecurePass123!",
  "rol": "ARCHIVO"
}
```

**Validaciones:**
- `usuario`: 3-50 caracteres, debe ser único
- `nombre`: 2-150 caracteres
- `password`: mínimo 8 caracteres
- `rol`: uno de `CONSULTA`, `ARCHIVO`, `SUPERADMIN`

**Response 201:**
```json
{
  "id_usuario": 1,
  "usuario": "jgarcia",
  "nombre": "Juan García López",
  "rol": "ARCHIVO",
  "activo": true,
  "fecha_creacion": "2026-04-24T13:23:22.821Z"
}
```

**Errores:**
- `409 Conflict`: Usuario ya existe
- `400 Bad Request`: Validación fallida
- `500 Internal Server Error`: Error en base de datos

---

## 2️⃣ LISTAR USUARIOS

**Endpoint:** `GET /users`

**Autenticación:** ✅ Requerida - SUPERADMIN

**Headers:**
```
Authorization: Bearer <token_jwt>
```

**Response 200:**
```json
[
  {
    "id_usuario": 1,
    "usuario": "jgarcia",
    "nombre": "Juan García López",
    "rol": "ARCHIVO",
    "activo": true,
    "fecha_creacion": "2026-04-24T13:23:22.821Z"
  },
  {
    "id_usuario": 2,
    "usuario": "msmith",
    "nombre": "Mary Smith",
    "rol": "CONSULTA",
    "activo": true,
    "fecha_creacion": "2026-04-24T13:25:00.000Z"
  }
]
```

**Errores:**
- `401 Unauthorized`: Token ausente o inválido
- `403 Forbidden`: Usuario no tiene rol SUPERADMIN
- `500 Internal Server Error`: Error en base de datos

---

## 3️⃣ OBTENER USUARIO POR ID

**Endpoint:** `GET /users/{id_usuario}`

**Autenticación:** ✅ Requerida - SUPERADMIN

**Parámetros:**
- `id_usuario` (path): ID del usuario a consultar

**Headers:**
```
Authorization: Bearer <token_jwt>
```

**Response 200:**
```json
{
  "id_usuario": 1,
  "usuario": "jgarcia",
  "nombre": "Juan García López",
  "rol": "ARCHIVO",
  "activo": true,
  "fecha_creacion": "2026-04-24T13:23:22.821Z"
}
```

**Errores:**
- `401 Unauthorized`: Token ausente o inválido
- `403 Forbidden`: Usuario no tiene rol SUPERADMIN
- `404 Not Found`: Usuario no existe
- `500 Internal Server Error`: Error en base de datos

---

## 4️⃣ ACTUALIZAR USUARIO

**Endpoint:** `PUT /users/{id_usuario}`

**Autenticación:** ✅ Requerida - SUPERADMIN

**Parámetros:**
- `id_usuario` (path): ID del usuario a actualizar

**Headers:**
```
Authorization: Bearer <token_jwt>
```

**Request Body:**
```json
{
  "nombre": "Juan García Nuevo",
  "rol": "CONSULTA",
  "activo": true
}
```

**Validaciones:**
- `nombre`: 2-150 caracteres (requerido)
- `rol`: uno de `CONSULTA`, `ARCHIVO`, `SUPERADMIN` (requerido)
- `activo`: booleano (requerido)
- No se puede cambiar el campo `usuario`
- No se modifica la contraseña (usar PATCH para eso)

**Response 200:**
```json
{
  "id_usuario": 1,
  "usuario": "jgarcia",
  "nombre": "Juan García Nuevo",
  "rol": "CONSULTA",
  "activo": true,
  "fecha_creacion": "2026-04-24T13:23:22.821Z"
}
```

**Errores:**
- `401 Unauthorized`: Token ausente o inválido
- `403 Forbidden`: Usuario no tiene rol SUPERADMIN
- `404 Not Found`: Usuario no existe
- `400 Bad Request`: Validación fallida
- `500 Internal Server Error`: Error en base de datos

---

## 5️⃣ CAMBIAR CONTRASEÑA

**Endpoint:** `PATCH /users/{id_usuario}/password`

**Autenticación:** ✅ Requerida - SUPERADMIN

**Parámetros:**
- `id_usuario` (path): ID del usuario cuya contraseña se cambiar

**Headers:**
```
Authorization: Bearer <token_jwt>
Content-Type: application/json
```

**Request Body:**
```json
{
  "nueva_password": "NewSecurePass456!"
}
```

**Validaciones:**
- `nueva_password`: mínimo 8 caracteres (requerido)

**Response 200:**
```json
{
  "message": "Contraseña actualizada correctamente"
}
```

**Errores:**
- `401 Unauthorized`: Token ausente o inválido
- `403 Forbidden`: Usuario no tiene rol SUPERADMIN
- `404 Not Found`: Usuario no existe
- `400 Bad Request`: Validación fallida
- `500 Internal Server Error`: Error en base de datos

---

## 6️⃣ DESACTIVAR USUARIO (Soft Delete)

**Endpoint:** `DELETE /users/{id_usuario}`

**Autenticación:** ✅ Requerida - SUPERADMIN

**Comportamiento:** 
- No elimina físicamente el usuario
- Establece `activo = false`
- El usuario no puede iniciar sesión después de desactivarse

**Parámetros:**
- `id_usuario` (path): ID del usuario a desactivar

**Headers:**
```
Authorization: Bearer <token_jwt>
```

**Response 200:**
```json
{
  "message": "Usuario desactivado correctamente"
}
```

**Errores:**
- `401 Unauthorized`: Token ausente o inválido
- `403 Forbidden`: Usuario no tiene rol SUPERADMIN
- `404 Not Found`: Usuario no existe
- `500 Internal Server Error`: Error en base de datos

---

## 🧪 Ejemplos de Uso

### Crear usuario inicial (SUPERADMIN)
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "usuario": "admin",
    "nombre": "Administrador",
    "password": "AdminPass123!",
    "rol": "SUPERADMIN"
  }'
```

### Login y obtener token
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "usuario": "admin",
    "password": "AdminPass123!"
  }'
```

### Listar todos los usuarios
```bash
TOKEN="<token_from_login>"
curl -X GET http://localhost:8000/users \
  -H "Authorization: Bearer $TOKEN"
```

### Actualizar usuario
```bash
TOKEN="<token_from_login>"
curl -X PUT http://localhost:8000/users/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Nuevo Nombre",
    "rol": "ARCHIVO",
    "activo": true
  }'
```

### Cambiar contraseña
```bash
TOKEN="<token_from_login>"
curl -X PATCH http://localhost:8000/users/1/password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nueva_password": "NewPassword789!"
  }'
```

### Desactivar usuario
```bash
TOKEN="<token_from_login>"
curl -X DELETE http://localhost:8000/users/1 \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🏗️ Estructura del Código

```
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── users.py          # Endpoints CRUD
│   ├── core/
│   │   ├── config.py             # Configuración
│   │   └── security.py           # JWT + bcrypt + autorización
│   ├── db/
│   │   └── session.py            # Conexión a BD
│   ├── schemas/
│   │   └── user_schema.py        # Modelos Pydantic
│   └── services/
│       └── user_service.py       # Lógica de negocio
```

---

## 🔒 Seguridad

✅ **Implementado:**
- Contraseñas hasheadas con bcrypt
- JWT con expiración
- Control de roles (SUPERADMIN)
- Validación de entrada con Pydantic
- Manejo de errores seguro (sin exponer detalles)
- Soft delete (nunca eliminar físicamente)
- No se retorna password_hash en respuestas

---

## ⚠️ Reglas de Negocio

1. **Solo SUPERADMIN** puede:
   - Listar usuarios
   - Ver detalles de usuario
   - Actualizar usuario
   - Cambiar contraseña
   - Desactivar usuario

2. **Cualquiera** puede:
   - Crear usuario (POST /users) - endpoint público

3. **Nunca se debe:**
   - Eliminar físicamente un usuario
   - Cambiar el usuario después de creado
   - Exponer password_hash
   - Permitir roles inválidos

4. **Usuario inactivo:**
   - No puede iniciar sesión
   - Sigue existiendo en BD (auditoría)
   - Puede reactivarse con PUT (setear activo=true)

---

## 🚀 Próximos Pasos

- [ ] Implementar auditoría de cambios en log_auditoria
- [ ] Agregar endpoint para resetear contraseña
- [ ] Implementar 2FA (dos factores)
- [ ] Agregar endpoint para cambiar contraseña propia
- [ ] Implementar rate limiting en endpoints críticos
