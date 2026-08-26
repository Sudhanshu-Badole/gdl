/**
 * Shared client-side helper for calling gdl whitelisted API methods
 * (Task 1.4 convention). Every portal page should use this instead of
 * hand-rolled fetch() calls.
 *
 * Usage:
 *   const res = await gdl.call("gdl.api.example.ping", { name: "Ada" });
 *   if (res.success) { ... res.data ... } else { ... res.message ... }
 */
window.gdl = window.gdl || {};

function parseGdlResponse(body) {
	// Frappe wraps whitelisted-method return values under "message"
	if (body.message !== undefined) {
		return body.message;
	}

	// frappe.throw()/gdl_error() land here instead: no "message" key, the
	// user-facing text is JSON-encoded inside _server_messages.
	let errorText = body.exc_type || "Unknown error";
	if (body._server_messages) {
		try {
			const serverMessages = JSON.parse(body._server_messages);
			const first = JSON.parse(serverMessages[0]);
			errorText = first.message || errorText;
		} catch {
			// keep the exc_type fallback if _server_messages isn't parseable
		}
	}
	return { success: false, data: null, message: errorText };
}

window.gdl.call = async function (method, args) {
	const params = new URLSearchParams(args || {});
	const response = await fetch(`/api/method/${method}`, {
		method: "POST",
		headers: {
			"Content-Type": "application/x-www-form-urlencoded",
			"X-Frappe-CSRF-Token": window.csrf_token || "",
		},
		body: params,
	});
	return parseGdlResponse(await response.json());
};

/**
 * Upload a File to a whitelisted method that expects multipart/form-data
 * with the file under the "file" key (see gdl.utils.uploads.save_upload).
 * `fields` (optional) adds extra form fields alongside the file.
 *
 * Usage:
 *   const res = await gdl.upload("gdl.api.applicant.upload_profile_photo", fileInput.files[0]);
 *   const res2 = await gdl.upload("gdl.api.applicant.add_other_document", file, { document_type: "Reference Letter" });
 */
window.gdl.upload = async function (method, file, fields) {
	const form = new FormData();
	form.append("file", file);
	for (const [key, value] of Object.entries(fields || {})) {
		form.append(key, value);
	}
	const response = await fetch(`/api/method/${method}`, {
		method: "POST",
		headers: { "X-Frappe-CSRF-Token": window.csrf_token || "" },
		body: form,
	});
	return parseGdlResponse(await response.json());
};

/**
 * Render the profile-completeness reminder banner (Task 3.4) into the given
 * container. Shared between /complete-profile and /dashboard so both stay
 * in sync with the same threshold/copy.
 */
window.gdl.COMPLETENESS_THRESHOLD = 80;

window.gdl.renderCompletenessBanner = function (containerId, completeness) {
	const container = document.getElementById(containerId);
	if (!container) return;

	if (completeness >= window.gdl.COMPLETENESS_THRESHOLD) {
		container.innerHTML = "";
		return;
	}

	container.innerHTML = `
		<div class="alert alert-warning mb-6">
			<strong>${completeness}% complete.</strong>
			Your profile needs to be at least ${window.gdl.COMPLETENESS_THRESHOLD}% complete before you can apply for a vacancy.
			<a href="/complete-profile">Finish your profile</a>.
		</div>
	`;
};

