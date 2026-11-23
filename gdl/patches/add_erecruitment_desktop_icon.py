import frappe

# label -> (link, roles allowed to see the tile)
ICONS = {
	"e-Recruitment": ("/HR/Dashboard", ["HR Officer", "System Manager"]),
	"e-Recruitment Panel": ("/panel/dashboard", ["Panel Member"]),
}


def execute():
	"""Frappe desktop tiles: HR -> HR dashboard, Panel Member -> panel dashboard.
	Applicants get no tile. Idempotent (also repairs links/roles)."""
	for label, (link, roles) in ICONS.items():
		icon = (
			frappe.get_doc("Desktop Icon", label)
			if frappe.db.exists("Desktop Icon", label)
			else frappe.new_doc("Desktop Icon")
		)
		icon.label = label
		icon.icon_type = "App"
		icon.link_type = "External"
		icon.app = "gdl"
		icon.link = link
		icon.logo_url = "/assets/gdl/frontend/icon-192.png"
		icon.set("roles", [{"role": r} for r in roles])
		icon.save(ignore_permissions=True)
