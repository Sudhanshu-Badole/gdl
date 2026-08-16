"""Ad hoc permission boundary check for Task 1.3 (updated Phase 3 / Task 3.1
for the new if_owner Job Applicant grant).

Run via: bench --site <site> execute gdl.verify_role_boundaries.run

Creates throwaway users (one per custom role, plus two Applicant Portal
Users with their own Job Applicant records) and checks their permission
boundaries with frappe.has_permission(), then deletes everything. Not part
of the automated test suite (that's Phase 11) - just a one-time sanity check
that the Custom DocPerm setup in setup_roles_permissions.py actually
enforces what permission_matrix.md claims.
"""

import frappe

# "User" is deliberately excluded: Frappe's own has_permission hook for User
# (frappe.core.doctype.user.user.has_permission) allows any logged-in,
# non-Administrator user to read basic User records - core behaviour needed
# for things like assignments/@mentions across the whole framework, not
# something Custom DocPerm can (or should) override without a core edit.
# Sensitive fields (password, roles, etc.) stay protected by permlevel, not
# by blocking the doctype outright.
INTERNAL_ONLY_DOCTYPES = ["Department", "Designation", "Staffing Plan"]


def _make_user(email, role):
	if frappe.db.exists("User", email):
		frappe.delete_doc("User", email, force=True)
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": role.replace(" ", ""),
			"send_welcome_email": 0,
			"roles": [{"role": role}],
		}
	)
	user.insert(ignore_permissions=True)
	return user.name


def _make_job_applicant(email):
	if frappe.db.exists("Job Applicant", {"email_id": email}):
		frappe.delete_doc("Job Applicant", email, force=True)
	doc = frappe.get_doc(
		{
			"doctype": "Job Applicant",
			"applicant_name": email,
			"email_id": email,
			"status": "Open",
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert()
	# Same fix as gdl.api.public.register_applicant(): insert() always forces
	# owner = the acting session user, not the dict value.
	frappe.db.set_value("Job Applicant", doc.name, "owner", email)
	return doc.name


def _check(label, condition):
	status = "PASS" if condition else "FAIL"
	print(f"[{status}] {label}")
	return condition


def run():
	results = []
	panel_email = "gdl-verify-panel@example.com"
	applicant_a_email = "gdl-verify-applicant-a@example.com"
	applicant_b_email = "gdl-verify-applicant-b@example.com"

	try:
		_make_user(panel_email, "Panel Member")
		_make_user(applicant_a_email, "Applicant Portal User")
		_make_user(applicant_b_email, "Applicant Portal User")
		job_applicant_a = _make_job_applicant(applicant_a_email)

		frappe.set_user(panel_email)
		for doctype in INTERNAL_ONLY_DOCTYPES:
			results.append(
				_check(
					f"Panel Member blocked from reading {doctype}",
					not frappe.has_permission(doctype, ptype="read"),
				)
			)
		results.append(
			_check(
				"Panel Member can read Job Applicant",
				frappe.has_permission("Job Applicant", ptype="read"),
			)
		)
		results.append(
			_check(
				"Panel Member cannot write Job Applicant",
				not frappe.has_permission("Job Applicant", ptype="write"),
			)
		)

		frappe.set_user(applicant_a_email)
		for doctype in [*INTERNAL_ONLY_DOCTYPES, "Job Opening"]:
			results.append(
				_check(
					f"Applicant Portal User blocked from reading {doctype}",
					not frappe.has_permission(doctype, ptype="read"),
				)
			)
		results.append(
			_check(
				"Applicant A can read their own Job Applicant record",
				frappe.has_permission("Job Applicant", doc=job_applicant_a, ptype="read"),
			)
		)

		frappe.set_user(applicant_b_email)
		results.append(
			_check(
				"Applicant B CANNOT read Applicant A's Job Applicant record (if_owner)",
				not frappe.has_permission("Job Applicant", doc=job_applicant_a, ptype="read"),
			)
		)

		frappe.set_user(applicant_a_email)
		applicant_role = frappe.get_doc("Role", "Applicant Portal User")
		results.append(
			_check("Applicant Portal User role has no Desk Access", not applicant_role.desk_access)
		)

	finally:
		frappe.set_user("Administrator")
		for email in (applicant_a_email, applicant_b_email):
			if frappe.db.exists("Job Applicant", {"email_id": email}):
				frappe.delete_doc("Job Applicant", email, force=True)
		for email in (panel_email, applicant_a_email, applicant_b_email):
			if frappe.db.exists("User", email):
				frappe.delete_doc("User", email, force=True)
		frappe.db.commit()

	passed = sum(results)
	print(f"\n{passed}/{len(results)} checks passed")
