"""One-time bootstrap for Custom Fields (Task 2.2 email verification, Task 3.1
personal info, Task 3.3 documents, Task 3.4 profile completeness).

Run via: bench --site <site> execute gdl.setup_custom_fields.run

Idempotent - safe to re-run. Exported as a fixture afterwards (custom_field.json)
so new sites get this via `bench migrate` on install.
"""

from frappe.custom.doctype.custom_field.custom_field import create_custom_field

CUSTOM_FIELDS = {
	"User": [
		{
			"fieldname": "gdl_email_verified",
			"label": "GDL Email Verified",
			"fieldtype": "Check",
			"default": "0",
			"insert_after": "enabled",
			"read_only": 1,
			"no_copy": 1,
		}
	],
	"Job Applicant": [
		# Task 3.1 - Personal info
		{
			"fieldname": "gdl_date_of_birth",
			"label": "Date of Birth",
			"fieldtype": "Date",
			"insert_after": "phone_number",
		},
		{
			"fieldname": "gdl_gender",
			"label": "Gender",
			"fieldtype": "Link",
			"options": "Gender",
			"insert_after": "gdl_date_of_birth",
		},
		{
			"fieldname": "gdl_nationality",
			"label": "Nationality",
			"fieldtype": "Link",
			"options": "Country",
			"insert_after": "gdl_gender",
		},
		{
			"fieldname": "gdl_permanent_address",
			"label": "Permanent Address",
			"fieldtype": "Small Text",
			"insert_after": "gdl_nationality",
		},
		{
			"fieldname": "gdl_current_address",
			"label": "Current Address",
			"fieldtype": "Small Text",
			"insert_after": "gdl_permanent_address",
		},
		{
			"fieldname": "gdl_profile_photo",
			"label": "Profile Photo",
			"fieldtype": "Attach Image",
			"insert_after": "gdl_current_address",
		},
		# Task 3.2 - Education & employment history (child doctypes created by
		# setup_doctypes.py - must run before this)
		{
			"fieldname": "gdl_education",
			"label": "Education",
			"fieldtype": "Table",
			"options": "Job Applicant Education",
			"insert_after": "gdl_profile_photo",
		},
		{
			"fieldname": "gdl_employment_history",
			"label": "Employment History",
			"fieldtype": "Table",
			"options": "Job Applicant Employment History",
			"insert_after": "gdl_education",
		},
		# Task 3.3 - Documents. CV reuses the standard resume_attachment field
		# rather than duplicating it - no gdl_cv field needed.
		{
			"fieldname": "gdl_national_id",
			"label": "CID / National ID",
			"fieldtype": "Attach",
			"insert_after": "gdl_employment_history",
		},
		{
			"fieldname": "gdl_academic_certificate",
			"label": "Academic Certificate",
			"fieldtype": "Attach",
			"insert_after": "gdl_national_id",
		},
		{
			"fieldname": "gdl_experience_letter",
			"label": "Experience Letter",
			"fieldtype": "Attach",
			"insert_after": "gdl_academic_certificate",
		},
		{
			"fieldname": "gdl_other_documents",
			"label": "Other Supporting Documents",
			"fieldtype": "Table",
			"options": "Job Applicant Document",
			"insert_after": "gdl_experience_letter",
		},
		# Task 3.4 - Profile completeness. Computed (see gdl/utils/completeness.py,
		# wired via the Job Applicant "validate" doc_event), never user-editable.
		{
			"fieldname": "gdl_profile_completeness",
			"label": "Profile Completeness",
			"fieldtype": "Percent",
			"insert_after": "gdl_other_documents",
			"read_only": 1,
			"no_copy": 1,
		},
	],
	"Job Opening": [
		# Task 4.0 - vacancy config (Vacancy Category doctype created by
		# setup_doctypes.py - must run before this)
		{
			"fieldname": "gdl_vacancy_category",
			"label": "Vacancy Category",
			"fieldtype": "Link",
			"options": "Vacancy Category",
			"insert_after": "designation",
		},
		{
			"fieldname": "gdl_number_of_positions",
			"label": "Number of Positions",
			"fieldtype": "Int",
			"insert_after": "gdl_vacancy_category",
			"description": "HR-set position count for auto-close-on-fill, independent of the Staffing Plan-driven 'Planned number of Positions'.",
		},
		{
			"fieldname": "gdl_eligibility_requirements",
			"label": "Eligibility Requirements",
			"fieldtype": "Text",
			"insert_after": "description",
		},
		{
			"fieldname": "gdl_terms_of_reference",
			"label": "Terms of Reference (ToR)",
			"fieldtype": "Attach",
			"insert_after": "gdl_eligibility_requirements",
		},
		{
			"fieldname": "gdl_exam_required",
			"label": "Examination Required",
			"fieldtype": "Check",
			"insert_after": "gdl_terms_of_reference",
		},
		{
			"fieldname": "gdl_publish_exam_scores",
			"label": "Publish Exam Scores on Website",
			"fieldtype": "Check",
			"insert_after": "gdl_exam_required",
			"depends_on": "eval:doc.gdl_exam_required",
		},
	],
}


def run():
	for doctype, fields in CUSTOM_FIELDS.items():
		for field in fields:
			create_custom_field(doctype, field, ignore_validate=True)
	print("Custom fields bootstrap complete.")
