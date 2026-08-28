"""Shared file-upload validation + attach helper (Task 3.1 profile photo,
Task 3.3 documents). Wraps Frappe's own file storage (save_file) rather than
hand-rolling multipart/storage handling - only extension/size validation and
attaching the result to a docfield are custom.
"""

import os

import frappe
from frappe.utils.file_manager import save_file

from gdl.utils.exceptions import gdl_error

# First bytes of each allowed file type, checked against the actual upload
# content - the extension alone is just a filename string an attacker can
# freely spoof. Only covers the extensions this app's callers ever pass in
# (DOCUMENT_EXTENSIONS/PROFILE_PHOTO_EXTENSIONS in gdl.api.applicant); an
# extension with no entry here just skips the content check.
MAGIC_BYTES = {
	"pdf": (b"%PDF",),
	"jpg": (b"\xff\xd8\xff",),
	"jpeg": (b"\xff\xd8\xff",),
	"png": (b"\x89PNG\r\n\x1a\n",),
	"docx": (b"PK\x03\x04",),
}

CHUNK_SIZE = 1024 * 1024


def _read_with_limit(stream, max_size_mb):
	"""Reject an oversized upload as soon as it crosses the cap instead of
	buffering the whole thing into memory first just to measure it."""
	max_bytes = max_size_mb * 1024 * 1024
	buf = bytearray()
	while True:
		chunk = stream.read(CHUNK_SIZE)
		if not chunk:
			break
		buf.extend(chunk)
		if len(buf) > max_bytes:
			gdl_error(f"File too large. Maximum is {max_size_mb} MB")
	return bytes(buf)


def _validate_upload(allowed_extensions, max_size_mb):
	if "file" not in frappe.request.files:
		gdl_error("No file uploaded")

	upload = frappe.request.files["file"]
	filename = upload.filename or ""
	ext = os.path.splitext(filename)[1].lower().lstrip(".")
	if ext not in allowed_extensions:
		gdl_error(f"Unsupported file type .{ext}. Allowed: {', '.join(allowed_extensions)}")

	content = _read_with_limit(upload.stream, max_size_mb)

	signatures = MAGIC_BYTES.get(ext)
	if signatures and not any(content.startswith(sig) for sig in signatures):
		gdl_error(f"This file doesn't look like a valid .{ext} file.")

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
