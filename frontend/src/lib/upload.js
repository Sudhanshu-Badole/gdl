// Multipart-upload counterpart to ./call.js - that helper
// only POSTs JSON, but gdl.api.applicant's upload_* endpoints read
// frappe.request.files["file"] + frappe.form_dict, which requires an actual
// FormData body. Mirrors call.js's CSRF header and 401/403-redirect/error
// handling exactly so callers can treat the two helpers the same way.
import router from "../router";

export default async function upload(method, file, extraFields = {}) {
	const formData = new FormData();
	formData.append("file", file);
	for (const [key, value] of Object.entries(extraFields)) {
		formData.append(key, value);
	}

	// No Content-Type header: the browser sets the multipart boundary itself.
	const headers = { Accept: "application/json", "X-Frappe-Site-Name": window.location.hostname };
	if (window.csrf_token && window.csrf_token !== "{{ csrf_token }}") {
		headers["X-Frappe-CSRF-Token"] = window.csrf_token;
	}

	const res = await fetch(`/api/method/${method}`, { method: "POST", headers, body: formData });

	if (res.ok) {
		const data = await res.json();
		return data.message;
	}

	const responseText = await res.text();
	let error = {};
	try {
		error = JSON.parse(responseText);
	} catch (e) {
		// keep error = {} if the body isn't JSON
	}

	let exception = error.exc;
	if (exception) {
		try {
			exception = JSON.parse(exception)[0];
		} catch (e) {
			// keep the raw string if it isn't JSON-encoded
		}
	}

	let messages = error._server_messages ? JSON.parse(error._server_messages) : [];
	messages = messages.concat(error.message).map((m) => {
		try {
			return JSON.parse(m).message;
		} catch (e) {
			return m;
		}
	});
	messages = messages.filter(Boolean);
	if (!messages.length) {
		messages = [error._error_message || "Upload failed"];
	}

	const e = new Error(messages.join("\n"));
	e.exc_type = error.exc_type;
	e.exc = exception;
	e.messages = messages;

	if ([401, 403].includes(res.status) && router.currentRoute.value.name !== "Login") {
		router.push("/e-recruitment/login");
	}
	throw e;
}
