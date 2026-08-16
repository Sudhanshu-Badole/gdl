from gdl.utils.access import require_role


def get_context(context):
	context.no_cache = 1
	require_role("Panel Member")
