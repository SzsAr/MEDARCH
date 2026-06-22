import { getJson, patchJson } from "./api.js";
import { ensureSession, escapeHtml, logout, setButtonLoading, setMessage } from "./ui.js";

const state = {
	patients: [],
};

const messageBox = document.querySelector("#patientsMessage");
const searchForm = document.querySelector("#patientsSearchForm");
const queryInput = document.querySelector("#patientsQuery");
const searchButton = document.querySelector("#searchPatientsButton");
const tableBody = document.querySelector("#patientsTableBody");
const emptyState = document.querySelector("#patientsEmptyState");
const logoutButton = document.querySelector("#logoutButton");
const modalElement = document.querySelector("#patientNameModal");
const editForm = document.querySelector("#patientNameForm");
const patientIdInput = document.querySelector("#patientId");
const patientDocument = document.querySelector("#patientDocument");
const patientNameInput = document.querySelector("#patientName");
const saveButton = document.querySelector("#savePatientNameButton");
const modal = window.bootstrap ? window.bootstrap.Modal.getOrCreateInstance(modalElement) : null;

function renderPatients() {
	if (!state.patients.length) {
		tableBody.innerHTML = "";
		emptyState.classList.remove("d-none");
		return;
	}

	emptyState.classList.add("d-none");
	tableBody.innerHTML = state.patients.map((patient) => `
		<tr>
			<td class="fw-semibold">${escapeHtml(patient.numero_documento)}</td>
			<td>${escapeHtml(patient.nombre || "Sin nombre")}</td>
			<td class="text-end">
				<button class="btn btn-sm btn-outline-primary" type="button" data-action="edit-name" data-id="${patient.id_paciente}">
					Editar nombre
				</button>
			</td>
		</tr>
	`).join("");
}

async function searchPatients(event) {
	event?.preventDefault();
	const query = String(queryInput?.value || "").trim();

	if (!query) {
		setMessage(messageBox, "Ingresa un nombre o número de identificación para buscar.", "warning");
		return;
	}

	setMessage(messageBox, "");
	setButtonLoading(searchButton, true, "Buscando...");
	try {
		state.patients = await getJson(`/documents/meta/pacientes?q=${encodeURIComponent(query)}`);
		emptyState.textContent = "No se encontraron pacientes con ese criterio.";
		renderPatients();
	} catch (error) {
		setMessage(messageBox, error.message || "No fue posible buscar pacientes.");
	} finally {
		setButtonLoading(searchButton, false);
	}
}

function openEditModal(patientId) {
	const patient = state.patients.find((item) => item.id_paciente === patientId);
	if (!patient || !modal) {
		return;
	}

	patientIdInput.value = String(patient.id_paciente);
	patientDocument.textContent = patient.numero_documento;
	patientNameInput.value = patient.nombre || "";
	modal.show();
	patientNameInput.focus();
}

async function savePatientName(event) {
	event.preventDefault();
	const patientId = Number(patientIdInput.value);
	const name = String(patientNameInput.value || "").trim();

	if (!patientId || name.length < 2) {
		setMessage(messageBox, "Escribe un nombre válido de al menos 2 caracteres.");
		return;
	}

	setButtonLoading(saveButton, true, "Guardando...");
	try {
		await patchJson(`/documents/meta/pacientes/${patientId}/nombre`, { nombre: name });
		modal?.hide();
		setMessage(messageBox, "Nombre del paciente actualizado correctamente.", "success");
		await searchPatients();
	} catch (error) {
		setMessage(messageBox, error.message || "No fue posible actualizar el nombre.");
	} finally {
		setButtonLoading(saveButton, false);
	}
}

function bindEvents() {
	logoutButton?.addEventListener("click", logout);
	searchForm?.addEventListener("submit", searchPatients);
	editForm?.addEventListener("submit", savePatientName);
	tableBody?.addEventListener("click", (event) => {
		const button = event.target.closest("button[data-action='edit-name']");
		if (button) {
			openEditModal(Number(button.dataset.id));
		}
	});
}

if (ensureSession()) {
	bindEvents();
	renderPatients();
}
