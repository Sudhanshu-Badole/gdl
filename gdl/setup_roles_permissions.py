"""One-time bootstrap for the Phase 1 role/permission model (Task 1.3).

Run via: bench --site <site> execute gdl.setup_roles_permissions.run

Idempotent — safe to re-run. The resulting Role Profile / Custom DocPerm
records are exported as fixtures afterwards so new sites get this for free
via `bench migrate` on install, without needing to run this again.
"""

import frappe
from frappe.permissions import add_permission, update_permission_property

HR_OFFICER_GRANTS = {
	"Job Opening": {"read": 1, "write": 1, "create": 1, "delete": 1},
	"Job Applicant": {"read": 1, "write": 1, "create": 1},
	"Department": {"read": 1},
	"Designation": {"read": 1},
	"Staffing Plan": {"read": 1},
	"User": {"read": 1},
	# Task 4.0
	"Job Application": {"read": 1, "write": 1, "create": 1, "delete": 1},
	"Vacancy Category": {"read": 1, "write": 1, "create": 1, "delete": 1},
}

PANEL_MEMBER_GRANTS = {
	"Job Applicant": {"read": 1},
	# Task 4.0 - panel members will need this once Phase 7 assigns them
	# interview sessions tied to specific applications; harmless read-only
	# grant to add now while touching this doctype.
	"Job Application": {"read": 1},
}

# Applicants need to read/write their own Job Applicant "profile" record
# (Phase 3), but only their own - if_owner scopes this to doc.owner ==
# session user. See gdl/api/public.py's register_applicant(), which sets
# owner explicitly to the new user's email for this to work correctly.
APPLICANT_PORTAL_USER_GRANTS = {
	"Job Applicant": {"read": 1, "write": 1, "if_owner": 1},
	# Task 4.0 - applicants can submit (create) and view their own
	# applications, but not edit them after submission - no "write" here,
	# deliberately, an application is a point-in-time record, not a mutable
	# profile. Same owner-setting caveat as Job Applicant: whatever creates
	# the Job Application record must explicitly set owner afterwards.
	"Job Application": {"read": 1, "create": 1, "if_owner": 1},
}

ROLE_PROFILES = {
	"HR Officer": ["HR Officer"],
	"Panel Member": ["Panel Member"],
	"Super Admin": ["System Manager", "HR Manager", "HR Officer", "Panel Member"],
}


def grant(doctype, role, if_owner=0, **flags):
	if not frappe.db.get_value("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}):
		add_permission(doctype, role, 0, "read")
	for ptype, value in flags.items():
		if ptype == "read":
			continue
		update_permission_property(doctype, role, 0, ptype, value)
	if if_owner:
		update_permission_property(doctype, role, 0, "if_owner", 1)


def ensure_role_profile(name, roles):
	if frappe.db.exists("Role Profile", name):
		doc = frappe.get_doc("Role Profile", name)
	else:
		doc = frappe.new_doc("Role Profile")
		doc.role_profile = name
	existing = {row.role for row in doc.roles}
	for role in roles:
		if role not in existing:
			doc.append("roles", {"role": role})
	doc.save()


def run():
	role = frappe.get_doc("Role", "Applicant Portal User")
	if role.desk_access:
		role.desk_access = 0
		role.save()

	for name, roles in ROLE_PROFILES.items():
		ensure_role_profile(name, roles)

	for doctype, flags in HR_OFFICER_GRANTS.items():
		grant(doctype, "HR Officer", **flags)

	for doctype, flags in PANEL_MEMBER_GRANTS.items():
		grant(doctype, "Panel Member", **flags)

	for doctype, flags in APPLICANT_PORTAL_USER_GRANTS.items():
		flags = dict(flags)
		if_owner = flags.pop("if_owner", 0)
		grant(doctype, "Applicant Portal User", if_owner=if_owner, **flags)

	frappe.db.commit()
	print("Roles & permissions bootstrap complete.")
