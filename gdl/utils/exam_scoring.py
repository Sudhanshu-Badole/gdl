"""Shared Exam Attempt scoring logic (Phase 6) - used both when HR finishes
manually grading a Short Answer question (gdl.api.hr_exam.grade_answers) and
when an applicant submits a pure Multiple Choice / True-or-False exam that
needs no manual grading at all (gdl.api.applicant.submit_exam_attempt).
Kept in one place so both paths compute total_score/is_fully_graded/is_pass
identically.
"""

import frappe

from gdl.utils.audit import set_application_status


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
		set_application_status(attempt.job_application, "Exam Completed")


def get_exam_result_summary(job_application):
	"""Read-only exam breakdown for a Job Application's most recent Exam
	Attempt (title/status/score/pass-fail/per-question breakdown), or None
	if the candidate was never invited to an exam. Shared by
	gdl.api.panel.get_candidate_exam_result (Panel Self Entry) and
	gdl.api.hr_interview.get_proxy_scorecard (HR Proxy Entry) so both
	score-entry modes show the same written-test context."""
	attempt = frappe.db.get_value(
		"Exam Attempt",
		{"job_application": job_application},
		["name", "exam", "status", "total_score", "is_pass", "is_fully_graded", "evaluator_comment", "panel_comment"],
		as_dict=True,
		order_by="creation desc",
	)
	if not attempt:
		return None

	exam_title = frappe.db.get_value("Exam", attempt.exam, "title")
	questions = frappe.get_all(
		"Exam Question",
		filters={"exam": attempt.exam},
		fields=["name", "sequence", "question_type", "question_text", "marks"],
		order_by="sequence asc, creation asc",
	)
	answers = {
		row.question: row
		for row in frappe.get_all(
			"Exam Attempt Answer",
			filters={"parent": attempt.name},
			fields=[
				"question",
				"selected_option",
				"short_answer_text",
				"score_given",
				"is_graded",
				"is_correct",
				"evaluator_comment",
			],
		)
	}

	rows = []
	for question in questions:
		answer = answers.get(question.name)
		rows.append(
			{
				"question_type": question.question_type,
				"question_text": question.question_text,
				"marks": question.marks,
				"selected_option": answer.selected_option if answer else None,
				"short_answer_text": answer.short_answer_text if answer else None,
				"score_given": answer.score_given if answer else None,
				"is_graded": bool(answer.is_graded) if answer else False,
				"is_correct": bool(answer.is_correct) if answer else False,
				"evaluator_comment": answer.evaluator_comment if answer else None,
			}
		)

	return {
		"exam_title": exam_title,
		"status": attempt.status,
		"total_score": attempt.total_score,
		"is_pass": attempt.is_pass,
		"is_fully_graded": bool(attempt.is_fully_graded),
		"evaluator_comment": attempt.evaluator_comment,
		"panel_comment": attempt.panel_comment,
		"questions": rows,
	}
