import { decodeJwtPayload, deleteJson, getJson, postJson, putJson } from "./api.js";
import { ensureSession, escapeHtml, logout, setButtonLoading, setMessage } from "./ui.js";

const currentUserPayload = decodeJwtPayload();
const currentUserRole = String(currentUserPayload?.rol || "");
const canEditTypes = currentUserRole === "SUPERADMIN";

const state = {
	types: [],
	editingId: null,
	showInactive: false,
};

const messageBox = document.querySelector("#documentTypesMessage");
const refreshButton = document.querySelector("#refreshTypes");
const newTypeButton = document.querySelector("#newTypeButton");
const logoutButton = document.querySelector("#logoutButton");
const showInactiveInput = document.querySelector("#showInactiveTypes");
const tableBody = document.querySelector("#typesTableBody");
const emptyState = document.querySelector("#typesEmptyState");
const activeKpi = document.querySelector("#typesActiveKpi");
const inactiveKpi = document.querySelector("#typesInactiveKpi");
const totalKpi = document.querySelector("#typesTotalKpi");
const modalEl = document.querySelector("#typeModal");
const modalTitle = document.querySelector("#typeModalLabel");
const form = document.querySelector("#typeForm");
const currentTypeIdInput = document.querySelector("#currentTypeId");
const typeCodigoInput = document.querySelector("#typeCodigo");
const typeDescripcionInput = document.querySelector("#typeDescripcion");
const typeActivoInput = document.querySelector("#typeActivo");
const submitButton = document.querySelector("#submitTypeButton");
const modal = window.bootstrap ? window.bootstrap.Modal.getOrCreateInstance(modalEl) : null;

function normalizeCode(value) {
	return String(value || "").trim().toUpperCase();
}

function resetForm() {
	state.editingId = null;
	currentTypeIdInput.value = "";
	form.reset();
	typeActivoInput.checked = true;
	modalTitle.textContent = "Nuevo tipo de documento";
	submitButton.textContent = "Guardar tipo";
}

function fillForm(type) {
	state.editingId = type.id_tipo;
	currentTypeIdInput.value = String(type.id_tipo);
	typeCodigoInput.value = type.codigo || "";
	typeDescripcionInput.value = type.descripcion || "";
	typeActivoInput.checked = Boolean(type.activo);
	modalTitle.textContent = `Editar ${type.codigo}`;
	submitButton.textContent = "Actualizar tipo";
}

function openModal(type = null) {
	if (!modal) {
		return;
	}

	resetForm();
	if (type) {
		fillForm(type);
	}
	modal.show();
}

function renderKpis() {
	const activeCount = state.types.filter((type) => type.activo).length;
	const inactiveCount = state.types.filter((type) => !type.activo).length;

	if (activeKpi) {
		activeKpi.textContent = String(activeCount);
	}
	if (inactiveKpi) {
		inactiveKpi.textContent = String(inactiveCount);
	}
	if (totalKpi) {
		totalKpi.textContent = String(state.types.length);
	}
}

function renderTypes() {
	if (!tableBody || !emptyState) {
		return;
	}

	if (!state.types.length) {
		tableBody.innerHTML = "";
		emptyState.classList.remove("d-none");
		renderKpis();
		return;
	}

	emptyState.classList.add("d-none");
	tableBody.innerHTML = state.types.map((type) => `
		<tr>
			<td class="fw-semibold">${escapeHtml(type.codigo)}</td>
			<td>${escapeHtml(type.descripcion)}</td>
			<td>
				<span class="medarch-chip ${type.activo ? "medarch-chip-processed" : "medarch-chip-error"}">${type.activo ? "Activo" : "Inactivo"}</span>
			</td>
			<td class="text-end">
				<div class="btn-group btn-group-sm" role="group">
					<button type="button" class="btn btn-outline-primary" data-action="edit" data-id="${type.id_tipo}" ${canEditTypes ? "" : "disabled"}>Editar</button>
					<button type="button" class="btn btn-outline-secondary" data-action="toggle" data-id="${type.id_tipo}" ${canEditTypes ? "" : "disabled"}>${type.activo ? "Desactivar" : "Activar"}</button>
				</div>
			</td>
		</tr>
	`).join("");

	renderKpis();
}

async function loadTypes(options = {}) {
	if (!options.preserveMessage) {
		setMessage(messageBox, "");
	}

	setButtonLoading(refreshButton, true, "Cargando...");

	try {
		const query = state.showInactive ? "?incluir_inactivos=true" : "";
		state.types = await getJson(`/documents/meta/tipos${query}`);
		renderTypes();
	} catch (error) {
		setMessage(messageBox, error.message || "No fue posible cargar los tipos de documento.");
	} finally {
		setButtonLoading(refreshButton, false);
	}
}

function validatePayload(payload) {
	if (!payload.codigo || payload.codigo.length < 2) {
		return "El código debe tener al menos 2 caracteres.";
	}

	if (!payload.descripcion || payload.descripcion.length < 2) {
		return "La descripción debe tener al menos 2 caracteres.";
	}

	return null;
}

function getFormPayload() {
	return {
		codigo: normalizeCode(typeCodigoInput?.value),
		descripcion: String(typeDescripcionInput?.value || "").trim(),
		activo: Boolean(typeActivoInput?.checked),
	};
}

async function handleSubmit(event) {
	event.preventDefault();
	setMessage(messageBox, "");

	const payload = getFormPayload();
	const validationMessage = validatePayload(payload);

	if (validationMessage) {
		setMessage(messageBox, validationMessage);
		return;
	}

	setButtonLoading(submitButton, true, "Guardando...");

	try {
		if (state.editingId) {
			await putJson(`/documents/meta/tipos/${state.editingId}`, payload);
			setMessage(messageBox, "Tipo de documento actualizado correctamente.", "success");
		} else {
			await postJson("/documents/meta/tipos", payload);
			setMessage(messageBox, "Tipo de documento creado correctamente.", "success");
		}

		modal?.hide();
		resetForm();
		await loadTypes({ preserveMessage: true });
	} catch (error) {
		setMessage(messageBox, error.message || "No fue posible guardar el tipo de documento.");
	} finally {
		setButtonLoading(submitButton, false);
	}
}

async function handleTableClick(event) {
	const button = event.target.closest("button[data-action]");
	if (!button) {
		return;
	}

	const typeId = Number(button.dataset.id || 0);
	const action = button.dataset.action;
	const type = state.types.find((item) => item.id_tipo === typeId);

	if (!type) {
		return;
	}

	if (action === "edit") {
		openModal(type);
		return;
	}

	if (action === "toggle") {
		const confirmationMessage = type.activo
			? `¿Deseas desactivar el tipo ${type.codigo}?`
			: `¿Deseas activar el tipo ${type.codigo}?`;

		if (!window.confirm(confirmationMessage)) {
			return;
		}

		button.disabled = true;
		try {
			await deleteJson(`/documents/meta/tipos/${typeId}`);
			setMessage(messageBox, `Tipo ${type.codigo} actualizado correctamente.`, "success");
			await loadTypes({ preserveMessage: true });
		} catch (error) {
			setMessage(messageBox, error.message || "No fue posible cambiar el estado del tipo de documento.");
		} finally {
			button.disabled = false;
		}
	}
}

function bindEvents() {
	refreshButton?.addEventListener("click", () => loadTypes());
	newTypeButton?.addEventListener("click", () => openModal());
	logoutButton?.addEventListener("click", logout);
	showInactiveInput?.addEventListener("change", () => {
		state.showInactive = Boolean(showInactiveInput.checked);
		loadTypes();
	});
	form?.addEventListener("submit", handleSubmit);
	tableBody?.addEventListener("click", handleTableClick);
	modalEl?.addEventListener("hidden.bs.modal", resetForm);
}

function initAccessState() {
	if (!canEditTypes) {
		newTypeButton?.setAttribute("disabled", "disabled");
		newTypeButton?.classList.add("disabled");
		setMessage(
			messageBox,
			"Tienes acceso de solo lectura. Solo SUPERADMIN puede crear, editar o desactivar tipos de documento.",
			"warning",
		);
	}
}

if (ensureSession()) {
	initAccessState();
	bindEvents();
	loadTypes();
}