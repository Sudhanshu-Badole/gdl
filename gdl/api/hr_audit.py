"""Audit trail viewer (Phase 10, partial). Read-only - rows are written
exclusively by gdl.utils.audit.log_action/set_application_status, never
directly by a user.
"""

import frappe

from gdl.api.hr import require_hr
from gdl.api.response import success


@frappe.whitelist()
def list_audit_log(reference_doctype=None, limit=100):
	require_hr()

	filters = {}
	if reference_doctype:
		filters["reference_doctype"] = reference_doctype

	rows = frappe.get_all(
		"Audit Log",
		filters=filters,
		fields=["name", "action", "reference_doctype", "reference_name", "user", "timestamp", "previous_value", "new_value", "details"],
		order_by="timestamp desc",
		limit_page_length=frappe.utils.cint(limit) or 100,
	)
	doctypes = frappe.get_all("Audit Log", distinct=True, pluck="reference_doctype")
	return success(data={"rows": rows, "reference_doctypes": sorted(doctypes)})
