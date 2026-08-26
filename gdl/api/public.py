import re

import frappe
from frappe.utils import validate_email_address
from frappe.utils.verified_command import verify_request

from gdl.api.response import success
from gdl.utils.exceptions import gdl_error
from gdl.utils.logger import get_logger
from gdl.utils.vacancies import list_open_vacancies, list_vacancies
from gdl.utils.verification import send_verification_email

logger = get_logger("api.public")

APPLICANT_ROLE = "Applicant Portal User"
PHONE_RE = re.compile(r"^\+?[0-9 ()-]{7,20}$")
HOME_VACANCIES_LIMIT = 6


@frappe.whitelist(allow_guest=True)
def get_home_vacancies():
	"""Featured openings for the Vue public home page (gdl/frontend).

	Fetches the full open list (not just a limited query) so the hero/CTA
	"N open positions" count reflects the true total, not just the featured
	subset shown on the card grid.
	"""
	all_open = list_open_vacancies()
	return success(data={"total": len(all_open), "vacancies": all_open[:HOME_VACANCIES_LIMIT]})


@frappe.whitelist(allow_guest=True)
def get_open_vacancies(include_recent=0):
	"""Vacancy listing for the Vue /jobs page (gdl/frontend). include_recent
	unions in vacancies that closed/filled within the last 90 days, for the
	"include recently closed or filled positions" checkbox."""
	return success(data=list_vacancies(include_recent=frappe.utils.cint(include_recent)))


@frappe.whitelist(allow_guest=True, methods=["POST"])
def register_applicant(full_name, email, phone, password):
	"""Applicant self-registration. Deliberately has no `role` parameter -
	the only role this can ever grant is Applicant Portal User, hardcoded
	below. HR/Panel accounts cannot be created through this or any other
	guest-accessible endpoint.
	"""
	full_name = (full_name or "").strip()
	email = (email or "").strip().lower()
	phone = (phone or "").strip()
	password = password or ""

	_validate_registration_input(full_name, email, phone, password)

	if frappe.db.exists("User", email):
		gdl_error("An account with this email already exists")

	name_parts = full_name.split(" ", 1)
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": name_parts[0],
			"last_name": name_parts[1] if len(name_parts) > 1 else None,
			"phone": phone,
			"enabled": 1,
			"user_type": "Website User",
			"new_password": password,
			"send_welcome_email": 0,
			"roles": [{"role": APPLICANT_ROLE}],
		}
	)
	user.flags.ignore_permissions = True
	# We already enforce our own policy (8+ chars, upper+lower) above; skip
	# Frappe's system-wide zxcvbn strength check so submission behaviour
	# matches exactly what the registration form promises the applicant.
	user.flags.ignore_password_policy = True
	user.insert()

	if not frappe.db.exists("Job Applicant", {"email_id": email}):
		applicant = frappe.get_doc(
			{
				"doctype": "Job Applicant",
				"applicant_name": full_name,
				"email_id": email,
				"phone_number": phone,
				"status": "Open",
			}
		)
		applicant.flags.ignore_permissions = True
		applicant.insert()
		# Document.set_user_and_timestamp() always forces owner = the acting
		# session user on insert (Guest, for this whole request) - setting
		# "owner" in the dict above is silently overwritten. Fix it up after
		# the fact so the if_owner Custom DocPerm grant for Applicant Portal
		# User actually scopes to this applicant's own record.
		frappe.db.set_value("Job Applicant", applicant.name, "owner", email)

	send_verification_email(email, full_name)
	logger.info(f"applicant registered: {email}")

	return success(
		data={"redirect_to": "/complete-profile"},
		message="Registration successful. Please check your email to verify your account.",
	)


@frappe.whitelist(allow_guest=True)
def verify_applicant_email():
	if not verify_request():
		return

	email = frappe.form_dict.get("email")
	if email and frappe.db.exists("User", email):
		frappe.db.set_value("User", email, "gdl_email_verified", 1)
		frappe.db.commit()
		frappe.respond_as_web_page(
			"Email Verified", "Your email has been verified. You can now sign in.", indicator_color="green"
		)
	else:
		frappe.respond_as_web_page(
			"Invalid Link", "This verification link is invalid.", indicator_color="red"
		)


@frappe.whitelist(allow_guest=True)
def get_vacancy_detail(name):
	"""Full payload for the public vacancy detail page (Vue /jobs/:name).

	Guest-accessible: get_all (not get_list) since Guest has no Job Opening
	DocPerm - same reasoning as the home page's vacancy query. Filters on
	publish=1 only (not status="Open"), matching the old get_vacancy_extras
	this replaces, so a shared link to a since-closed vacancy doesn't
	dead-end.
	"""
	fields = [
		"name",
		"job_title",
		"department",
		"gdl_vacancy_category",
		"gdl_job_type",
		"gdl_number_of_positions",
		"closes_on",
		"posted_on",
		"description",
		"gdl_eligibility_requirements",
		"gdl_terms_of_reference",
		"gdl_min_experience_years",
		"gdl_degree_required",
		"gdl_min_degree_score",
		"gdl_experienced_vacancy",
	]
	opening = frappe.get_all(
		"Job Opening", filters={"name": name, "publish": 1}, fields=fields, limit_page_length=1
	)
	if not opening:
		return success(data=None)

	opening = opening[0]
	opening["gdl_terms_of_reference_filename"] = _tor_filename(opening.get("gdl_terms_of_reference"))
	opening["gdl_required_documents"] = frappe.get_all(
		"Job Opening Required Document",
		filters={"parent": name},
		fields=["document_label"],
		order_by="idx",
		pluck="document_label",
	)
	return success(data=opening)


def _tor_filename(file_url):
	if not file_url:
		return None
	from urllib.parse import unquote

	return unquote(file_url).rsplit("/", 1)[-1]


def _validate_registration_input(full_name, email, phone, password):
	if not full_name:
		gdl_error("Full name is required")

	validate_email_address(email, throw=True)

	if not PHONE_RE.match(phone):
		gdl_error("Enter a valid phone number")

	if len(password) < 8:
		gdl_error("Password must be at least 8 characters long")
	if not re.search(r"[a-z]", password) or not re.search(r"[A-Z]", password):
		gdl_error("Password must contain both uppercase and lowercase letters")
