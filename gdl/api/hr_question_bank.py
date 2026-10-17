"""Question Bank (client feedback, Phase 2): a reusable pool of questions,
independent of any one Exam, that HR can draw from when building an exam -
either by hand-picking specific bank items or by pulling a random sample.

Assigning is copy-on-assign, not link/move: a bank item's fields are copied
into a brand new Exam Question row (via gdl.api.hr_exam.add_question, so the
sequencing/validation logic lives in exactly one place). The bank item itself
is untouched and stays available for reuse in any future exam.
"""

import random

import frappe

from gdl.api.hr import require_hr
from gdl.api.hr_exam import add_question
from gdl.api.response import success
from gdl.utils.exceptions import gdl_error

BANK_FIELDS = ("question_type", "question_text", "category", "tags", "option_a", "option_b", "option_c", "option_d", "correct_option", "marks")


@frappe.whitelist()
def list_vacancy_categories():
	require_hr()
	return success(data=frappe.get_all("Vacancy Category", pluck="name", order_by="name asc"))


@frappe.whitelist()
def list_bank_questions(question_type=None, category=None, search=None):
	require_hr()

	filters = {}
	if question_type:
		filters["question_type"] = question_type
	if category:
		filters["category"] = category

	or_filters = None
	if search:
		like = f"%{search}%"
		or_filters = [["question_text", "like", like], ["tags", "like", like]]

	rows = frappe.get_all(
		"Question Bank Item",
		filters=filters,
		or_filters=or_filters,
		fields=["name", *BANK_FIELDS],
		order_by="creation desc",
	)
	return success(data=rows)


@frappe.whitelist(methods=["POST"])
def create_bank_question(question_type, question_text, marks, category=None, tags=None, option_a=None, option_b=None, option_c=None, option_d=None, correct_option=None):
	require_hr()

	if question_type == "True or False":
		option_a, option_b, option_c, option_d = "True", "False", None, None

	doc = frappe.get_doc(
		{
			"doctype": "Question Bank Item",
			"question_type": question_type,
			"question_text": question_text,
			"category": category,
			"tags": tags,
			"option_a": option_a,
			"option_b": option_b,
			"option_c": option_c,
			"option_d": option_d,
			"correct_option": correct_option,
			"marks": marks,
		}
	)
	doc.insert()
	return success(data=doc.as_dict(), message="Question added to bank.")


@frappe.whitelist(methods=["POST"])
def update_bank_question(name, **fields):
	require_hr()

	doc = frappe.get_doc("Question Bank Item", name)
	for field in BANK_FIELDS:
		if field in fields:
			doc.set(field, fields[field])
	doc.save()
	return success(data=doc.as_dict(), message="Question updated.")


@frappe.whitelist(methods=["POST"])
def delete_bank_question(name):
	require_hr()
	frappe.delete_doc("Question Bank Item", name)
	return success(message="Question removed from bank.")


@frappe.whitelist(methods=["POST"])
def bulk_upload_bank_questions(rows):
	"""rows: a list of dicts, each shaped like create_bank_question's params.
	Inserts what it can and reports per-row success/failure rather than
	failing the whole batch on one bad row."""
	require_hr()

	if isinstance(rows, str):
		rows = frappe.parse_json(rows)
	if not rows:
		gdl_error("No rows to upload.")

	results = []
	added = 0
	for i, row in enumerate(rows):
		try:
			question_type = row.get("question_type")
			question_text = row.get("question_text")
			marks = row.get("marks")
			if not question_type or not question_text or marks in (None, ""):
				raise ValueError("question_type, question_text, and marks are required.")

			option_a, option_b, option_c, option_d = row.get("option_a"), row.get("option_b"), row.get("option_c"), row.get("option_d")
			if question_type == "True or False":
				option_a, option_b, option_c, option_d = "True", "False", None, None

			frappe.get_doc(
				{
					"doctype": "Question Bank Item",
					"question_type": question_type,
					"question_text": question_text,
					"category": row.get("category"),
					"tags": row.get("tags"),
					"option_a": option_a,
					"option_b": option_b,
					"option_c": option_c,
					"option_d": option_d,
					"correct_option": row.get("correct_option"),
					"marks": marks,
				}
			).insert()
			added += 1
			results.append({"row": i + 1, "success": True})
		except Exception as e:
			results.append({"row": i + 1, "success": False, "error": str(e)})

	return success(data={"added": added, "results": results}, message=f"{added} of {len(rows)} question(s) added.")


@frappe.whitelist(methods=["POST"])
def assign_manual(exam, bank_question_names):
	require_hr()

	if isinstance(bank_question_names, str):
		bank_question_names = frappe.parse_json(bank_question_names)
	if not bank_question_names:
		gdl_error("Select at least one question to assign.")

	added = 0
	for name in bank_question_names:
		item = frappe.get_doc("Question Bank Item", name)
		add_question(
			exam=exam,
			question_type=item.question_type,
			question_text=item.question_text,
			marks=item.marks,
			option_a=item.option_a,
			option_b=item.option_b,
			option_c=item.option_c,
			option_d=item.option_d,
			correct_option=item.correct_option,
		)
		added += 1

	return success(data={"added": added}, message=f"{added} question(s) assigned from the bank.")


@frappe.whitelist(methods=["POST"])
def assign_random_sample(exam, count, question_type=None, category=None):
	require_hr()

	count = frappe.utils.cint(count)
	if count < 1:
		gdl_error("Enter how many questions to sample.")

	filters = {}
	if question_type:
		filters["question_type"] = question_type
	if category:
		filters["category"] = category

	candidates = frappe.get_all("Question Bank Item", filters=filters, pluck="name")
	if not candidates:
		gdl_error("No matching questions found in the bank.")

	sample = random.sample(candidates, min(count, len(candidates)))
	return assign_manual(exam, sample)
