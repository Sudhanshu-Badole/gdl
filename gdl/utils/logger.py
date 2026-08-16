import frappe


def get_logger(module):
	"""Return a frappe logger tagged gdl.<module>, e.g. get_logger("applicant.registration").

	Default level is WARNING (dev) / ERROR (prod) - set via bench's `logging`
	site config key if .info()/.debug() calls need to actually show up in
	sites/<site>/logs/gdl.<module>.log.
	"""
	return frappe.logger(f"gdl.{module}", allow_site=True, file_count=5)
