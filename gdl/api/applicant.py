"""Applicant portal API (Phase 3): profile (personal info, education,
employment, documents) and the dashboard data feed.

Every method here operates only on the logged-in user's own Job Applicant
record - looked up by email (Job Applicant.email_id == frappe.session.user,
the same convention used since Task 2.2's registration flow, since Job
Applicant has no direct Link-to-User field). No method accepts a Job
Applicant name/id from the caller for this reason: there would be no way to
tell "my own record" from "someone else's" if we did.
"""

import frappe

from gdl.api.hr_offer import _maybe_auto_issue_appointment_letter
from gdl.api.response import success
from gdl.utils.audit import set_application_status
from gdl.utils.completeness import COMPLETENESS_THRESHOLD
from gdl.utils.documents import DOCUMENT_KEYS, document_status_info, reset_document_status, tor_filename
from gdl.utils.eligibility import check_vacancy_eligibility
from gdl.utils.exam_scoring import finalize_attempt_grading
from gdl.utils.exceptions import gdl_error
from gdl.utils.logger import get_logger
from gdl.utils.notifications import notify_user, send_email_or_log
from gdl.utils.uploads import save_upload, save_upload_for_child_row

logger = get_logger("api.applicant")

PROFILE_PHOTO_EXTENSIONS = ["jpg", "jpeg", "png"]
DOCUMENT_EXTENSIONS = ["pdf", "jpg", "jpeg", "png", "docx"]


def _get_own_job_applicant():
	if frappe.session.user == "Guest":
		gdl_error("Please sign in first")

	# Prefer a record actually owned by the session user. email_id alone
	# isn't a safe-enough lookup on its own: a real duplicate-record bug hit
	# a live user once (two Job Applicant rows for one email, one orphaned
	# with owner="Guest" from a pre-fix registration) and this picked the
	# wrong one, causing every save to fail with a permission error even
	# though the user was genuinely logged in. Trying the owner-matched
	# record first makes this self-healing if duplicates ever reappear.
	name = frappe.db.get_value(
		"Job Applicant", {"email_id": frappe.session.user, "owner": frappe.session.user}
	)
	if not name:
		name = frappe.db.get_value("Job Applicant", {"email_id": frappe.session.user})
	if not name:
		gdl_error("No applicant profile found for this account")

	doc = frappe.get_doc("Job Applicant", name)
	# Belt and braces: the lookup above already scopes this to the caller's
	# own record, but also lean on the real if_owner Custom DocPerm grant
	# (setup_roles_permissions.py) rather than only our own lookup logic.
	doc.check_permission("read")
	return doc


@frappe.whitelist()
def get_profile():
	doc = _get_own_job_applicant()
	return success(data=doc.as_dict())


PERSONAL_INFO_FIELDS = [
	"gdl_date_of_birth",
	"gdl_gender",
	"gdl_nationality",
	"gdl_permanent_address",
	"gdl_current_address",
	"gdl_cid_number",
]


@frappe.whitelist(methods=["POST"])
def update_personal_info(**fields):
	doc = _get_own_job_applicant()

	cid_changed = "gdl_cid_number" in fields and fields["gdl_cid_number"] != doc.gdl_cid_number
	for fieldname in PERSONAL_INFO_FIELDS:
		if fieldname in fields:
			doc.set(fieldname, fields[fieldname])

	doc.save()
	# A changed CID invalidates any prior National ID verification - HR needs
	# to re-check the document against the new number (see
	# PersonalInfoSection.vue's warning copy, which promises exactly this).
	if cid_changed and doc.gdl_national_id:
		reset_document_status(doc, "national_id")
	logger.info(f"personal info updated for {frappe.session.user}")
	return success(data=doc.as_dict(), message="Personal information updated.")


@frappe.whitelist(methods=["POST"])
def upload_profile_photo():
	doc = _get_own_job_applicant()
	# Public (not private): just a display avatar, not a sensitive document -
	# contrast with Task 3.3's ID/certificate uploads, which are private.
	url = save_upload(doc, "gdl_profile_photo", PROFILE_PHOTO_EXTENSIONS, max_size_mb=2, is_private=0)
	logger.info(f"profile photo updated for {frappe.session.user}")
	return success(data={"file_url": url}, message="Profile photo updated.")


# Task 3.2 - Education & employment history: generic child-table CRUD, reused
# by both doctypes below rather than duplicated per-doctype.


def _add_child_row(fieldname, fields, allowed_fields):
	doc = _get_own_job_applicant()
	row = {k: v for k, v in fields.items() if k in allowed_fields}
	doc.append(fieldname, row)
	doc.save()
	return doc


def _find_child_row(doc, fieldname, row_name):
	for row in doc.get(fieldname):
		if row.name == row_name:
			return row
	gdl_error("Record not found")


def _update_child_row(fieldname, row_name, fields, allowed_fields):
	doc = _get_own_job_applicant()
	row = _find_child_row(doc, fieldname, row_name)
	for k, v in fields.items():
		if k in allowed_fields:
			row.set(k, v)
	doc.save()
	return doc


def _delete_child_row(fieldname, row_name):
	doc = _get_own_job_applicant()
	row = _find_child_row(doc, fieldname, row_name)
	doc.remove(row)
	doc.save()
	return doc


EDUCATION_FIELDS = ["qualification", "institution_name", "start_date", "completion_date", "grade_or_result", "score_percent"]


@frappe.whitelist(methods=["POST"])
def add_education(**fields):
	doc = _add_child_row("gdl_education", fields, EDUCATION_FIELDS)
	return success(data=doc.get("gdl_education"), message="Education record added.")


@frappe.whitelist(methods=["POST"])
def update_education(row_name, **fields):
	doc = _update_child_row("gdl_education", row_name, fields, EDUCATION_FIELDS)
	return success(data=doc.get("gdl_education"), message="Education record updated.")


@frappe.whitelist(methods=["POST"])
def delete_education(row_name):
	doc = _delete_child_row("gdl_education", row_name)
	return success(data=doc.get("gdl_education"), message="Education record deleted.")


EMPLOYMENT_FIELDS = [
	"company_name",
	"job_title",
	"start_date",
	"end_date",
	"currently_working",
	"responsibilities",
]


@frappe.whitelist(methods=["POST"])
def add_employment(**fields):
	doc = _add_child_row("gdl_employment_history", fields, EMPLOYMENT_FIELDS)
	return success(data=doc.get("gdl_employment_history"), message="Employment record added.")


@frappe.whitelist(methods=["POST"])
def update_employment(row_name, **fields):
	doc = _update_child_row("gdl_employment_history", row_name, fields, EMPLOYMENT_FIELDS)
	return success(data=doc.get("gdl_employment_history"), message="Employment record updated.")


@frappe.whitelist(methods=["POST"])
def delete_employment(row_name):
	doc = _delete_child_row("gdl_employment_history", row_name)
	return success(data=doc.get("gdl_employment_history"), message="Employment record deleted.")


# Task 3.3 - Document management. All uploads are private (is_private=1):
# these are CV/ID/certificate scans, not something to expose on a public URL -
# contrast with the public profile photo above. View/download reuses
# Frappe's own /private/files/... route, which checks read permission on the
# attached-to doc (Job Applicant) - the if_owner grant from Task 3.1 covers
# the applicant themselves; HR Officer's existing Job Applicant read grant
# (Task 1.3) covers HR access.

def _upload_document(document_key):
	fieldname = DOCUMENT_KEYS[document_key][0]
	doc = _get_own_job_applicant()
	url = save_upload(doc, fieldname, DOCUMENT_EXTENSIONS, max_size_mb=5, is_private=1)
	# Every (re)upload reverts any prior HR verification decision - a new file
	# needs a fresh look, it can't inherit the old file's Verified/Sent Back
	# status.
	reset_document_status(doc, document_key)
	logger.info(f"{fieldname} uploaded for {frappe.session.user}")
	return success(data={"file_url": url}, message="Document uploaded.")


@frappe.whitelist(methods=["POST"])
def upload_cv():
	return _upload_document("cv")


@frappe.whitelist(methods=["POST"])
def upload_national_id():
	return _upload_document("national_id")


@frappe.whitelist(methods=["POST"])
def upload_academic_certificate():
	return _upload_document("academic_certificate")


@frappe.whitelist(methods=["POST"])
def upload_experience_letter():
	return _upload_document("experience_letter")


@frappe.whitelist(methods=["POST"])
def upload_medical_certificate():
	return _upload_document("medical_certificate")


@frappe.whitelist(methods=["POST"])
def upload_security_clearance():
	return _upload_document("security_clearance")


@frappe.whitelist(methods=["POST"])
def add_other_document():
	doc = _get_own_job_applicant()
	document_type = (frappe.form_dict.get("document_type") or "Other Document").strip()
	url = save_upload_for_child_row(doc, DOCUMENT_EXTENSIONS, max_size_mb=5, is_private=1)
	doc.append("gdl_other_documents", {"document_type": document_type, "attachment": url})
	doc.save()
	logger.info(f"other document ({document_type}) added for {frappe.session.user}")
	return success(data=doc.get("gdl_other_documents"), message="Document added.")


@frappe.whitelist(methods=["POST"])
def delete_other_document(row_name):
	doc = _delete_child_row("gdl_other_documents", row_name)
	return success(data=doc.get("gdl_other_documents"), message="Document deleted.")


# Task 3.5 - Dashboard data feed. Exam/notifications are still empty for now
# - Examination and Notification doctypes don't exist until Phases 5/10.
# Applications are real (Job Application exists as of Task 4.0) - this was
# left hardcoded to [] when first written, before that doctype existed, and
# never wired up once Phase 4 landed. Fixed live after a real user hit it
# (dashboard said "No applications yet" despite a real submitted application).


@frappe.whitelist()
def get_dashboard_data():
	doc = _get_own_job_applicant()

	documents = {key: bool(doc.get(fieldname)) for key, (fieldname, _label, _mandatory) in DOCUMENT_KEYS.items()}
	documents["other"] = [
		{"name": d.name, "document_type": d.document_type, "attachment": d.attachment, "status": d.status}
		for d in doc.gdl_other_documents
	]
	# Verify/Sent Back/Verified status per fixed document key, plus any HR
	# remark on a Sent Back document - so the applicant sees what to fix.
	document_status_map = {key: document_status_info(doc, key) for key in DOCUMENT_KEYS}

	return success(
		data={
			"applicant_name": doc.applicant_name,
			"profile_completeness": doc.gdl_profile_completeness or 0,
			"documents": documents,
			"document_status": document_status_map,
			"applications": _get_applications_for(doc.name),
			"upcoming_exams": [],  # Phase 5
			"notifications": [],  # Phase 10
		}
	)


# Task 4.4 - Job application submission.


def _missing_mandatory_documents(applicant_doc):
	return [
		label
		for fieldname, label, mandatory in DOCUMENT_KEYS.values()
		if mandatory and not applicant_doc.get(fieldname)
	]


def _get_open_job_opening(job_opening_name):
	opening = frappe.db.get_value(
		"Job Opening",
		{"name": job_opening_name, "status": "Open", "publish": 1},
		[
			"name",
			"job_title",
			"closes_on",
			"description",
			"gdl_job_type",
			"gdl_min_experience_years",
			"gdl_degree_required",
			"gdl_min_degree_score",
			"gdl_experienced_vacancy",
		],
		as_dict=True,
	)
	if not opening:
		gdl_error("This vacancy is not open for applications.")
	if opening.closes_on and opening.closes_on < frappe.utils.getdate():
		gdl_error("The application deadline for this vacancy has passed.")
	return opening


def _has_existing_application(job_applicant_name, job_opening_name):
	"""Always block a second application to the same vacancy from the same
	applicant - regardless of Job Opening's standard `prevent_duplicate_applicant`
	checkbox (which defaults off and is really HRMS's own, opt-in, concept for
	its native Job Applicant-per-application model). There's no legitimate
	workflow in this spec for re-applying to the exact same vacancy, so this
	isn't something we leave to per-vacancy HR configuration.
	"""
	return frappe.db.exists(
		"Job Application", {"job_applicant": job_applicant_name, "job_opening": job_opening_name}
	)


def _send_application_confirmation_email(applicant_doc, opening, reference_number):
	send_email_or_log(
		recipients=[applicant_doc.email_id],
		subject=f"Application received - {opening.job_title}",
		message=f"""
			<p>Hi {frappe.utils.escape_html(applicant_doc.applicant_name)},</p>
			<p>We've received your application for <strong>{frappe.utils.escape_html(opening.job_title)}</strong>.</p>
			<p>Your reference number is <strong>{reference_number}</strong>. You can track your application status
			from your <a href="{frappe.utils.get_url("/applications")}">My Applications</a> page.</p>
		""",
		log_fallback=f"application confirmation for {applicant_doc.email_id}, reference {reference_number}",
	)


@frappe.whitelist()
def get_apply_context(job_opening):
	"""Data for the /apply/new page: vacancy summary, profile snapshot,
	and whether the applicant is actually eligible to submit right now."""
	applicant_doc = _get_own_job_applicant()
	opening = _get_open_job_opening(job_opening)

	blockers = []
	completeness = applicant_doc.gdl_profile_completeness or 0
	if completeness < COMPLETENESS_THRESHOLD:
		blockers.append(
			f"Your profile is only {completeness}% complete. At least {COMPLETENESS_THRESHOLD}% is required before you can apply."
		)
	missing_docs = _missing_mandatory_documents(applicant_doc)
	if missing_docs:
		blockers.append("Missing required document(s): " + ", ".join(missing_docs))
	if _has_existing_application(applicant_doc.name, opening.name):
		blockers.append("You have already applied to this vacancy.")
	blockers.extend(check_vacancy_eligibility(applicant_doc, opening))

	return success(
		data={
			"job_opening": opening,
			"applicant": applicant_doc.as_dict(),
			"can_apply": not blockers,
			"blockers": blockers,
		}
	)


@frappe.whitelist(methods=["POST"])
def submit_application(job_opening, cover_letter=None):
	applicant_doc = _get_own_job_applicant()
	opening = _get_open_job_opening(job_opening)

	if (applicant_doc.gdl_profile_completeness or 0) < COMPLETENESS_THRESHOLD:
		gdl_error(f"Your profile must be at least {COMPLETENESS_THRESHOLD}% complete before you can apply.")
	if _missing_mandatory_documents(applicant_doc):
		gdl_error("Please upload all required documents before applying.")
	if _has_existing_application(applicant_doc.name, opening.name):
		gdl_error("You have already applied to this vacancy.")
	eligibility_blockers = check_vacancy_eligibility(applicant_doc, opening)
	if eligibility_blockers:
		gdl_error(" ".join(eligibility_blockers))

	application = frappe.get_doc(
		{
			"doctype": "Job Application",
			"job_applicant": applicant_doc.name,
			"job_opening": opening.name,
			"cover_letter": cover_letter,
			"status": "Submitted",
		}
	)
	application.flags.ignore_permissions = True
	application.insert()
	# Same fix as gdl.api.public.register_applicant(): insert() always forces
	# owner = the acting session user, not something we can set beforehand.
	frappe.db.set_value("Job Application", application.name, "owner", frappe.session.user)

	_send_application_confirmation_email(applicant_doc, opening, application.name)
	notify_user(
		applicant_doc.owner,
		subject=f"Application received - {opening.job_title}",
		document_type="Job Application",
		document_name=application.name,
		link=f"/applications/{application.name}",
	)
	logger.info(f"application {application.name} submitted by {frappe.session.user} for {opening.name}")

	return success(
		data={"reference_number": application.name, "redirect_to": "/applications"},
		message=f"Application submitted. Your reference number is {application.name}.",
	)


# Task 4.5 - My Applications + details page.


def _get_applications_for(applicant_name):
	applications = frappe.get_all(
		"Job Application",
		filters={"job_applicant": applicant_name},
		fields=["name", "job_opening", "status", "creation"],
		order_by="creation desc",
	)
	for app in applications:
		app.job_title = frappe.db.get_value("Job Opening", app.job_opening, "job_title")
	return applications


@frappe.whitelist()
def get_my_applications():
	applicant_doc = _get_own_job_applicant()
	return success(data=_get_applications_for(applicant_doc.name))


@frappe.whitelist()
def get_application_detail(name):
	applicant_doc = _get_own_job_applicant()
	application = frappe.get_doc("Job Application", name)
	application.check_permission("read")
	if application.job_applicant != applicant_doc.name:
		gdl_error("Application not found.")

	job_opening = frappe.db.get_value(
		"Job Opening", application.job_opening, ["job_title", "description"], as_dict=True
	)

	return success(
		data={
			"application": application.as_dict(),
			"job_opening": job_opening,
			"exam_schedule": _exam_schedule_for(application),
			"interview_schedule": _interview_schedule_for(application),
			"offer": _offer_for(application),
			"terms_of_reference": _terms_of_reference_for(application),
			# Honest empty state - Phase 9 dashboard/report work will populate
			# this once there's an aggregate score view to show.
			"scores": None,
		}
	)


# Statuses before an applicant has been Shortlisted - TOR stays hidden here
# (client feedback, Phase 3: "TOR should be made available if the applicant
# is shortlisted"). Once Shortlisted it stays visible for the rest of the
# application's life, including terminal statuses like Rejected/Offer
# Declined - simplest reading, no re-hiding logic needed.
PRE_SHORTLIST_STATUSES = {"Submitted", "Under Review", "Review on Hold", "Not Shortlisted"}


def _terms_of_reference_for(application):
	if application.status in PRE_SHORTLIST_STATUSES:
		return None

	file_url = frappe.db.get_value("Job Opening", application.job_opening, "gdl_terms_of_reference")
	if not file_url:
		return None
	return {"file_url": file_url, "filename": tor_filename(file_url)}


def _offer_for(application):
	"""None until a Job Offer exists for this application. Status/response
	fields mirror gdl.api.hr_offer's Job Offer shape."""
	offer = frappe.db.get_value(
		"Job Offer",
		{"gdl_job_application": application.name, "docstatus": ["!=", 2]},
		["name", "designation", "gdl_salary", "gdl_joining_date", "gdl_response_deadline", "status"],
		as_dict=True,
		order_by="creation desc",
	)
	if not offer:
		return None

	appointment_letter = frappe.db.get_value("Appointment Letter", {"gdl_job_offer": offer.name}, "name")
	return {
		"job_offer": offer.name,
		"designation": offer.designation,
		"salary": offer.gdl_salary,
		"joining_date": offer.gdl_joining_date,
		"response_deadline": offer.gdl_response_deadline,
		"status": offer.status,
		"appointment_letter": appointment_letter,
	}


@frappe.whitelist(methods=["POST"])
def respond_to_offer(job_offer, response):
	"""Applicant's own self-service accept/decline - counterpart to
	gdl.api.hr_offer.record_offer_response (the HR-proxy path). Appointment
	letter generation stays a separate explicit HR action unless
	Recruitment Settings.auto_issue_appointment_letter is on (Phase 9)."""
	if response not in ("Accepted", "Rejected"):
		gdl_error("Response must be Accepted or Rejected.")

	applicant_doc = _get_own_job_applicant()
	offer = frappe.get_doc("Job Offer", job_offer)
	if offer.job_applicant != applicant_doc.name:
		gdl_error("Offer not found.")
	if offer.status == "Expired":
		gdl_error("This offer has expired and can no longer be responded to.")
	if offer.status != "Awaiting Response":
		gdl_error("This offer has already been responded to.")

	offer.db_set("status", response)
	offer.db_set("gdl_responded_on", frappe.utils.now_datetime())

	application_status = "Offer Accepted" if response == "Accepted" else "Offer Declined"
	set_application_status(offer.gdl_job_application, application_status)

	if response == "Accepted":
		_maybe_auto_issue_appointment_letter(offer)

	return success(message=f"You have {response.lower()} the offer.")


def _exam_schedule_for(application):
	"""None until an Exam Attempt exists for this application (i.e. an exam
	has actually been published for the vacancy and this applicant invited).
	Score/pass-fail are withheld unless the vacancy owner opted into
	publishing them (gdl_publish_exam_scores) and grading is complete."""
	attempt = frappe.db.get_value(
		"Exam Attempt",
		{"job_application": application.name},
		["name", "exam", "status", "total_score", "is_pass", "is_fully_graded", "attendance_response"],
		as_dict=True,
		order_by="creation desc",
	)
	if not attempt:
		return None

	exam = frappe.db.get_value("Exam", attempt.exam, ["title", "opens_on", "closes_on"], as_dict=True)
	publish_scores = frappe.db.get_value("Job Opening", application.job_opening, "gdl_publish_exam_scores")
	show_score = bool(publish_scores) and bool(attempt.is_fully_graded)

	return {
		"attempt": attempt.name,
		"exam_title": exam.title,
		"opens_on": exam.opens_on,
		"closes_on": exam.closes_on,
		"status": attempt.status,
		"total_score": attempt.total_score if show_score else None,
		"is_pass": attempt.is_pass if show_score else None,
		"attendance_response": attempt.attendance_response,
	}


def _interview_schedule_for(application):
	"""None until an Interview Session exists for this application. Score is
	withheld unless the vacancy owner opted into publishing it
	(gdl_publish_interview_scores) and the session is Completed - same gating
	shape as _exam_schedule_for's gdl_publish_exam_scores/is_fully_graded."""
	session = frappe.db.get_value(
		"Interview Session",
		{"job_application": application.name},
		["name", "interview", "status", "total_score", "scheduled_on", "attendance_response"],
		as_dict=True,
		order_by="creation desc",
	)
	if not session:
		return None

	interview = frappe.db.get_value(
		"Interview Schedule", session.interview, ["title", "scheduled_on", "venue_or_link", "gdl_location_map_link"], as_dict=True
	)
	publish_scores = frappe.db.get_value("Job Opening", application.job_opening, "gdl_publish_interview_scores")
	show_score = bool(publish_scores) and session.status == "Completed"

	return {
		"session": session.name,
		"interview_title": interview.title,
		# Per-candidate slot when HR has set one, else the shared schedule time.
		"scheduled_on": session.scheduled_on or interview.scheduled_on,
		"venue_or_link": interview.venue_or_link,
		"location_map_link": interview.gdl_location_map_link,
		"status": session.status,
		"total_score": session.total_score if show_score else None,
		"attendance_response": session.attendance_response,
	}


# Phase 6 - Examination (online exam core). Every method below re-checks
# ownership via _get_own_attempt (job_applicant on the attempt must match the
# caller's own Job Applicant), same convention as _get_own_job_applicant used
# throughout this file.


def _get_own_attempt(name):
	applicant_doc = _get_own_job_applicant()
	attempt = frappe.get_doc("Exam Attempt", name)
	if attempt.job_applicant != applicant_doc.name:
		gdl_error("Test not found.")
	return attempt


def _check_exam_window(attempt, exam):
	"""Only enforced for an attempt still Invited/In Progress - a Submitted
	(or already Not Attended) attempt must stay viewable after the window
	closes, e.g. from the applicant revisiting the link on their application
	detail page, so this is a no-op for those terminal statuses."""
	if attempt.status not in ("Invited", "In Progress"):
		return

	now = frappe.utils.now_datetime()
	if now < exam.opens_on:
		gdl_error("This test has not opened yet.")
	if now > exam.closes_on:
		frappe.db.set_value("Exam Attempt", attempt.name, "status", "Not Attended")
		set_application_status(attempt.job_application, "Exam Not Attended")
		gdl_error("The test window has closed.")


@frappe.whitelist(methods=["POST"])
def confirm_exam_attendance(attempt, response):
	"""Purely informational - does not drive Exam Attempt.status or the
	Job Application pipeline (HR still marks absence via
	gdl.api.hr_exam.close_and_mark_absent). Lets HR see ahead of time who
	plans to attend, same accept/decline shape as respond_to_offer()."""
	if response not in ("Confirmed", "Declined"):
		gdl_error("Response must be Confirmed or Declined.")

	attempt_doc = _get_own_attempt(attempt)
	attempt_doc.db_set("attendance_response", response)
	attempt_doc.db_set("attendance_responded_on", frappe.utils.now_datetime())
	return success(message=f"You have {response.lower()} attendance for this test.")


def _get_own_interview_session(name):
	applicant_doc = _get_own_job_applicant()
	session = frappe.get_doc("Interview Session", name)
	if session.job_applicant != applicant_doc.name:
		gdl_error("Interview not found.")
	return session


@frappe.whitelist(methods=["POST"])
def confirm_interview_attendance(session, response):
	"""Same informational-only shape as confirm_exam_attendance - HR still
	marks absence via gdl.api.hr_interview.mark_not_attended."""
	if response not in ("Confirmed", "Declined"):
		gdl_error("Response must be Confirmed or Declined.")

	session_doc = _get_own_interview_session(session)
	session_doc.db_set("attendance_response", response)
	session_doc.db_set("attendance_responded_on", frappe.utils.now_datetime())
	return success(message=f"You have {response.lower()} attendance for this interview.")


@frappe.whitelist()
def get_active_exam():
	"""Dashboard banner data: the caller's own Exam Attempt (not yet
	submitted) whose exam window is currently open, if any."""
	applicant_doc = _get_own_job_applicant()
	attempts = frappe.get_all(
		"Exam Attempt",
		filters={"job_applicant": applicant_doc.name, "status": ["in", ["Invited", "In Progress"]]},
		fields=["name", "exam", "job_application"],
	)
	now = frappe.utils.now_datetime()
	for attempt in attempts:
		exam = frappe.db.get_value(
			"Exam", attempt.exam, ["title", "opens_on", "closes_on"], as_dict=True
		)
		if exam and exam.opens_on <= now <= exam.closes_on:
			job_opening = frappe.db.get_value("Job Application", attempt.job_application, "job_opening")
			return success(
				data={
					"attempt": attempt.name,
					"exam_title": exam.title,
					"job_title": frappe.db.get_value("Job Opening", job_opening, "job_title"),
					"opens_on": exam.opens_on,
					"closes_on": exam.closes_on,
				}
			)
	return success(data=None)


@frappe.whitelist(methods=["POST"])
def start_exam_attempt(name):
	attempt = _get_own_attempt(name)
	exam = frappe.get_doc("Exam", attempt.exam)
	_check_exam_window(attempt, exam)

	if attempt.status == "Invited":
		attempt.db_set("status", "In Progress")
		attempt.db_set("started_on", frappe.utils.now_datetime())
	elif attempt.status != "In Progress":
		gdl_error("This test can no longer be started.")

	return success(data={"status": "In Progress"})


@frappe.whitelist()
def get_exam_attempt(name):
	attempt = _get_own_attempt(name)
	exam = frappe.get_doc("Exam", attempt.exam)
	_check_exam_window(attempt, exam)

	questions = frappe.get_all(
		"Exam Question",
		filters={"exam": exam.name},
		fields=[
			"name",
			"sequence",
			"question_type",
			"question_text",
			"option_a",
			"option_b",
			"option_c",
			"option_d",
			"marks",
		],
		order_by="sequence asc, creation asc",
	)
	question_count = len(questions)
	if attempt.status != "In Progress":
		# Don't leak question content before the applicant has started the timer.
		questions = []
	saved_answers = {
		row.question: row
		for row in frappe.get_all(
			"Exam Attempt Answer",
			filters={"parent": name},
			fields=["question", "selected_option", "short_answer_text"],
		)
	}
	job_opening = frappe.db.get_value("Job Application", attempt.job_application, "job_opening")
	max_violations = frappe.db.get_single_value("Recruitment Settings", "max_exam_violations_before_autosubmit")

	return success(
		data={
			"attempt": {
				"name": attempt.name,
				"status": attempt.status,
				"started_on": attempt.started_on,
				"violation_count": len(attempt.violations),
			},
			"job_title": frappe.db.get_value("Job Opening", job_opening, "job_title"),
			"exam": {
				"title": exam.title,
				"instructions": exam.instructions,
				"duration_minutes": exam.duration_minutes,
				"opens_on": exam.opens_on,
				"closes_on": exam.closes_on,
			},
			"question_count": question_count,
			"questions": [{**q, "answer": saved_answers.get(q.name)} for q in questions],
			"max_violations": max_violations or 0,
		}
	)


@frappe.whitelist(methods=["POST"])
def log_exam_violation(attempt, event_type):
	"""Fullscreen-exit/tab-switch detection is inherently best-effort (the
	client can't truly prevent OS-level app-switching) - this just builds an
	audit trail for HR and returns whether the caller should auto-submit now
	that the violation count crossed Recruitment Settings' threshold. See
	frontend/src/views/applicant/ExamAttempt.vue for the detection side."""
	if event_type not in ("Fullscreen Exit", "Tab Switch / Window Blur"):
		gdl_error("Invalid violation event type.")

	attempt_doc = _get_own_attempt(attempt)
	if attempt_doc.status != "In Progress":
		return success(data={"violation_count": len(attempt_doc.violations), "should_auto_submit": False})

	attempt_doc.append("violations", {"event_type": event_type, "occurred_on": frappe.utils.now_datetime()})
	attempt_doc.save(ignore_permissions=True)

	max_violations = frappe.utils.cint(frappe.db.get_single_value("Recruitment Settings", "max_exam_violations_before_autosubmit"))
	violation_count = len(attempt_doc.violations)
	should_auto_submit = bool(max_violations) and violation_count >= max_violations
	return success(data={"violation_count": violation_count, "should_auto_submit": should_auto_submit})


@frappe.whitelist(methods=["POST"])
def save_exam_answer(attempt, question, selected_option=None, short_answer_text=None):
	attempt_doc = _get_own_attempt(attempt)
	if attempt_doc.status != "In Progress":
		gdl_error("This test is not in progress.")
	exam = frappe.get_doc("Exam", attempt_doc.exam)
	_check_exam_window(attempt_doc, exam)
	if not frappe.db.exists("Exam Question", {"name": question, "exam": attempt_doc.exam}):
		gdl_error("Invalid question for this test.")

	# Direct child-row insert/update (parent/parenttype/parentfield set by
	# hand) rather than loading + re-saving the whole Exam Attempt on every
	# keystroke's autosave - cheaper, and avoids concurrent autosave calls
	# clobbering each other's writes to other questions.
	row_name = frappe.db.get_value("Exam Attempt Answer", {"parent": attempt, "question": question}, "name")
	if row_name:
		answer = frappe.get_doc("Exam Attempt Answer", row_name)
		answer.selected_option = selected_option
		answer.short_answer_text = short_answer_text
		answer.save(ignore_permissions=True)
	else:
		frappe.get_doc(
			{
				"doctype": "Exam Attempt Answer",
				"parent": attempt,
				"parenttype": "Exam Attempt",
				"parentfield": "answers",
				"question": question,
				"selected_option": selected_option,
				"short_answer_text": short_answer_text,
			}
		).insert(ignore_permissions=True)

	return success(message="Saved.")


@frappe.whitelist(methods=["POST"])
def submit_exam_attempt(name):
	attempt = _get_own_attempt(name)
	if attempt.status != "In Progress":
		gdl_error("This test is not in progress.")
	exam = frappe.get_doc("Exam", attempt.exam)
	_check_exam_window(attempt, exam)

	questions = frappe.get_all(
		"Exam Question", filters={"exam": attempt.exam}, fields=["name", "question_type", "correct_option", "marks"]
	)
	question_by_name = {q.name: q for q in questions}

	existing_rows = frappe.get_all(
		"Exam Attempt Answer", filters={"parent": name}, fields=["name", "question", "selected_option"]
	)
	answered_questions = {row.question for row in existing_rows}

	for row in existing_rows:
		question = question_by_name.get(row.question)
		if not question or question.question_type == "Short Answer":
			continue
		is_correct = row.selected_option == question.correct_option
		frappe.db.set_value(
			"Exam Attempt Answer",
			row.name,
			{
				"is_correct": 1 if is_correct else 0,
				"score_given": question.marks if is_correct else 0,
				"is_graded": 1,
			},
		)

	# A question the applicant left completely blank still needs a row -
	# Short Answer so grading (and is_fully_graded) sees it as pending
	# rather than silently skipped, Multiple Choice/True-or-False so it's
	# scored 0 like any other wrong answer instead of just missing.
	for question in questions:
		if question.name in answered_questions:
			continue
		if question.question_type == "Short Answer":
			row = {
				"doctype": "Exam Attempt Answer",
				"parent": name,
				"parenttype": "Exam Attempt",
				"parentfield": "answers",
				"question": question.name,
				"short_answer_text": "",
			}
		else:
			row = {
				"doctype": "Exam Attempt Answer",
				"parent": name,
				"parenttype": "Exam Attempt",
				"parentfield": "answers",
				"question": question.name,
				"is_correct": 0,
				"score_given": 0,
				"is_graded": 1,
			}
		frappe.get_doc(row).insert(ignore_permissions=True)

	attempt.db_set("status", "Submitted")
	attempt.db_set("submitted_on", frappe.utils.now_datetime())
	attempt.reload()
	finalize_attempt_grading(attempt)

	return success(message="Test submitted.")
