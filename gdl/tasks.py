"""Scheduled tasks (client feedback, Phase 3). First real entry in
gdl.hooks.scheduler_events["daily"] - mirrors the structure of HRMS's own
close_expired_job_openings (hrms.hr.doctype.job_opening.job_opening).
"""

from frappe.utils import getdate

import frappe

from gdl.utils.audit import set_application_status


def expire_stale_offers():
	"""Any Job Offer still Awaiting Response past its gdl_response_deadline
	is flipped to the "Expired" option added via setup_property_setters, and
	the linked Job Application follows to "Offer Expired". Response
	deadlines are Date fields (no time component), so a deadline of "today"
	is not yet expired - only strictly-past dates are."""
	today = getdate()

	Offer = frappe.qb.DocType("Job Offer")
	offers = (
		frappe.qb.from_(Offer)
		.select(Offer.name, Offer.gdl_job_application)
		.where(
			(Offer.status == "Awaiting Response")
			& (Offer.gdl_response_deadline.isnotnull())
			& (Offer.gdl_response_deadline < today)
			& (Offer.docstatus != 2)
		)
	).run(as_dict=True)

	for offer in offers:
		frappe.db.set_value("Job Offer", offer.name, "status", "Expired")
		if offer.gdl_job_application:
			set_application_status(offer.gdl_job_application, "Offer Expired", action="Offer expired (response deadline passed)")
