# 🔐 CONTEXTO AUTENTICACIÓN Y USUARIOS - MEDARCH

---

# 📌 OBJETIVO

Implementar gestión de usuarios y autenticación segura en el sistema MEDARCH usando JWT.

---

# 🏗️ TECNOLOGÍA

* Backend: Python
* Framework: FastAPI
* Base de datos: PostgreSQL
* Autenticación: JWT
* Hash de contraseñas: bcrypt

---

# 🧩 TABLA USUARIOS

Tabla: gesdoc.usuarios

Campos:

* id_usuario (PK)
* usuario (único)
* nombre
* rol (string)
* activo (boolean)
* fecha_creacion
* password_hash (VARCHAR 255)

---

# 🧠 ROLES

* CONSULTA → consulta y revisión de documentos
* ARCHIVO → gestión operativa y archivo
* SUPERADMIN → control total

---

# 🔐 REQUERIMIENTOS

## 1. Crear usuario

Endpoint:

POST /users

Recibe:

* usuario
* nombre
* password
* rol

Debe:

* Validar que usuario no exista
* Hashear contraseña con bcrypt
* Guardar en BD
* activo = true por defecto

---

## 2. Login

Endpoint:

POST /auth/login

Recibe:

* usuario
* password

Debe:

* Validar usuario existe
* Validar activo = true
* Verificar contraseña (bcrypt)
* Retornar JWT

---

## 3. JWT

Debe contener:

* id_usuario
* usuario
* rol
* expiración (1 hora)

---

## 4. Seguridad

* No almacenar contraseñas en texto plano
* No retornar password_hash
* Mensajes de error genéricos
* Usar SECRET_KEY desde config
* Algoritmo HS256

---

## 5. Autorización

* Crear dependencia para validar JWT
* Crear dependencia para validar roles

---

# 📁 ESTRUCTURA DEL CÓDIGO

app/
├── core/
│   ├── config.py
│   ├── security.py
│
├── db/
│   ├── session.py
│
├── schemas/
│   ├── auth_schema.py
│   ├── user_schema.py
│
├── services/
│   ├── auth_service.py
│   ├── user_service.py
│
├── api/
│   ├── routes/
│   │   ├── auth.py
│   │   ├── users.py

---

# 🧠 RESPONSABILIDADES

* routes → reciben requests
* services → lógica de negocio
* security → JWT + bcrypt
* db → conexión BD

---

# ⚠️ REGLAS IMPORTANTES

* Separar capas (no mezclar lógica)
* Código modular
* Manejo de errores correcto
* Tipado con Pydantic
* Preparado para escalar

---

# 🎯 OBJETIVO FINAL

Sistema de autenticación profesional listo para producción.

---

# FIN