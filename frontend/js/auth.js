import { getToken, postJson, setToken } from "./api.js";
import { getLoginRedirect, setMessage, setButtonLoading } from "./ui.js";

const form = document.querySelector("#loginForm");
const messageBox = document.querySelector("#loginMessage");
const submitButton = document.querySelector("#loginSubmit");

if (getToken()) {
	window.location.href = getLoginRedirect();
}

function validateForm(usuario, password) {
	if (!usuario || !password) {
		return "Completa usuario y password.";
	}

	if (usuario.length < 3) {
		return "El usuario debe tener al menos 3 caracteres.";
	}

	if (password.length < 8) {
		return "La contraseña debe tener al menos 8 caracteres.";
	}

	return null;
}

async function handleSubmit(event) {
	event.preventDefault();
	setMessage(messageBox, "");

	const formData = new FormData(form);
	const usuario = String(formData.get("usuario") || "").trim();
	const password = String(formData.get("password") || "");
	const validationMessage = validateForm(usuario, password);

	if (validationMessage) {
		setMessage(messageBox, validationMessage);
		return;
	}

	setButtonLoading(submitButton, true, "Validando...");

	try {
		const response = await postJson("/auth/login", { usuario, password }, { token: null });
		setToken(response.access_token);
		window.location.href = getLoginRedirect();
	} catch (error) {
		setMessage(messageBox, error.message || "No fue posible iniciar sesión.");
	} finally {
		setButtonLoading(submitButton, false);
	}
}

if (form) {
	form.addEventListener("submit", handleSubmit);
}