"""One-time bootstrap for standard HRMS master data that was never seeded on
this site (HRMS's own `hrms.setup.setup_hr_defaults`, normally run during
`bench install-app hrms`, apparently never ran here - Job Applicant Source,
Employment Type, and others all came up empty).

Run via: bench --site <site> execute gdl.setup_master_data.run

Only seeding the two doctypes recruitment actually touches right now
(Job Applicant.source, Job Opening.employment_type) - not the unrelated
payroll/leave/expense master data HRMS also seeds, since nothing in this
project uses those yet. Revisit if a later phase needs them.

Idempotent - safe to re-run.
"""

import frappe

JOB_APPLICANT_SOURCES = ["Website Listing", "Walk In", "Employee Referral", "Campaign"]
EMPLOYMENT_TYPES = [
	"Full-time",
	"Part-time",
	"Probation",
	"Contract",
	"Commission",
	"Piecework",
	"Intern",
	"Apprentice",
]


def run():
	for source_name in JOB_APPLICANT_SOURCES:
		if not frappe.db.exists("Job Applicant Source", source_name):
			frappe.get_doc({"doctype": "Job Applicant Source", "source_name": source_name}).insert(
				ignore_permissions=True
			)

	for employee_type in EMPLOYMENT_TYPES:
		if not frappe.db.exists("Employment Type", employee_type):
			frappe.get_doc({"doctype": "Employment Type", "employee_type_name": employee_type}).insert(
				ignore_permissions=True
			)

	frappe.db.commit()
	print("Master data bootstrap complete.")
