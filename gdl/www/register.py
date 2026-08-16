import frappe


def get_context(context):
	context.no_cache = 1
	if frappe.session.user != "Guest":
		frappe.flags.redirect_location = "/"
		raise frappe.Redirect
