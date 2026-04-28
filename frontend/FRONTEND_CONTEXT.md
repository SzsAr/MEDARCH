"""
Proyecto: MEDARCH

Crear frontend profesional para sistema de gestión documental clínico.

---

OBJETIVO INICIAL:

Construir la vista de login conectada al backend en FastAPI.

---

BACKEND:

* Endpoint:
  POST http://127.0.0.1:8000/auth/login

* Request JSON:
  {
  "usuario": "string",
  "password": "string"
  }

* Response:
  {
  "access_token": "JWT"
  }

---

⚠️ REGLAS DE ARQUITECTURA (OBLIGATORIAS)

1. NO crear todo en un solo archivo
2. NO usar estilos inline
3. NO mezclar JS dentro del HTML
4. Separar en múltiples archivos:

   * HTML → estructura
   * CSS → estilos
   * JS → lógica

---

📁 ESTRUCTURA OBLIGATORIA:

frontend/
├── pages/
│   ├── login.html
│   ├── dashboard.html
│
├── js/
│   ├── auth.js
│   ├── api.js
│   ├── ui.js
│
├── css/
│   ├── styles.css

---

🎨 DISEÑO UI/UX (MUY IMPORTANTE)

Estilo:

* Profesional (tipo hospital / sistema documental)
* Minimalista
* Limpio
* Sobrio

Colores:

* Primario: #1F3A5F
* Secundario: #4A90E2
* Fondo: #F4F6F8
* Texto: #2C3E50
* Error: #E74C3C

---

🧩 LOGIN PAGE (login.html)

Debe contener:

* Formulario centrado
* Card moderna con sombra
* Inputs:
  usuario
  password
* Botón "Iniciar sesión"

---

⚙️ FUNCIONALIDAD (JS)

Crear archivo js/auth.js:

Debe:

1. Capturar submit del formulario
2. Validar campos
3. Enviar request con fetch
4. Manejar respuesta:

   ✔ Éxito:

   * Guardar token en localStorage
   * Redirigir a dashboard.html

   ❌ Error:

   * Mostrar mensaje elegante en pantalla

---

🧠 API LAYER (IMPORTANTE)

Crear archivo js/api.js:

* Función reutilizable para requests
* Manejo de errores HTTP
* Preparado para enviar token en futuras requests

---

🎯 UX (OBLIGATORIO)

* Mostrar loader mientras hace login
* Deshabilitar botón durante petición
* Mostrar errores debajo del formulario (NO alert)
* Animaciones suaves (hover, focus)

---

🧼 CSS (styles.css)

* Usar Bootstrap como base
* Personalizar con estilos propios
* Bordes redondeados
* Sombras suaves
* Espaciado limpio

---

🚫 EVITAR (MUY IMPORTANTE)

* NO usar alert()
* NO usar inline styles
* NO usar JS dentro de HTML
* NO usar diseño básico sin estilos
* NO duplicar código
* NO acoplar lógica de API directamente en HTML

---

🎯 OUTPUT ESPERADO

Generar:

1. login.html completo
2. styles.css profesional
3. auth.js funcional
4. api.js reutilizable

Todo listo para integrarse con FastAPI.

---

BONUS:

* Preparar base para dashboard.html (aunque sea vacío)
* Código limpio y escalable
  """
