# MEDARCH Frontend

Frontend estático para el login y el CRUD de usuarios de MEDARCH.

## Estructura

- `pages/login.html`: formulario de autenticación.
- `pages/dashboard.html`: panel inicial después del login.
- `pages/users.html`: lista y mantenimiento de usuarios.
- `js/api.js`: capa reutilizable para consumir la API.
- `js/auth.js`: flujo de login.
- `js/users.js`: CRUD de usuarios.
- `js/ui.js`: utilidades de interfaz y sesión.
- `css/styles.css`: estilos personalizados.

## Requisitos

- Backend FastAPI ejecutándose en `http://127.0.0.1:8000`.
- Servir esta carpeta con un servidor estático, por ejemplo:

```powershell
cd frontend
python -m http.server 5500
```

## Flujo

1. Abrir `http://127.0.0.1:5500/pages/login.html`.
2. Iniciar sesión con `usuario` y `password`.
3. El token se guarda en `localStorage`.
4. El panel permite entrar al CRUD de usuarios.

## Configuración

Si necesitas otro backend, actualiza `window.MEDARCH_API_BASE_URL` antes de cargar los módulos o edita `js/api.js`.