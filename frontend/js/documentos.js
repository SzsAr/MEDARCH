import { decodeJwtPayload, getJson, patchJson } from "./api.js";
import { ensureSession, escapeHtml, formatDateTime, logout, setButtonLoading, setMessage } from "./ui.js";

const currentUserPayload = decodeJwtPayload();

const state = {
	documents: [],
	selectedId: null,
	documentTypes: [],
	patients: [],
	audit: [],
};

const documentsMessage = document.querySelector("#documentsMessage");
const refreshDocumentsButton = document.querySelector("#refreshDocuments");
const viewErrorsButton = document.querySelector("#viewErrorsButton");
const logoutButton = document.querySelector("#logoutButton");
const documentsFilterForm = document.querySelector("#documentsFilterForm");
const filterQuery = document.querySelector("#filterQuery");
const filterFechaDesde = document.querySelector("#filterFechaDesde");
const filterFechaHasta = document.querySelector("#filterFechaHasta");
const resetFiltersButton = document.querySelector("#resetFiltersButton");
const pendingDocumentsTableBody = document.querySelector("#pendingDocumentsTableBody");
const pendingDocumentsEmptyState = document.querySelector("#pendingDocumentsEmptyState");
const kpiPending = document.querySelector("#kpiPending");
const kpiReview = document.querySelector("#kpiReview");
const kpiError = document.querySelector("#kpiError");
const selectedDocumentEmpty = document.querySelector("#selectedDocumentEmpty");
const selectedDocumentPanel = document.querySelector("#selectedDocumentPanel");
const selectedDocumentEstado = document.querySelector("#selectedDocumentEstado");
const selectedDocumentId = document.querySelector("#selectedDocumentId");
const selectedDocumentOriginal = document.querySelector("#selectedDocumentOriginal");
const selectedDocumentPaciente = document.querySelector("#selectedDocumentPaciente");
const selectedDocumentTipo = document.querySelector("#selectedDocumentTipo");
const selectedDocumentFechaCarga = document.querySelector("#selectedDocumentFechaCarga");
const selectedDocumentFechaProcesado = document.querySelector("#selectedDocumentFechaProcesado");
const selectedDocumentNombreFinal = document.querySelector("#selectedDocumentNombreFinal");
const selectedDocumentRuta = document.querySelector("#selectedDocumentRuta");
const reviewDocumentButton = document.querySelector("#reviewDocumentButton");
const processDocumentButton = document.querySelector("#processDocumentButton");
const errorDocumentButton = document.querySelector("#errorDocumentButton");
const documentAuditEmpty = document.querySelector("#documentAuditEmpty");
const documentAuditList = document.querySelector("#documentAuditList");

const reviewConsecutiveDisplay = document.querySelector("#reviewConsecutiveDisplay");
const reviewPatientStatus = document.querySelector("#reviewPatientStatus");

const reviewModalEl = document.querySelector("#documentReviewModal");
const errorModalEl = document.querySelector("#documentErrorModal");
const errorDocumentsModalEl = document.querySelector("#documentErrorsModal");

const reviewForm = document.querySelector("#documentReviewForm");
const errorForm = document.querySelector("#documentErrorForm");

const reviewModalTitle = document.querySelector("#documentReviewModalLabel");
const errorModalTitle = document.querySelector("#documentErrorModalLabel");
const errorDocumentsTableBody = document.querySelector("#errorDocumentsTableBody");
const errorDocumentsEmptyState = document.querySelector("#errorDocumentsEmptyState");

const reviewDocumentIdInput = document.querySelector("#reviewDocumentId");
const reviewPatientIdInput = document.querySelector("#reviewPatientId");
const reviewPatientDocumentInput = document.querySelector("#reviewPatientDocument");
const reviewPatientNameInput = document.querySelector("#reviewPatientName");
const reviewTypeSelect = document.querySelector("#reviewType");
const reviewDateInput = document.querySelector("#reviewDate");
const reviewConsecutiveInput = document.querySelector("#reviewConsecutive");
const reviewSubmitButton = document.querySelector("#reviewSubmitButton");

const errorDocumentIdInput = document.querySelector("#errorDocumentId");
const errorDetailInput = document.querySelector("#errorDetail");
const errorSubmitButton = document.querySelector("#errorSubmitButton");

const reviewModal = window.bootstrap ? window.bootstrap.Modal.getOrCreateInstance(reviewModalEl) : null;
const errorModal = window.bootstrap ? window.bootstrap.Modal.getOrCreateInstance(errorModalEl) : null;
const errorDocumentsModal = window.bootstrap ? window.bootstrap.Modal.getOrCreateInstance(errorDocumentsModalEl) : null;

function formatDateOnly(value) {
	if (!value) {
		return "-";
	}

	const dateValue = new Date(value);
	if (Number.isNaN(dateValue.getTime())) {
		return String(value).slice(0, 10);
	}

	return new Intl.DateTimeFormat("es-CO", { dateStyle: "medium" }).format(dateValue);
}

function stateLabel(estado) {
	const labels = {
		PENDIENTE: "Pendiente",
		EN_REVISION: "En revisión",
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

function toDateInputValue(value) {
	if (!value) {
		return "";
	}

	if (typeof value === "string") {
		return value.slice(0, 10);
	}

	const dateValue = new Date(value);
	if (Number.isNaN(dateValue.getTime())) {
		return "";
	}

	return dateValue.toISOString().slice(0, 10);
}

function renderLookups() {
	const patientOptions = state.patients.length
		? state.patients.map((patient) => `
			<option value="${patient.id_paciente}" data-numero-documento="${escapeHtml(patient.numero_documento)}">${escapeHtml(patient.numero_documento)} · ${escapeHtml(patient.nombre || "Sin nombre")}</option>
		`).join("")
		: `<option value="">No hay pacientes disponibles</option>`;

	const typeOptions = state.documentTypes.length
		? state.documentTypes.map((type) => `
			<option value="${type.id_tipo}" data-codigo="${escapeHtml(type.codigo)}">${escapeHtml(type.codigo)} · ${escapeHtml(type.descripcion)}</option>
		`).join("")
		: `<option value="">No hay tipos disponibles</option>`;

	if (reviewTypeSelect) {
		reviewTypeSelect.innerHTML = typeOptions;
	}
}

function renderKpis() {
	const counts = {
		PENDIENTE: 0,
		EN_REVISION: 0,
		PROCESADO: 0,
		ERROR: 0,
	};

	for (const document of state.documents) {
		if (counts[document.estado] !== undefined) {
			counts[document.estado] += 1;
		}
	}

	if (kpiPending) {
		kpiPending.textContent = String(counts.PENDIENTE);
	}
	if (kpiReview) {
		kpiReview.textContent = String(counts.EN_REVISION);
	}
	if (kpiError) {
		kpiError.textContent = String(counts.ERROR);
	}
}

function renderDocuments() {
	if (!pendingDocumentsTableBody || !pendingDocumentsEmptyState) {
		return;
	}

	const pendingDocuments = state.documents.filter((document) => document.estado !== "PROCESADO");

	if (!pendingDocuments.length) {
		pendingDocumentsTableBody.innerHTML = "";
		pendingDocumentsEmptyState.classList.remove("d-none");
	} else {
		pendingDocumentsEmptyState.classList.add("d-none");
		pendingDocumentsTableBody.innerHTML = pendingDocuments.map((document) => `
		<tr class="${document.id_documento === state.selectedId ? "medarch-table-row-active" : ""}" data-id="${document.id_documento}">
			<td class="fw-semibold">#${document.id_documento}</td>
			<td>
				<div class="fw-semibold text-break">${escapeHtml(document.nombre_archivo_original)}</div>
				<div class="small medarch-muted text-break">${escapeHtml(document.ruta_temporal)}</div>
			</td>
			<td><span class="medarch-chip ${stateClass(document.estado)}">${stateLabel(document.estado)}</span></td>
			<td>
				<div class="fw-semibold">${escapeHtml(document.paciente_numero_documento || "-")}</div>
				<div class="small medarch-muted text-break">${escapeHtml(document.paciente_nombre || "Sin validar")}</div>
			</td>
			<td>
				<div class="fw-semibold">${escapeHtml(document.tipo_codigo || "-")}</div>
				<div class="small medarch-muted text-break">${escapeHtml(document.tipo_descripcion || "Sin validar")}</div>
			</td>
			<td>${formatDateTime(document.fecha_carga)}</td>
			<td class="text-end">
				<div class="btn-group btn-group-sm" role="group">
					<button type="button" class="btn btn-outline-success" data-action="review" data-id="${document.id_documento}">Revisar</button>
					<button type="button" class="btn btn-outline-primary" data-action="process" data-id="${document.id_documento}" ${canProcessDocument(document) ? "" : "disabled title=\"Primero guarda la revisión\""}>Procesar</button>
					<button type="button" class="btn btn-outline-danger" data-action="error" data-id="${document.id_documento}">Error</button>
				</div>
			</td>
		</tr>
		`).join("");
	}

}

function canProcessDocument(document) {
	return ["EN_REVISION", "ERROR"].includes(document?.estado)
		&& Number(document.id_paciente) > 0
		&& Number(document.id_tipo) > 0
		&& Boolean(document.fecha)
		&& Number(document.consecutivo) > 0;
}

function renderErrorDocuments() {
	if (!errorDocumentsTableBody || !errorDocumentsEmptyState) {
		return;
	}

	const errorDocuments = state.documents.filter((document) => document.estado === "ERROR");

	if (!errorDocuments.length) {
		errorDocumentsTableBody.innerHTML = "";
		errorDocumentsEmptyState.classList.remove("d-none");
		return;
	}

	errorDocumentsEmptyState.classList.add("d-none");
	errorDocumentsTableBody.innerHTML = errorDocuments.map((document) => `
		<tr data-id="${document.id_documento}">
			<td class="fw-semibold">#${document.id_documento}</td>
			<td>
				<div class="fw-semibold text-break">${escapeHtml(document.nombre_archivo_original)}</div>
				<div class="small medarch-muted text-break">${escapeHtml(document.estado)}</div>
			</td>
			<td>
				<div class="fw-semibold">${escapeHtml(document.paciente_numero_documento || "-")}</div>
				<div class="small medarch-muted text-break">${escapeHtml(document.paciente_nombre || "Sin validar")}</div>
			</td>
			<td>
				<div class="fw-semibold">${escapeHtml(document.tipo_codigo || "-")}</div>
				<div class="small medarch-muted text-break">${escapeHtml(document.tipo_descripcion || "Sin validar")}</div>
			</td>
			<td class="text-break">${escapeHtml(document.ruta_temporal || "-")}</td>
			<td class="text-end">
				<button type="button" class="btn btn-sm btn-outline-primary" data-action="select-error" data-id="${document.id_documento}">Ver</button>
			</td>
		</tr>
	`).join("");
}

function renderSelectedDocument() {
	const document = state.documents.find((item) => item.id_documento === state.selectedId);

	if (!document) {
		selectedDocumentEmpty?.classList.remove("d-none");
		selectedDocumentPanel?.classList.add("d-none");
		if (selectedDocumentEstado) {
			selectedDocumentEstado.textContent = "Sin selección";
			selectedDocumentEstado.className = "medarch-chip medarch-chip-muted";
		}
		renderAudit([]);
		return;
	}

	selectedDocumentEmpty?.classList.add("d-none");
	selectedDocumentPanel?.classList.remove("d-none");

	if (selectedDocumentEstado) {
		selectedDocumentEstado.textContent = stateLabel(document.estado);
		selectedDocumentEstado.className = `medarch-chip ${stateClass(document.estado)}`;
	}

	if (selectedDocumentId) {
		selectedDocumentId.textContent = `#${document.id_documento}`;
	}
	if (selectedDocumentOriginal) {
		selectedDocumentOriginal.textContent = document.nombre_archivo_original || "-";
	}
	if (selectedDocumentPaciente) {
		selectedDocumentPaciente.textContent = document.paciente_numero_documento
			? `${document.paciente_numero_documento} · ${document.paciente_nombre || "Sin nombre"}`
			: "Sin validar";
	}
	if (selectedDocumentTipo) {
		selectedDocumentTipo.textContent = document.tipo_codigo
			? `${document.tipo_codigo} · ${document.tipo_descripcion || "Sin descripción"}`
			: "Sin validar";
	}
	if (selectedDocumentFechaCarga) {
		selectedDocumentFechaCarga.textContent = formatDateTime(document.fecha_carga);
	}
	if (selectedDocumentFechaProcesado) {
		selectedDocumentFechaProcesado.textContent = formatDateTime(document.fecha_procesado);
	}
	if (selectedDocumentNombreFinal) {
		selectedDocumentNombreFinal.textContent = document.nombre_archivo || "-";
	}
	if (selectedDocumentRuta) {
		selectedDocumentRuta.textContent = document.ruta_archivo || "-";
	}
}

function renderAudit(logs) {
	state.audit = logs;

	if (!documentAuditEmpty || !documentAuditList) {
		return;
	}

	if (!logs.length) {
		documentAuditEmpty.classList.remove("d-none");
		documentAuditList.classList.add("d-none");
		documentAuditList.innerHTML = "";
		return;
	}

	documentAuditEmpty.classList.add("d-none");
	documentAuditList.classList.remove("d-none");
	documentAuditList.innerHTML = logs.map((log) => `
		<div class="medarch-timeline-item">
			<div class="medarch-timeline-marker"></div>
			<div class="medarch-timeline-content">
				<div class="d-flex justify-content-between gap-3 mb-1">
					<div class="fw-semibold">${escapeHtml(log.accion)}</div>
					<div class="small medarch-muted text-end">${formatDateTime(log.fecha)}</div>
				</div>
				<div class="small medarch-muted mb-1">Usuario: ${escapeHtml(log.usuario || `#${log.id_usuario}`)}</div>
				<div>${escapeHtml(log.detalle || "Sin detalle")}</div>
			</div>
		</div>
	`).join("");
}

function setSelectedDocument(id) {
	state.selectedId = Number(id) || null;
	renderDocuments();
}

function buildDocumentsQuery() {
	const params = new URLSearchParams();
	if (filterQuery?.value.trim()) {
		params.set("q", filterQuery.value.trim());
	}
	if (filterFechaDesde?.value) {
		params.set("fecha_desde", filterFechaDesde.value);
	}
	if (filterFechaHasta?.value) {
		params.set("fecha_hasta", filterFechaHasta.value);
	}

	const queryString = params.toString();
	return queryString ? `?${queryString}` : "";
}

async function loadLookups() {
	const [documentTypes, patients] = await Promise.all([
		getJson("/documents/meta/tipos"),
		getJson("/documents/meta/pacientes"),
	]);

	state.documentTypes = documentTypes;
	state.patients = patients;
	renderLookups();
}

async function loadDocuments(options = {}) {
	if (!options.preserveMessage) {
		setMessage(documentsMessage, "");
	}
	setButtonLoading(refreshDocumentsButton, true, "Cargando...");

	try {
		state.documents = await getJson(`/documents${buildDocumentsQuery()}`);
		renderKpis();
		renderDocuments();
		state.selectedId = null;
	} catch (error) {
		setMessage(documentsMessage, error.message || "No fue posible cargar los documentos.");
	} finally {
		setButtonLoading(refreshDocumentsButton, false);
	}
}

async function loadAudit(idDocumento) {
	try {
		const logs = await getJson(`/documents/${idDocumento}/audit`);
		renderAudit(logs);
	} catch (error) {
		renderAudit([]);
		setMessage(documentsMessage, error.message || "No fue posible cargar la auditoría.");
	}
}

function fillModalSelections(document) {
	if (!document) {
		return;
	}

	const patient = document.id_paciente
		? state.patients.find((item) => item.id_paciente === document.id_paciente)
		: null;
	const patientId = document.id_paciente ? String(document.id_paciente) : "";
	const patientDocument = patient?.numero_documento || document.paciente_numero_documento || "";
	const patientName = patient?.nombre || document.paciente_nombre || "";
	const typeId = document.id_tipo ? String(document.id_tipo) : "";
	const documentDate = toDateInputValue(document.fecha || document.fecha_carga);
	const consecutive = document.consecutivo || 1;

	if (reviewDocumentIdInput) {
		reviewDocumentIdInput.value = String(document.id_documento);
	}
	if (reviewPatientIdInput) {
		reviewPatientIdInput.value = patientId;
	}
	if (errorDocumentIdInput) {
		errorDocumentIdInput.value = String(document.id_documento);
	}

	if (reviewPatientDocumentInput) {
		reviewPatientDocumentInput.value = patientDocument;
	}
	if (reviewPatientNameInput) {
		reviewPatientNameInput.value = patientName;
		reviewPatientNameInput.dataset.autofilled = patient ? "true" : "false";
	}
	if (reviewTypeSelect) {
		reviewTypeSelect.value = typeId;
	}
	if (reviewDateInput) {
		reviewDateInput.value = documentDate;
	}
	if (reviewConsecutiveInput) {
		const reviewPatientId = Number(patientId);
		const reviewTypeId = Number(typeId);
		const nextConsecutive = calculateNextConsecutive(reviewPatientId, reviewTypeId, documentDate, document.id_documento);
		reviewConsecutiveInput.value = nextConsecutive;
		if (reviewConsecutiveDisplay) {
			reviewConsecutiveDisplay.textContent = String(nextConsecutive).padStart(3, "0");
		}
	}

	syncReviewPatientFromDocument();
}

function findPatientByDocument(numeroDocumento) {
	const normalizedDocument = String(numeroDocumento || "").trim();
	if (!normalizedDocument) {
		return null;
	}

	return state.patients.find((patient) => String(patient.numero_documento).trim() === normalizedDocument) || null;
}

function syncReviewPatientFromDocument() {
	const patientDoc = String(reviewPatientDocumentInput?.value || "").trim();
	const patient = findPatientByDocument(patientDoc);

	if (!patientDoc) {
		if (reviewPatientIdInput) {
			reviewPatientIdInput.value = "";
		}
		if (reviewPatientStatus) {
			reviewPatientStatus.textContent = "Si el paciente existe, sus datos se cargan automaticamente.";
		}
		return;
	}

	if (patient) {
		if (reviewPatientIdInput) {
			reviewPatientIdInput.value = String(patient.id_paciente);
		}
		if (reviewPatientNameInput) {
			reviewPatientNameInput.value = patient.nombre || "";
			reviewPatientNameInput.dataset.autofilled = "true";
		}
		if (reviewPatientStatus) {
			reviewPatientStatus.textContent = `Paciente encontrado: ${patient.numero_documento} - ${patient.nombre || "Sin nombre"}.`;
		}
		return;
	}

	if (reviewPatientIdInput) {
		reviewPatientIdInput.value = "";
	}
	if (reviewPatientNameInput?.dataset.autofilled === "true") {
		reviewPatientNameInput.value = "";
		reviewPatientNameInput.dataset.autofilled = "false";
	}
	if (reviewPatientStatus) {
		reviewPatientStatus.textContent = "Paciente no encontrado. Al guardar la revision se creara con los datos ingresados.";
	}
}

function calculateNextConsecutive(idPaciente, idTipo, fecha, currentDocumentId = null) {
	if (!idPaciente || !idTipo || !fecha) {
		return 1;
	}

	const currentId = Number(currentDocumentId || 0);
	const matchingDocs = state.documents.filter((doc) => {
		const isCurrentDocument = currentId > 0 && Number(doc.id_documento) === currentId;
		return !isCurrentDocument
			&& doc.estado === "PROCESADO"
			&& Number(doc.id_paciente) === Number(idPaciente)
			&& Number(doc.id_tipo) === Number(idTipo)
			&& doc.fecha === fecha;
	});

	if (matchingDocs.length === 0) {
		return 1;
	}

	const maxConsecutive = Math.max(...matchingDocs.map((doc) => doc.consecutivo || 0));
	return maxConsecutive + 1;
}

function updateReviewConsecutive() {
	syncReviewPatientFromDocument();
	const patientDoc = String(reviewPatientDocumentInput?.value || "").trim();
	const typeId = Number(reviewTypeSelect?.value || 0);
	const date = reviewDateInput?.value || "";

	let patientId = 0;
	if (patientDoc) {
		const patient = findPatientByDocument(patientDoc);
		if (patient) {
			patientId = patient.id_paciente;
		}
	}

	const currentDocumentId = Number(reviewDocumentIdInput?.value || 0);
	const nextConsecutive = calculateNextConsecutive(patientId, typeId, date, currentDocumentId);
	if (reviewConsecutiveInput) {
		reviewConsecutiveInput.value = nextConsecutive;
	}
	if (reviewConsecutiveDisplay) {
		reviewConsecutiveDisplay.textContent = String(nextConsecutive).padStart(3, "0");
	}
}

function openReviewModal(documentId) {
	const document = state.documents.find((item) => item.id_documento === Number(documentId)) || state.documents.find((item) => item.id_documento === state.selectedId);
	if (!document || !reviewModal) {
		return;
	}

	fillModalSelections(document);
	reviewModalTitle.textContent = `Revisar documento #${document.id_documento}`;
	reviewModal.show();
}

function openErrorModal(documentId) {
	const document = state.documents.find((item) => item.id_documento === Number(documentId)) || state.documents.find((item) => item.id_documento === state.selectedId);
	if (!document || !errorModal) {
		return;
	}

	if (errorDocumentIdInput) {
		errorDocumentIdInput.value = String(document.id_documento);
	}
	if (errorDetailInput) {
		errorDetailInput.value = "";
	}
	errorModalTitle.textContent = `Marcar error · documento #${document.id_documento}`;
	errorModal.show();
}

function openErrorDocumentsModal() {
	if (!errorDocumentsModal) {
		return;
	}

	renderErrorDocuments();
	errorDocumentsModal.show();
}

async function handleReviewSubmit(event) {
	event.preventDefault();
	setMessage(documentsMessage, "");

	const documentId = Number(reviewDocumentIdInput?.value || 0);
	const patientId = Number(reviewPatientIdInput?.value || 0);
	const numeroDocumento = String(reviewPatientDocumentInput?.value || "").trim();
	const nombrePaciente = String(reviewPatientNameInput?.value || "").trim();
	const payload = {
		id_paciente: patientId || null,
		numero_documento: numeroDocumento,
		nombre_paciente: nombrePaciente,
		id_tipo: Number(reviewTypeSelect?.value || 0),
		fecha: reviewDateInput?.value || "",
		consecutivo: Number(reviewConsecutiveInput?.value || 0),
	};

	if (!documentId || !payload.numero_documento || !payload.nombre_paciente || !payload.id_tipo || !payload.fecha || !payload.consecutivo) {
		setMessage(documentsMessage, "Completa identificación, nombre, tipo, fecha y consecutivo para guardar la revisión.");
		return;
	}

	setButtonLoading(reviewSubmitButton, true, "Guardando...");
	try {
		await patchJson(`/documents/${documentId}/review`, payload);
		setMessage(documentsMessage, "Documento marcado en revisión correctamente.", "success");
		reviewModal?.hide();
		await loadLookups();
		await loadDocuments({ preserveMessage: true });
		setSelectedDocument(documentId);
	} catch (error) {
		setMessage(documentsMessage, error.message || "No fue posible guardar la revisión.");
	} finally {
		setButtonLoading(reviewSubmitButton, false);
	}
}

async function processDocumentDirectly(documentId, triggerButton = null) {
	setMessage(documentsMessage, "");

	const document = state.documents.find((item) => item.id_documento === Number(documentId));
	if (!document) {
		setMessage(documentsMessage, "No se encontró el documento seleccionado.");
		return;
	}

	if (!canProcessDocument(document)) {
		setMessage(documentsMessage, "Primero guarda la revisión con paciente, tipo, fecha y consecutivo antes de procesar.");
		return;
	}

	const payload = {
		id_paciente: Number(document.id_paciente),
		id_tipo: Number(document.id_tipo),
		fecha: document.fecha,
		consecutivo: Number(document.consecutivo),
	};

	if (!documentId || !payload.id_paciente || !payload.id_tipo || !payload.fecha || !payload.consecutivo) {
		setMessage(documentsMessage, "Completa todos los datos para procesar el documento.");
		return;
	}

	setButtonLoading(triggerButton, true, "Procesando...");
	try {
		await patchJson(`/documents/${documentId}/process`, payload);
		setMessage(documentsMessage, "Documento procesado correctamente.", "success");
		await loadDocuments({ preserveMessage: true });
		setSelectedDocument(documentId);
	} catch (error) {
		setMessage(documentsMessage, error.message || "No fue posible procesar el documento.");
		await loadDocuments({ preserveMessage: true });
	} finally {
		setButtonLoading(triggerButton, false);
	}
}

async function handleErrorSubmit(event) {
	event.preventDefault();
	setMessage(documentsMessage, "");

	const documentId = Number(errorDocumentIdInput?.value || 0);
	const detalle = String(errorDetailInput?.value || "").trim();

	if (!documentId || detalle.length < 3) {
		setMessage(documentsMessage, "Escribe un motivo válido para marcar el error.");
		return;
	}

	setButtonLoading(errorSubmitButton, true, "Guardando...");
	try {
		await patchJson(`/documents/${documentId}/error`, { detalle });
		setMessage(documentsMessage, "Documento marcado como error.", "success");
		errorModal?.hide();
		await loadDocuments({ preserveMessage: true });
		setSelectedDocument(documentId);
	} catch (error) {
		setMessage(documentsMessage, error.message || "No fue posible marcar el error.");
	} finally {
		setButtonLoading(errorSubmitButton, false);
	}
}

function handleTableClick(event) {
	const button = event.target.closest("button[data-action]");
	const row = event.target.closest("tr[data-id]");

	if (button) {
		const documentId = Number(button.dataset.id);
		const action = button.dataset.action;

		if (action === "select") {
			setSelectedDocument(documentId);
			return;
		}
		if (action === "review") {
			openReviewModal(documentId);
			return;
		}
		if (action === "process") {
			processDocumentDirectly(documentId, button);
			return;
		}
		if (action === "error") {
			openErrorModal(documentId);
			return;
		}
	}

	if (row) {
		setSelectedDocument(row.dataset.id);
	}
}

function handleErrorDocumentsClick(event) {
	const button = event.target.closest("button[data-action='select-error']");
	if (!button) {
		return;
	}

	const documentId = Number(button.dataset.id);
	if (!documentId) {
		return;
	}

	setSelectedDocument(documentId);
	errorDocumentsModal?.hide();
}

function bindEvents() {
	refreshDocumentsButton?.addEventListener("click", () => loadDocuments());
	viewErrorsButton?.addEventListener("click", openErrorDocumentsModal);
	logoutButton?.addEventListener("click", logout);
	reviewDocumentButton?.addEventListener("click", () => {
		if (state.selectedId) {
			openReviewModal(state.selectedId);
		}
	});
	processDocumentButton?.addEventListener("click", () => {
		if (state.selectedId) {
			processDocumentDirectly(state.selectedId, processDocumentButton);
		}
	});
	errorDocumentButton?.addEventListener("click", () => {
		if (state.selectedId) {
			openErrorModal(state.selectedId);
		}
	});
	errorDocumentsTableBody?.addEventListener("click", handleErrorDocumentsClick);
	documentsFilterForm?.addEventListener("submit", (event) => {
		event.preventDefault();
		loadDocuments();
	});
	resetFiltersButton?.addEventListener("click", () => {
		if (filterQuery) {
			filterQuery.value = "";
		}
		if (filterFechaDesde) {
			filterFechaDesde.value = "";
		}
		if (filterFechaHasta) {
			filterFechaHasta.value = "";
		}
		loadDocuments();
	});
	pendingDocumentsTableBody?.addEventListener("click", handleTableClick);
	reviewForm?.addEventListener("submit", handleReviewSubmit);
	errorForm?.addEventListener("submit", handleErrorSubmit);

	reviewPatientDocumentInput?.addEventListener("input", updateReviewConsecutive);
	reviewPatientNameInput?.addEventListener("input", () => {
		if (reviewPatientNameInput) {
			reviewPatientNameInput.dataset.autofilled = "false";
		}
	});
	reviewTypeSelect?.addEventListener("change", updateReviewConsecutive);
	reviewDateInput?.addEventListener("change", updateReviewConsecutive);

	reviewModalEl?.addEventListener("show.bs.modal", () => {
		if (!state.selectedId) {
			return;
		}
		const document = state.documents.find((item) => item.id_documento === state.selectedId);
		if (document) {
			fillModalSelections(document);
		}
	});

	reviewModalEl?.addEventListener("hidden.bs.modal", () => {
		reviewForm?.reset();
		if (reviewPatientIdInput) {
			reviewPatientIdInput.value = "";
		}
		if (reviewPatientNameInput) {
			reviewPatientNameInput.dataset.autofilled = "false";
		}
		if (reviewPatientStatus) {
			reviewPatientStatus.textContent = "Si el paciente existe, sus datos se cargan automaticamente.";
		}
	});
	errorModalEl?.addEventListener("hidden.bs.modal", () => {
		errorForm?.reset();
	});
}

async function initialize() {
	try {
		setMessage(documentsMessage, "Cargando documentos...", "info");
		await loadLookups();
		await loadDocuments({ preserveMessage: true });
		setMessage(documentsMessage, "");
	} catch (error) {
		setMessage(documentsMessage, error.message || "No fue posible inicializar el módulo de documentos.");
	}
}

if (ensureSession()) {
	bindEvents();
	initialize();
}
