"""Shared Exam Attempt scoring logic (Phase 6) - used both when HR finishes
manually grading a Short Answer question (gdl.api.hr_exam.grade_answers) and
when an applicant submits a pure Multiple Choice / True-or-False exam that
needs no manual grading at all (gdl.api.applicant.submit_exam_attempt).
Kept in one place so both paths compute total_score/is_fully_graded/is_pass
identically.
"""

import frappe


def finalize_attempt_grading(attempt):
	"""attempt: a loaded Exam Attempt Document. Recomputes total_score and
	is_fully_graded from its answer rows, and - once fully graded and the
	attempt was actually Submitted (never for Not Attended) - is_pass plus
	the linked Job Application's status."""
	rows = frappe.get_all(
		"Exam Attempt Answer", filters={"parent": attempt.name}, fields=["score_given", "is_graded"]
	)
	is_fully_graded = all(row.is_graded for row in rows)
	total_score = sum(row.score_given or 0 for row in rows)

	attempt.db_set("total_score", total_score)
	attempt.db_set("is_fully_graded", 1 if is_fully_graded else 0)

	if is_fully_graded and attempt.status == "Submitted":
		exam = frappe.get_doc("Exam", attempt.exam)
		is_pass = total_score >= (exam.pass_marks or 0)
		attempt.db_set("is_pass", 1 if is_pass else 0)
		frappe.db.set_value("Job Application", attempt.job_application, "status", "Exam Completed")
