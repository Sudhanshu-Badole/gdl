import frappe


def gdl_error(msg, exc=None, title=None):
	"""Raise a user-facing error (frappe.throw equivalent).

	Routine validation failures (bad input, duplicate email, etc.) are
	*not* written to the Error Log - that would flood it with expected,
	non-actionable noise. Pass `exc` (a caught exception) only when this is
	wrapping a genuine unexpected failure that's also worth recording.
	"""
	if exc is not None:
		gdl_log_error(msg, exc=exc, title=title)
	frappe.throw(msg, title=title)


def gdl_log_error(msg, exc=None, title=None):
	"""Record an error to the Error Log without raising - use in except blocks
	for failures that shouldn't interrupt the caller (e.g. a notification
	email that failed to send)."""
	frappe.log_error(
		title=title or "GDL Error", message=msg if not exc else f"{msg}\n\n{frappe.get_traceback()}"
	)
