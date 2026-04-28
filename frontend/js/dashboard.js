import { ensureSession, logout } from "./ui.js";

if (ensureSession()) {
	document.querySelector("#logoutButton")?.addEventListener("click", logout);
}