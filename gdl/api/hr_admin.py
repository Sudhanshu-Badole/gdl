"""Super Admin staff account management (Phase 9, partial). Every function
is gated to System Manager specifically, not just any HR Officer - same
code-level-gate-not-DocPerm pattern already used by
gdl.api.hr_interview.unlock_session. Operates directly on the native User
doctype; all writes use ignore_permissions=True since the System Manager
check above is the real gate, not a Custom DocPerm.
"""

import frappe

from gdl.api.response import success
from gdl.utils.audit import log_action
from gdl.utils.exceptions import gdl_error

STAFF_ROLES = ("HR Officer", "Panel Member")


def require_super_admin():
	frappe.only_for("System Manager")


@frappe.whitelist()
def list_staff_accounts():
	require_super_admin()

	rows = frappe.get_all(
		"Has Role", filters={"role": ["in", STAFF_ROLES], "parenttype": "User"}, fields=["parent", "role"]
	)
	role_by_user = {}
	for row in rows:
		# an account is expected to hold exactly one of the two staff roles;
		# if it somehow holds both, the first one found just wins for display.
		role_by_user.setdefault(row.parent, row.role)
	if not role_by_user:
		return success(data=[])

	users = frappe.get_all(
		"User",
		filters={"name": ["in", list(role_by_user.keys())]},
		fields=["name", "full_name", "email", "enabled"],
		order_by="full_name asc",
	)
	for user in users:
		user["role"] = role_by_user.get(user.name)
	return success(data=users)


@frappe.whitelist(methods=["POST"])
def create_staff_account(email, first_name, last_name, role, password):
	require_super_admin()

	if role not in STAFF_ROLES:
		gdl_error("Role must be HR Officer or Panel Member.")
	if frappe.db.exists("User", email):
		gdl_error("An account with this email already exists.")

	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": first_name,
			"last_name": last_name,
			"enabled": 1,
			"send_welcome_email": 0,
			"new_password": password,
			"roles": [{"role": role}],
		}
	)
	user.flags.ignore_permissions = True
	user.flags.ignore_password_policy = True
	user.insert()
	log_action(
		action="Staff account created",
		reference_doctype="User",
		reference_name=user.name,
		details=f"role: {role}",
	)
	return success(data={"name": user.name}, message="Account created.")


@frappe.whitelist(methods=["POST"])
def update_staff_account(user, first_name=None, last_name=None, role=None):
	require_super_admin()

	if role is not None and role not in STAFF_ROLES:
		gdl_error("Role must be HR Officer or Panel Member.")

	doc = frappe.get_doc("User", user)
	if first_name is not None:
		doc.first_name = first_name
	if last_name is not None:
		doc.last_name = last_name
	if role is not None:
		doc.roles = [row for row in doc.roles if row.role not in STAFF_ROLES]
		doc.append("roles", {"role": role})

	doc.flags.ignore_permissions = True
	doc.save()
	log_action(action="Staff account updated", reference_doctype="User", reference_name=doc.name)
	return success(message="Account updated.")


@frappe.whitelist(methods=["POST"])
def set_account_enabled(user, enabled):
	require_super_admin()

	enabled = 1 if frappe.utils.cint(enabled) else 0
	frappe.db.set_value("User", user, "enabled", enabled)
	log_action(
		action="Staff account enabled" if enabled else "Staff account deactivated",
		reference_doctype="User",
		reference_name=user,
	)
	return success(message="Account enabled." if enabled else "Account deactivated.")


@frappe.whitelist(methods=["POST"])
def reset_staff_password(user, new_password):
	require_super_admin()

	doc = frappe.get_doc("User", user)
	doc.new_password = new_password
	doc.flags.ignore_permissions = True
	doc.flags.ignore_password_policy = True
	doc.save()
	log_action(action="Staff password reset", reference_doctype="User", reference_name=doc.name)
	return success(message="Password reset.")
