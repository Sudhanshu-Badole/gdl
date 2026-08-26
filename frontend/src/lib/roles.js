// Maps a user's Frappe roles to the portal they belong to - used for the
// "My dashboard" link (AppHeader) and the avatar dropdown's role label
// (UserMenu). First match wins, same priority convention as gdl.auth's
// ROLE_HOME_PAGES on the backend.
const ROLE_HOME = [
	{ roles: ["HR Officer", "System Manager"], label: "HR", homePath: "/HR/Dashboard" },
	{ roles: ["Applicant Portal User"], label: "Applicant", homePath: "/dashboard" },
];

export function getRoleInfo(roles = []) {
	return ROLE_HOME.find((entry) => entry.roles.some((r) => roles.includes(r))) || null;
}
