import frappe

PORTAL_ROLES = {"HR Officer", "System Manager", "Panel Member"}


def has_app_permission():
	"""Gate for the e-Recruitment desktop tiles. Applicants never see them;
	which tile each role gets is set by the roles on each Desktop Icon
	(see gdl.patches.add_erecruitment_desktop_icon)."""
	return bool(PORTAL_ROLES & set(frappe.get_roles()))
