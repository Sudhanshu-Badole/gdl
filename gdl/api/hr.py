"""HR-only endpoints backing the Vue /HR/* portal (gdl/frontend).

Every function starts with require_hr() - the SPA's router guard is UX only
(reads window.boot.roles), this is the real server-side gate. Several
dashboard stats are literal 0 by design, not fake queries: Examination,
Interview, Job Offer, and Appointment Letter doctypes don't exist yet
(Phases 5-8 of the project plan haven't started), so there's nothing real to
count for those widgets until then.
"""

import frappe
from frappe.utils import add_days, get_first_day, get_first_day_of_week, today

from gdl.api.response import success
from gdl.utils.vacancies import FILLED_STATUSES

HR_ROLES = ("HR Officer", "System Manager")
HR_CLOSING_SOON_WINDOW_DAYS = 3
CANDIDATES_SORT_OPTIONS = {
	"creation desc": "creation desc",
	"creation asc": "creation asc",
}

PIPELINE_BUCKETS = {
	"submitted_under_review": {"Submitted", "Under Review", "Review on Hold"},
	"shortlisted": {"Shortlisted"},
	"exam_stage": {"Exam Invited / Scheduled", "Exam Completed", "Exam Not Attended"},
	"interview_stage": {"Interview Invited / Scheduled", "Interview Completed", "Interview Not Attended"},
	"selected": {"Selected"},
	"offer_appointed": {"Offer Sent", "Offer Accepted", "Offer Declined", "Appointed"},
}


def require_hr():
	frappe.only_for(HR_ROLES)


def _positions_filled(job_opening):
	return frappe.db.count(
		"Job Application",
		filters={"job_opening": job_opening, "status": ["in", list(FILLED_STATUSES)]},
	)


def _computed_status(opening, positions_filled):
	if not opening.publish:
		return "Draft"
	if opening.status == "Open":
		return "Published"
	if positions_filled >= (opening.gdl_number_of_positions or 0):
		return "Filled"
	return "Closed"


@frappe.whitelist()
def get_dashboard_stats():
	require_hr()

	week_start = get_first_day_of_week(today())
	month_start = get_first_day(today())

	open_vacancies = frappe.db.count("Job Opening", {"status": "Open"})
	applications_this_week = frappe.db.count("Job Application", {"creation": [">=", week_start]})
	pending_document_review = frappe.db.count("Job Application", {"status": "Submitted"})

	repeat_applicant_ids = frappe.db.sql_list(
		"""
		select job_applicant from `tabJob Application`
		group by job_applicant
		having count(*) > 1
		"""
	)
	repeat_applicants_this_month = 0
	if repeat_applicant_ids:
		repeat_applicants_this_month = len(
			frappe.db.sql_list(
				"""
				select distinct job_applicant from `tabJob Application`
				where job_applicant in %(ids)s and creation >= %(month_start)s
				""",
				{"ids": repeat_applicant_ids, "month_start": month_start},
			)
		)

	closing_soon = frappe.get_all(
		"Job Opening",
		filters={
			"status": "Open",
			"publish": 1,
			"closes_on": ["between", [today(), add_days(today(), HR_CLOSING_SOON_WINDOW_DAYS)]],
		},
		fields=["name", "job_title", "route", "closes_on"],
		order_by="closes_on asc",
		limit_page_length=5,
	)

	return success(
		data={
			"overview": {
				"open_vacancies": open_vacancies,
				"applications_this_week": applications_this_week,
				# Placeholders - no Examination/Interview doctype yet (Phases 5/6).
				"upcoming_exams_14d": 0,
				"upcoming_interviews_14d": 0,
			},
			"needs_action": {
				"pending_document_review": pending_document_review,
				# Placeholders - no Examination doctype yet (Phase 5).
				"ready_to_publish_exam": 0,
				# Placeholder - no Interview doctype yet (Phase 6).
				"ready_to_publish_interview": 0,
				# Placeholder - no Examination doctype yet (Phase 5).
				"exam_grades_pending": 0,
				# Placeholder - no Job Offer equivalent yet (Phase 8).
				"offers_awaiting_response": 0,
				# Placeholder - no Appointment Letter doctype yet (Phase 8).
				"appointment_letters_to_issue": 0,
				"repeat_applicants_this_month": repeat_applicants_this_month,
			},
			"closing_soon": closing_soon,
		}
	)


@frappe.whitelist()
def list_vacancies():
	"""All Job Openings (drafts/closed/filled included) for the internal HR
	Vacancies list - unlike gdl.api.public.get_open_vacancies, which only
	returns published+open openings for the public site.
	"""
	require_hr()

	openings = frappe.get_all(
		"Job Opening",
		fields=[
			"name",
			"job_title",
			"department",
			"status",
			"publish",
			"closes_on",
			"gdl_number_of_positions",
		],
		order_by="creation desc",
	)

	rows = []
	for opening in openings:
		positions_filled = _positions_filled(opening.name)
		applications_count = frappe.db.count("Job Application", {"job_opening": opening.name})
		rows.append(
			{
				"name": opening.name,
				"job_title": opening.job_title,
				"department": opening.department,
				"applications_count": applications_count,
				"positions_filled": positions_filled,
				"positions_total": opening.gdl_number_of_positions or 0,
				"closes_on": opening.closes_on,
				"computed_status": _computed_status(opening, positions_filled),
			}
		)
	return success(data=rows)


@frappe.whitelist()
def get_vacancy(name):
	require_hr()

	opening = frappe.get_doc("Job Opening", name)
	positions_filled = _positions_filled(name)

	statuses = frappe.get_all("Job Application", filters={"job_opening": name}, pluck="status")
	pipeline = {bucket: 0 for bucket in PIPELINE_BUCKETS}
	for status in statuses:
		for bucket, values in PIPELINE_BUCKETS.items():
			if status in values:
				pipeline[bucket] += 1
				break

	return success(
		data={
			"opening": opening.as_dict(),
			"computed_status": _computed_status(opening, positions_filled),
			"positions_filled": positions_filled,
			"positions_total": opening.gdl_number_of_positions or 0,
			"pipeline": pipeline,
			"totals": {"applications": len(statuses)},
		}
	)


@frappe.whitelist(methods=["POST"])
def close_vacancy_applications(name):
	require_hr()

	opening = frappe.get_doc("Job Opening", name)
	if opening.status == "Closed":
		frappe.throw("This vacancy is already closed.")

	opening.db_set("status", "Closed")
	opening.db_set("closed_on", today())

	positions_filled = _positions_filled(name)
	return success(
		data={
			"computed_status": _computed_status(opening, positions_filled),
			"closed_on": opening.closed_on,
		}
	)


@frappe.whitelist()
def get_vacancy_applications(job_opening):
	require_hr()

	applications = frappe.get_all(
		"Job Application",
		filters={"job_opening": job_opening},
		fields=["name", "job_applicant", "status", "creation"],
		order_by="creation desc",
	)
	if not applications:
		return success(data=[])

	applicants = {
		row.name: row
		for row in frappe.get_all(
			"Job Applicant",
			filters={"name": ["in", [a.job_applicant for a in applications]]},
			fields=["name", "applicant_name", "email_id"],
		)
	}
	return success(
		data=[
			{
				"name": a.name,
				"applicant_name": applicants.get(a.job_applicant, {}).get("applicant_name"),
				"email_id": applicants.get(a.job_applicant, {}).get("email_id"),
				"status": a.status,
				"creation": a.creation,
			}
			for a in applications
		]
	)


@frappe.whitelist()
def list_candidates(search=None, sort="creation desc"):
	require_hr()

	order_by = CANDIDATES_SORT_OPTIONS.get(sort, "creation desc")
	if search:
		like = f"%{search}%"
		or_filters = [
			["applicant_name", "like", like],
			["email_id", "like", like],
			["gdl_cid_number", "like", like],
		]
		applicants = frappe.get_all(
			"Job Applicant",
			or_filters=or_filters,
			fields=["name", "applicant_name", "email_id", "gdl_cid_number", "creation"],
			order_by=order_by,
		)
	else:
		applicants = frappe.get_all(
			"Job Applicant",
			fields=["name", "applicant_name", "email_id", "gdl_cid_number", "creation"],
			order_by=order_by,
		)

	rows = []
	for applicant in applicants:
		applications_count = frappe.db.count("Job Application", {"job_applicant": applicant.name})
		rows.append(
			{
				"name": applicant.name,
				"applicant_name": applicant.applicant_name,
				"email_id": applicant.email_id,
				"gdl_cid_number": applicant.gdl_cid_number,
				"creation": applicant.creation,
				"applications_count": applications_count,
			}
		)
	return success(data=rows)
