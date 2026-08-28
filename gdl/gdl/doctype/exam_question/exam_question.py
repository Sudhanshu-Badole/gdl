# Copyright (c) 2026, Sudhanshu Badole and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ExamQuestion(Document):
	def validate(self):
		if self.question_type != "Short Answer" and not self.correct_option:
			frappe.throw("Select the correct option for this question.")
