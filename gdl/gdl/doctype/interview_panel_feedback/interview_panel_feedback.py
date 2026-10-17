# Copyright (c) 2026, Sudhanshu Badole and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class InterviewPanelFeedback(Document):
	def validate(self):
		duplicate = frappe.db.exists(
			"Interview Panel Feedback",
			{
				"interview_session": self.interview_session,
				"panel_member": self.panel_member,
				"name": ["!=", self.name or ""],
			},
		)
		if duplicate:
			frappe.throw("You've already submitted feedback for this candidate.")

		self.total_score = sum(row.score_given or 0 for row in self.criterion_scores)
