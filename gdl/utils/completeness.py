"""Profile completeness scoring (Task 3.4).

Weighted so that a mostly-filled-out profile can cross the spec's 80%
threshold, but every section still needs genuine substance to get there:
- Personal info (30%): split evenly across 6 fields
- Education (20%): at least one record
- Employment history (20%): at least one record
- Mandatory documents (30%): split evenly across CV/ID/Certificate

Wired via the Job Applicant "validate" doc_event (hooks.py) - runs as part
of every save, not a separate write, so there's no double-save/hook-loop risk.
"""

from gdl.utils.documents import DOCUMENT_KEYS

PERSONAL_INFO_FIELDS = [
	"gdl_date_of_birth",
	"gdl_gender",
	"gdl_nationality",
	"gdl_permanent_address",
	"gdl_current_address",
	"gdl_profile_photo",
]
# Derived from the shared registry so a new mandatory document (e.g. client
# feedback's Medical Certificate/Security Clearance) automatically counts
# here too, instead of needing this list updated separately.
MANDATORY_DOCUMENT_FIELDS = [fieldname for fieldname, _label, mandatory in DOCUMENT_KEYS.values() if mandatory]

PERSONAL_INFO_WEIGHT = 30
EDUCATION_WEIGHT = 20
EMPLOYMENT_WEIGHT = 20
DOCUMENTS_WEIGHT = 30

COMPLETENESS_THRESHOLD = 80


def compute_completeness(doc):
	"""Weighted profile completeness score (0-100) for a Job Applicant doc."""
	score = 0.0

	filled_personal = sum(1 for f in PERSONAL_INFO_FIELDS if doc.get(f))
	score += PERSONAL_INFO_WEIGHT * (filled_personal / len(PERSONAL_INFO_FIELDS))

	if doc.get("gdl_education"):
		score += EDUCATION_WEIGHT

	if doc.get("gdl_employment_history"):
		score += EMPLOYMENT_WEIGHT

	filled_docs = sum(1 for f in MANDATORY_DOCUMENT_FIELDS if doc.get(f))
	score += DOCUMENTS_WEIGHT * (filled_docs / len(MANDATORY_DOCUMENT_FIELDS))

	return round(score, 2)


def set_completeness_on_save(doc, method=None):
	doc.gdl_profile_completeness = compute_completeness(doc)
