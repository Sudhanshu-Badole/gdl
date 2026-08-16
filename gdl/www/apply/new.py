from urllib.parse import quote

import frappe


def get_context(context):
	context.no_cache = 1

	if frappe.session.user == "Guest":
		# Preserve ?job_title=... across the login round-trip so the applicant
		# lands back here (not just at /apply/new) once they've signed in.
		query_string = frappe.request.query_string.decode()
		full_path = frappe.request.path + (f"?{query_string}" if query_string else "")
		frappe.flags.redirect_location = f"/login?redirect-to={quote(full_path)}"
		raise frappe.Redirect

	context.job_opening = frappe.form_dict.get("job_title")
	if not context.job_opening:
		frappe.throw("Missing vacancy reference.", frappe.DoesNotExistError)
