import { auth } from "../firebase";

async function getIdToken() {
	const user = auth.currentUser;
	if (!user) return null;
	return await user.getIdToken();
}

export default async function fetchWithAuth(path, options = {}) {
	const base = import.meta.env.VITE_BACKEND_URL || "";
	const token = await getIdToken();
	const headers = new Headers(options.headers || {});
	if (token) headers.set("Authorization", `Bearer ${token}`);
	headers.set("Content-Type", headers.get("Content-Type") || "application/json");

	const res = await fetch(base + path, { ...options, headers });
	if (!res.ok) {
		const text = await res.text();
		const err = new Error(`Request failed ${res.status}: ${text}`);
		err.response = res;
		throw err;
	}
	return res.json().catch(() => null);
}
