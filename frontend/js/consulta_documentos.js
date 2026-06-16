import { getJson } from "./api.js";
import { ensureSession, escapeHtml, formatDateTime, logout, setButtonLoading, setMessage } from "./ui.js";

const consultaMessage = document.querySelector("#consultaMessage");
const refreshButton = document.querySelector("#refreshConsulta");
const clearFiltersButton = document.querySelector("#clearConsultaFilters");
const logoutButton = document.querySelector("#logoutButton");
const consultaForm = document.querySelector("#consultaForm");
const consultaQuery = document.querySelector("#consultaQuery");
const consultaTableBody = document.querySelector("#consultaTableBody");
const consultaEmptyState = document.querySelector("#consultaEmptyState");

const state = {
	documents: [],
};

function stateLabel(estado) {
	const labels = {
		PENDIENTE: "Pendiente",
		EN_REVISION: "En revision",
		PROCESADO: "Procesado",
		ERROR: "Error",
	};

	return labels[estado] || estado || "-";
}

function stateClass(estado) {
	const map = {
		PENDIENTE: "medarch-chip-pending",
		EN_REVISION: "medarch-chip-review",
		PROCESADO: "medarch-chip-processed",
		ERROR: "medarch-chip-error",
	};

	return map[estado] || "medarch-chip-muted";
}

function buildQuery() {
	const params = new URLSearchParams();
	const query = getSearchTerm();

	if (query) {
		params.set("q", query);
	}

	const queryString = params.toString();
	return queryString ? `?${queryString}` : "";
}

function getSearchTerm() {
	return String(consultaQuery?.value || "").trim();
}

function renderDocuments() {
	if (!consultaTableBody || !consultaEmptyState) {
		return;
	}

	if (!state.documents.length) {
		consultaTableBody.innerHTML = "";
		consultaEmptyState.classList.remove("d-none");
		return;
	}

	consultaEmptyState.classList.add("d-none");
	consultaTableBody.innerHTML = state.documents.map((document) => `
		<tr>
			<td class="fw-semibold">#${document.id_documento}</td>
			<td>
				<div class="fw-semibold">${escapeHtml(document.paciente_numero_documento || "-")}</div>
				<div class="small medarch-muted text-break">${escapeHtml(document.paciente_nombre || "Sin nombre")}</div>
			</td>
			<td>
				<div class="fw-semibold text-break">${escapeHtml(document.nombre_archivo || document.nombre_archivo_original || "-")}</div>
				<div class="small medarch-muted">${formatDateTime(document.fecha_procesado || document.fecha_carga)}</div>
			</td>
			<td>
				<div class="fw-semibold">${escapeHtml(document.tipo_codigo || "-")}</div>
				<div class="small medarch-muted text-break">${escapeHtml(document.tipo_descripcion || "Sin tipo")}</div>
			</td>
			<td><span class="medarch-chip ${stateClass(document.estado)}">${stateLabel(document.estado)}</span></td>
			<td class="text-break">${escapeHtml(document.ruta_archivo || "-")}</td>
		</tr>
	`).join("");
}

async function loadDocuments(options = {}) {
	if (!options.preserveMessage) {
		setMessage(consultaMessage, "");
	}

	if (!getSearchTerm()) {
		state.documents = [];
		if (consultaEmptyState) {
			consultaEmptyState.textContent = "Ingresa un nombre o identificacion para consultar documentos.";
		}
		renderDocuments();
		setMessage(consultaMessage, "Ingresa el nombre del paciente o su identificacion para consultar.", "warning");
		return;
	}

	setButtonLoading(refreshButton, true, "Consultando...");

	try {
		state.documents = await getJson(`/documents${buildQuery()}`);
		if (consultaEmptyState) {
			consultaEmptyState.textContent = "No hay documentos para los filtros aplicados.";
		}
		renderDocuments();
	} catch (error) {
		setMessage(consultaMessage, error.message || "No fue posible consultar los documentos.");
	} finally {
		setButtonLoading(refreshButton, false);
	}
}

function bindEvents() {
	logoutButton?.addEventListener("click", logout);
	refreshButton?.addEventListener("click", () => loadDocuments());
	consultaForm?.addEventListener("submit", (event) => {
		event.preventDefault();
		loadDocuments();
	});
	clearFiltersButton?.addEventListener("click", () => {
		if (consultaQuery) {
			consultaQuery.value = "";
		}
		state.documents = [];
		if (consultaEmptyState) {
			consultaEmptyState.textContent = "Ingresa un nombre o identificacion para consultar documentos.";
		}
		renderDocuments();
		setMessage(consultaMessage, "");
	});
}

if (ensureSession()) {
	bindEvents();
	renderDocuments();
}
