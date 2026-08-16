import frappe


def get_context(context):
	context.no_cache = 1
	if frappe.session.user == "Guest":
		frappe.flags.redirect_location = "/login?redirect-to=/complete-profile"
		raise frappe.Redirect

	# Personal info is shown immediately on page load (per spec) - fetched
	# server-side here rather than async, unlike education/employment/documents
	# which the page loads asynchronously via gdl.call().
	context.applicant = frappe.db.get_value(
		"Job Applicant",
		{"email_id": frappe.session.user},
		[
			"applicant_name",
			"phone_number",
			"gdl_date_of_birth",
			"gdl_gender",
			"gdl_nationality",
			"gdl_permanent_address",
			"gdl_current_address",
			"gdl_profile_photo",
		],
		as_dict=True,
	)
	context.genders = frappe.get_all("Gender", pluck="name", order_by="name")
	context.countries = frappe.get_all("Country", pluck="name", order_by="name")
