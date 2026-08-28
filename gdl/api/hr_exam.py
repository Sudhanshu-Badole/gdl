"""Examination (Phase 6, online exam core): question bank, scheduling,
publish + invite, and manual grading of Short Answer questions.

Mirrors gdl.api.hr_shortlisting's shape - Job Application.status already
carries the full exam vocabulary from Phase 4 ("Exam Invited / Scheduled",
"Exam Completed", "Exam Not Attended"); this module only ever transitions
between those, same as Shortlisting only transitions between its own
already-existing status values.
"""

import frappe
from frappe.utils import get_url, now_datetime

from gdl.api.hr import require_hr
from gdl.api.response import success
from gdl.utils.exam_scoring import finalize_attempt_grading
from gdl.utils.exceptions import gdl_error, gdl_log_error
from gdl.utils.notifications import send_email_or_log

ACTIVE_STATUSES = ("Draft", "Published")


def _get_active_exam(job_opening):
	name = frappe.db.get_value(
		"Exam", {"job_opening": job_opening, "status": ["in", ACTIVE_STATUSES]}, "name", order_by="creation desc"
	)
	return frappe.get_doc("Exam", name) if name else None


def _questions_for(exam_name, include_answers=True):
	fields = ["name", "sequence", "question_type", "question_text", "option_a", "option_b", "option_c", "option_d", "marks"]
	if include_answers:
		fields.append("correct_option")
	return frappe.get_all("Exam Question", filters={"exam": exam_name}, fields=fields, order_by="sequence asc, creation asc")


@frappe.whitelist()
def get_exam(job_opening):
	require_hr()

	exam = _get_active_exam(job_opening)
	if not exam:
		return success(data=None)

	return success(
		data={
			"exam": exam.as_dict(),
			"questions": _questions_for(exam.name),
		}
	)


@frappe.whitelist(methods=["POST"])
def create_exam(job_opening, title, instructions, duration_minutes, opens_on, closes_on, pass_marks):
	require_hr()

	if _get_active_exam(job_opening):
		gdl_error("An exam already exists for this vacancy. Edit or archive it before creating another.")

	exam = frappe.get_doc(
		{
			"doctype": "Exam",
			"job_opening": job_opening,
			"title": title,
			"instructions": instructions,
			"duration_minutes": duration_minutes,
			"opens_on": opens_on,
			"closes_on": closes_on,
			"pass_marks": pass_marks,
			"status": "Draft",
		}
	)
	exam.insert()
	return success(data=exam.as_dict(), message="Exam created.")


@frappe.whitelist(methods=["POST"])
def update_exam(name, **fields):
	require_hr()

	exam = frappe.get_doc("Exam", name)
	if exam.status != "Draft":
		gdl_error("Only a Draft exam can be edited.")

	for field in ("title", "instructions", "duration_minutes", "opens_on", "closes_on", "pass_marks"):
		if field in fields:
			exam.set(field, fields[field])
	exam.save()
	return success(data=exam.as_dict(), message="Exam updated.")


@frappe.whitelist(methods=["POST"])
def add_question(exam, question_type, question_text, marks, option_a=None, option_b=None, option_c=None, option_d=None, correct_option=None):
	require_hr()

	exam_doc = frappe.get_doc("Exam", exam)
	if exam_doc.status != "Draft":
		gdl_error("Questions can only be added while the exam is a Draft.")

	next_sequence = (frappe.db.count("Exam Question", {"exam": exam}) or 0) + 1
	if question_type == "True or False":
		option_a, option_b, option_c, option_d = "True", "False", None, None

	question = frappe.get_doc(
		{
			"doctype": "Exam Question",
			"exam": exam,
			"sequence": next_sequence,
			"question_type": question_type,
			"question_text": question_text,
			"option_a": option_a,
			"option_b": option_b,
			"option_c": option_c,
			"option_d": option_d,
			"correct_option": correct_option,
			"marks": marks,
		}
	)
	question.insert()
	return success(data=question.as_dict(), message="Question added.")


@frappe.whitelist(methods=["POST"])
def update_question(name, **fields):
	require_hr()

	question = frappe.get_doc("Exam Question", name)
	exam_doc = frappe.get_doc("Exam", question.exam)
	if exam_doc.status != "Draft":
		gdl_error("Questions can only be edited while the exam is a Draft.")

	for field in (
		"question_type",
		"question_text",
		"option_a",
		"option_b",
		"option_c",
		"option_d",
		"correct_option",
		"marks",
	):
		if field in fields:
			question.set(field, fields[field])
	if question.question_type == "True or False":
		question.option_a, question.option_b, question.option_c, question.option_d = "True", "False", None, None
	question.save()
	return success(data=question.as_dict(), message="Question updated.")


@frappe.whitelist(methods=["POST"])
def delete_question(name):
	require_hr()

	question = frappe.get_doc("Exam Question", name)
	exam_doc = frappe.get_doc("Exam", question.exam)
	if exam_doc.status != "Draft":
		gdl_error("Questions can only be removed while the exam is a Draft.")

	frappe.delete_doc("Exam Question", name)
	return success(message="Question removed.")


def _exam_invite_email(applicant, exam, job_title):
	link = get_url(f"/exams/{applicant['attempt_name']}")
	message = f"""
		<p>Hi {frappe.utils.escape_html(applicant['applicant_name'])},</p>
		<p>You've been invited to take the exam for <strong>{frappe.utils.escape_html(job_title)}</strong>.</p>
		<p>Exam window: {exam.opens_on} to {exam.closes_on} ({exam.duration_minutes} minutes).</p>
		<p>Take the exam here: <a href="{link}">{link}</a></p>
	"""
	send_email_or_log(
		recipients=[applicant["email_id"]],
		subject=f"Exam scheduled - {job_title}",
		message=message,
		log_fallback=f"exam invite for {applicant['email_id']}, exam {exam.name}",
	)


@frappe.whitelist(methods=["POST"])
def publish_exam(name):
	require_hr()

	exam = frappe.get_doc("Exam", name)
	if exam.status != "Draft":
		gdl_error("Only a Draft exam can be published.")

	questions = _questions_for(exam.name, include_answers=False)
	if not questions:
		gdl_error("Add at least one question before publishing.")

	# Only one Published exam per vacancy at a time - archive whatever was
	# live before (there shouldn't normally be one, since create_exam blocks
	# a second Draft/Published exam, but a prior Published exam from before
	# this Draft was created is still possible).
	for other in frappe.get_all("Exam", filters={"job_opening": exam.job_opening, "status": "Published"}):
		frappe.db.set_value("Exam", other.name, "status", "Archived")

	job_title = frappe.db.get_value("Job Opening", exam.job_opening, "job_title")

	candidates = frappe.get_all(
		"Job Application",
		filters={"job_opening": exam.job_opening, "status": "Exam Invited / Scheduled"},
		fields=["name", "job_applicant"],
	)
	already_invited = set(
		frappe.get_all("Exam Attempt", filters={"exam": exam.name}, pluck="job_application")
	)

	applicants = {}
	if candidates:
		applicants = {
			row.name: row
			for row in frappe.get_all(
				"Job Applicant",
				filters={"name": ["in", [c.job_applicant for c in candidates]]},
				fields=["name", "applicant_name", "email_id"],
			)
		}

	invited = 0
	for candidate in candidates:
		if candidate.name in already_invited:
			continue
		attempt = frappe.get_doc(
			{
				"doctype": "Exam Attempt",
				"exam": exam.name,
				"job_application": candidate.name,
				"job_applicant": candidate.job_applicant,
				"status": "Invited",
			}
		)
		attempt.insert(ignore_permissions=True)
		invited += 1

		applicant = applicants.get(candidate.job_applicant)
		if applicant:
			# insert() always forces owner = the acting (HR) session user,
			# not something we can set beforehand - same fix already used
			# for Job Applicant/Job Application, needed here too so the
			# if_owner Custom DocPerm grant actually scopes to the applicant.
			frappe.db.set_value("Exam Attempt", attempt.name, "owner", applicant.email_id)
			try:
				_exam_invite_email(
					{
						"applicant_name": applicant.applicant_name,
						"email_id": applicant.email_id,
						"attempt_name": attempt.name,
					},
					exam,
					job_title,
				)
			except Exception as e:
				# One candidate's malformed data (or any other unexpected
				# failure) shouldn't roll back every attempt already created
				# for the rest of the invited candidates in this publish.
				gdl_log_error(f"Exam invite email failed for {applicant.email_id}", exc=e)

	exam.total_marks = sum(q.marks or 0 for q in questions)
	exam.status = "Published"
	exam.save()

	return success(data={"invited": invited}, message=f"Exam published. {invited} candidate(s) invited.")


@frappe.whitelist()
def get_exam_queue(job_opening):
	require_hr()

	exam = _get_active_exam(job_opening)
	if not exam or exam.status != "Published":
		return success(data={"exam": exam.as_dict() if exam else None, "attempts": []})

	attempts = frappe.get_all(
		"Exam Attempt",
		filters={"exam": exam.name},
		fields=["name", "job_application", "job_applicant", "status", "total_score", "is_fully_graded", "is_pass"],
		order_by="creation asc",
	)
	if not attempts:
		return success(data={"exam": exam.as_dict(), "attempts": []})

	applicants = {
		row.name: row
		for row in frappe.get_all(
			"Job Applicant",
			filters={"name": ["in", [a.job_applicant for a in attempts]]},
			fields=["name", "applicant_name", "email_id"],
		)
	}
	pending_attempts = set(
		frappe.get_all(
			"Exam Attempt Answer",
			filters={"parent": ["in", [a.name for a in attempts]], "is_graded": 0},
			pluck="parent",
		)
	)

	rows = []
	for attempt in attempts:
		applicant = applicants.get(attempt.job_applicant, {})
		rows.append(
			{
				"name": attempt.name,
				"applicant_name": applicant.get("applicant_name"),
				"email_id": applicant.get("email_id"),
				"status": attempt.status,
				"total_score": attempt.total_score,
				"is_fully_graded": attempt.is_fully_graded,
				"is_pass": attempt.is_pass,
				"has_pending_grading": attempt.status == "Submitted" and attempt.name in pending_attempts,
			}
		)

	return success(data={"exam": exam.as_dict(), "attempts": rows})


@frappe.whitelist()
def get_attempt_detail(attempt):
	"""One attempt's full question-by-question detail - backs the manual
	Short Answer grading form (only the Short Answer rows are editable
	there, but MCQ/True-or-False rows are included too so HR can review the
	whole attempt in one place)."""
	require_hr()

	attempt_doc = frappe.get_doc("Exam Attempt", attempt)
	questions = frappe.get_all(
		"Exam Question",
		filters={"exam": attempt_doc.exam},
		fields=["name", "sequence", "question_type", "question_text", "marks"],
		order_by="sequence asc, creation asc",
	)
	answers = {
		row.question: row
		for row in frappe.get_all(
			"Exam Attempt Answer",
			filters={"parent": attempt},
			fields=["name", "question", "selected_option", "short_answer_text", "score_given", "is_graded", "is_correct"],
		)
	}

	rows = []
	for question in questions:
		answer = answers.get(question.name)
		rows.append(
			{
				"question": question.name,
				"question_type": question.question_type,
				"question_text": question.question_text,
				"marks": question.marks,
				"answer_name": answer.name if answer else None,
				"selected_option": answer.selected_option if answer else None,
				"short_answer_text": answer.short_answer_text if answer else None,
				"score_given": answer.score_given if answer else None,
				"is_graded": bool(answer.is_graded) if answer else False,
				"is_correct": bool(answer.is_correct) if answer else False,
			}
		)

	return success(data={"attempt": attempt_doc.as_dict(), "questions": rows})


@frappe.whitelist(methods=["POST"])
def close_and_mark_absent(exam):
	require_hr()

	exam_doc = frappe.get_doc("Exam", exam)
	if now_datetime() < exam_doc.closes_on:
		gdl_error("The exam window hasn't closed yet.")

	attempts = frappe.get_all(
		"Exam Attempt", filters={"exam": exam, "status": ["in", ["Invited", "In Progress"]]}, fields=["name", "job_application"]
	)
	for attempt in attempts:
		frappe.db.set_value("Exam Attempt", attempt.name, "status", "Not Attended")
		frappe.db.set_value("Job Application", attempt.job_application, "status", "Exam Not Attended")

	return success(data={"marked_absent": len(attempts)}, message=f"{len(attempts)} candidate(s) marked not attended.")


@frappe.whitelist(methods=["POST"])
def grade_answers(attempt, scores):
	require_hr()

	if isinstance(scores, str):
		scores = frappe.parse_json(scores)
	if not scores:
		gdl_error("Enter at least one score before saving.")

	attempt_doc = frappe.get_doc("Exam Attempt", attempt)
	question_marks = {q.name: q.marks for q in frappe.get_all("Exam Question", filters={"exam": attempt_doc.exam}, fields=["name", "marks"])}

	for answer_name, score in scores.items():
		answer = frappe.get_doc("Exam Attempt Answer", answer_name)
		if answer.parent != attempt:
			continue
		max_score = question_marks.get(answer.question, 0)
		clamped = max(0, min(frappe.utils.flt(score), max_score))
		answer.db_set("score_given", clamped)
		answer.db_set("is_graded", 1)

	finalize_attempt_grading(attempt_doc)
	attempt_doc.reload()
	return success(data=attempt_doc.as_dict(), message="Scores saved.")


@frappe.whitelist(methods=["POST"])
def advance_from_exam(job_opening, cutoff):
	require_hr()

	cutoff = frappe.utils.cint(cutoff)
	if cutoff <= 0:
		gdl_error("Enter a cutoff greater than 0.")

	completed = frappe.get_all(
		"Job Application", filters={"job_opening": job_opening, "status": "Exam Completed"}, fields=["name"]
	)
	if not completed:
		gdl_error("No completed exam candidates to advance.")

	scores = {
		row.job_application: row.total_score or 0
		for row in frappe.get_all(
			"Exam Attempt",
			filters={"job_application": ["in", [a.name for a in completed]]},
			fields=["job_application", "total_score"],
		)
	}
	ranked = sorted(completed, key=lambda a: scores.get(a.name, 0), reverse=True)
	advancing = ranked[:cutoff]

	for app in advancing:
		frappe.db.set_value("Job Application", app.name, "status", "Interview Invited / Scheduled")

	return success(
		data={"advanced": len(advancing)},
		message=f"{len(advancing)} candidate(s) advanced to Interview Invited / Scheduled.",
	)
