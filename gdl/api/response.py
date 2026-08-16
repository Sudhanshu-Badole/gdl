def success(data=None, message=None):
	"""Standard success envelope for gdl whitelisted API methods.

	Frappe wraps whatever a whitelisted method returns under a top-level
	"message" key in the JSON response, so the client actually receives
	{"message": {"success": true, "data": ..., "message": ...}}. The
	gdl.call() JS helper (public/js/gdl_api.js) unwraps that automatically.
	"""
	return {"success": True, "data": data, "message": message}


def failure(message, data=None):
	return {"success": False, "data": data, "message": message}
