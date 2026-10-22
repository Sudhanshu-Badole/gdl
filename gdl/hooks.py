app_name = "gdl"
app_title = "Gdl"
app_publisher = "Sudhanshu Badole"
app_description = "GDL"
app_email = "sudhanshubadole@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "gdl",
# 		"logo": "/assets/gdl/logo.png",
# 		"title": "Gdl",
# 		"route": "/gdl",
# 		"has_permission": "gdl.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/gdl/css/gdl.css"
# app_include_js = "/assets/gdl/js/gdl.js"

# include js, css files in header of web template
# web_include_css = "/assets/gdl/css/gdl.css"
# web_include_js = "/assets/gdl/js/gdl.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "gdl/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "gdl/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# gdl/frontend (Vue SPA, served via gdl/gdl/www/frontend.py/.html) - public
# vacancy showcase, no login required. Only affects Guests: for logged-in
# users, get_home_page_via_hooks() checks get_website_user_home_page (below)
# first, which already returns a real role dashboard before ever falling
# back to this hook.
home_page = "frontend"

# website user home page by role (Task 2.3). Using get_website_user_home_page
# (a function) instead of the simpler role_home_page dict: role_home_page
# picks whichever role happens to come first in frappe.get_roles(), which is
# not a guaranteed/deterministic order - a user with multiple roles (e.g.
# Super Admin, which bundles System Manager + HR Officer + Panel Member)
# could get bounced to the wrong dashboard. get_website_user_home_page lets
# us enforce an explicit priority order instead.
get_website_user_home_page = "gdl.auth.get_home_page"

# Fixtures
# --------
# master data + roles/permissions exported so staging/production can be seeded
# identically instead of re-entered by hand (Phase 1 / Task 1.2 & 1.3)

fixtures = [
	{"dt": "Role", "filters": [["name", "in", ["HR Officer", "Panel Member", "Applicant Portal User"]]]},
	{"dt": "Role Profile", "filters": [["name", "in", ["HR Officer", "Panel Member", "Super Admin"]]]},
	{
		"dt": "Custom DocPerm",
		"filters": [["role", "in", ["HR Officer", "Panel Member", "Applicant Portal User"]]],
	},
	{"dt": "Department", "filters": [["company", "=", "GreenDigital Limited"]]},
	{"dt": "Designation"},
	{"dt": "Staffing Plan", "filters": [["company", "=", "GreenDigital Limited"]]},
	# every gdl_-prefixed custom field, on any doctype, auto-captured. New
	# Custom Fields use the custom_ prefix instead (Frappe's own Customize
	# Form convention) - or_filters, not two separate entries: two fixture
	# entries for the same dt export to the same filename (frappe.scrub(dt)
	# + ".json") and the second silently overwrites the first's output.
	{
		"dt": "Custom Field",
		"filters": [["dt", "in", ["Job Applicant", "Job Opening", "Job Offer", "Appointment Letter", "User"]]],
	},
	# Job Opening customizations made via Customize Form: the VAC-.YYYY.-.####
	# naming series (property=autoname), plus label relabels (Department ->
	# Office, posted_on -> Open Date - client feedback, Phase 1).
	{"dt": "Property Setter", "filters": [["doc_type", "in", ["Job Opening", "Job Offer"]]]},
	# Standard HRMS master data that isn't guaranteed to exist on every site
	# (see gdl/setup_master_data.py - this bit a real user when it was missing)
	{"dt": "Job Applicant Source"},
	{"dt": "Employment Type"},
	# Phase 10 - the 5 recruitment Query Reports (see gdl.setup_reports).
	{"dt": "Report", "filters": [["module", "=", "Gdl"]]},
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# custom portal URL rules (e.g. /HR/*, /panel/*) — populated as Phase 2/3+ pages are added
website_route_rules = [
	# HR portal (role-gated /HR/* routes inside the same Vue SPA as the public
	# site, not a separate app - <path:app_path> greedily matches every HR
	# sub-path, e.g. /HR/Dashboard, /HR/Vacancies, /HR/Vacancies/<name>).
	{"from_route": "/HR/<path:app_path>", "to_route": "frontend"},
	# Panel Member portal (Phase 7) - same pattern as /HR/* above, replaces
	# the bare Jinja stub at gdl/www/panel/dashboard.* (now deleted).
	# gdl.auth.get_home_page still redirects Panel Member logins to the
	# lowercase "panel/dashboard" path, hence the lowercase route here.
	{"from_route": "/panel/<path:app_path>", "to_route": "frontend"},
	# Applicant portal (ported from gdl/www/{dashboard,applications,
	# complete-profile}.* into the same Vue SPA - role-gated client-side by
	# the Applicant Portal User guard in frontend/src/router/index.js, same
	# pattern as /HR/* above). URLs are unchanged from the old Jinja pages -
	# they're hardcoded in gdl.api.public.register_applicant's redirect_to,
	# confirmation emails, and "Apply now" links - only what serves them
	# changed. /apply/new was the last surviving old Jinja page (it had a
	# real, previously-undetected CSRF bug - see ApplyNew.vue's history for
	# details) and is now ported here too, same pattern as the rest.
	{"from_route": "/dashboard", "to_route": "frontend"},
	{"from_route": "/applications", "to_route": "frontend"},
	{"from_route": "/applications/<path:name>", "to_route": "frontend"},
	{"from_route": "/complete-profile", "to_route": "frontend"},
	{"from_route": "/apply/new", "to_route": "frontend"},
	# Phase 6 - one applicant-facing exam-taking page per Exam Attempt.
	{"from_route": "/exams/<path:name>", "to_route": "frontend"},
	# Vue public site (gdl/frontend). "/" itself is handled entirely by the
	# home_page hook (get_home_page() substitutes it before route rules are
	# even consulted - see resolve_path() in Frappe core), not a rule here.
	# The rules below take priority over a same-path physical www/*.html page
	# (verified against Frappe core's resolve_from_map(), which runs before
	# any file lookup), so they safely shadow the now-deleted
	# gdl/www/{index,jobs,register}.* pages and Frappe core's stock /login
	# page. /frontend/<path:app_path> is the SPA's own asset/deep-link
	# passthrough, kept from the original doppio scaffold.
	{"from_route": "/jobs", "to_route": "frontend"},
	# Public vacancy detail page (Vue), identified by Job Opening docname
	# (e.g. /jobs/VAC-2026-0011) - shadows HRMS's own website-generator page
	# for Job Opening (which used the route field, e.g.
	# jobs/greendigital_ltd/associate), same priority as /login/-register
	# above.
	{"from_route": "/jobs/<path:name>", "to_route": "frontend"},
	{"from_route": "/register", "to_route": "frontend"},
	{"from_route": "/login", "to_route": "frontend"},
	{"from_route": "/frontend/<path:app_path>", "to_route": "frontend"},
]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "gdl.utils.jinja_methods",
# 	"filters": "gdl.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "gdl.install.before_install"
# after_install = "gdl.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "gdl.uninstall.before_uninstall"
# after_uninstall = "gdl.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "gdl.utils.before_app_install"
# after_app_install = "gdl.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "gdl.utils.before_app_uninstall"
# after_app_uninstall = "gdl.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "gdl.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "gdl.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events — populated as later phases need it
# (e.g. Job Applicant status changes -> audit trail / notifications in Phase 6/10)

doc_events = {
	"Job Applicant": {
		# validate (not on_update) - runs as part of the same save, no
		# separate write/recursion risk. See gdl/utils/completeness.py.
		"validate": "gdl.utils.completeness.set_completeness_on_save",
	},
	"Job Opening": {
		# validate - sets a field on this same doc, so it must run pre-save
		# like completeness above, for the same reason.
		"validate": "gdl.utils.vacancies.set_apply_route_on_save",
	},
	"Job Application": {
		# on_update (not validate) - this hook writes to a *different* doc
		# (the linked Job Opening) and needs to count already-committed
		# sibling applications, so it must run after this save is persisted.
		"on_update": "gdl.utils.vacancies.auto_close_job_opening_if_filled",
	},
}

# Scheduled Tasks
# ---------------
# expire_stale_offers: client feedback (Phase 3) - flips a Job Offer past its
# response deadline to "Expired". Reminder notifications (24h-before
# exam/interview jobs) remain a Phase 10 TODO.

scheduler_events = {
	"daily": [
		"gdl.tasks.expire_stale_offers",
	],
}

# Testing
# -------

# before_tests = "gdl.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "gdl.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "gdl.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "gdl.task.get_dashboard_data"
# }
# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["gdl.utils.before_request"]
# after_request = ["gdl.utils.after_request"]

# Job Events
# ----------
# before_job = ["gdl.utils.before_job"]
# after_job = ["gdl.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"gdl.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []