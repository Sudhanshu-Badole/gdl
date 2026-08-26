// Display-only mirror of gdl/utils/completeness.py's section boundaries, for
// the Profile page's "what to complete" checklist. The actual score always
// comes from the server (Job Applicant.gdl_profile_completeness) - this only
// decides which sections to list as done/not-done and where "Continue:
// {section}" should scroll to. Keep in sync with completeness.py by hand if
// its field lists ever change; there's no API that exposes them dynamically.
export const CHECKLIST_SECTIONS = [
	{
		key: "personal",
		label: "Personal details",
		weight: 30,
		anchor: "personal-info-section",
		isDone: (doc) =>
			[
				"gdl_date_of_birth",
				"gdl_gender",
				"gdl_nationality",
				"gdl_permanent_address",
				"gdl_current_address",
				"gdl_profile_photo",
			].every((f) => !!doc[f]),
	},
	{
		key: "education",
		label: "Education",
		weight: 20,
		anchor: "education-section",
		isDone: (doc) => (doc.gdl_education || []).length > 0,
	},
	{
		key: "employment",
		label: "Work experience",
		weight: 20,
		anchor: "employment-section",
		isDone: (doc) => (doc.gdl_employment_history || []).length > 0,
	},
	{
		key: "documents",
		label: "Documents",
		weight: 30,
		anchor: "documents-section",
		isDone: (doc) => ["resume_attachment", "gdl_national_id", "gdl_academic_certificate"].every((f) => !!doc[f]),
	},
];
