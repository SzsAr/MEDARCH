import { clearToken, getToken } from "./api.js";

export function getLoginRedirect() {
	return "./dashboard.html";
}

export function getUsersRedirect() {
	return "./users.html";
}

export function ensureSession() {
	if (!getToken()) {
		window.location.href = "./login.html";
		return false;
	}

	return true;
}

export function logout() {
	clearToken();
	window.location.href = "./login.html";
}

export function setMessage(container, message, type = "danger") {
	if (!container) {
		return;
	}

	if (!message) {
		container.innerHTML = "";
		return;
	}

	container.innerHTML = `
		<div class="alert alert-${type} medarch-fade-in mb-0" role="alert">
			${message}
		</div>
	`;
}

export function setButtonLoading(button, isLoading, loadingText = "Procesando...") {
	if (!button) {
		return;
	}

	if (isLoading) {
		button.dataset.originalText = button.textContent;
		button.disabled = true;
		button.innerHTML = `
			<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
			${loadingText}
		`;
		return;
	}

	button.disabled = false;
	button.textContent = button.dataset.originalText || button.textContent;
}

export function escapeHtml(value) {
	return String(value)
		.replaceAll("&", "&amp;")
		.replaceAll("<", "&lt;")
		.replaceAll(">", "&gt;")
		.replaceAll('"', "&quot;")
		.replaceAll("'", "&#39;");
}

export function formatDateTime(value) {
	if (!value) {
		return "-";
	}

	const date = new Date(value);
	if (Number.isNaN(date.getTime())) {
		return value;
	}

	return new Intl.DateTimeFormat("es-CO", {
		dateStyle: "medium",
		timeStyle: "short",
	}).format(date);
}