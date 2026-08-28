# Copyright (c) 2026, Sudhanshu Badole and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ExamAttemptAnswer(Document):
	def validate(self):
		# gdl.api.applicant.save_exam_answer's upsert is check-then-insert
		# with no DB-level backstop - this converts a rare near-simultaneous
		# autosave race into a clean error on whichever request loses,
		# rather than a silent duplicate row that corrupts grading.
		duplicate = frappe.db.exists(
			"Exam Attempt Answer",
			{"parent": self.parent, "question": self.question, "name": ["!=", self.name or ""]},
		)
		if duplicate:
			frappe.throw("An answer for this question was already saved.")
