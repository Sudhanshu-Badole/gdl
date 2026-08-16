"""Worked example for the API/error/logging conventions (Task 1.4).

Every later portal API module (public.py, applicant.py, hr.py, panel.py)
should follow this same shape:
- whitelisted with an explicit allow_guest where relevant
- validates input, raises via gdl_error() for user-facing failures
- logs via get_logger(), never bare print()/frappe.log_error() ad hoc
- returns via response.success()/failure(), never a raw dict
"""

import frappe

from gdl.api.response import failure, success
from gdl.utils.exceptions import gdl_error
from gdl.utils.logger import get_logger

logger = get_logger("api.example")


@frappe.whitelist(allow_guest=True)
def ping(name=None):
	if name is not None and not isinstance(name, str):
		gdl_error("`name` must be a string")

	logger.info(f"ping called with name={name!r}")

	if not name:
		return failure("Provide a `name` query param to try the happy path")

	return success(data={"greeting": f"Hello, {name}!"}, message="pong")
