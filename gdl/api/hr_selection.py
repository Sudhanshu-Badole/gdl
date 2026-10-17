"""Selection (Phase 8): rank candidates by a per-vacancy exam/interview
weighted score, let HR assign Selected/Reserve/Rejected, and promote a
Reserve candidate to Selected. No new doctype - ranking is computed on the
fly from Job Application + Exam Attempt + Interview Session, same
"compute, don't persist" approach as gdl.api.hr_shortlisting's queue.
"""

import frappe

from gdl.api.hr import require_hr
from gdl.api.response import success
from gdl.utils.audit import set_application_status
from gdl.utils.exceptions import gdl_error

# Applications an HR user should see/rank in the Selection tab: candidates
# who finished the interview stage, plus anyone already decided (so HR can
# review/revise a prior Selected/Reserve/Rejected call).
QUEUE_STATUSES = ["Interview Completed", "Selected", "Reserve", "Rejected"]
BULK_ALLOWED_STATUSES = {"Selected", "Reserve", "Rejected"}


@frappe.whitelist()
def get_selection_ranking(job_opening):
	require_hr()

	opening = frappe.db.get_value(
		"Job Opening", job_opening, ["gdl_exam_required", "gdl_interview_weight_percent"], as_dict=True
	)
	if not opening:
		gdl_error("Vacancy not found.")

	interview_weight = (opening.gdl_interview_weight_percent if opening.gdl_exam_required else 100) or 0
	exam_weight = 100 - interview_weight if opening.gdl_exam_required else 0

	applications = frappe.get_all(
		"Job Application",
		filters={"job_opening": job_opening, "status": ["in", QUEUE_STATUSES]},
		fields=["name", "job_applicant", "status"],
	)
	if not applications:
		return success(data={"interview_weight": interview_weight, "exam_weight": exam_weight, "rows": []})

	app_names = [a.name for a in applications]
	applicants = {
		row.name: row
		for row in frappe.get_all(
			"Job Applicant", filters={"name": ["in", [a.job_applicant for a in applications]]}, fields=["name", "applicant_name", "email_id"]
		)
	}
	exam_scores = {
		row.job_application: row.total_score
		for row in frappe.get_all("Exam Attempt", filters={"job_application": ["in", app_names]}, fields=["job_application", "total_score"])
	}
	interview_scores = {
		row.job_application: row.total_score
		for row in frappe.get_all(
			"Interview Session", filters={"job_application": ["in", app_names]}, fields=["job_application", "total_score"]
		)
	}

	rows = []
	for app in applications:
		applicant = applicants.get(app.job_applicant, {})
		exam_score = exam_scores.get(app.name)
		interview_score = interview_scores.get(app.name)
		if opening.gdl_exam_required and exam_score is not None:
			composite = (interview_score or 0) * interview_weight / 100 + exam_score * exam_weight / 100
		else:
			composite = interview_score or 0
		rows.append(
			{
				"name": app.name,
				"applicant_name": applicant.get("applicant_name"),
				"email_id": applicant.get("email_id"),
				"status": app.status,
				"exam_score": exam_score,
				"interview_score": interview_score,
				"composite_score": round(composite, 2),
			}
		)

	rows.sort(key=lambda r: r["composite_score"], reverse=True)
	return success(data={"interview_weight": interview_weight, "exam_weight": exam_weight, "rows": rows})


@frappe.whitelist(methods=["POST"])
def bulk_set_selection_status(job_applications, status):
	require_hr()

	if status not in BULK_ALLOWED_STATUSES:
		gdl_error("Invalid status for this action.")
	if isinstance(job_applications, str):
		job_applications = frappe.parse_json(job_applications)
	if not job_applications:
		gdl_error("Select at least one application.")

	revisable = set(
		frappe.get_all(
			"Job Application", filters={"name": ["in", job_applications], "status": ["in", QUEUE_STATUSES]}, pluck="name"
		)
	)
	skipped = [name for name in job_applications if name not in revisable]
	job_applications = [name for name in job_applications if name in revisable]
	if not job_applications:
		gdl_error("None of the selected applications can still be revised at this stage.")

	for name in job_applications:
		set_application_status(name, status)

	message = f"{len(job_applications)} application(s) marked {status}."
	if skipped:
		message += f" {len(skipped)} skipped (already past selection)."
	return success(data={"updated": len(job_applications), "skipped": len(skipped)}, message=message)


@frappe.whitelist(methods=["POST"])
def promote_reserve(job_application):
	require_hr()

	application = frappe.get_doc("Job Application", job_application)
	if application.status != "Reserve":
		gdl_error("Only a Reserve candidate can be promoted.")

	set_application_status(application.name, "Selected")
	return success(message="Candidate promoted to Selected.")
