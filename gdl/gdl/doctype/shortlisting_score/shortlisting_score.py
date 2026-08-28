# Copyright (c) 2026, Sudhanshu Badole and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ShortlistingScore(Document):
	def validate(self):
		self.total_score = sum(row.score_given or 0 for row in self.criterion_scores)
