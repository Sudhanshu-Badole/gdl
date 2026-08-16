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

/**
 * Task 4.2 - inject eligibility requirements + ToR onto HRMS's own vacancy
 * detail page (hrms/templates/generators/job_opening.html), which we can't
 * edit directly (core app). Detected via the "Apply Now" link HRMS's
 * template already renders - its href always contains ?job_title=<opening>
 * since Task 4.0's hook points job_application_route at our /apply page.
 * Degrades silently if the page doesn't look like a vacancy detail page, or
 * if HRMS's markup changes and the expected insertion point isn't found.
 */
async function enhanceVacancyDetailPage() {
	const applyLink = document.querySelector('a[href*="job_title="]');
	if (!applyLink) return;

	const jobOpening = new URL(applyLink.href, window.location.origin).searchParams.get("job_title");
	if (!jobOpening) return;

	const res = await gdl.call("gdl.api.public.get_vacancy_extras", { job_opening: jobOpening });
	if (!res.success || !res.data) return;

	const { gdl_eligibility_requirements, gdl_terms_of_reference } = res.data;
	if (!gdl_eligibility_requirements && !gdl_terms_of_reference) return;

	let html = '<div class="card border p-6 mb-6">';
	if (gdl_eligibility_requirements) {
		html += `<h4 class="mt-0 mb-3">Eligibility Requirements</h4><p style="white-space: pre-wrap">${gdl_eligibility_requirements.replace(/</g, "&lt;")}</p>`;
	}
	if (gdl_terms_of_reference) {
		html += `<a href="${gdl_terms_of_reference}" target="_blank" class="btn btn-default btn-sm">Download Terms of Reference</a>`;
	}
	html += "</div>";

	// Insert after the description paragraph if we can find it (matches
	// HRMS's template structure); otherwise fall back to inserting right
	// before the Apply button's container so it's still visible somewhere.
	const descriptionParagraph = document.querySelector(".py-12 > p");
	const insertTarget = descriptionParagraph || applyLink.closest("div");
	if (insertTarget) {
		insertTarget.insertAdjacentHTML("afterend", html);
	}
}

document.addEventListener("DOMContentLoaded", enhanceVacancyDetailPage);
