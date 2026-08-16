"""Route guards for portal www pages (Task 2.3).

Call from a page's get_context(): require_role("HR Officer", "System Manager")
Guests are sent to /login; logged-in users with the wrong role are bounced
to their own home page rather than shown someone else's portal.
"""

import frappe


def require_role(*allowed_roles):
	if frappe.session.user == "Guest":
		frappe.flags.redirect_location = f"/login?redirect-to={frappe.request.path}"
		raise frappe.Redirect

	user_roles = set(frappe.get_roles())
	if not user_roles.intersection(allowed_roles):
		from frappe.website.utils import get_home_page

		frappe.flags.redirect_location = "/" + get_home_page()
		raise frappe.Redirect
