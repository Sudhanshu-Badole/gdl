"""Panel Member portal API (Phase 7, Panel Self Entry).

Every method re-verifies the caller is actually assigned to the interview or
session in question - Interview only carries a broad read grant and
Interview Feedback only an if_owner backstop (see setup_roles_permissions.py),
the real gate is the explicit assignment check here, same convention as
gdl.api.applicant's _get_own_job_applicant()/_get_own_attempt().
"""

import frappe
from frappe.utils import cint, now_datetime

from gdl.api.response import success
from gdl.utils.documents import tor_filename
from gdl.utils.exam_scoring import get_exam_result_summary
from gdl.utils.exceptions import gdl_error
from gdl.utils.notifications import notify_user


def require_panel():
	frappe.only_for("Panel Member")


def _is_assigned(interview_name, user):
	return frappe.db.exists("Interview Panel Member", {"parent": interview_name, "user": user})


def _get_own_session(session):
	session_doc = frappe.get_doc("Interview Session", session)
	if not _is_assigned(session_doc.interview, frappe.session.user):
		gdl_error("You are not assigned to this interview.")
	return session_doc


def _get_own_feedback(session, create_if_missing=False):
	name = frappe.db.get_value(
		"Interview Panel Feedback", {"interview_session": session, "panel_member": frappe.session.user}, "name"
	)
	if name:
		return frappe.get_doc("Interview Panel Feedback", name)
	if not create_if_missing:
		return None
	return frappe.get_doc(
		{"doctype": "Interview Panel Feedback", "interview_session": session, "panel_member": frappe.session.user}
	)


def _conflict_status(session):
	"""None if not yet confirmed either way, else the has_conflict_of_interest value."""
	feedback = _get_own_feedback(session)
	if not feedback or not feedback.conflict_of_interest_confirmed:
		return None
	return bool(feedback.has_conflict_of_interest)


@frappe.whitelist()
def get_dashboard():
	require_panel()
	user = frappe.session.user

	interview_names = frappe.get_all("Interview Panel Member", filters={"user": user}, pluck="parent")
	if not interview_names:
		return success(data=[])

	interviews = frappe.get_all(
		"Interview Schedule",
		# HR Proxy Entry / Compiled Scores interviews have nothing for a
		# panelist to act on here - HR enters those scores instead.
		filters={"name": ["in", interview_names], "status": "Published", "score_entry_mode": "Panel Self Entry"},
		fields=["name", "title", "job_opening", "scheduled_on", "venue_or_link"],
	)

	rows = []
	for interview in interviews:
		open_count = frappe.db.count("Interview Session", {"interview": interview.name, "status": "Invited"})
		if not open_count:
			continue
		candidate_count = frappe.db.count("Interview Session", {"interview": interview.name})
		rows.append(
			{
				"interview": interview.name,
				"title": interview.title,
				"job_title": frappe.db.get_value("Job Opening", interview.job_opening, "job_title"),
				"scheduled_on": interview.scheduled_on,
				"venue_or_link": interview.venue_or_link,
				"candidate_count": candidate_count,
				"open_count": open_count,
			}
		)
	rows.sort(key=lambda r: r["scheduled_on"] or "")
	return success(data=rows)


@frappe.whitelist()
def get_interview_candidates(interview):
	require_panel()
	user = frappe.session.user
	if not _is_assigned(interview, user):
		gdl_error("You are not assigned to this interview.")

	interview_doc = frappe.get_doc("Interview Schedule", interview)
	job_title = frappe.db.get_value("Job Opening", interview_doc.job_opening, "job_title")

	sessions = frappe.get_all(
		"Interview Session",
		filters={"interview": interview},
		fields=["name", "job_applicant", "status", "scheduled_on", "attendance_response"],
		order_by="creation asc",
	)
	applicants = {}
	submitted = set()
	if sessions:
		applicants = {
			row.name: row
			for row in frappe.get_all(
				"Job Applicant",
				filters={"name": ["in", [s.job_applicant for s in sessions]]},
				fields=["name", "applicant_name"],
			)
		}
		submitted = set(
			frappe.get_all(
				"Interview Panel Feedback",
				filters={"interview_session": ["in", [s.name for s in sessions]], "panel_member": user},
				pluck="interview_session",
			)
		)

	rows = [
		{
			"session": s.name,
			"applicant_name": applicants.get(s.job_applicant, {}).get("applicant_name"),
			"status": s.status,
			"submitted": s.name in submitted,
			"scheduled_on": s.scheduled_on or interview_doc.scheduled_on,
			"attendance_response": s.attendance_response,
		}
		for s in sessions
	]

	return success(
		data={
			"interview": {
				"name": interview_doc.name,
				"title": interview_doc.title,
				"job_title": job_title,
				"scheduled_on": interview_doc.scheduled_on,
				"venue_or_link": interview_doc.venue_or_link,
			},
			"sessions": rows,
		}
	)


@frappe.whitelist(methods=["POST"])
def confirm_no_conflict(session, has_conflict=False):
	require_panel()
	session_doc = _get_own_session(session)
	has_conflict = frappe.utils.cint(has_conflict)

	feedback = _get_own_feedback(session, create_if_missing=True)
	feedback.conflict_of_interest_confirmed = 1
	feedback.conflict_of_interest_confirmed_on = frappe.utils.now_datetime()
	feedback.has_conflict_of_interest = has_conflict
	feedback.flags.ignore_permissions = True
	feedback.save()

	if has_conflict:
		interview_doc = frappe.get_doc("Interview Schedule", session_doc.interview)
		applicant_name = frappe.db.get_value("Job Applicant", session_doc.job_applicant, "applicant_name")
		for hr_user in frappe.get_all("Has Role", filters={"role": "HR Officer", "parenttype": "User"}, pluck="parent"):
			notify_user(
				hr_user,
				subject=f"Panel conflict of interest declared - {applicant_name}",
				document_type="Interview Session",
				document_name=session,
				link=f"/HR/Vacancies/{interview_doc.job_opening}",
			)
		return success(message="Conflict recorded. HR has been notified to reassign this candidate.")

	return success(message="Thank you - you can now view this candidate.")


@frappe.whitelist()
def get_scorecard(session):
	require_panel()
	session_doc = _get_own_session(session)
	interview_doc = frappe.get_doc("Interview Schedule", session_doc.interview)

	conflict = _conflict_status(session)
	if conflict is None:
		return success(data={"needs_conflict_confirmation": True})
	if conflict:
		return success(data={"has_conflict_of_interest": True})

	applicant_name = frappe.db.get_value("Job Applicant", session_doc.job_applicant, "applicant_name")

	criteria = frappe.get_all(
		"Interview Criterion",
		filters={"interview": interview_doc.name},
		fields=["name", "sequence", "criterion_label", "description", "max_score"],
		order_by="sequence asc, creation asc",
	)

	existing_name = frappe.db.get_value(
		"Interview Panel Feedback", {"interview_session": session, "panel_member": frappe.session.user}, "name"
	)
	existing_scores = []
	existing_overall_comments = None
	is_submitted = False
	if existing_name:
		existing_scores = frappe.get_all(
			"Interview Feedback Criterion Score",
			filters={"parent": existing_name},
			fields=["criterion", "score_given", "comments"],
		)
		existing_overall_comments = frappe.db.get_value("Interview Panel Feedback", existing_name, "overall_comments")
		is_submitted = bool(frappe.db.get_value("Interview Panel Feedback", existing_name, "is_submitted"))

	# TOR is available to Panel Members every time (client feedback, Phase 3)
	# - unlike the applicant side, no shortlisted/status gate here.
	job_opening = frappe.db.get_value("Job Application", session_doc.job_application, "job_opening")
	tor_url = frappe.db.get_value("Job Opening", job_opening, "gdl_terms_of_reference") if job_opening else None
	terms_of_reference = {"file_url": tor_url, "filename": tor_filename(tor_url)} if tor_url else None

	documents = None
	if interview_doc.panel_can_view_documents:
		documents = frappe.db.get_value(
			"Job Applicant",
			session_doc.job_applicant,
			["resume_attachment", "gdl_national_id", "gdl_academic_certificate"],
			as_dict=True,
		)

	return success(
		data={
			"applicant_name": applicant_name,
			"locked": session_doc.status == "Completed" or is_submitted,
			"is_submitted": is_submitted,
			"criteria": criteria,
			"existing_scores": existing_scores,
			"existing_overall_comments": existing_overall_comments,
			"documents": documents,
			"terms_of_reference": terms_of_reference,
			"venue_or_link": interview_doc.venue_or_link,
			"location_map_link": interview_doc.gdl_location_map_link,
			"panel_can_view_exam_result": bool(interview_doc.panel_can_view_exam_result),
		}
	)


@frappe.whitelist(methods=["POST"])
def save_scorecard(session, criterion_scores, overall_comments=None, submit=0):
	require_panel()
	session_doc = _get_own_session(session)
	if session_doc.status == "Completed":
		gdl_error("This session is locked and can no longer be edited.")

	if isinstance(criterion_scores, str):
		criterion_scores = frappe.parse_json(criterion_scores)
	if not criterion_scores:
		gdl_error("Enter at least one score before saving.")

	existing_name = frappe.db.get_value(
		"Interview Panel Feedback", {"interview_session": session, "panel_member": frappe.session.user}, "name"
	)
	if existing_name:
		feedback = frappe.get_doc("Interview Panel Feedback", existing_name)
		if feedback.is_submitted:
			gdl_error("You have already submitted this scorecard and can no longer change it.")
		feedback.set("criterion_scores", [])
	else:
		feedback = frappe.get_doc(
			{"doctype": "Interview Panel Feedback", "interview_session": session, "panel_member": frappe.session.user}
		)

	for row in criterion_scores:
		feedback.append(
			"criterion_scores",
			{
				"criterion": row.get("criterion"),
				"max_score": row.get("max_score") or 0,
				"score_given": row.get("score_given") or 0,
				"comments": row.get("comments"),
			},
		)
	feedback.entered_by = frappe.session.user
	feedback.overall_comments = overall_comments
	if cint(submit):
		feedback.is_submitted = 1
		feedback.submitted_on = now_datetime()

	feedback.flags.ignore_permissions = True
	if existing_name:
		feedback.save()
	else:
		feedback.insert()
		# insert() forces owner = the acting session user - which is already
		# the panel member here (unlike Exam Attempt/Job Application, which
		# are created by HR on the applicant's behalf), so no correction needed.

	message = "Score submitted. It can no longer be changed." if cint(submit) else "Draft saved. Submit it when you are done."
	return success(data={"total_score": feedback.total_score, "is_submitted": bool(feedback.is_submitted)}, message=message)


@frappe.whitelist()
def get_candidate_exam_result(session):
	"""Read-only exam breakdown for the candidate this session belongs to -
	explicit "what to add" item from the clarification doc: panelists should
	be able to see the written test alongside the interview scorecard.
	Gated behind Interview Schedule.panel_can_view_exam_result (separate from
	panel_can_view_documents, which is about personal documents like ID/
	certificates, not exam performance) and behind the conflict-of-interest
	confirmation, same as get_scorecard."""
	require_panel()
	session_doc = _get_own_session(session)

	conflict = _conflict_status(session)
	if conflict is None or conflict:
		return success(data=None)

	interview_doc = frappe.get_doc("Interview Schedule", session_doc.interview)
	if not interview_doc.panel_can_view_exam_result:
		return success(data=None)

	return success(data=get_exam_result_summary(session_doc.job_application))


@frappe.whitelist(methods=["POST"])
def save_exam_result_comment(session, comment):
	require_panel()
	session_doc = _get_own_session(session)

	interview_doc = frappe.get_doc("Interview Schedule", session_doc.interview)
	if not interview_doc.panel_can_view_exam_result:
		gdl_error("Test results are not shared for this interview.")
	if _conflict_status(session):
		gdl_error("You have declared a conflict of interest for this candidate.")

	attempt_name = frappe.db.get_value("Exam Attempt", {"job_application": session_doc.job_application}, "name")
	if not attempt_name:
		gdl_error("No test attempt found for this candidate.")

	frappe.db.set_value("Exam Attempt", attempt_name, "panel_comment", comment)
	return success(message="Comment saved.")


@frappe.whitelist()
def get_past_sessions():
	require_panel()
	user = frappe.session.user

	feedback_rows = frappe.get_all(
		"Interview Panel Feedback", filters={"panel_member": user}, fields=["interview_session", "total_score", "modified"]
	)
	if not feedback_rows:
		return success(data=[])

	session_names = [r.interview_session for r in feedback_rows]
	sessions = {
		row.name: row
		for row in frappe.get_all(
			"Interview Session",
			filters={"name": ["in", session_names], "status": "Completed"},
			fields=["name", "job_application", "job_applicant", "interview"],
		)
	}
	if not sessions:
		return success(data=[])

	applicants = {
		row.name: row
		for row in frappe.get_all(
			"Job Applicant",
			filters={"name": ["in", [s.job_applicant for s in sessions.values()]]},
			fields=["name", "applicant_name"],
		)
	}
	interviews = {
		row.name: row
		for row in frappe.get_all(
			"Interview Schedule",
			filters={"name": ["in", [s.interview for s in sessions.values()]]},
			fields=["name", "title", "job_opening"],
		)
	}

	rows = []
	for feedback in feedback_rows:
		session = sessions.get(feedback.interview_session)
		if not session:
			continue
		applicant = applicants.get(session.job_applicant, {})
		interview = interviews.get(session.interview, {})
		rows.append(
			{
				"session": session.name,
				"applicant_name": applicant.get("applicant_name"),
				"job_application": session.job_application,
				"interview_title": interview.get("title"),
				"job_title": frappe.db.get_value("Job Opening", interview.get("job_opening"), "job_title"),
				"score": feedback.total_score,
				"submitted_on": feedback.modified,
			}
		)
	rows.sort(key=lambda r: r["submitted_on"] or "", reverse=True)
	return success(data=rows)
