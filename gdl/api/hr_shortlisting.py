"""Shortlisting (Phase 5): checklist-based document review, bulk
Shortlist/Reject/Hold actions, and advancing top-ranked candidates to the
next stage. Job Application.status already has every status value this
needs (from Phase 4) - shortlisting only transitions between them, no
dependency on the Examination/Interview doctypes that don't exist yet.
"""

import frappe

from gdl.api.hr import require_hr
from gdl.api.response import success
from gdl.utils.exceptions import gdl_error

# Applications an HR user should see in the Shortlist tab: still awaiting a
# decision, or already decided (so HR can review/revise and so the ranked
# "advance" step can see who's currently Shortlisted).
QUEUE_STATUSES = ["Submitted", "Under Review", "Review on Hold", "Shortlisted", "Not Shortlisted"]
BULK_ALLOWED_STATUSES = {"Shortlisted", "Not Shortlisted", "Review on Hold"}


@frappe.whitelist()
def get_shortlisting_queue(job_opening):
	require_hr()

	opening = frappe.db.get_value(
		"Job Opening", job_opening, ["gdl_vacancy_category", "gdl_exam_required"], as_dict=True
	)
	if not opening:
		gdl_error("Vacancy not found.")

	template = None
	if opening.gdl_vacancy_category and frappe.db.exists(
		"Shortlisting Checklist Template", opening.gdl_vacancy_category
	):
		template_doc = frappe.get_doc("Shortlisting Checklist Template", opening.gdl_vacancy_category)
		template = {
			"name": template_doc.name,
			"criteria": [
				{"criterion_label": c.criterion_label, "max_score": c.max_score} for c in template_doc.criteria
			],
		}

	applications = frappe.get_all(
		"Job Application",
		filters={"job_opening": job_opening, "status": ["in", QUEUE_STATUSES]},
		fields=["name", "job_applicant", "status", "creation"],
		order_by="creation asc",
	)

	applicants = {}
	scores = {}
	criterion_rows_by_app = {}
	if applications:
		applicant_names = [a.job_applicant for a in applications]
		applicants = {
			row.name: row
			for row in frappe.get_all(
				"Job Applicant", filters={"name": ["in", applicant_names]}, fields=["name", "applicant_name", "email_id"]
			)
		}

		app_names = [a.name for a in applications]
		scores = {
			row.name: row.total_score
			for row in frappe.get_all(
				"Shortlisting Score", filters={"name": ["in", app_names]}, fields=["name", "total_score"]
			)
		}
		for row in frappe.get_all(
			"Shortlisting Criterion Score",
			filters={"parent": ["in", app_names]},
			fields=["parent", "criterion_label", "max_score", "score_given"],
			order_by="parent, idx",
		):
			criterion_rows_by_app.setdefault(row.parent, []).append(
				{"criterion_label": row.criterion_label, "max_score": row.max_score, "score_given": row.score_given}
			)

	rows = []
	for app in applications:
		applicant = applicants.get(app.job_applicant, {})
		rows.append(
			{
				"name": app.name,
				"applicant_name": applicant.get("applicant_name"),
				"email_id": applicant.get("email_id"),
				"status": app.status,
				"creation": app.creation,
				"total_score": scores.get(app.name),
				"criterion_scores": criterion_rows_by_app.get(app.name, []),
			}
		)

	return success(
		data={"template": template, "applications": rows, "exam_required": bool(opening.gdl_exam_required)}
	)


@frappe.whitelist(methods=["POST"])
def save_shortlisting_score(job_application, criterion_scores):
	require_hr()

	if isinstance(criterion_scores, str):
		criterion_scores = frappe.parse_json(criterion_scores)
	if not criterion_scores:
		gdl_error("Enter at least one score before saving.")

	application = frappe.get_doc("Job Application", job_application)
	application.check_permission("read")

	if frappe.db.exists("Shortlisting Score", job_application):
		score_doc = frappe.get_doc("Shortlisting Score", job_application)
		score_doc.set("criterion_scores", [])
	else:
		score_doc = frappe.get_doc(
			{
				"doctype": "Shortlisting Score",
				"job_application": job_application,
				"job_opening": application.job_opening,
				"job_applicant": application.job_applicant,
			}
		)

	for row in criterion_scores:
		score_doc.append(
			"criterion_scores",
			{
				"criterion_label": row.get("criterion_label"),
				"max_score": row.get("max_score") or 0,
				"score_given": row.get("score_given") or 0,
			},
		)

	score_doc.reviewed_by = frappe.session.user
	score_doc.reviewed_on = frappe.utils.now()
	score_doc.save()

	if application.status == "Submitted":
		application.db_set("status", "Under Review")

	return success(data={"total_score": score_doc.total_score}, message="Score saved.")


@frappe.whitelist(methods=["POST"])
def bulk_set_shortlist_status(job_applications, status):
	require_hr()

	if status not in BULK_ALLOWED_STATUSES:
		gdl_error("Invalid status for this action.")
	if isinstance(job_applications, str):
		job_applications = frappe.parse_json(job_applications)
	if not job_applications:
		gdl_error("Select at least one application.")

	# Forward-only: skip any application a stale/concurrent client already
	# moved past shortlisting (e.g. "Exam Invited / Scheduled") rather than
	# silently regressing it back to "Not Shortlisted".
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
		frappe.db.set_value("Job Application", name, "status", status)

	message = f"{len(job_applications)} application(s) marked {status}."
	if skipped:
		message += f" {len(skipped)} skipped (already past shortlisting)."
	return success(data={"updated": len(job_applications), "skipped": len(skipped)}, message=message)


@frappe.whitelist(methods=["POST"])
def advance_shortlisted(job_opening, cutoff):
	require_hr()

	cutoff = frappe.utils.cint(cutoff)
	if cutoff <= 0:
		gdl_error("Enter a cutoff greater than 0.")

	exam_required = frappe.db.get_value("Job Opening", job_opening, "gdl_exam_required")
	# Per spec: skip straight to interview when the vacancy doesn't require
	# an exam - Phase 6 (Examination) not existing yet doesn't block this,
	# since gdl_exam_required is just a boolean HR sets per vacancy already.
	next_status = "Exam Invited / Scheduled" if exam_required else "Interview Invited / Scheduled"

	shortlisted = frappe.get_all("Job Application", filters={"job_opening": job_opening, "status": "Shortlisted"}, fields=["name"])
	if not shortlisted:
		gdl_error("No shortlisted candidates to advance.")

	scores = {
		row.name: row.total_score or 0
		for row in frappe.get_all(
			"Shortlisting Score", filters={"name": ["in", [a.name for a in shortlisted]]}, fields=["name", "total_score"]
		)
	}
	ranked = sorted(shortlisted, key=lambda a: scores.get(a.name, 0), reverse=True)
	advancing = ranked[:cutoff]

	for app in advancing:
		frappe.db.set_value("Job Application", app.name, "status", next_status)

	return success(
		data={"advanced": len(advancing), "next_status": next_status},
		message=f"{len(advancing)} candidate(s) advanced to {next_status}.",
	)
