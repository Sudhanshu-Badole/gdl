"""Shared file-upload validation + attach helper (Task 3.1 profile photo,
Task 3.3 documents). Wraps Frappe's own file storage (save_file) rather than
hand-rolling multipart/storage handling - only extension/size validation and
attaching the result to a docfield are custom.
"""

import os

import frappe
from frappe.utils.file_manager import save_file

from gdl.utils.exceptions import gdl_error


def _validate_upload(allowed_extensions, max_size_mb):
	if "file" not in frappe.request.files:
		gdl_error("No file uploaded")

	upload = frappe.request.files["file"]
	filename = upload.filename or ""
	ext = os.path.splitext(filename)[1].lower().lstrip(".")
	if ext not in allowed_extensions:
		gdl_error(f"Unsupported file type .{ext}. Allowed: {', '.join(allowed_extensions)}")

	content = upload.stream.read()
	size_mb = len(content) / (1024 * 1024)
	if size_mb > max_size_mb:
		gdl_error(f"File too large ({size_mb:.1f} MB). Maximum is {max_size_mb} MB")

	return filename, content


def save_upload(doc, fieldname, allowed_extensions, max_size_mb=5, is_private=1):
	"""Validate frappe.request.files['file'] and attach it to doc.fieldname.

	Caller is responsible for having already verified the requester owns `doc`.
	"""
	filename, content = _validate_upload(allowed_extensions, max_size_mb)
	file_doc = save_file(filename, content, doc.doctype, doc.name, is_private=is_private, df=fieldname)
	doc.set(fieldname, file_doc.file_url)
	doc.save()
	return file_doc.file_url


def save_upload_for_child_row(doc, allowed_extensions, max_size_mb=5, is_private=1):
	"""Same validation as save_upload(), but for an Attach field that lives on
	a child-table row rather than directly on `doc` - there's no single
	docfield to auto-attach to here, so this just stores the file and returns
	its URL for the caller to set on the child row themselves.
	"""
	filename, content = _validate_upload(allowed_extensions, max_size_mb)
	file_doc = save_file(filename, content, doc.doctype, doc.name, is_private=is_private)
	return file_doc.file_url
