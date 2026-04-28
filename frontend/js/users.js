import { decodeJwtPayload, deleteJson, getJson, patchJson, postJson, putJson } from "./api.js";
import { ensureSession, escapeHtml, formatDateTime, logout, setButtonLoading, setMessage } from "./ui.js";

const usersTableBody = document.querySelector("#usersTableBody");
const emptyState = document.querySelector("#usersEmptyState");
const statusMessage = document.querySelector("#usersMessage");
const refreshButton = document.querySelector("#refreshUsers");
const newUserButton = document.querySelector("#newUserButton");
const logoutButton = document.querySelector("#logoutButton");
const userForm = document.querySelector("#userForm");
const passwordForm = document.querySelector("#passwordForm");
const userModalEl = document.querySelector("#userModal");
const passwordModalEl = document.querySelector("#passwordModal");
const userModalTitle = document.querySelector("#userModalLabel");
const passwordModalTitle = document.querySelector("#passwordModalLabel");
const submitUserButton = document.querySelector("#submitUserButton");
const passwordSubmitButton = document.querySelector("#passwordSubmitButton");
const passwordUserLabel = document.querySelector("#passwordUserLabel");
const currentUserIdInput = document.querySelector("#currentUserId");
const passwordUserIdInput = document.querySelector("#passwordUserId");
const userUsuarioInput = document.querySelector("#userUsuario");
const userNombreInput = document.querySelector("#userNombre");
const userPasswordInput = document.querySelector("#userPassword");
const userRolInput = document.querySelector("#userRol");
const userActivoInput = document.querySelector("#userActivo");
const newPasswordInput = document.querySelector("#newPassword");

const userModal = window.bootstrap ? window.bootstrap.Modal.getOrCreateInstance(userModalEl) : null;
const passwordModal = window.bootstrap ? window.bootstrap.Modal.getOrCreateInstance(passwordModalEl) : null;
const currentUserPayload = decodeJwtPayload();
const currentUserId = Number(currentUserPayload?.id_usuario || 0);

const state = {
	users: [],
	editingId: null,
};

function getFormData() {
	const formData = new FormData(userForm);
	return {
		usuario: String(formData.get("usuario") || "").trim(),
		nombre: String(formData.get("nombre") || "").trim(),
		password: String(formData.get("password") || ""),
		rol: String(formData.get("rol") || "SUPERADMIN"),
		activo: formData.get("activo") === "on",
	};
}

function resetUserForm() {
	state.editingId = null;
	currentUserIdInput.value = "";
	userForm.reset();
	userActivoInput.checked = true;
	userModalTitle.textContent = "Crear usuario";
	submitUserButton.textContent = "Guardar usuario";
	userPasswordInput.disabled = false;
	userPasswordInput.required = true;
}

function fillUserForm(user) {
	state.editingId = user.id_usuario;
	currentUserIdInput.value = String(user.id_usuario);
	userUsuarioInput.value = user.usuario;
	userNombreInput.value = user.nombre;
	userRolInput.value = user.rol;
	userActivoInput.checked = Boolean(user.activo);
	userPasswordInput.value = "";
	userPasswordInput.disabled = true;
	userPasswordInput.required = false;
	userModalTitle.textContent = `Editar ${user.usuario}`;
	submitUserButton.textContent = "Actualizar usuario";
}

function syncPasswordPanel(user) {
	passwordUserIdInput.value = String(user.id_usuario);
	passwordModalTitle.textContent = `Cambiar contraseña · ${user.usuario}`;
	passwordUserLabel.textContent = `${user.usuario} · ${user.nombre}`;
	newPasswordInput.value = "";
}

function openUserModal(user = null) {
	if (!userModal) {
		return;
	}

	resetUserForm();
	if (user) {
		fillUserForm(user);
	}
	userModal.show();
}

function openPasswordModal(user) {
	if (!passwordModal) {
		return;
	}

	syncPasswordPanel(user);
	passwordModal.show();
}

function renderUsers() {
	if (!usersTableBody || !emptyState) {
		return;
	}

	if (!state.users.length) {
		usersTableBody.innerHTML = "";
		emptyState.classList.remove("d-none");
		return;
	}

	emptyState.classList.add("d-none");
	usersTableBody.innerHTML = state.users.map((user) => `
		<tr>
			<td class="fw-semibold">${escapeHtml(user.usuario)}</td>
			<td>${escapeHtml(user.nombre)}</td>
			<td>${escapeHtml(user.rol)}</td>
			<td>
				<div class="form-check form-switch m-0 d-inline-flex align-items-center gap-2">
					<input class="form-check-input medarch-status-switch" type="checkbox" role="switch" data-action="toggle" data-id="${user.id_usuario}" ${user.activo ? "checked" : ""} ${user.id_usuario === currentUserId ? "disabled" : ""} aria-label="Cambiar estado de ${escapeHtml(user.usuario)}">
					<span class="medarch-badge ${user.activo ? "medarch-badge-active" : "medarch-badge-inactive"}">${user.activo ? "Activo" : "Inactivo"}</span>
				</div>
			</td>
			<td>${formatDateTime(user.fecha_creacion)}</td>
			<td class="text-end">
				<div class="btn-group btn-group-sm" role="group">
					<button type="button" class="btn btn-outline-primary" data-action="edit" data-id="${user.id_usuario}">Editar</button>
					<button type="button" class="btn btn-outline-secondary" data-action="password" data-id="${user.id_usuario}">Clave</button>
				</div>
			</td>
		</tr>
	`).join("");
}

async function loadUsers(options = {}) {
	if (!options.preserveMessage) {
		setMessage(statusMessage, "");
	}
	setButtonLoading(refreshButton, true, "Cargando...");

	try {
		state.users = await getJson("/users");
		renderUsers();
	} catch (error) {
		setMessage(statusMessage, error.message || "No fue posible cargar los usuarios.");
	} finally {
		setButtonLoading(refreshButton, false);
	}
}

function validateUserPayload(payload) {
	if (!payload.usuario || payload.usuario.length < 3) {
		return "El usuario debe tener al menos 3 caracteres.";
	}

	if (!payload.nombre || payload.nombre.length < 2) {
		return "El nombre debe tener al menos 2 caracteres.";
	}

	if (!payload.rol) {
		return "Selecciona un rol.";
	}

	if (!state.editingId && payload.password.length < 8) {
		return "La contraseña debe tener al menos 8 caracteres.";
	}

	return null;
}

async function handleUserSubmit(event) {
	event.preventDefault();
	setMessage(statusMessage, "");

	const payload = getFormData();
	const validationMessage = validateUserPayload(payload);

	if (validationMessage) {
		setMessage(statusMessage, validationMessage);
		return;
	}

	setButtonLoading(submitUserButton, true, "Guardando...");

	try {
		if (state.editingId) {
			const updatePayload = {
				nombre: payload.nombre,
				rol: payload.rol,
				activo: payload.activo,
			};
			await putJson(`/users/${state.editingId}`, updatePayload);
			setMessage(statusMessage, "Usuario actualizado correctamente.", "success");
		} else {
			const createPayload = {
				usuario: payload.usuario,
				nombre: payload.nombre,
				password: payload.password,
				rol: payload.rol,
			};
			await postJson("/users", createPayload);
			setMessage(statusMessage, "Usuario creado correctamente.", "success");
		}

		resetUserForm();
		userModal?.hide();
		await loadUsers({ preserveMessage: true });
	} catch (error) {
		setMessage(statusMessage, error.message || "No fue posible guardar el usuario.");
	} finally {
		setButtonLoading(submitUserButton, false);
	}
}

async function handlePasswordSubmit(event) {
	event.preventDefault();
	setMessage(statusMessage, "");

	const formData = new FormData(passwordForm);
	const id = Number(formData.get("passwordUserId"));
	const nueva_password = String(formData.get("newPassword") || "");

	if (!id) {
		setMessage(statusMessage, "Selecciona un usuario para cambiar la contraseña.");
		return;
	}

	if (nueva_password.length < 8) {
		setMessage(statusMessage, "La nueva contraseña debe tener al menos 8 caracteres.");
		return;
	}

	setButtonLoading(passwordSubmitButton, true, "Actualizando...");

	try {
		await patchJson(`/users/${id}/password`, { nueva_password });
		setMessage(statusMessage, "Contraseña actualizada correctamente.", "success");
		passwordForm.reset();
		passwordModal?.hide();
	} catch (error) {
		setMessage(statusMessage, error.message || "No fue posible cambiar la contraseña.");
	} finally {
		setButtonLoading(passwordSubmitButton, false);
	}
}

async function handleToggleChange(event) {
	const switchInput = event.target.closest("input[data-action='toggle']");
	if (!switchInput) {
		return;
	}

	if (Number(switchInput.dataset.id) === currentUserId) {
		switchInput.checked = true;
		setMessage(statusMessage, "No puedes desactivar tu propio usuario.");
		return;
	}

	const userId = Number(switchInput.dataset.id);
	const user = state.users.find((item) => item.id_usuario === userId);
	if (!user) {
		return;
	}

	const desiredActive = switchInput.checked;
	switchInput.disabled = true;

	try {
		await deleteJson(`/users/${userId}`);
		await loadUsers({ preserveMessage: true });
		setMessage(statusMessage, `Estado de ${user.usuario} actualizado.`, "success");
	} catch (error) {
		switchInput.checked = !desiredActive;
		setMessage(statusMessage, error.message || "No fue posible cambiar el estado del usuario.");
	} finally {
		switchInput.disabled = false;
	}
}

async function handleActionClick(event) {
	const button = event.target.closest("button[data-action]");
	if (!button) {
		return;
	}

	const userId = Number(button.dataset.id);
	const action = button.dataset.action;
	const user = state.users.find((item) => item.id_usuario === userId);

	if (!user) {
		return;
	}

	if (action === "edit") {
		openUserModal(user);
		return;
	}

	if (action === "password") {
		openPasswordModal(user);
		return;
	}
}

function bindEvents() {
	refreshButton?.addEventListener("click", loadUsers);
	newUserButton?.addEventListener("click", () => openUserModal());
	logoutButton?.addEventListener("click", logout);
	userForm?.addEventListener("submit", handleUserSubmit);
	passwordForm?.addEventListener("submit", handlePasswordSubmit);
	usersTableBody?.addEventListener("click", handleActionClick);
	usersTableBody?.addEventListener("change", handleToggleChange);
	userModalEl?.addEventListener("hidden.bs.modal", resetUserForm);
	passwordModalEl?.addEventListener("hidden.bs.modal", () => {
		passwordForm.reset();
		passwordUserIdInput.value = "";
		passwordUserLabel.textContent = "Ninguno";
		passwordModalTitle.textContent = "Cambiar contraseña";
	});
}

if (ensureSession()) {
	bindEvents();
	loadUsers();
}