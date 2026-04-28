export const API_BASE_URL = window.MEDARCH_API_BASE_URL || "http://127.0.0.1:8000";
const TOKEN_KEY = "medarch_access_token";

export function getToken() {
	return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
	localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
	localStorage.removeItem(TOKEN_KEY);
}

export function decodeJwtPayload(token = getToken()) {
	if (!token) {
		return null;
	}

	const parts = token.split(".");
	if (parts.length !== 3) {
		return null;
	}

	try {
		const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
		const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
		const json = atob(padded);
		return JSON.parse(json);
	} catch {
		return null;
	}
}

export function buildUrl(path) {
	if (/^https?:\/\//i.test(path)) {
		return path;
	}

	return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export async function request(path, options = {}) {
	const headers = new Headers(options.headers || {});
	const token = options.token ?? getToken();

	if (!headers.has("Content-Type") && options.body && !(options.body instanceof FormData)) {
		headers.set("Content-Type", "application/json");
	}

	if (token) {
		headers.set("Authorization", `Bearer ${token}`);
	}

	const response = await fetch(buildUrl(path), {
		...options,
		headers,
	});

	const contentType = response.headers.get("content-type") || "";
	let payload = null;

	if (contentType.includes("application/json")) {
		payload = await response.json();
	} else {
		payload = await response.text();
	}

	if (!response.ok) {
		const message = typeof payload === "string"
			? payload
			: payload?.detail || payload?.message || `HTTP ${response.status}`;
		const error = new Error(message);
		error.status = response.status;
		error.payload = payload;
		throw error;
	}

	return payload;
}

export async function getJson(path, options = {}) {
	return request(path, { ...options, method: "GET" });
}

export async function postJson(path, body, options = {}) {
	return request(path, {
		...options,
		method: "POST",
		body: JSON.stringify(body),
	});
}

export async function putJson(path, body, options = {}) {
	return request(path, {
		...options,
		method: "PUT",
		body: JSON.stringify(body),
	});
}

export async function patchJson(path, body, options = {}) {
	return request(path, {
		...options,
		method: "PATCH",
		body: JSON.stringify(body),
	});
}

export async function deleteJson(path, options = {}) {
	return request(path, {
		...options,
		method: "DELETE",
	});
}