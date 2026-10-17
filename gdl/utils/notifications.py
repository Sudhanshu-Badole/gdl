"""Shared resilient-email-send helper (Task 2.2 email verification, Task 4.4
application confirmation). Queues via frappe.sendmail(); if no outgoing
Email Account is configured, falls back to logging instead of failing the
calling request - per the "log emails in dev when SMTP is unset" requirement.
"""

import frappe
from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification

from gdl.utils.logger import get_logger

logger = get_logger("utils.notifications")


def send_email_or_log(recipients, subject, message, log_fallback, attachments=None):
	try:
		frappe.sendmail(recipients=recipients, subject=subject, message=message, attachments=attachments)
		logger.info(f"email queued for {recipients}: {subject}")
	except frappe.OutgoingEmailError:
		frappe.clear_last_message()
		logger.warning(f"SMTP not configured - {log_fallback}")


def notify_user(user, subject, document_type=None, document_name=None, link=None, dedupe_on=None):
	"""In-app bell notification via Frappe core's Notification Log - a thin
	wrapper, not a replacement for send_email_or_log above; call both at each
	event point. `user` is the recipient's email (User.name in this app).

	Deliberately leaves from_user unset (not frappe.session.user): these are
	system-generated recruitment-lifecycle notifications, not user-to-user
	mentions/shares, and several fire from the recipient's own self-service
	action (e.g. submit_application) - make_notification_logs() silently
	drops a notification when for_user == from_user, so attributing it to
	the acting session user would make an applicant's own confirmation
	notification vanish.
	"""
	enqueue_create_notification(
		users=user,
		doc={
			"subject": subject,
			"document_type": document_type,
			"document_name": document_name,
			"link": link,
		},
		dedupe_on=dedupe_on,
	)
