"""HR-only endpoints backing the Vue /HR/* portal (gdl/frontend).

Every function starts with require_hr() - the SPA's router guard is UX only
(reads window.boot.roles), this is the real server-side gate. A few
dashboard stats are still literal 0 by design, not fake queries: Job Offer
and Appointment Letter doctypes don't exist yet (Phase 8 of the project plan
hasn't started), so there's nothing real to count for those widgets until
then. Examination stats are wired to gdl.api.hr_exam's doctypes (Phase 6);
Interview stats to gdl.api.hr_interview's (Phase 7).
"""

import frappe
from frappe.utils import add_days, escape_html, get_first_day, get_first_day_of_week, get_url, today

from gdl.api.response import success
from gdl.utils.audit import log_action
from gdl.utils.documents import DOCUMENT_KEYS, set_verification_status
from gdl.utils.exceptions import gdl_error
from gdl.utils.notifications import notify_user, send_email_or_log
from gdl.utils.vacancies import FILLED_STATUSES

DOCUMENT_VERIFICATION_STATUSES = {"Verified", "Sent Back"}

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
	"selected": {"Selected", "Reserve", "Rejected"},
	"offer_appointed": {"Offer Sent", "Offer Accepted", "Offer Declined", "Offer Expired", "Appointed"},
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

	upcoming_exams_14d = frappe.db.count(
		"Exam", {"status": "Published", "closes_on": ["between", [today(), add_days(today(), 14)]]}
	)

	draft_exam_names = frappe.get_all("Exam", {"status": "Draft"}, pluck="name")
	ready_to_publish_exam = (
		len(set(frappe.get_all("Exam Question", filters={"exam": ["in", draft_exam_names]}, pluck="exam")))
		if draft_exam_names
		else 0
	)

	submitted_attempt_names = frappe.get_all("Exam Attempt", {"status": "Submitted"}, pluck="name")
	exam_grades_pending = (
		len(
			set(
				frappe.get_all(
					"Exam Attempt Answer",
					filters={"is_graded": 0, "parent": ["in", submitted_attempt_names]},
					pluck="parent",
				)
			)
		)
		if submitted_attempt_names
		else 0
	)

	upcoming_interviews_14d = frappe.db.count(
		"Interview Schedule", {"status": "Published", "scheduled_on": ["between", [today(), add_days(today(), 14)]]}
	)

	draft_interview_names = frappe.get_all("Interview Schedule", {"status": "Draft"}, pluck="name")
	ready_to_publish_interview = (
		len(set(frappe.get_all("Interview Criterion", filters={"interview": ["in", draft_interview_names]}, pluck="interview")))
		if draft_interview_names
		else 0
	)

	return success(
		data={
			"overview": {
				"open_vacancies": open_vacancies,
				"applications_this_week": applications_this_week,
				"upcoming_exams_14d": upcoming_exams_14d,
				"upcoming_interviews_14d": upcoming_interviews_14d,
			},
			"needs_action": {
				"pending_document_review": pending_document_review,
				"ready_to_publish_exam": ready_to_publish_exam,
				"ready_to_publish_interview": ready_to_publish_interview,
				"exam_grades_pending": exam_grades_pending,
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
			"posted_on",
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
				"posted_on": opening.posted_on,
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
		gdl_error("This vacancy is already closed.")

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
				"job_applicant": a.job_applicant,
				"applicant_name": applicants.get(a.job_applicant, {}).get("applicant_name"),
				"email_id": applicants.get(a.job_applicant, {}).get("email_id"),
				"status": a.status,
				"creation": a.creation,
			}
			for a in applications
		]
	)


@frappe.whitelist()
def get_applicant_documents(job_applicant):
	"""Every fixed document + its verification status, plus the free-form
	"Other Supporting Documents" rows - backs both the Applications tab's
	per-row expand panel and the Candidates "Verification" tab."""
	require_hr()

	doc = frappe.get_doc("Job Applicant", job_applicant)
	rows = []
	for key, (fieldname, label, mandatory) in DOCUMENT_KEYS.items():
		file_url = doc.get(fieldname)
		verification = next(
			(r for r in doc.custom_document_verifications if r.document_key == key), None
		)
		rows.append(
			{
				"key": key,
				"label": label,
				"mandatory": mandatory,
				"file_url": file_url,
				"status": verification.status if verification else "Submitted",
				"remark": verification.remark if verification else None,
				"reviewed_by": verification.reviewed_by if verification else None,
				"reviewed_on": verification.reviewed_on if verification else None,
			}
		)

	other = [
		{
			"key": row.name,
			"label": row.document_type,
			"mandatory": False,
			"file_url": row.attachment,
			"status": row.status or "Submitted",
			"remark": row.remark,
			"reviewed_by": row.reviewed_by,
			"reviewed_on": row.reviewed_on,
		}
		for row in doc.gdl_other_documents
	]
	return success(data={"applicant_name": doc.applicant_name, "documents": rows, "other_documents": other})


@frappe.whitelist(methods=["POST"])
def set_document_verification_status(job_applicant, document_key, status, remark=None):
	"""HR Verify/Send Back action on one document. document_key is either a
	fixed key from gdl.utils.documents.DOCUMENT_KEYS, or the row name of an
	"Other Supporting Documents" entry (see the "other" branch below)."""
	require_hr()

	if status not in DOCUMENT_VERIFICATION_STATUSES:
		gdl_error("Status must be Verified or Sent Back.")
	if status == "Sent Back" and not (remark or "").strip():
		gdl_error("A remark is required when sending a document back.")

	doc = frappe.get_doc("Job Applicant", job_applicant)

	if document_key in DOCUMENT_KEYS:
		fieldname = DOCUMENT_KEYS[document_key][0]
		if not doc.get(fieldname):
			gdl_error("This document hasn't been uploaded yet.")
		set_verification_status(doc, document_key, status, remark=remark, reviewed_by=frappe.session.user)
	else:
		row = next((r for r in doc.gdl_other_documents if r.name == document_key), None)
		if not row:
			gdl_error("Document not found.")
		row.status = status
		row.remark = remark
		row.reviewed_by = frappe.session.user
		row.reviewed_on = frappe.utils.now_datetime()
		doc.save()

	log_action(
		action=f"Document {status}",
		reference_doctype="Job Applicant",
		reference_name=job_applicant,
		new_value=status,
		details=f"{document_key}: {remark}" if remark else document_key,
	)

	if status == "Sent Back":
		link = "/complete-profile"
		message = f"""
			<p>Hi {escape_html(doc.applicant_name)},</p>
			<p>One of your submitted documents needs attention: <strong>{escape_html(remark)}</strong></p>
			<p>Please update it here: <a href="{get_url(link)}">{get_url(link)}</a></p>
		"""
		send_email_or_log(
			recipients=[doc.email_id],
			subject="A document needs your attention",
			message=message,
			log_fallback=f"document sent back for {doc.email_id} ({document_key})",
		)
		notify_user(
			doc.email_id,
			subject=f"Document sent back: {remark}",
			document_type="Job Applicant",
			document_name=doc.name,
			link=link,
		)

	return success(message=f"Document marked {status}.")


@frappe.whitelist()
def list_pending_document_verifications():
	"""Applicants with at least one uploaded document still awaiting HR
	review (status Submitted, or no verification row yet) - backs the
	Candidates "Verification" tab."""
	require_hr()

	fixed_fieldnames = [fieldname for fieldname, _label, _mandatory in DOCUMENT_KEYS.values()]
	applicants = frappe.get_all("Job Applicant", fields=["name", *fixed_fieldnames])

	resolved_by_parent = {}
	for row in frappe.get_all(
		"Job Applicant Document Verification",
		filters={"status": ["!=", "Submitted"]},
		fields=["parent", "document_key"],
	):
		resolved_by_parent.setdefault(row.parent, set()).add(row.document_key)

	pending_names = {
		applicant.name
		for applicant in applicants
		if any(
			applicant.get(fieldname) and key not in resolved_by_parent.get(applicant.name, set())
			for key, (fieldname, _label, _mandatory) in DOCUMENT_KEYS.items()
		)
	}
	pending_names.update(
		frappe.get_all("Job Applicant Document", filters={"status": "Submitted"}, pluck="parent")
	)

	if not pending_names:
		return success(data=[])

	rows = frappe.get_all(
		"Job Applicant",
		filters={"name": ["in", list(pending_names)]},
		fields=["name", "applicant_name", "email_id", "gdl_cid_number", "creation"],
		order_by="creation desc",
	)
	return success(data=rows)


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
