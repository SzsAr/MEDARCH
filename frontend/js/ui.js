import { clearToken, decodeJwtPayload, hasValidToken } from "./api.js";

const PAGE_ROLES = {
	"dashboard.html": ["SUPERADMIN", "ARCHIVO", "CONSULTA"],
	"documentos.html": ["SUPERADMIN", "ARCHIVO"],
	"consulta_documentos.html": ["SUPERADMIN", "ARCHIVO", "CONSULTA"],
	"pacientes.html": ["SUPERADMIN"],
	"tipos_documento.html": ["SUPERADMIN"],
	"users.html": ["SUPERADMIN"],
};

export function getLoginRedirect() {
	return "./dashboard.html";
}

export function getUsersRedirect() {
	return "./users.html";
}

export function ensureSession() {
	if (!hasValidToken()) {
		clearToken();
		window.location.href = "./login.html";
		return false;
	}

	const role = String(decodeJwtPayload()?.rol || "").toUpperCase();
	const currentPage = window.location.pathname.split("/").pop() || "dashboard.html";
	const allowedRoles = PAGE_ROLES[currentPage];

	if (allowedRoles && !allowedRoles.includes(role)) {
		window.location.replace("./dashboard.html");
		return false;
	}

	configureNavigation(role, currentPage);

	return true;
}

export function configureNavigation(role, currentPage) {
	document.querySelectorAll("[data-nav-roles]").forEach((element) => {
		const allowedRoles = String(element.dataset.navRoles || "")
			.split(",")
			.map((item) => item.trim())
			.filter(Boolean);
		element.hidden = !allowedRoles.includes(role);
	});

	document.querySelectorAll(".medarch-nav-pill[href]").forEach((link) => {
		const targetPage = link.getAttribute("href")?.split("/").pop();
		const isActive = targetPage === currentPage;
		link.classList.toggle("active", isActive);
		if (isActive) {
			link.setAttribute("aria-current", "page");
		} else {
			link.removeAttribute("aria-current");
		}
	});
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
