"""Shared resilient-email-send helper (Task 2.2 email verification, Task 4.4
application confirmation). Queues via frappe.sendmail(); if no outgoing
Email Account is configured, falls back to logging instead of failing the
calling request - per the "log emails in dev when SMTP is unset" requirement.
"""

import frappe

from gdl.utils.logger import get_logger

logger = get_logger("utils.notifications")


def send_email_or_log(recipients, subject, message, log_fallback):
	try:
		frappe.sendmail(recipients=recipients, subject=subject, message=message)
		logger.info(f"email queued for {recipients}: {subject}")
	except frappe.OutgoingEmailError:
		frappe.clear_last_message()
		logger.warning(f"SMTP not configured - {log_fallback}")
