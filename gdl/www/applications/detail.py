import frappe

from gdl.utils.access import require_role


def get_context(context):
	context.no_cache = 1
	require_role("Applicant Portal User")
	context.application_name = frappe.form_dict.get("name")
