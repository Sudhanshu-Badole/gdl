# Copyright (c) 2026, Sudhanshu Badole and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class InterviewSchedule(Document):
	def validate(self):
		# gdl.api.hr_interview.create_interview's own "one Draft/Published
		# interview per vacancy" check is check-then-insert - this closes
		# that race at the model layer, regardless of call path (same
		# pattern as Exam.validate()).
		if self.status not in ("Draft", "Published"):
			return
		duplicate = frappe.db.exists(
			"Interview Schedule",
			{
				"job_opening": self.job_opening,
				"status": ["in", ("Draft", "Published")],
				"name": ["!=", self.name or ""],
			},
		)
		if duplicate:
			frappe.throw("An interview already exists for this vacancy. Edit or archive it before creating another.")
