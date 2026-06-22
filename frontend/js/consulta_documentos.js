import { buildUrl, getJson, getToken, redirectToLogin } from "./api.js";
import { ensureSession, escapeHtml, logout, setButtonLoading, setMessage } from "./ui.js";

const consultaMessage = document.querySelector("#consultaMessage");
const refreshButton = document.querySelector("#refreshConsulta");
const clearFiltersButton = document.querySelector("#clearConsultaFilters");
const logoutButton = document.querySelector("#logoutButton");
const consultaForm = document.querySelector("#consultaForm");
const consultaType = document.querySelector("#consultaType");
const consultaQuery = document.querySelector("#consultaQuery");
const consultaTableBody = document.querySelector("#consultaTableBody");
const consultaEmptyState = document.querySelector("#consultaEmptyState");

const state = {
	documents: [],
	documentTypes: [],
};

function formatDocumentDate(value) {
	if (!value) {
		return "-";
	}

	const [year, month, day] = String(value).slice(0, 10).split("-");
	if (!year || !month || !day) {
		return escapeHtml(value);
	}

	return `${day}/${month}/${year}`;
}

function buildQuery() {
	const params = new URLSearchParams();
	const query = getSearchTerm();
	const typeId = getSelectedTypeId();

	params.set("estado", "PROCESADO");
	if (query) {
		params.set("q", query);
	}
	if (typeId) {
		params.set("id_tipo", typeId);
	}

	const queryString = params.toString();
	return queryString ? `?${queryString}` : "";
}

function getSelectedTypeId() {
	return String(consultaType?.value || "").trim();
}

function getSearchTerm() {
	return String(consultaQuery?.value || "").trim();
}

function renderDocumentTypes() {
	if (!consultaType) {
		return;
	}

	const options = state.documentTypes.map((type) => `
		<option value="${type.id_tipo}">${escapeHtml(type.codigo)} - ${escapeHtml(type.descripcion)}</option>
	`).join("");

	consultaType.innerHTML = `<option value="">Todos los tipos</option>${options}`;
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
			</td>
			<td>
				<div class="fw-semibold">${escapeHtml(document.tipo_codigo || "-")}</div>
				<div class="small medarch-muted text-break">${escapeHtml(document.tipo_descripcion || "Sin tipo")}</div>
			</td>
			<td class="text-nowrap">${formatDocumentDate(document.fecha)}</td>
			<td class="text-end">
				<button type="button" class="btn btn-sm btn-outline-primary" data-action="open-file" data-id="${document.id_documento}" ${document.ruta_archivo ? "" : "disabled"}>
					Abrir archivo
				</button>
			</td>
		</tr>
	`).join("");
}

async function loadDocumentTypes() {
	state.documentTypes = await getJson("/documents/meta/tipos");
	renderDocumentTypes();
}

async function loadDocuments(options = {}) {
	if (!options.preserveMessage) {
		setMessage(consultaMessage, "");
	}

	if (!getSearchTerm() && !getSelectedTypeId()) {
		state.documents = [];
		if (consultaEmptyState) {
			consultaEmptyState.textContent = "Selecciona un tipo o ingresa nombre/identificacion para consultar documentos.";
		}
		renderDocuments();
		setMessage(consultaMessage, "Selecciona un tipo de documento o ingresa el nombre/identificacion del paciente para consultar.", "warning");
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

async function openDocumentFile(documentId, button = null) {
	setMessage(consultaMessage, "");
	setButtonLoading(button, true, "Abriendo...");

	try {
		const response = await fetch(buildUrl(`/documents/${documentId}/file`), {
			headers: {
				Authorization: `Bearer ${getToken()}`,
			},
		});

		if (!response.ok) {
			if (response.status === 401) {
				redirectToLogin();
				return;
			}

			let message = `HTTP ${response.status}`;
			try {
				const payload = await response.json();
				message = payload?.detail || payload?.message || message;
			} catch {
				message = await response.text() || message;
			}
			throw new Error(message);
		}

		const blob = await response.blob();
		const url = URL.createObjectURL(blob);
		const link = document.createElement("a");
		link.href = url;
		link.target = "_blank";
		link.rel = "noopener";
		link.click();
		setTimeout(() => URL.revokeObjectURL(url), 300000);
	} catch (error) {
		setMessage(consultaMessage, error.message || "No fue posible abrir el archivo.");
	} finally {
		setButtonLoading(button, false);
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
		if (consultaType) {
			consultaType.value = "";
		}
		if (consultaQuery) {
			consultaQuery.value = "";
		}
		state.documents = [];
		if (consultaEmptyState) {
			consultaEmptyState.textContent = "Selecciona un tipo o ingresa nombre/identificacion para consultar documentos.";
		}
		renderDocuments();
		setMessage(consultaMessage, "");
	});
	consultaTableBody?.addEventListener("click", (event) => {
		const button = event.target.closest("button[data-action='open-file']");
		if (!button) {
			return;
		}

		openDocumentFile(Number(button.dataset.id), button);
	});
}

if (ensureSession()) {
	loadDocumentTypes()
		.catch((error) => setMessage(consultaMessage, error.message || "No fue posible cargar los tipos de documento."))
		.finally(() => {
			bindEvents();
			renderDocuments();
		});
}
