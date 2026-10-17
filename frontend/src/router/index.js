import { createRouter, createWebHistory } from "vue-router";

const routes = [
	{
		path: "/",
		name: "Home",
		component: () => import("../views/Home.vue"),
	},
	{
		path: "/jobs",
		name: "Jobs",
		component: () => import("../views/Jobs.vue"),
	},
	{
		path: "/jobs/:name",
		name: "VacancyDetail",
		component: () => import("../views/public/VacancyDetail.vue"),
		props: true,
	},
	{
		path: "/register",
		name: "Register",
		component: () => import("../views/Register.vue"),
	},
	{
		path: "/login",
		name: "Login",
		component: () => import("../views/Login.vue"),
	},
	{
		path: "/HR",
		component: () => import("../layouts/AdminLayout.vue"),
		meta: { isAdmin: true },
		children: [
			{ path: "Dashboard", name: "HRDashboard", component: () => import("../views/hr/Dashboard.vue") },
			{ path: "Vacancies", name: "HRVacancies", component: () => import("../views/hr/Vacancies.vue") },
			{
				path: "Vacancies/:name",
				name: "HRVacancyDetail",
				component: () => import("../views/hr/VacancyDetail.vue"),
				props: true,
			},
			{ path: "Candidates", name: "HRCandidates", component: () => import("../views/hr/Candidates.vue") },
			{ path: "Question-bank", name: "HRQuestionBank", component: () => import("../views/hr/QuestionBank.vue") },
			{ path: "Letters", name: "HRLetters", component: () => import("../views/hr/Letters.vue") },
			{ path: "Audit-log", name: "HRAuditLog", component: () => import("../views/hr/AuditLog.vue") },
			{ path: "Settings", name: "HRSettings", component: () => import("../views/hr/Settings.vue") },
		],
	},
	// Applicant portal - flat top-level paths (not a shared /prefix like /HR)
	// because these exact URLs are hardcoded elsewhere: the post-registration
	// redirect in gdl.api.public.register_applicant, confirmation emails, and
	// apply/new.html's "Edit Profile" link all point at "/complete-profile"
	// etc. Each route independently wraps its subtree in ApplicantLayout -
	// Vue Router has no problem with several unrelated top-level routes
	// sharing one layout component.
	{
		path: "/dashboard",
		component: () => import("../layouts/ApplicantLayout.vue"),
		meta: { isAdmin: true },
		children: [{ path: "", name: "ApplicantDashboard", component: () => import("../views/applicant/Dashboard.vue") }],
	},
	{
		path: "/applications",
		component: () => import("../layouts/ApplicantLayout.vue"),
		meta: { isAdmin: true },
		children: [
			{ path: "", name: "ApplicantApplications", component: () => import("../views/applicant/Applications.vue") },
			{
				path: ":name",
				name: "ApplicantApplicationDetail",
				component: () => import("../views/applicant/ApplicationDetail.vue"),
				props: true,
			},
		],
	},
	{
		path: "/complete-profile",
		component: () => import("../layouts/ApplicantLayout.vue"),
		meta: { isAdmin: true },
		children: [{ path: "", name: "ApplicantProfile", component: () => import("../views/applicant/Profile.vue") }],
	},
	{
		path: "/apply/new",
		component: () => import("../layouts/ApplicantLayout.vue"),
		meta: { isAdmin: true },
		children: [{ path: "", name: "ApplyNew", component: () => import("../views/applicant/ApplyNew.vue") }],
	},
	{
		path: "/exams/:name",
		component: () => import("../layouts/ApplicantLayout.vue"),
		meta: { isAdmin: true },
		children: [{ path: "", name: "ExamAttempt", component: () => import("../views/applicant/ExamAttempt.vue") }],
	},
	// Panel portal (Phase 7) - lowercase "panel" prefix matches
	// gdl.auth.get_home_page's existing redirect target for the Panel
	// Member role, same shared-prefix pattern as /HR above.
	{
		path: "/panel",
		component: () => import("../layouts/PanelLayout.vue"),
		meta: { isAdmin: true },
		children: [
			{ path: "dashboard", name: "PanelDashboard", component: () => import("../views/panel/Dashboard.vue") },
			{ path: "past", name: "PanelPast", component: () => import("../views/panel/Past.vue") },
			{
				path: "interviews/:interview",
				name: "PanelInterviewCandidates",
				component: () => import("../views/panel/InterviewCandidates.vue"),
				props: true,
			},
			{
				path: "sessions/:session",
				name: "PanelScorecard",
				component: () => import("../views/panel/Scorecard.vue"),
				props: true,
			},
		],
	},
];

const router = createRouter({
	history: createWebHistory("/"),
	routes,
});

// Every gated portal - HR and Applicant so far - resolves server-side to the
// exact same generic SPA shell (see hooks.py's website_route_rules), so
// get_website_user_home_page's server-side role resolution for "/" is
// invisible to Vue Router, which only ever looks at the real browser URL.
// This table drives both the "/" root-redirect and the per-portal Guest/
// wrong-role gate, so adding another gated portal never means duplicating
// this guard logic again - just add an entry here.
const GATED_PORTALS = [
	{ prefixes: ["/HR"], roles: ["HR Officer", "System Manager"], homePath: "/HR/Dashboard" },
	{
		prefixes: ["/dashboard", "/applications", "/complete-profile", "/apply", "/exams"],
		roles: ["Applicant Portal User"],
		homePath: "/dashboard",
	},
	{ prefixes: ["/panel"], roles: ["Panel Member"], homePath: "/panel/dashboard" },
];

function matchPortal(path) {
	return GATED_PORTALS.find((p) => p.prefixes.some((prefix) => path === prefix || path.startsWith(prefix + "/")));
}

router.beforeEach((to) => {
	const boot = window.boot || {};
	const roles = boot.roles || [];
	const isGuest = !boot.user || boot.user === "Guest";

	if (to.path === "/" && !isGuest) {
		// The Administrator account always holds every role, including System
		// Manager, so it would otherwise match GATED_PORTALS' HR entry below
		// and never reach Frappe's own Desk - see gdl.auth.get_home_page's
		// matching server-side exclusion.
		if (boot.user === "Administrator") {
			window.location.href = "/desk";
			return false;
		}
		const home = GATED_PORTALS.find((p) => p.roles.some((r) => roles.includes(r)));
		if (home) return home.homePath;
	}

	const portal = matchPortal(to.path);
	if (!portal) return true;

	if (isGuest) {
		window.location.href = `/login?redirect-to=${encodeURIComponent(to.fullPath)}`;
		return false;
	}

	if (!portal.roles.some((r) => roles.includes(r))) {
		// Full page nav (not router.push): get_website_user_home_page
		// (gdl.auth.get_home_page) still reliably resolves "/" server-side to
		// whatever page this user's actual role owns.
		window.location.href = "/";
		return false;
	}
	return true;
});

export default router;
