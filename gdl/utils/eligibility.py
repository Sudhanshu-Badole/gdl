"""Vacancy eligibility enforcement (client feedback, Phase 1).

Job Opening's gdl_min_experience_years/gdl_degree_required/
gdl_min_degree_score/gdl_experienced_vacancy/gdl_required_documents fields
existed before this only to drive display (the public vacancy page's
"Eligibility" tags) - nothing checked them server-side before an application
could be submitted. check_vacancy_eligibility() is the single choke point
gdl.api.applicant's get_apply_context() (informational) and
submit_application() (enforced) both call, so the two can never drift.
"""

import frappe
from frappe.utils import flt, getdate

from gdl.utils.documents import DOCUMENT_KEYS


def _total_experience_years(applicant_doc):
	today = getdate()
	total_days = 0
	for row in applicant_doc.get("gdl_employment_history") or []:
		if not row.start_date:
			continue
		start = getdate(row.start_date)
		end = today if row.currently_working else (getdate(row.end_date) if row.end_date else start)
		if end > start:
			total_days += (end - start).days
	return total_days / 365.25


def _meets_min_degree_score(applicant_doc, min_score):
	for row in applicant_doc.get("gdl_education") or []:
		if row.score_percent not in (None, "") and flt(row.score_percent) >= flt(min_score):
			return True
	return False


def _required_document_keys(job_opening_name):
	return frappe.get_all(
		"Job Opening Required Document",
		filters={"parent": job_opening_name, "document_key": ["not in", ["Other", ""]]},
		pluck="document_key",
	)


def check_vacancy_eligibility(applicant_doc, opening):
	"""Returns a list of human-readable blocker messages - empty if eligible.

	`opening` needs at least: name, gdl_job_type, gdl_min_experience_years,
	gdl_degree_required, gdl_min_degree_score, gdl_experienced_vacancy (see
	gdl.api.applicant._get_open_job_opening).
	"""
	blockers = []
	min_experience_years = opening.get("gdl_min_experience_years")
	min_degree_score = opening.get("gdl_min_degree_score")

	if min_experience_years and opening.get("gdl_job_type") != "Fresh Graduate":
		if _total_experience_years(applicant_doc) < flt(min_experience_years):
			blockers.append(
				f"This role requires at least {min_experience_years} year(s) of work experience. "
				"Add more entries to your Employment section."
			)

	if opening.get("gdl_degree_required"):
		if not applicant_doc.get("gdl_education"):
			blockers.append(
				"This role requires a qualification on file. Add at least one entry to your Education section."
			)
		elif min_degree_score and not _meets_min_degree_score(applicant_doc, min_degree_score):
			blockers.append(
				f"This role requires a minimum qualification score of {min_degree_score}%. "
				"Enter your score in the Education section."
			)

	if opening.get("gdl_experienced_vacancy") and not applicant_doc.get("gdl_experience_letter"):
		blockers.append(
			"This vacancy requires proof of work experience. Upload your Experience Letter in the Employment section."
		)

	for key in _required_document_keys(opening.get("name")):
		entry = DOCUMENT_KEYS.get(key)
		if not entry:
			continue
		fieldname, label, _mandatory = entry
		if not applicant_doc.get(fieldname):
			blockers.append(f"This vacancy requires {label}. Upload it in your profile.")

	return blockers
