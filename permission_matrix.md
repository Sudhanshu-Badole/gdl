# GDL e-Recruitment — Role & Permission Matrix

Phase 1 / Task 1.3 deliverable. Source of truth is the live Custom DocPerm /
Role Profile records on the site — exported as fixtures in `gdl/gdl/fixtures/`
(`role.json`, `role_profile.json`, `custom_docperm.json`) so any site that
installs the `gdl` app gets this identically via `bench migrate`. This file
is generated from that state; regenerate it if permissions change.

## Roles

| Role | Type | Desk Access | Notes |
|---|---|---|---|
| System Manager | Standard (Frappe) | Yes | Reused as-is for Super Admin — no new Role doc created |
| HR Officer | Custom | Yes | Manages vacancies, applicants, shortlisting etc. |
| Panel Member | Custom | Yes | Interview scorecard access only |
| Applicant Portal User | Custom | **No** | Portal-only; paired with Website User on applicant accounts |

## Role Profiles

| Role Profile | Bundled Roles | Default Home Page |
|---|---|---|
| Super Admin | System Manager, HR Manager, HR Officer, Panel Member | `/HR/Dashboard` (Task 2.3) |
| HR Officer | HR Officer | `/HR/Dashboard` (Task 2.3) |
| Panel Member | Panel Member | `/panel/dashboard` (Task 2.3) |

Applicant Portal User has no Role Profile — it's assigned directly alongside
Website User at registration time (Task 2.2), not through Desk-side profile
assignment.

## Doctype × Role Permission Levels (permlevel 0)

| Doctype | Role | Read | Write | Create | Delete |
|---|---|:---:|:---:|:---:|:---:|
| Job Opening | HR Officer | ✓ | ✓ | ✓ | ✓ |
| Job Applicant | HR Officer | ✓ | ✓ | ✓ | – |
| Job Applicant | Panel Member | ✓ | – | – | – |
| Department | HR Officer | ✓ | – | – | – |
| Designation | HR Officer | ✓ | – | – | – |
| Staffing Plan | HR Officer | ✓ | – | – | – |
| User | HR Officer | ✓ | – | – | – |
| Job Applicant | Applicant Portal User | ✓ (own record only) | ✓ (own record only) | – | – |
| Job Application | HR Officer | ✓ | ✓ | ✓ | ✓ |
| Job Application | Panel Member | ✓ | – | – | – |
| Job Application | Applicant Portal User | ✓ (own record only) | – | ✓ | – |
| Vacancy Category | HR Officer | ✓ | ✓ | ✓ | ✓ |

Panel Member and Applicant Portal User have no access to Department,
Designation, or Staffing Plan — verified in the boundary test below.

**Job Application / Applicant Portal User** (Phase 4 / Task 4.0): same
`if_owner` row-level pattern as Job Applicant, but deliberately **no write**
grant — an application is a point-in-time submitted record, not something
the applicant can edit after the fact (unlike their profile). Create + read
only. Same owner-setting caveat applies: whatever creates the record must
`frappe.db.set_value(..., "owner", ...)` afterward, since insert() always
forces owner to the acting session user.

**Job Applicant / Applicant Portal User is row-level scoped (`if_owner`)**
— added in Phase 3 / Task 3.1 so applicants can read and edit their own
profile (personal info, education, employment, documents) but never anyone
else's. This only works because `gdl.api.public.register_applicant()`
explicitly sets the new Job Applicant record's `owner` to the applicant's
own email after insert (`Document.set_user_and_timestamp()` otherwise always
forces `owner` to the acting session user, which is `Guest` throughout the
registration request). Verified live with two separate test applicants:
each can read/write only their own record; `frappe.has_permission()` denies
cross-user access at the framework level, not just via the API's own
lookup-by-email convenience.

**Note on User:** the row above (HR Officer → read-only) is the only
*explicit* grant. In stock Frappe, any authenticated non-Administrator user
can already read basic User records regardless of role — this is a built-in
`has_permission` hook on the core User doctype (used for assignments,
@mentions, "created by" display, etc. across the whole framework) and isn't
something Custom DocPerm controls or that we can restrict without a core
edit. Sensitive fields (password, API keys, roles) stay protected by
permlevel, not by blocking the doctype outright. So Panel Member and
Applicant Portal User can see basic user info (name/email) like any Frappe
user, but nothing else internal.

**Rationale for the gaps:**
- HR Officer can't delete Job Applicant or write/create Department, Designation,
  Staffing Plan, or User — those are org-structure/account-admin actions
  reserved for Super Admin (System Manager).
- Panel Member is read-only on Job Applicant for now; Phase 7 will add
  Interview/Scorecard doctypes with their own scoped permissions.

## How this was produced

`gdl/gdl/setup_roles_permissions.py::run()` — an idempotent bootstrap script
(run via `bench execute gdl.setup_roles_permissions.run`) that creates the
Role Profiles and Custom DocPerm rows above, and clears Desk Access on
Applicant Portal User. Re-run it (or extend it) as new doctypes are added in
later phases, then re-run `bench export-fixtures --app gdl` to refresh the
fixtures and this document.

## Boundary test

`gdl/gdl/verify_role_boundaries.py::run()` (run via
`bench execute gdl.verify_role_boundaries.run`, 12/12 passing as of Phase 3)
— asserts via `frappe.set_user()` that:
- A Panel Member cannot read/write Department, Designation, or Staffing Plan.
- An Applicant Portal User cannot read Department, Designation, Staffing
  Plan, or Job Opening, and has no Desk access.
- An Applicant Portal User *can* read their own Job Applicant record but
  *cannot* read a different applicant's (the `if_owner` grant from Task 3.1,
  tested with two separate applicant accounts + real Job Applicant records).

This is a lightweight ad hoc check, not part of the formal automated test
suite — that's Phase 11 (Task: test infrastructure).
