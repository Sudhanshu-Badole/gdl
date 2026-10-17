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
		# Was fixture-only until client feedback (Phase 1) needed it enforced
		# as unique (one account per CID) - now brought under this script so
		# re-runs stay authoritative. See FIELD_PROPERTY_UPDATES below: on an
		# existing site this field already exists, so create_custom_field()
		# here is a no-op for it and the `unique` flip is applied separately.
		{
			"fieldname": "gdl_cid_number",
			"label": "CID / National ID Number",
			"fieldtype": "Data",
			"insert_after": "gdl_national_id",
			"in_standard_filter": 1,
			"unique": 1,
			"description": "Plain-text CID / National ID number, used for HR candidate search. Separate from the gdl_national_id upload (the scanned ID document itself).",
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
		# Client feedback (Phase 1) - new mandatory documents. New Custom
		# Fields use the custom_ prefix per hooks.py's stated policy.
		{
			"fieldname": "custom_medical_certificate",
			"label": "Medical Certificate",
			"fieldtype": "Attach",
			"insert_after": "gdl_profile_completeness",
		},
		{
			"fieldname": "custom_security_clearance",
			"label": "Security Clearance",
			"fieldtype": "Attach",
			"insert_after": "custom_medical_certificate",
		},
		# Client feedback (Phase 1) - per-document Verify/Send Back workflow.
		# One row per document key (see gdl/utils/documents.py), get-or-created
		# lazily rather than pre-seeded, so adding a new document type later
		# never requires a schema change here.
		{
			"fieldname": "custom_document_verifications",
			"label": "Document Verifications",
			"fieldtype": "Table",
			"options": "Job Applicant Document Verification",
			"insert_after": "custom_security_clearance",
			"read_only": 1,
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
		{
			"fieldname": "gdl_publish_interview_scores",
			"label": "Publish Interview Scores on Website",
			"fieldtype": "Check",
			"insert_after": "gdl_publish_exam_scores",
		},
		# Phase 8 - final ranking weighting (exam weight is implicitly
		# 100 - this). Only used when gdl_exam_required is on; a vacancy with
		# no exam is always ranked 100% on interview score regardless of this
		# field's value.
		{
			"fieldname": "gdl_interview_weight_percent",
			"label": "Interview Weight (%) in Final Ranking",
			"fieldtype": "Int",
			"default": "100",
			"insert_after": "gdl_publish_interview_scores",
		},
	],
	# Phase 8 - native HRMS doctypes, extended the same way Job Applicant/Job
	# Opening already are, rather than building parallel custom doctypes (see
	# the Interview/Interview Feedback naming-collision lesson from Phase 7).
	"Job Offer": [
		{
			"fieldname": "gdl_job_application",
			"label": "Job Application",
			"fieldtype": "Link",
			"options": "Job Application",
			"insert_after": "job_applicant",
			"reqd": 1,
		},
		{
			"fieldname": "gdl_joining_date",
			"label": "Joining Date",
			"fieldtype": "Date",
			"insert_after": "offer_date",
		},
		{
			"fieldname": "gdl_reporting_manager",
			"label": "Reporting Manager",
			"fieldtype": "Link",
			"options": "User",
			"insert_after": "gdl_joining_date",
		},
		{
			"fieldname": "gdl_department",
			"label": "Department",
			"fieldtype": "Link",
			"options": "Department",
			"insert_after": "gdl_reporting_manager",
		},
		{
			# Client feedback (Phase 3): renamed "Salary" -> "TFMR" and
			# switched from Currency to free text, since content/structure
			# varies per applicant and gets printed as-is into the offer
			# letter (see FIELD_PROPERTY_UPDATES below for existing sites).
			"fieldname": "gdl_salary",
			"label": "TFMR",
			"fieldtype": "Small Text",
			"insert_after": "gdl_department",
		},
		{
			"fieldname": "gdl_response_deadline",
			"label": "Response Deadline",
			"fieldtype": "Date",
			"insert_after": "gdl_salary",
		},
		{
			"fieldname": "gdl_responded_on",
			"label": "Responded On",
			"fieldtype": "Datetime",
			"insert_after": "gdl_response_deadline",
			"read_only": 1,
		},
		{
			"fieldname": "gdl_response_recorded_by",
			"label": "Response Recorded By (HR proxy)",
			"fieldtype": "Link",
			"options": "User",
			"insert_after": "gdl_responded_on",
			"read_only": 1,
			"description": "Set only when HR records the candidate's response on their behalf, rather than the candidate responding themselves via the portal.",
		},
	],
	"Appointment Letter": [
		{
			"fieldname": "gdl_job_application",
			"label": "Job Application",
			"fieldtype": "Link",
			"options": "Job Application",
			"insert_after": "job_applicant",
			"reqd": 1,
		},
		{
			"fieldname": "gdl_job_offer",
			"label": "Job Offer",
			"fieldtype": "Link",
			"options": "Job Offer",
			"insert_after": "gdl_job_application",
			"reqd": 1,
		},
	],
}


# create_custom_field() only inserts when the field doesn't already exist -
# it never updates an existing one. Properties here are applied directly via
# frappe.db.set_value so re-running this script also catches up a field that
# already existed on a site before a property (e.g. `unique`) was added
# above.
FIELD_PROPERTY_UPDATES = {
	("Job Applicant", "gdl_cid_number"): {"unique": 1},
	("Job Offer", "gdl_salary"): {"label": "TFMR", "fieldtype": "Small Text"},
}


def run():
	import frappe

	for doctype, fields in CUSTOM_FIELDS.items():
		for field in fields:
			create_custom_field(doctype, field, ignore_validate=True)

	updated_doctypes = set()
	for (doctype, fieldname), properties in FIELD_PROPERTY_UPDATES.items():
		frappe.db.set_value("Custom Field", {"dt": doctype, "fieldname": fieldname}, properties)
		updated_doctypes.add(doctype)
	if updated_doctypes:
		frappe.clear_cache()
		# frappe.db.set_value() bypasses Custom Field's own on_update (which is
		# what normally calls frappe.db.updatedb() to alter the actual MySQL
		# column/index) - call it explicitly so e.g. `unique: 1` becomes a real
		# unique index, not just a value on the Custom Field record.
		for doctype in updated_doctypes:
			frappe.db.updatedb(doctype)

	print("Custom fields bootstrap complete.")
