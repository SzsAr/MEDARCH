# ✅ CAMBIO: DELETE → Toggle de Estado Usuario

**Fecha:** 2026-04-24  
**Cambio:** Endpoint DELETE /users/{id} ahora es un toggle (activar/desactivar)

---

## 🔄 Lo que cambió

### Antes (Solo desactivar)

```
DELETE /users/1
↓
activo = false (solo desactivar)
```

### Ahora (Toggle)

```
DELETE /users/1 (usuario activo)
↓
activo = false (desactivado)

DELETE /users/1 (usuario inactivo)
↓
activo = true (reactivado)
```

---

## 📋 Cambios en Código

### app/services/user_service.py

**Función renombrada y mejorada:**

```python
# ANTES
def delete_user(id_usuario: int) -> Dict[str, str]:
    # Solo ponía activo = FALSE

# AHORA
def toggle_user_status(id_usuario: int) -> Dict[str, str]:
    # Lee estado actual
    # Si activo=true → pone false
    # Si activo=false → pone true
```

### app/api/routes/users.py

**Endpoint actualizado:**

```python
# ANTES
@router.delete("/{id_usuario}")
def delete_user_endpoint(...):
    return delete_user(id_usuario)

# AHORA
@router.delete("/{id_usuario}")
def toggle_user_status_endpoint(...):
    return toggle_user_status(id_usuario)
```

---

## 🧪 Ejemplos de Uso

### Desactivar usuario (primer toggle)

```bash
DELETE http://localhost:8000/users/2
Header: Authorization: Bearer <token>

Respuesta 200:
{
  "message": "Usuario desactivado correctamente"
}
```

### Reactivar usuario (segundo toggle)

```bash
DELETE http://localhost:8000/users/2
Header: Authorization: Bearer <token>

Respuesta 200:
{
  "message": "Usuario activado correctamente"
}
```

---

## 📊 Estados del Usuario

| Operación | Estado Anterior | Estado Nuevo | Mensaje |
|-----------|-----------------|--------------|---------|
| DELETE /users/2 (1er vez) | activo=true | activo=false | "Usuario desactivado correctamente" |
| DELETE /users/2 (2da vez) | activo=false | activo=true | "Usuario activado correctamente" |
| DELETE /users/2 (3ra vez) | activo=true | activo=false | "Usuario desactivado correctamente" |

---

## ✅ Ventajas

✅ Toggle permite activar/desactivar sin eliminar datos  
✅ No hay soft delete unidireccional  
✅ Se puede reactivar un usuario fácilmente  
✅ Auditoría completa en la BD  
✅ Mismo endpoint para ambas operaciones  

---

## 🔍 Verificación

**Verificar estado antes y después:**

```bash
# Obtener usuario
curl -X GET http://localhost:8000/users/2 \
  -H "Authorization: Bearer <token>"

# Ver campo "activo": true/false
```

---

**El sistema ahora usa toggle en lugar de desactivación unidireccional.**
