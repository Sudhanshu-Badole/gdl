"""Job Opening / Job Application doc_event hooks (Task 4.0).

Wired via hooks.py's doc_events.
"""

import frappe

# HRMS's own "Apply Now" button (hrms/templates/generators/job_opening.html,
# a template we can't edit - core app) links to
# "/{{ job_application_route or 'job_application' }}/new?job_title={{ name }}".
# Setting job_application_route to "apply" here makes that stock button land
# on our own www/apply/new.py page instead of HRMS's generic Web Form -
# without touching HRMS's template at all.
APPLY_ROUTE = "apply"

FILLED_STATUSES = {"Selected", "Appointed"}


def set_apply_route_on_save(doc, method=None):
	if doc.job_application_route != APPLY_ROUTE:
		doc.job_application_route = APPLY_ROUTE


def backfill_apply_routes():
	"""One-off backfill for Job Openings that existed before this hook was
	wired up (set_apply_route_on_save only fires on save, so pre-existing
	records keep whatever job_application_route they had - empty, meaning
	HRMS's stock/broken form - until someone edits and re-saves them, which
	might never happen for an already-published vacancy). Safe to re-run.
	"""
	stale = frappe.get_all(
		"Job Opening", filters={"job_application_route": ["!=", APPLY_ROUTE]}, pluck="name"
	)
	for name in stale:
		frappe.db.set_value("Job Opening", name, "job_application_route", APPLY_ROUTE)
	frappe.db.commit()
	print(f"Backfilled job_application_route on {len(stale)} Job Opening(s).")


def auto_close_job_opening_if_filled(doc, method=None):
	if doc.status not in FILLED_STATUSES:
		return

	job_opening = frappe.get_doc("Job Opening", doc.job_opening)
	if job_opening.status != "Open" or not job_opening.gdl_number_of_positions:
		return

	filled_count = frappe.db.count(
		"Job Application",
		filters={"job_opening": doc.job_opening, "status": ["in", list(FILLED_STATUSES)]},
	)
	if filled_count >= job_opening.gdl_number_of_positions:
		job_opening.db_set("status", "Closed")
		job_opening.db_set("closed_on", frappe.utils.today())
