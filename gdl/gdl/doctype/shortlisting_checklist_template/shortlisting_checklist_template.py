# Copyright (c) 2026, Sudhanshu Badole and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ShortlistingChecklistTemplate(Document):
	def validate(self):
		if not self.criteria:
			frappe.throw("Add at least one criterion before saving the checklist template.")
