"""One-time bootstrap for app-owned doctypes: child tables (Task 3.2
education/employment, Task 3.3 other supporting documents) and standalone
doctypes (Task 4.0 Job Application, Vacancy Category).

Run via: bench --site <site> execute gdl.setup_doctypes.run

Idempotent - safe to re-run. With developer_mode=1, inserting these DocType
records also exports their JSON definitions to gdl/gdl/gdl/doctype/<name>/,
which is how Frappe apps normally own their own doctypes (vs. Custom
Doctype/Custom Field, which are for site-level extensions of doctypes owned
by *other* apps, like Job Applicant/Job Opening here).

Must run before setup_custom_fields.run() - the gdl_education /
gdl_employment_history / gdl_other_documents Table fields on Job Applicant,
and gdl_vacancy_category on Job Opening, reference these.
"""

import frappe

SYSTEM_MANAGER_FULL_PERM = {
	"role": "System Manager",
	"read": 1,
	"write": 1,
	"create": 1,
	"delete": 1,
	"report": 1,
	"export": 1,
	"print": 1,
	"email": 1,
	"share": 1,
}

# Full application status lifecycle, per the requirement doc's "Application
# Status Lifecycle" section. Most of these states aren't reachable until
# Phases 5-9 build shortlisting/exams/interviews/offers, but the schema is
# defined complete now rather than migrated piecemeal later.
JOB_APPLICATION_STATUSES = [
	"Submitted",
	"Under Review",
	"Review on Hold",
	"Shortlisted",
	"Not Shortlisted",
	"Exam Invited / Scheduled",
	"Exam Completed",
	"Exam Not Attended",
	"Interview Invited / Scheduled",
	"Interview Completed",
	"Interview Not Attended",
	"Selected",
	"Rejected",
	"Offer Sent",
	"Offer Accepted",
	"Offer Declined",
	"Appointed",
]

CHILD_DOCTYPES = {
	"Job Applicant Education": [
		{
			"fieldname": "qualification",
			"fieldtype": "Data",
			"label": "Qualification",
			"reqd": 1,
			"in_list_view": 1,
		},
		{
			"fieldname": "institution_name",
			"fieldtype": "Data",
			"label": "Institution Name",
			"reqd": 1,
			"in_list_view": 1,
		},
		{"fieldname": "start_date", "fieldtype": "Date", "label": "Start Date", "in_list_view": 1},
		{"fieldname": "completion_date", "fieldtype": "Date", "label": "Completion Date", "in_list_view": 1},
		{"fieldname": "grade_or_result", "fieldtype": "Data", "label": "Grade or Result", "in_list_view": 1},
	],
	"Job Applicant Employment History": [
		{
			"fieldname": "company_name",
			"fieldtype": "Data",
			"label": "Company Name",
			"reqd": 1,
			"in_list_view": 1,
		},
		{"fieldname": "job_title", "fieldtype": "Data", "label": "Job Title", "in_list_view": 1},
		{"fieldname": "start_date", "fieldtype": "Date", "label": "Start Date", "in_list_view": 1},
		{"fieldname": "end_date", "fieldtype": "Date", "label": "End Date", "in_list_view": 1},
		{"fieldname": "currently_working", "fieldtype": "Check", "label": "Currently Working"},
		{"fieldname": "responsibilities", "fieldtype": "Small Text", "label": "Responsibilities"},
	],
	"Job Applicant Document": [
		{
			"fieldname": "document_type",
			"fieldtype": "Data",
			"label": "Document Type",
			"reqd": 1,
			"in_list_view": 1,
		},
		{
			"fieldname": "attachment",
			"fieldtype": "Attach",
			"label": "Attachment",
			"reqd": 1,
			"in_list_view": 1,
		},
	],
}

# Standalone (non-child-table) app-owned doctypes. Custom DocPerm grants for
# HR Officer / Panel Member / Applicant Portal User are added separately in
# setup_roles_permissions.py, same pattern as Job Applicant - the base
# permission here is just System Manager, matching Frappe's own convention
# for a freshly-created doctype.
STANDALONE_DOCTYPES = {
	"Vacancy Category": {
		"autoname": "field:category_name",
		"fields": [
			{
				"fieldname": "category_name",
				"fieldtype": "Data",
				"label": "Category Name",
				"reqd": 1,
				"unique": 1,
				"in_list_view": 1,
			},
		],
		"permissions": [SYSTEM_MANAGER_FULL_PERM],
	},
	"Job Application": {
		"autoname": "APP-.YYYY.-.#####",
		"fields": [
			{
				"fieldname": "job_applicant",
				"fieldtype": "Link",
				"options": "Job Applicant",
				"label": "Applicant",
				"reqd": 1,
				"in_list_view": 1,
			},
			{
				"fieldname": "job_opening",
				"fieldtype": "Link",
				"options": "Job Opening",
				"label": "Vacancy",
				"reqd": 1,
				"in_list_view": 1,
			},
			{
				"fieldname": "status",
				"fieldtype": "Select",
				"options": "\n".join(JOB_APPLICATION_STATUSES),
				"label": "Status",
				"default": "Submitted",
				"reqd": 1,
				"in_list_view": 1,
				"in_standard_filter": 1,
			},
			{"fieldname": "cover_letter", "fieldtype": "Text", "label": "Cover Letter"},
		],
		"permissions": [SYSTEM_MANAGER_FULL_PERM],
	},
}


def _create_child_doctype(name, fields):
	if frappe.db.exists("DocType", name):
		return
	doc = frappe.get_doc(
		{
			"doctype": "DocType",
			"name": name,
			"module": "Gdl",
			"custom": 0,
			"istable": 1,
			"editable_grid": 1,
			"engine": "InnoDB",
			"permissions": [],
			"fields": fields,
		}
	)
	doc.insert()


def _create_standalone_doctype(name, meta):
	if frappe.db.exists("DocType", name):
		return
	doc = frappe.get_doc(
		{
			"doctype": "DocType",
			"name": name,
			"module": "Gdl",
			"custom": 0,
			"istable": 0,
			"editable_grid": 1,
			"engine": "InnoDB",
			"autoname": meta["autoname"],
			"permissions": meta["permissions"],
			"fields": meta["fields"],
		}
	)
	doc.insert()


def run():
	for name, fields in CHILD_DOCTYPES.items():
		_create_child_doctype(name, fields)
	for name, meta in STANDALONE_DOCTYPES.items():
		_create_standalone_doctype(name, meta)
	frappe.db.commit()
	print("Doctypes bootstrap complete.")
