"""Post-login / role-based home page resolution (Task 2.3).

Wired via the `get_website_user_home_page` hook in hooks.py.
"""

import frappe

# Checked in order - first matching role wins. Explicit priority instead of
# relying on frappe.get_roles() ordering, which isn't guaranteed and would
# make the redirect non-deterministic for a user holding multiple roles
# (e.g. Super Admin, which bundles System Manager + HR Officer + Panel
# Member all at once).
ROLE_HOME_PAGES = [
	("System Manager", "HR/Dashboard"),
	("HR Officer", "HR/Dashboard"),
	("Panel Member", "panel/dashboard"),
	("Applicant Portal User", "dashboard"),
]


def get_home_page(user):
	# The Administrator account always holds every role, including System
	# Manager - without this it would match ROLE_HOME_PAGES' first entry and
	# land on the HR portal instead of Frappe's own Desk, which is the
	# expected default for this specific superuser account (not for other
	# System Manager holders, e.g. the Super Admin role profile, who should
	# still default to the HR portal below).
	if user == "Administrator":
		return "desk"

	user_roles = set(frappe.get_roles(user))
	for role, page in ROLE_HOME_PAGES:
		if role in user_roles:
			return page
	return None
