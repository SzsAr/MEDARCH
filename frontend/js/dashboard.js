import { decodeJwtPayload, getJson } from "./api.js";
import { ensureSession, logout, setButtonLoading, setMessage } from "./ui.js";

const dashboardMessage = document.querySelector("#dashboardMessage");
const refreshDashboardButton = document.querySelector("#refreshDashboard");
const logoutButton = document.querySelector("#logoutButton");

const metricElements = {
	PENDIENTE: document.querySelector("#dashboardPending"),
	EN_REVISION: document.querySelector("#dashboardReview"),
	PROCESADO: document.querySelector("#dashboardProcessed"),
	ERROR: document.querySelector("#dashboardError"),
};

function configureDashboardForUser() {
	const payload = decodeJwtPayload() || {};
	const role = String(payload.rol || "CONSULTA").toUpperCase();
	const displayName = String(payload.nombre || payload.usuario || "").trim();
	const canManageDocuments = ["ARCHIVO", "SUPERADMIN"].includes(role);

	const greeting = document.querySelector("#dashboardGreeting");
	const intro = document.querySelector("#dashboardIntro");
	const primaryAction = document.querySelector("#primaryAction");
	const adminAccess = document.querySelector("#adminAccess");

	if (greeting) {
		greeting.textContent = displayName ? `Hola, ${displayName}` : "Bienvenido";
	}

	document.querySelectorAll("[data-role-access='ARCHIVO']").forEach((element) => {
		element.classList.toggle("d-none", !canManageDocuments);
	});

	if (!canManageDocuments && primaryAction) {
		primaryAction.href = "./consulta_documentos.html";
		primaryAction.querySelector("span")?.replaceChildren("Consultar documentos");
	}

	if (!canManageDocuments && intro) {
		intro.textContent = "Encuentra rápidamente los documentos de un paciente desde la consulta.";
	}

	adminAccess?.classList.toggle("d-none", role !== "SUPERADMIN");
}

function renderMetrics(documents) {
	const counts = {
		PENDIENTE: 0,
		EN_REVISION: 0,
		PROCESADO: 0,
		ERROR: 0,
	};

	for (const document of documents) {
		if (Object.hasOwn(counts, document.estado)) {
			counts[document.estado] += 1;
		}
	}

	for (const [state, element] of Object.entries(metricElements)) {
		if (element) {
			element.textContent = String(counts[state]);
		}
	}
}

async function loadDashboard() {
	setMessage(dashboardMessage, "");
	setButtonLoading(refreshDashboardButton, true, "Actualizando...");

	try {
		const documents = await getJson("/documents");
		renderMetrics(documents);
	} catch (error) {
		setMessage(
			dashboardMessage,
			error.message || "No fue posible actualizar el resumen. Puedes seguir usando los accesos rápidos.",
			"warning",
		);
	} finally {
		setButtonLoading(refreshDashboardButton, false);
	}
}

if (ensureSession()) {
	configureDashboardForUser();
	logoutButton?.addEventListener("click", logout);
	refreshDashboardButton?.addEventListener("click", loadDashboard);
	loadDashboard();
}
