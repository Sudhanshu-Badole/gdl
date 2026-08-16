import frappe
from frappe.utils import nowdate

MAX_VACANCIES_ON_HOME = 6


def get_context(context):
	context.no_cache = 1
	context.vacancies = get_open_vacancies()
	context.how_to_apply_page = get_how_to_apply_page()


def get_open_vacancies():
	# get_all (not get_list) deliberately skips permission checks: "publish=1"
	# openings are meant to be publicly visible to Guests, same as HRMS's
	# own /jobs page (which uses raw query builder for the same reason).
	return frappe.get_all(
		"Job Opening",
		filters={"status": "Open", "publish": 1},
		# SQL "IN (NULL)" never matches, so an unset closes_on needs "is not set"
		# rather than being lumped into the IN list.
		or_filters=[["closes_on", ">=", nowdate()], ["closes_on", "is", "not set"]],
		fields=["name", "job_title", "route", "department", "location", "employment_type", "closes_on"],
		order_by="posted_on desc",
		limit_page_length=MAX_VACANCIES_ON_HOME,
	)


def get_how_to_apply_page():
	"""Optional Web Page (route: how-to-apply) HR can edit without a deploy."""
	route = frappe.db.get_value("Web Page", {"route": "how-to-apply", "published": 1}, ["route", "title"])
	if route:
		return {"route": route[0], "title": route[1]}
	return None
