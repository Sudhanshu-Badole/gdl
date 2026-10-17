"""Shared document-key registry + verification-status helpers (client
feedback, Phase 1). A single source of truth for every fixed document an
applicant uploads onto Job Applicant, used by both the applicant-side upload
endpoints (gdl/api/applicant.py) and the HR-side verification endpoints
(gdl/api/hr.py) so adding a new document type in future never means updating
two independent lists.

Verification status lives in a child table (custom_document_verifications ->
Job Applicant Document Verification) rather than one Custom Field per
document, since rows are keyed by document_key and created lazily - no
schema change needed to add a 7th document type later.

The free-form "Other Supporting Documents" list (gdl_other_documents ->
Job Applicant Document) is unrelated to this registry - each of its rows
carries its own "status" field directly (see that doctype's JSON) since
those rows aren't fixed/keyed.
"""

from urllib.parse import unquote

from frappe.utils import now_datetime

# key -> (fieldname on Job Applicant, display label, mandatory for submission)
DOCUMENT_KEYS = {
	"cv": ("resume_attachment", "Curriculum Vitae (CV)", True),
	"national_id": ("gdl_national_id", "CID / National ID", True),
	"academic_certificate": ("gdl_academic_certificate", "Academic Certificate", True),
	"experience_letter": ("gdl_experience_letter", "Experience Letter", False),
	"medical_certificate": ("custom_medical_certificate", "Medical Certificate", True),
	"security_clearance": ("custom_security_clearance", "Security Clearance", True),
}


def _find_verification_row(doc, document_key):
	for row in doc.get("custom_document_verifications"):
		if row.document_key == document_key:
			return row
	return None


def get_or_create_verification_row(doc, document_key):
	"""Return the verification row for this document key on an in-memory doc,
	appending a fresh "Submitted" row if none exists yet. Does not save -
	callers that mutate status are responsible for doc.save()."""
	row = _find_verification_row(doc, document_key)
	if row:
		return row
	return doc.append("custom_document_verifications", {"document_key": document_key, "status": "Submitted"})


def document_status(doc, document_key):
	"""Read-only: a document with no verification row yet is implicitly
	Submitted (or not-yet-uploaded - callers distinguish that via the file
	field itself), so this never mutates/saves the doc just to answer a
	status question."""
	row = _find_verification_row(doc, document_key)
	return row.status if row else "Submitted"


def document_status_info(doc, document_key):
	"""Read-only: status + any HR remark (set on Sent Back), for surfacing
	what the applicant needs to fix without mutating/saving the doc."""
	row = _find_verification_row(doc, document_key)
	return {"status": row.status if row else "Submitted", "remark": row.remark if row else None}


def reset_document_status(doc, document_key):
	"""Revert a document's verification status to Submitted - call whenever
	the applicant (re)uploads it, so a previously Verified/Sent Back
	document doesn't keep a stale status against a new file. Saves doc."""
	row = get_or_create_verification_row(doc, document_key)
	row.status = "Submitted"
	row.remark = None
	row.reviewed_by = None
	row.reviewed_on = None
	doc.save()


def tor_filename(file_url):
	"""Human-readable filename for a Job Opening's Terms of Reference
	attachment, used wherever the TOR link is rendered (public vacancy page,
	applicant portal once shortlisted, panel view - see [[gdl-client-feedback-batch]]
	Phase 3 TOR access rules)."""
	if not file_url:
		return None
	return unquote(file_url).rsplit("/", 1)[-1]


def set_verification_status(doc, document_key, status, remark=None, reviewed_by=None):
	"""HR sets Verified/Sent Back on a document. Saves doc."""
	row = get_or_create_verification_row(doc, document_key)
	row.status = status
	row.remark = remark
	row.reviewed_by = reviewed_by
	row.reviewed_on = now_datetime()
	doc.save()
	return row
