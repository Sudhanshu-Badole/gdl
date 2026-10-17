"""Audit trail (Phase 10, partial). `frappe.db.set_value`/`doc.db_set` - used
throughout this app for every status transition, since none of these are
full doc.save() calls - bypass Frappe's own doc_events hooks entirely, so
there's no generic way to catch a Job Application status change after the
fact. set_application_status() is the single choke point instead: every
existing call site that used to set Job Application.status directly now
routes through here so the change gets logged, with no other behaviour
change.
"""

import frappe


def log_action(action, reference_doctype, reference_name, previous_value=None, new_value=None, details=None):
	frappe.get_doc(
		{
			"doctype": "Audit Log",
			"action": action,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"user": frappe.session.user,
			"timestamp": frappe.utils.now_datetime(),
			"previous_value": previous_value,
			"new_value": new_value,
			"details": details,
		}
	).insert(ignore_permissions=True)


def set_application_status(application, new_status, action=None):
	previous_status = frappe.db.get_value("Job Application", application, "status")
	if previous_status == new_status:
		return

	frappe.db.set_value("Job Application", application, "status", new_status)
	log_action(
		action=action or f"Status changed to {new_status}",
		reference_doctype="Job Application",
		reference_name=application,
		previous_value=previous_status,
		new_value=new_status,
	)
