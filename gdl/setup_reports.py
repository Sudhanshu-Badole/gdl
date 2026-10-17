"""One-time bootstrap for the 5 recruitment Query Reports (Phase 10, partial).
Report is a core Frappe doctype - report_type "Query Report" needs no Python
file, just a doctype record holding hand-written SQL, viewable natively at
/app/query-report/<name>. Same reuse-a-native-mechanism pattern as Notification
Log for in-app notifications.

Run via: bench --site <site> execute gdl.setup_reports.run

Idempotent - safe to re-run. Exported as a fixture afterwards (report.json)
so new sites get this via `bench migrate` on install.

Turnaround Time relies on gdl.utils.audit's Audit Log rows (Phase 10), so it
only reflects applications that moved through a terminal status after Audit
Log existed - there's no way to backfill turnaround for older data.
"""

import frappe

REPORTS = {
	"Recruitment Pipeline Funnel": """
		SELECT
			job_opening AS "Vacancy:Link/Job Opening:220",
			status AS "Status:Data:200",
			COUNT(name) AS "Applications:Int:120"
		FROM `tabJob Application`
		GROUP BY job_opening, status
		ORDER BY job_opening, status
	""",
	"Turnaround Time": """
		SELECT
			ja.job_opening AS "Vacancy:Link/Job Opening:220",
			COUNT(DISTINCT t.job_application) AS "Applications:Int:120",
			ROUND(AVG(DATEDIFF(t.terminal_on, ja.creation)), 1) AS "Avg Turnaround (days):Float:180"
		FROM (
			SELECT reference_name AS job_application, MIN(timestamp) AS terminal_on
			FROM `tabAudit Log`
			WHERE reference_doctype = 'Job Application'
			  AND new_value IN ('Selected', 'Rejected', 'Appointed')
			GROUP BY reference_name
		) t
		JOIN `tabJob Application` ja ON ja.name = t.job_application
		GROUP BY ja.job_opening
		ORDER BY ja.job_opening
	""",
	"Exam Pass Rate": """
		SELECT
			ea.exam AS "Exam:Link/Exam:220",
			COUNT(ea.name) AS "Attempts:Int:100",
			SUM(CASE WHEN ea.is_pass = 1 THEN 1 ELSE 0 END) AS "Passes:Int:100",
			ROUND(100.0 * SUM(CASE WHEN ea.is_pass = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(ea.name), 0), 1) AS "Pass Rate (%):Float:130"
		FROM `tabExam Attempt` ea
		WHERE ea.status = 'Submitted'
		GROUP BY ea.exam
		ORDER BY ea.exam
	""",
	"Interview Score Summary": """
		SELECT
			sched.job_opening AS "Vacancy:Link/Job Opening:220",
			COUNT(s.name) AS "Sessions:Int:100",
			ROUND(AVG(s.total_score), 1) AS "Avg Score:Float:110",
			MIN(s.total_score) AS "Min Score:Float:100",
			MAX(s.total_score) AS "Max Score:Float:100"
		FROM `tabInterview Session` s
		JOIN `tabInterview Schedule` sched ON sched.name = s.interview
		WHERE s.status = 'Completed'
		GROUP BY sched.job_opening
		ORDER BY sched.job_opening
	""",
	"Offer Conversion": """
		SELECT
			ja.job_opening AS "Vacancy:Link/Job Opening:220",
			COUNT(o.name) AS "Offers Sent:Int:110",
			SUM(CASE WHEN o.status = 'Accepted' THEN 1 ELSE 0 END) AS "Accepted:Int:100",
			SUM(CASE WHEN o.status = 'Rejected' THEN 1 ELSE 0 END) AS "Declined:Int:100",
			SUM(CASE WHEN o.status = 'Awaiting Response' THEN 1 ELSE 0 END) AS "Pending:Int:100"
		FROM `tabJob Offer` o
		JOIN `tabJob Application` ja ON ja.name = o.gdl_job_application
		WHERE o.docstatus != 2
		GROUP BY ja.job_opening
		ORDER BY ja.job_opening
	""",
}


def run():
	for report_name, query in REPORTS.items():
		query = query.strip()
		if frappe.db.exists("Report", report_name):
			report = frappe.get_doc("Report", report_name)
			report.query = query
			report.save(ignore_permissions=True)
			continue

		report = frappe.get_doc(
			{
				"doctype": "Report",
				"report_name": report_name,
				"ref_doctype": "Job Application",
				"report_type": "Query Report",
				"module": "Gdl",
				"is_standard": "No",
				"query": query,
				"roles": [{"role": "HR Officer"}],
			}
		)
		report.insert(ignore_permissions=True)
