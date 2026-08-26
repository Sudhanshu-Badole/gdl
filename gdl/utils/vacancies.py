"""Job Opening / Job Application doc_event hooks (Task 4.0).

Wired via hooks.py's doc_events.
"""

import frappe
from frappe.utils import add_days, nowdate

# HRMS's own "Apply Now" button (hrms/templates/generators/job_opening.html,
# a template we can't edit - core app) links to
# "/{{ job_application_route or 'job_application' }}/new?job_title={{ name }}".
# Setting job_application_route to "apply" here makes that stock button land
# on our own www/apply/new.py page instead of HRMS's generic Web Form -
# without touching HRMS's template at all.
APPLY_ROUTE = "apply"

FILLED_STATUSES = {"Selected", "Appointed"}
RECENT_WINDOW_DAYS = 90

VACANCY_LIST_FIELDS = [
	"name",
	"job_title",
	"route",
	"department",
	"location",
	"employment_type",
	"gdl_vacancy_category",
	"gdl_job_type",
	"closes_on",
]


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


def list_open_vacancies(limit=None):
	"""Open + published vacancies for the public site (Vue home/jobs pages).

	get_all (not get_list) deliberately skips permission checks: "publish=1"
	openings are meant to be publicly visible to Guests. SQL "IN (NULL)" never
	matches, so an unset closes_on needs "is not set" rather than being lumped
	into the IN list (see gdl.gdl/www/jobs/index.py, which this replaces).
	"""
	return frappe.get_all(
		"Job Opening",
		filters={"status": "Open", "publish": 1},
		or_filters=[["closes_on", ">=", nowdate()], ["closes_on", "is", "not set"]],
		fields=VACANCY_LIST_FIELDS,
		order_by="posted_on desc",
		limit_page_length=limit or 0,
	)


def list_vacancies(limit=None, include_recent=False):
	"""Open vacancies for the /jobs page, optionally unioned with vacancies
	that closed/filled within the last RECENT_WINDOW_DAYS days (the "include
	recently closed or filled positions" checkbox). Two separate get_all
	calls unioned in Python rather than one query - the two branches need
	different compound conditions (open+unexpired vs recently-closed) that
	frappe.get_all's single-level filters+or_filters can't express together.
	"""
	open_vacancies = list_open_vacancies(limit=limit)
	if not include_recent:
		return open_vacancies

	cutoff = add_days(nowdate(), -RECENT_WINDOW_DAYS)
	recent = frappe.get_all(
		"Job Opening",
		filters={"publish": 1, "status": ["!=", "Open"]},
		or_filters=[["closes_on", ">=", cutoff], ["closed_on", ">=", cutoff]],
		fields=VACANCY_LIST_FIELDS,
		order_by="posted_on desc",
		limit_page_length=limit or 0,
	)
	seen = {v["name"] for v in open_vacancies}
	return open_vacancies + [v for v in recent if v["name"] not in seen]
