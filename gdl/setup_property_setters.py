"""One-time bootstrap for label-only Property Setters (client feedback,
Phase 1): "Department" -> "Office" and "Open Date" for Job Opening's native
posted_on field. These are pure display relabels - the underlying fieldnames
(department, posted_on) are untouched since other code keys off them.

Also extends native Select options without touching HRMS's own doctype JSON
(client feedback, Phase 3): Job Offer.status gets an "Expired" option, set by
gdl.tasks.expire_stale_offers once gdl_response_deadline passes.

Run via: bench --site <site> execute gdl.setup_property_setters.run

Idempotent - safe to re-run (make_property_setter deletes any prior setter
for the same doctype/field/property before inserting). Exported as a fixture
afterwards (property_setter.json) so new sites get this via `bench migrate`.
"""

from frappe.custom.doctype.property_setter.property_setter import make_property_setter

LABEL_PROPERTY_SETTERS = [
	("Job Opening", "department", "Office"),
	("Job Opening", "posted_on", "Open Date"),
]

OPTIONS_PROPERTY_SETTERS = [
	("Job Offer", "status", "Awaiting Response\nAccepted\nRejected\nCancelled\nExpired"),
]


def run():
	for doctype, fieldname, label in LABEL_PROPERTY_SETTERS:
		make_property_setter(doctype, fieldname, "label", label, "Data")
	for doctype, fieldname, options in OPTIONS_PROPERTY_SETTERS:
		make_property_setter(doctype, fieldname, "options", options, "Small Text")
	print(f"Set {len(LABEL_PROPERTY_SETTERS)} field label(s) and {len(OPTIONS_PROPERTY_SETTERS)} field option list(s).")
