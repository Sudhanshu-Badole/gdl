"""Offer & Appointment (Phase 8). Reuses HRMS's native Job Offer / Appointment
Letter doctypes (extended with gdl_ Custom Fields), the same pattern already
used for Job Applicant/Job Opening - see gdl.setup_custom_fields for the
added fields. PDF rendering uses Frappe's own "Standard" print format
(frappe.utils.print_utils.get_print) since no custom letter template has
been supplied yet.
"""

import frappe
from frappe.utils import add_days, get_url, today
from frappe.utils.print_utils import get_print

from gdl.api.hr import require_hr
from gdl.api.response import success
from gdl.utils.audit import set_application_status
from gdl.utils.exceptions import gdl_error, gdl_log_error
from gdl.utils.notifications import notify_user, send_email_or_log

RESPONSE_WINDOW_DAYS_FALLBACK = 5


def _response_window_days():
	"""Recruitment Settings.offer_response_window_days, falling back to the
	clarification doc's 5-day default if the setting is unset."""
	return frappe.db.get_single_value("Recruitment Settings", "offer_response_window_days") or RESPONSE_WINDOW_DAYS_FALLBACK


def _pdf_attachment(doctype, name, filename):
	pdf = get_print(doctype, name, as_pdf=True)
	return [{"fname": filename, "fcontent": pdf}]


DEFAULT_APPOINTMENT_TEMPLATE_NAME = "GDL Standard"


def _get_default_appointment_letter_template():
	"""Get-or-create a minimal Appointment Letter Template so
	generate_appointment_letter has content to satisfy the native doctype's
	mandatory introduction/terms fields. HR can edit this record's wording in
	Desk at any time (e.g. once the client's real templates arrive) without
	any code change - this is a content record, not a code default."""
	if frappe.db.exists("Appointment Letter Template", DEFAULT_APPOINTMENT_TEMPLATE_NAME):
		return frappe.get_doc("Appointment Letter Template", DEFAULT_APPOINTMENT_TEMPLATE_NAME)

	template = frappe.get_doc(
		{
			"doctype": "Appointment Letter Template",
			"template_name": DEFAULT_APPOINTMENT_TEMPLATE_NAME,
			"introduction": "We are pleased to confirm your appointment. Please find the details of your appointment below.",
			"closing_notes": "We look forward to having you on our team.",
			"terms": [{"title": "Reporting", "description": "You are required to report for duty on the joining date specified above."}],
		}
	)
	template.insert(ignore_permissions=True)
	return template


@frappe.whitelist(methods=["POST"])
def create_offer(
	job_application,
	designation,
	company,
	joining_date,
	reporting_manager=None,
	department=None,
	response_deadline=None,
	salary=None,
):
	require_hr()

	application = frappe.get_doc("Job Application", job_application)
	if application.status != "Selected":
		gdl_error("Only a Selected candidate can be sent an offer.")
	if frappe.db.exists("Job Offer", {"gdl_job_application": job_application, "docstatus": ["!=", 2]}):
		gdl_error("An offer already exists for this application.")
	# Job Offer is a native HRMS doctype whose own validate() enforces at most
	# one non-cancelled offer per Job Applicant *globally*, not per
	# application/vacancy - surface that as a clear error here rather than
	# letting HRMS's raw ValidationError bubble up from insert() below.
	other_offer = frappe.db.exists("Job Offer", {"job_applicant": application.job_applicant, "docstatus": ["!=", 2]})
	if other_offer:
		gdl_error("This candidate already has an active offer for another application. Cancel or resolve that one first.")

	applicant = frappe.get_doc("Job Applicant", application.job_applicant)
	offer = frappe.get_doc(
		{
			"doctype": "Job Offer",
			"job_applicant": applicant.name,
			"applicant_name": applicant.applicant_name,
			"applicant_email": applicant.email_id,
			"offer_date": today(),
			"designation": designation,
			"company": company,
			"status": "Awaiting Response",
			"gdl_job_application": job_application,
			"gdl_joining_date": joining_date,
			"gdl_reporting_manager": reporting_manager,
			"gdl_department": department,
			"gdl_response_deadline": response_deadline or add_days(today(), _response_window_days()),
			"gdl_salary": salary,
		}
	)
	offer.flags.ignore_permissions = True
	offer.insert()
	offer.submit()
	# insert()/submit() force owner = the acting HR user - correct it to the
	# candidate so the if_owner portal grant actually scopes to them, same
	# caveat documented elsewhere in this app (Exam Attempt, Interview Panel
	# Feedback under Proxy Entry).
	frappe.db.set_value("Job Offer", offer.name, "owner", applicant.owner)

	set_application_status(application.name, "Offer Sent")

	link = get_url(f"/applications/{job_application}")
	message = f"""
		<p>Hi {frappe.utils.escape_html(applicant.applicant_name)},</p>
		<p>You've been offered the position of <strong>{frappe.utils.escape_html(designation)}</strong>.</p>
		<p>Please accept or decline this offer through the recruitment portal: <a href="{link}">{link}</a></p>
	"""
	try:
		send_email_or_log(
			recipients=[applicant.email_id],
			subject=f"Job offer - {designation}",
			message=message,
			log_fallback=f"offer email for {applicant.email_id}, offer {offer.name}",
		)
	except Exception as e:
		gdl_log_error(f"Offer email failed for {applicant.email_id}", exc=e)

	notify_user(
		applicant.email_id,
		subject=f"Job offer - {designation}",
		document_type="Job Offer",
		document_name=offer.name,
		link=f"/applications/{job_application}",
	)

	return success(data=offer.as_dict(), message="Offer created and sent.")


LETTERS_STATUSES = ["Selected", "Offer Sent", "Offer Accepted", "Offer Declined", "Offer Expired", "Appointed"]


@frappe.whitelist()
def get_letters_queue(job_opening):
	"""Batched queue for the Letters tab - every candidate from Selected
	onward, with their offer/appointment-letter state, in one round trip
	(same shape as gdl.api.hr_exam.get_exam_queue / hr_interview.get_interview_queue)."""
	require_hr()

	applications = frappe.get_all(
		"Job Application",
		filters={"job_opening": job_opening, "status": ["in", LETTERS_STATUSES]},
		fields=["name", "job_applicant", "status"],
		order_by="creation asc",
	)
	if not applications:
		return success(data=[])

	app_names = [a.name for a in applications]
	applicants = {
		row.name: row
		for row in frappe.get_all(
			"Job Applicant", filters={"name": ["in", [a.job_applicant for a in applications]]}, fields=["name", "applicant_name", "email_id"]
		)
	}
	offers = {
		row.gdl_job_application: row
		for row in frappe.get_all(
			"Job Offer",
			filters={"gdl_job_application": ["in", app_names], "docstatus": ["!=", 2]},
			fields=["name", "gdl_job_application", "designation", "gdl_salary", "gdl_joining_date", "gdl_response_deadline", "status"],
		)
	}
	appointments = {
		row.gdl_job_offer: row.name
		for row in frappe.get_all("Appointment Letter", filters={"gdl_job_offer": ["in", [o.name for o in offers.values()]]}, fields=["name", "gdl_job_offer"])
	}

	rows = []
	for app in applications:
		applicant = applicants.get(app.job_applicant, {})
		offer = offers.get(app.name)
		rows.append(
			{
				"job_application": app.name,
				"applicant_name": applicant.get("applicant_name"),
				"email_id": applicant.get("email_id"),
				"status": app.status,
				"offer": offer,
				"appointment_letter": appointments.get(offer.name) if offer else None,
			}
		)
	return success(data=rows)


@frappe.whitelist()
def get_offer(job_application):
	require_hr()

	offer = frappe.db.get_value(
		"Job Offer",
		{"gdl_job_application": job_application, "docstatus": ["!=", 2]},
		["*"],
		as_dict=True,
		order_by="creation desc",
	)
	if not offer:
		return success(data=None)

	appointment = frappe.db.get_value(
		"Appointment Letter", {"gdl_job_offer": offer.name}, ["name", "appointment_date"], as_dict=True
	)
	return success(data={"offer": offer, "appointment_letter": appointment})


@frappe.whitelist(methods=["POST"])
def record_offer_response(job_offer, response, reason=None):
	require_hr()

	if response not in ("Accepted", "Rejected"):
		gdl_error("Response must be Accepted or Rejected.")

	offer = frappe.get_doc("Job Offer", job_offer)
	if offer.status == "Expired":
		gdl_error("This offer has expired and can no longer be responded to.")
	if offer.status != "Awaiting Response":
		gdl_error("This offer has already been responded to.")

	offer.db_set("status", response)
	offer.db_set("gdl_responded_on", frappe.utils.now_datetime())
	offer.db_set("gdl_response_recorded_by", frappe.session.user)

	application_status = "Offer Accepted" if response == "Accepted" else "Offer Declined"
	set_application_status(offer.gdl_job_application, application_status)

	if response == "Accepted":
		_maybe_auto_issue_appointment_letter(offer)

	return success(message=f"Response recorded: {response}.")


@frappe.whitelist(methods=["POST"])
def generate_appointment_letter(job_offer):
	require_hr()

	offer = frappe.get_doc("Job Offer", job_offer)
	if offer.status != "Accepted":
		gdl_error("An appointment letter can only be generated once the offer is Accepted.")
	if frappe.db.exists("Appointment Letter", {"gdl_job_offer": job_offer}):
		gdl_error("An appointment letter already exists for this offer.")

	letter = _generate_appointment_letter_for(offer)
	return success(data=letter.as_dict(), message="Appointment letter generated and sent.")


def _maybe_auto_issue_appointment_letter(offer):
	"""Called right after an offer is accepted (HR-proxy or applicant
	self-service) - if Recruitment Settings.auto_issue_appointment_letter is
	on, generate the appointment letter immediately instead of waiting for a
	separate explicit HR action. Silently does nothing if a letter already
	exists or the setting is off - this is a convenience trigger, never the
	only path to generating a letter."""
	if not frappe.db.get_single_value("Recruitment Settings", "auto_issue_appointment_letter"):
		return
	if frappe.db.exists("Appointment Letter", {"gdl_job_offer": offer.name}):
		return
	_generate_appointment_letter_for(offer)


def _generate_appointment_letter_for(offer):
	applicant = frappe.get_doc("Job Applicant", offer.job_applicant)
	template = _get_default_appointment_letter_template()
	letter = frappe.get_doc(
		{
			"doctype": "Appointment Letter",
			"job_applicant": applicant.name,
			"applicant_name": applicant.applicant_name,
			"appointment_date": offer.gdl_joining_date,
			"company": offer.company,
			"appointment_letter_template": template.name,
			"introduction": template.introduction,
			"closing_notes": template.closing_notes,
			"terms": [{"title": row.title, "description": row.description} for row in template.terms],
			"gdl_job_application": offer.gdl_job_application,
			"gdl_job_offer": offer.name,
		}
	)
	letter.flags.ignore_permissions = True
	letter.insert()
	frappe.db.set_value("Appointment Letter", letter.name, "owner", applicant.owner)

	set_application_status(offer.gdl_job_application, "Appointed")

	dashboard_link = get_url("/dashboard")
	message = f"""
		<p>Hi {frappe.utils.escape_html(applicant.applicant_name)},</p>
		<p>Congratulations! Your appointment letter is attached.</p>
		<p>View your dashboard: <a href="{dashboard_link}">{dashboard_link}</a></p>
	"""
	try:
		send_email_or_log(
			recipients=[applicant.email_id],
			subject="Appointment letter",
			message=message,
			log_fallback=f"appointment letter email for {applicant.email_id}, letter {letter.name}",
			attachments=_pdf_attachment("Appointment Letter", letter.name, f"Appointment Letter - {applicant.applicant_name}.pdf"),
		)
	except Exception as e:
		gdl_log_error(f"Appointment letter email failed for {applicant.email_id}", exc=e)

	notify_user(
		applicant.email_id,
		subject="Appointment letter issued",
		document_type="Appointment Letter",
		document_name=letter.name,
		link="/dashboard",
	)

	return letter

	return success(data=letter.as_dict(), message="Appointment letter generated and sent.")
