"""Organization & Offer/Appointment policy settings (Phase 9, partial).
Single doctype - one record for the whole site, editable by any HR Officer
(unlike staff account management in gdl.api.hr_admin, which the spec
restricts to Super Administrators).
"""

import frappe

from gdl.api.hr import require_hr
from gdl.api.response import success
from gdl.utils.uploads import save_upload

EDITABLE_FIELDS = (
	"organization_name",
	"time_zone",
	"offer_response_window_days",
	"auto_issue_appointment_letter",
	"max_exam_violations_before_autosubmit",
)
LOGO_EXTENSIONS = ["jpg", "jpeg", "png"]


@frappe.whitelist()
def get_recruitment_settings():
	require_hr()
	return success(data=frappe.get_single("Recruitment Settings").as_dict())


@frappe.whitelist(methods=["POST"])
def update_recruitment_settings(**fields):
	require_hr()

	settings = frappe.get_single("Recruitment Settings")
	for field in EDITABLE_FIELDS:
		if field in fields:
			settings.set(field, fields[field])
	settings.save()
	return success(data=settings.as_dict(), message="Settings saved.")


@frappe.whitelist(methods=["POST"])
def upload_organization_logo():
	require_hr()

	settings = frappe.get_single("Recruitment Settings")
	url = save_upload(settings, "organization_logo", LOGO_EXTENSIONS, max_size_mb=2, is_private=0)
	return success(data={"file_url": url}, message="Logo updated.")
