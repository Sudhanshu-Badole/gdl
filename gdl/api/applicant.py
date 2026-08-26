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

from gdl.api.response import success
from gdl.utils.completeness import COMPLETENESS_THRESHOLD
from gdl.utils.exceptions import gdl_error
from gdl.utils.logger import get_logger
from gdl.utils.notifications import send_email_or_log
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

	for fieldname in PERSONAL_INFO_FIELDS:
		if fieldname in fields:
			doc.set(fieldname, fields[fieldname])

	doc.save()
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


EDUCATION_FIELDS = ["qualification", "institution_name", "start_date", "completion_date", "grade_or_result"]


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

MANDATORY_DOCUMENT_FIELDS = {
	"cv": "resume_attachment",  # reuse the standard field, not a new gdl_ one
	"national_id": "gdl_national_id",
	"academic_certificate": "gdl_academic_certificate",
}
OPTIONAL_DOCUMENT_FIELDS = {
	"experience_letter": "gdl_experience_letter",
}


def _upload_document(fieldname):
	doc = _get_own_job_applicant()
	url = save_upload(doc, fieldname, DOCUMENT_EXTENSIONS, max_size_mb=5, is_private=1)
	logger.info(f"{fieldname} uploaded for {frappe.session.user}")
	return success(data={"file_url": url}, message="Document uploaded.")


@frappe.whitelist(methods=["POST"])
def upload_cv():
	return _upload_document(MANDATORY_DOCUMENT_FIELDS["cv"])


@frappe.whitelist(methods=["POST"])
def upload_national_id():
	return _upload_document(MANDATORY_DOCUMENT_FIELDS["national_id"])


@frappe.whitelist(methods=["POST"])
def upload_academic_certificate():
	return _upload_document(MANDATORY_DOCUMENT_FIELDS["academic_certificate"])


@frappe.whitelist(methods=["POST"])
def upload_experience_letter():
	return _upload_document(OPTIONAL_DOCUMENT_FIELDS["experience_letter"])


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

	documents = {
		"cv": bool(doc.resume_attachment),
		"national_id": bool(doc.gdl_national_id),
		"academic_certificate": bool(doc.gdl_academic_certificate),
		"experience_letter": bool(doc.gdl_experience_letter),
		"other": [
			{"name": d.name, "document_type": d.document_type, "attachment": d.attachment}
			for d in doc.gdl_other_documents
		],
	}

	return success(
		data={
			"applicant_name": doc.applicant_name,
			"profile_completeness": doc.gdl_profile_completeness or 0,
			"documents": documents,
			"applications": _get_applications_for(doc.name),
			"upcoming_exams": [],  # Phase 5
			"notifications": [],  # Phase 10
		}
	)


# Task 4.4 - Job application submission.

MANDATORY_DOCUMENT_LABELS = {
	"resume_attachment": "Curriculum Vitae (CV)",
	"gdl_national_id": "CID / National ID",
	"gdl_academic_certificate": "Academic Certificate",
}


def _missing_mandatory_documents(applicant_doc):
	return [
		label for fieldname, label in MANDATORY_DOCUMENT_LABELS.items() if not applicant_doc.get(fieldname)
	]


def _get_open_job_opening(job_opening_name):
	opening = frappe.db.get_value(
		"Job Opening",
		{"name": job_opening_name, "status": "Open", "publish": 1},
		["name", "job_title", "closes_on", "description"],
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
			# Honest empty states - Phases 5-9 will populate these once
			# exams/interviews/offers exist, same pattern as the Phase 3 dashboard.
			"exam_schedule": None,
			"interview_schedule": None,
			"scores": None,
			"offer": None,
		}
	)
