import frappe
from frappe.utils import add_days, nowdate

MAX_VACANCIES = 50


def get_context(context):
	context.no_cache = 1
	context.show_closed = frappe.form_dict.get("show_closed") == "1"
	context.selected_category = frappe.form_dict.get("category") or ""
	context.selected_department = frappe.form_dict.get("department") or ""

	context.vacancies = get_open_vacancies(context.selected_category, context.selected_department)
	if context.show_closed:
		context.vacancies += get_recently_closed_vacancies(
			context.selected_category, context.selected_department
		)

	context.categories = frappe.get_all("Vacancy Category", pluck="category_name", order_by="category_name")
	context.departments = frappe.get_all(
		"Department",
		filters={"company": "GreenDigital Ltd"},
		pluck="department_name",
		order_by="department_name",
	)


def _base_filters(category, department):
	filters = {"publish": 1}
	if category:
		filters["gdl_vacancy_category"] = category
	if department:
		filters["department"] = department
	return filters


def get_open_vacancies(category, department):
	filters = _base_filters(category, department)
	filters["status"] = "Open"
	return frappe.get_all(
		"Job Opening",
		filters=filters,
		or_filters=[["closes_on", ">=", nowdate()], ["closes_on", "is", "not set"]],
		fields=["name", "job_title", "route", "department", "location", "employment_type", "closes_on"],
		order_by="posted_on desc",
		limit_page_length=MAX_VACANCIES,
	)


def get_recently_closed_vacancies(category, department):
	filters = _base_filters(category, department)
	filters["status"] = "Closed"
	filters["closed_on"] = [">=", add_days(nowdate(), -90)]
	vacancies = frappe.get_all(
		"Job Opening",
		filters=filters,
		fields=["name", "job_title", "route", "department", "location", "employment_type", "closed_on"],
		order_by="closed_on desc",
		limit_page_length=MAX_VACANCIES,
	)
	for v in vacancies:
		v.is_closed = True
	return vacancies
