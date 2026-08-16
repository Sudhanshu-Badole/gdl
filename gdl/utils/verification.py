import frappe
from frappe.utils.verified_command import get_signed_params

from gdl.utils.notifications import send_email_or_log


def send_verification_email(email, full_name):
	"""Email a signed verify-your-email link (Task 2.2). Uses Frappe's own
	HMAC-signed-URL primitive (frappe.utils.verified_command) rather than a
	hand-rolled token scheme, per the spec's "don't roll your own" guidance.
	"""
	verify_url = build_verify_url(email)

	send_email_or_log(
		recipients=[email],
		subject="Verify your GDL e-Recruitment account",
		message=f"""
			<p>Hi {frappe.utils.escape_html(full_name)},</p>
			<p>Thanks for registering. Please verify your email address to activate your account:</p>
			<p><a href="{verify_url}">Verify my email</a></p>
		""",
		log_fallback=f"verification link for {email}: {verify_url}",
	)


def build_verify_url(email):
	"""Test/debug helper - build the same signed URL send_verification_email() emails."""
	params = get_signed_params({"email": email})
	return frappe.utils.get_url(f"/api/method/gdl.api.public.verify_applicant_email?{params}")
