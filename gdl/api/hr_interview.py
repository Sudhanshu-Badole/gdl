"""Interview scheduling + all 3 score-entry modes (Phase 7). Mirrors
gdl.api.hr_exam's shape - Job Application.status already carries the full
interview vocabulary from Phase 4 ("Interview Invited / Scheduled",
"Interview Completed", "Interview Not Attended"); this module only ever
transitions between those.

Score-entry modes (Interview Schedule.score_entry_mode): Panel Self Entry
(panelists score via gdl.api.panel), HR Proxy Entry (HR fills the same
Interview Panel Feedback rows on a panelist's behalf via get/save_proxy_scorecard
below), Compiled Scores (no panel involvement - HR sets Interview
Session.total_score directly via set_compiled_score, no Interview Panel
Feedback rows at all).

Ranking candidates into Selected/Reserve/Rejected is Phase 8 - this module
stops at get_interview_queue's score column, which is enough for HR to judge
ranking today.
"""

import frappe
from frappe.utils import flt, get_url, now_datetime

from gdl.api.hr import require_hr
from gdl.api.response import success
from gdl.utils.audit import log_action, set_application_status
from gdl.utils.exam_scoring import get_exam_result_summary
from gdl.utils.exceptions import gdl_error, gdl_log_error
from gdl.utils.notifications import notify_user, send_email_or_log

ACTIVE_STATUSES = ("Draft", "Published")

# Standard interview criteria per the clarification doc's Q5 - HR's usual
# 5-criterion rubric, offered as a one-click preset rather than typed in by
# hand every time. HR can still edit/remove any of these after loading them.
STANDARD_CRITERIA = [
	("Understanding of the ToR of the given position", 10),
	("Prior work experience", 10),
	("Technical qualifications or knowledge", 10),
	("Leadership aptitude/ability", 10),
	("Attitude and overall impression", 10),
]


def _get_active_interview(job_opening):
	name = frappe.db.get_value(
		"Interview Schedule", {"job_opening": job_opening, "status": ["in", ACTIVE_STATUSES]}, "name", order_by="creation desc"
	)
	return frappe.get_doc("Interview Schedule", name) if name else None


def _criteria_for(interview_name):
	return frappe.get_all(
		"Interview Criterion",
		filters={"interview": interview_name},
		fields=["name", "sequence", "criterion_label", "description", "max_score"],
		order_by="sequence asc, creation asc",
	)


@frappe.whitelist()
def list_panel_members():
	require_hr()

	rows = frappe.get_all("Has Role", filters={"role": "Panel Member", "parenttype": "User"}, pluck="parent")
	if not rows:
		return success(data=[])
	users = frappe.get_all(
		"User", filters={"name": ["in", rows], "enabled": 1}, fields=["name", "full_name"], order_by="full_name asc"
	)
	return success(data=users)


@frappe.whitelist()
def get_interview(job_opening):
	require_hr()

	interview = _get_active_interview(job_opening)
	if not interview:
		return success(data=None)

	return success(data={"interview": interview.as_dict(), "criteria": _criteria_for(interview.name)})


@frappe.whitelist(methods=["POST"])
def create_interview(
	job_opening,
	title,
	instructions,
	venue_or_link,
	scheduled_on,
	panel_can_view_documents=0,
	panel_can_view_exam_result=0,
	score_entry_mode="Panel Self Entry",
	gdl_location_map_link=None,
):
	require_hr()

	if _get_active_interview(job_opening):
		gdl_error("An interview already exists for this vacancy. Edit or archive it before creating another.")

	interview = frappe.get_doc(
		{
			"doctype": "Interview Schedule",
			"job_opening": job_opening,
			"title": title,
			"instructions": instructions,
			"venue_or_link": venue_or_link,
			"gdl_location_map_link": gdl_location_map_link,
			"scheduled_on": scheduled_on,
			"panel_can_view_documents": 1 if frappe.utils.cint(panel_can_view_documents) else 0,
			"panel_can_view_exam_result": 1 if frappe.utils.cint(panel_can_view_exam_result) else 0,
			"score_entry_mode": score_entry_mode,
			"status": "Draft",
		}
	)
	interview.insert()
	return success(data=interview.as_dict(), message="Interview created.")


@frappe.whitelist(methods=["POST"])
def update_interview(name, **fields):
	require_hr()

	interview = frappe.get_doc("Interview Schedule", name)
	if interview.status != "Draft":
		gdl_error("Only a Draft interview can be edited.")

	for field in (
		"title",
		"instructions",
		"venue_or_link",
		"gdl_location_map_link",
		"scheduled_on",
		"panel_can_view_documents",
		"panel_can_view_exam_result",
		"score_entry_mode",
	):
		if field in fields:
			interview.set(field, fields[field])
	interview.save()
	return success(data=interview.as_dict(), message="Interview updated.")


@frappe.whitelist(methods=["POST"])
def add_criterion(interview, criterion_label, max_score, description=None):
	require_hr()

	interview_doc = frappe.get_doc("Interview Schedule", interview)
	if interview_doc.status != "Draft":
		gdl_error("Criteria can only be added while the interview is a Draft.")

	next_sequence = (frappe.db.count("Interview Criterion", {"interview": interview}) or 0) + 1
	criterion = frappe.get_doc(
		{
			"doctype": "Interview Criterion",
			"interview": interview,
			"sequence": next_sequence,
			"criterion_label": criterion_label,
			"description": description,
			"max_score": max_score,
		}
	)
	criterion.insert()
	return success(data=criterion.as_dict(), message="Criterion added.")


@frappe.whitelist(methods=["POST"])
def add_standard_criteria(interview):
	require_hr()

	interview_doc = frappe.get_doc("Interview Schedule", interview)
	if interview_doc.status != "Draft":
		gdl_error("Criteria can only be added while the interview is a Draft.")

	existing_labels = {
		label.lower() for label in frappe.get_all("Interview Criterion", {"interview": interview}, pluck="criterion_label")
	}
	next_sequence = len(existing_labels) + 1
	added = 0
	for label, max_score in STANDARD_CRITERIA:
		if label.lower() in existing_labels:
			continue
		frappe.get_doc(
			{
				"doctype": "Interview Criterion",
				"interview": interview,
				"sequence": next_sequence,
				"criterion_label": label,
				"max_score": max_score,
			}
		).insert()
		next_sequence += 1
		added += 1

	return success(data={"added": added}, message=f"{added} standard criterion/criteria added." if added else "Standard criteria already present.")


@frappe.whitelist(methods=["POST"])
def update_criterion(name, **fields):
	require_hr()

	criterion = frappe.get_doc("Interview Criterion", name)
	interview_doc = frappe.get_doc("Interview Schedule", criterion.interview)
	if interview_doc.status != "Draft":
		gdl_error("Criteria can only be edited while the interview is a Draft.")

	for field in ("criterion_label", "description", "max_score"):
		if field in fields:
			criterion.set(field, fields[field])
	criterion.save()
	return success(data=criterion.as_dict(), message="Criterion updated.")


@frappe.whitelist(methods=["POST"])
def delete_criterion(name):
	require_hr()

	criterion = frappe.get_doc("Interview Criterion", name)
	interview_doc = frappe.get_doc("Interview Schedule", criterion.interview)
	if interview_doc.status != "Draft":
		gdl_error("Criteria can only be removed while the interview is a Draft.")

	frappe.delete_doc("Interview Criterion", name)
	return success(message="Criterion removed.")


@frappe.whitelist(methods=["POST"])
def add_panel_member(interview, user):
	require_hr()

	interview_doc = frappe.get_doc("Interview Schedule", interview)
	if interview_doc.status != "Draft":
		gdl_error("Panel members can only be assigned while the interview is a Draft.")
	if any(row.user == user for row in interview_doc.panel_members):
		gdl_error("This panel member is already assigned.")

	interview_doc.append("panel_members", {"user": user})
	interview_doc.save()
	return success(data=interview_doc.as_dict(), message="Panel member assigned.")


@frappe.whitelist(methods=["POST"])
def remove_panel_member(interview, user):
	require_hr()

	interview_doc = frappe.get_doc("Interview Schedule", interview)
	if interview_doc.status != "Draft":
		gdl_error("Panel members can only be changed while the interview is a Draft.")

	interview_doc.panel_members = [row for row in interview_doc.panel_members if row.user != user]
	interview_doc.save()
	return success(data=interview_doc.as_dict(), message="Panel member removed.")


def _interview_invite_email(applicant_name, email_id, interview, job_title, job_application):
	message = f"""
		<p>Hi {frappe.utils.escape_html(applicant_name)},</p>
		<p>You've been invited to interview for <strong>{frappe.utils.escape_html(job_title)}</strong>.</p>
		<p>When: {interview.scheduled_on}</p>
		<p>Where: {frappe.utils.escape_html(interview.venue_or_link or "To be confirmed")}</p>
		{f'<p><a href="{interview.gdl_location_map_link}">View location on map</a></p>' if interview.gdl_location_map_link else ""}
		<p>Please confirm whether you'll be attending through the recruitment portal.</p>
	"""
	send_email_or_log(
		recipients=[email_id],
		subject=f"Interview scheduled - {job_title}",
		message=message,
		log_fallback=f"interview invite for {email_id}, interview {interview.name}",
	)
	notify_user(
		email_id,
		subject=f"Interview scheduled - {job_title}",
		document_type="Job Application",
		document_name=job_application,
		link=f"/applications/{job_application}",
	)


def _panel_assignment_email(user_email, interview, job_title, candidate_count):
	link = get_url(f"/panel/interviews/{interview.name}")
	message = f"""
		<p>You've been assigned as a panel member for <strong>{frappe.utils.escape_html(job_title)}</strong>.</p>
		<p>When: {interview.scheduled_on}</p>
		<p>Where: {frappe.utils.escape_html(interview.venue_or_link or "To be confirmed")}</p>
		{f'<p><a href="{interview.gdl_location_map_link}">View location on map</a></p>' if interview.gdl_location_map_link else ""}
		<p>Candidates to review: {candidate_count}</p>
		<p><a href="{link}">{link}</a></p>
	"""
	send_email_or_log(
		recipients=[user_email],
		subject=f"Interview panel assignment - {job_title}",
		message=message,
		log_fallback=f"panel assignment email for {user_email}, interview {interview.name}",
	)
	notify_user(
		user_email,
		subject=f"Interview panel assignment - {job_title}",
		document_type="Interview Schedule",
		document_name=interview.name,
		link=f"/panel/interviews/{interview.name}",
	)


@frappe.whitelist(methods=["POST"])
def publish_interview(name):
	require_hr()

	interview = frappe.get_doc("Interview Schedule", name)
	# Draft -> first publish. Published -> re-publish: a candidate advanced
	# to "Interview Invited / Scheduled" after the first publish would
	# otherwise never get an Interview Session, since that only happens
	# here - so calling this again on an already-Published interview is how
	# HR sweeps in anyone who arrived late (the loop below already skips
	# anyone already invited).
	if interview.status not in ("Draft", "Published"):
		gdl_error("Only a Draft or Published interview can be published.")

	# Compiled Scores has no panel involvement at all - nothing to configure
	# but the interview itself.
	if interview.score_entry_mode != "Compiled Scores":
		criteria = _criteria_for(interview.name)
		if not criteria:
			gdl_error("Add at least one criterion before publishing.")
		if not interview.panel_members:
			gdl_error("Assign at least one panel member before publishing.")

	# Only one Published interview per vacancy at a time - archive whatever
	# else was live before (excluding this interview itself, in case it's
	# already the Published one being re-run to invite late arrivals).
	for other in frappe.get_all(
		"Interview Schedule", filters={"job_opening": interview.job_opening, "status": "Published", "name": ["!=", interview.name]}
	):
		frappe.db.set_value("Interview Schedule", other.name, "status", "Archived")

	job_title = frappe.db.get_value("Job Opening", interview.job_opening, "job_title")

	candidates = frappe.get_all(
		"Job Application",
		filters={"job_opening": interview.job_opening, "status": "Interview Invited / Scheduled"},
		fields=["name", "job_applicant"],
	)
	already_invited = set(frappe.get_all("Interview Session", filters={"interview": interview.name}, pluck="job_application"))

	applicants = {}
	if candidates:
		applicants = {
			row.name: row
			for row in frappe.get_all(
				"Job Applicant",
				filters={"name": ["in", [c.job_applicant for c in candidates]]},
				fields=["name", "applicant_name", "email_id"],
			)
		}

	invited = 0
	for candidate in candidates:
		if candidate.name in already_invited:
			continue
		session = frappe.get_doc(
			{
				"doctype": "Interview Session",
				"interview": interview.name,
				"job_application": candidate.name,
				"job_applicant": candidate.job_applicant,
				"status": "Invited",
			}
		)
		session.insert(ignore_permissions=True)
		invited += 1

		applicant = applicants.get(candidate.job_applicant)
		if applicant:
			try:
				_interview_invite_email(applicant.applicant_name, applicant.email_id, interview, job_title, candidate.name)
			except Exception as e:
				gdl_log_error(f"Interview invite email failed for {applicant.email_id}", exc=e)

	# Panelists only have something to act on in the Panel Portal under Panel
	# Self Entry - HR Proxy Entry panelists never log in for this interview,
	# and Compiled Scores has no panelists at all.
	if interview.score_entry_mode == "Panel Self Entry" and invited:
		for panel_row in interview.panel_members:
			user_email = frappe.db.get_value("User", panel_row.user, "email") or panel_row.user
			try:
				_panel_assignment_email(user_email, interview, job_title, invited)
			except Exception as e:
				gdl_log_error(f"Panel assignment email failed for {user_email}", exc=e)

	interview.status = "Published"
	interview.save()

	return success(data={"invited": invited}, message=f"Interview published. {invited} candidate(s) invited.")


@frappe.whitelist()
def get_interview_queue(job_opening):
	require_hr()

	interview = _get_active_interview(job_opening)
	if not interview or interview.status != "Published":
		return success(data={"interview": interview.as_dict() if interview else None, "sessions": []})

	sessions = frappe.get_all(
		"Interview Session",
		filters={"interview": interview.name},
		fields=["name", "job_application", "job_applicant", "status", "total_score", "scheduled_on", "attendance_response"],
		order_by="creation asc",
	)
	if not sessions:
		return success(data={"interview": interview.as_dict(), "sessions": []})

	applicants = {
		row.name: row
		for row in frappe.get_all(
			"Job Applicant",
			filters={"name": ["in", [s.job_applicant for s in sessions]]},
			fields=["name", "applicant_name", "email_id"],
		)
	}
	feedback_counts = {}
	for row in frappe.get_all(
		"Interview Panel Feedback",
		filters={"interview_session": ["in", [s.name for s in sessions]]},
		fields=["interview_session"],
	):
		feedback_counts[row.interview_session] = feedback_counts.get(row.interview_session, 0) + 1

	panel_count = len(interview.panel_members)
	rows = []
	for session in sessions:
		applicant = applicants.get(session.job_applicant, {})
		rows.append(
			{
				"name": session.name,
				"applicant_name": applicant.get("applicant_name"),
				"email_id": applicant.get("email_id"),
				"status": session.status,
				"total_score": session.total_score,
				"submitted_count": feedback_counts.get(session.name, 0),
				"panel_count": panel_count,
				"scheduled_on": session.scheduled_on,
				"attendance_response": session.attendance_response,
			}
		)

	return success(data={"interview": interview.as_dict(), "sessions": rows})


@frappe.whitelist(methods=["POST"])
def set_session_schedule(session, scheduled_on):
	"""Per-candidate interview time slot - overrides the Interview Schedule's
	shared scheduled_on for just this one candidate. Leave blank to fall back
	to the shared time again (gdl.api.applicant._interview_schedule_for and
	gdl.api.panel.get_interview_candidates both do `session.scheduled_on or
	interview.scheduled_on`)."""
	require_hr()

	session_doc = frappe.get_doc("Interview Session", session)
	session_doc.db_set("scheduled_on", scheduled_on or None)
	return success(message="Interview time updated.")


def _recompute_session_score(session_name):
	scores = frappe.get_all("Interview Panel Feedback", filters={"interview_session": session_name}, pluck="total_score")
	average = (sum(scores) / len(scores)) if scores else 0
	frappe.db.set_value("Interview Session", session_name, "total_score", average)


@frappe.whitelist(methods=["POST"])
def complete_session(session):
	require_hr()

	session_doc = frappe.get_doc("Interview Session", session)
	score_entry_mode = frappe.db.get_value("Interview Schedule", session_doc.interview, "score_entry_mode")
	# Compiled Scores has no Interview Panel Feedback rows to average -
	# recomputing here would overwrite the number HR already entered.
	if score_entry_mode != "Compiled Scores":
		_recompute_session_score(session)
	frappe.db.set_value("Interview Session", session, "status", "Completed")
	set_application_status(session_doc.job_application, "Interview Completed")
	return success(message="Session marked completed.")


@frappe.whitelist(methods=["POST"])
def set_compiled_score(session, score):
	require_hr()

	session_doc = frappe.get_doc("Interview Session", session)
	interview_doc = frappe.get_doc("Interview Schedule", session_doc.interview)
	if interview_doc.score_entry_mode != "Compiled Scores":
		gdl_error("This interview does not use Compiled Scores entry.")
	if session_doc.status != "Invited":
		gdl_error("This session is locked and can no longer be edited.")

	frappe.db.set_value("Interview Session", session, "total_score", flt(score))
	return success(message="Score saved.")


def _assigned_panel_member_or_error(interview_doc, panel_member):
	if not any(row.user == panel_member for row in interview_doc.panel_members):
		gdl_error("This user is not an assigned panel member for this interview.")


@frappe.whitelist()
def get_proxy_scorecard(session, panel_member):
	require_hr()

	session_doc = frappe.get_doc("Interview Session", session)
	interview_doc = frappe.get_doc("Interview Schedule", session_doc.interview)
	if interview_doc.score_entry_mode != "HR Proxy Entry":
		gdl_error("This interview does not use HR Proxy Entry.")
	_assigned_panel_member_or_error(interview_doc, panel_member)

	criteria = _criteria_for(interview_doc.name)
	existing_name = frappe.db.get_value(
		"Interview Panel Feedback", {"interview_session": session, "panel_member": panel_member}, "name"
	)
	existing_scores = []
	existing_overall_comments = None
	if existing_name:
		existing_scores = frappe.get_all(
			"Interview Feedback Criterion Score",
			filters={"parent": existing_name},
			fields=["criterion", "score_given", "comments"],
		)
		existing_overall_comments = frappe.db.get_value("Interview Panel Feedback", existing_name, "overall_comments")

	# Same two pieces of candidate context Panel Self Entry gets via
	# gdl.api.panel.get_scorecard/get_candidate_exam_result - HR entering
	# scores on a panelist's behalf needs the same profile/written-test
	# visibility the panelist would otherwise have seen themselves.
	documents = None
	if interview_doc.panel_can_view_documents:
		documents = frappe.db.get_value(
			"Job Applicant",
			session_doc.job_applicant,
			["resume_attachment", "gdl_national_id", "gdl_academic_certificate"],
			as_dict=True,
		)

	exam_result = get_exam_result_summary(session_doc.job_application) if interview_doc.panel_can_view_exam_result else None

	return success(
		data={
			"locked": session_doc.status == "Completed",
			"criteria": criteria,
			"existing_scores": existing_scores,
			"existing_overall_comments": existing_overall_comments,
			"documents": documents,
			"exam_result": exam_result,
		}
	)


@frappe.whitelist(methods=["POST"])
def save_proxy_scorecard(session, panel_member, criterion_scores, overall_comments=None):
	require_hr()

	session_doc = frappe.get_doc("Interview Session", session)
	interview_doc = frappe.get_doc("Interview Schedule", session_doc.interview)
	if interview_doc.score_entry_mode != "HR Proxy Entry":
		gdl_error("This interview does not use HR Proxy Entry.")
	_assigned_panel_member_or_error(interview_doc, panel_member)
	if session_doc.status == "Completed":
		gdl_error("This session is locked and can no longer be edited.")

	if isinstance(criterion_scores, str):
		criterion_scores = frappe.parse_json(criterion_scores)
	if not criterion_scores:
		gdl_error("Enter at least one score before saving.")

	existing_name = frappe.db.get_value(
		"Interview Panel Feedback", {"interview_session": session, "panel_member": panel_member}, "name"
	)
	if existing_name:
		feedback = frappe.get_doc("Interview Panel Feedback", existing_name)
		feedback.set("criterion_scores", [])
	else:
		feedback = frappe.get_doc(
			{"doctype": "Interview Panel Feedback", "interview_session": session, "panel_member": panel_member}
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

	feedback.flags.ignore_permissions = True
	if existing_name:
		feedback.save()
	else:
		feedback.insert()
		# insert() forces owner = the acting session user (HR here) - correct
		# it to the panelist being proxied for, same caveat documented
		# elsewhere in this app (e.g. Exam Attempt, Job Application).
		frappe.db.set_value("Interview Panel Feedback", feedback.name, "owner", panel_member)

	return success(data={"total_score": feedback.total_score}, message="Score saved.")


@frappe.whitelist(methods=["POST"])
def mark_not_attended(session):
	require_hr()

	session_doc = frappe.get_doc("Interview Session", session)
	frappe.db.set_value("Interview Session", session, "status", "Not Attended")
	set_application_status(session_doc.job_application, "Interview Not Attended")
	return success(message="Session marked not attended.")


@frappe.whitelist(methods=["POST"])
def unlock_session(session, reason):
	frappe.only_for("System Manager")

	session_doc = frappe.get_doc("Interview Session", session)
	if session_doc.status != "Completed":
		gdl_error("Only a completed session can be unlocked.")
	if not reason or not reason.strip():
		gdl_error("Enter a reason for unlocking this session.")

	frappe.db.set_value("Interview Session", session, "status", "Invited")
	# Reopen panelists' submitted scorecards too, otherwise unlocking the
	# session would leave every score still uneditable.
	for feedback_name in frappe.get_all("Interview Panel Feedback", filters={"interview_session": session}, pluck="name"):
		frappe.db.set_value("Interview Panel Feedback", feedback_name, {"is_submitted": 0, "submitted_on": None})

	log = frappe.get_doc(
		{
			"doctype": "Interview Unlock Log",
			"interview_session": session,
			"unlocked_by": frappe.session.user,
			"unlocked_on": now_datetime(),
			"reason": reason,
		}
	)
	log.insert(ignore_permissions=True)

	log_action(
		action="Interview session unlocked",
		reference_doctype="Interview Session",
		reference_name=session,
		details=reason,
	)

	return success(message="Session unlocked.")


@frappe.whitelist()
def get_unlock_log(session):
	require_hr()

	return success(
		data=frappe.get_all(
			"Interview Unlock Log",
			filters={"interview_session": session},
			fields=["unlocked_by", "unlocked_on", "reason"],
			order_by="unlocked_on desc",
		)
	)
