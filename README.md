### Gdl

GDL e-Recruitment — custom Frappe app for GDL's Applicant Tracking System.
Built on top of Frappe + ERPNext + HRMS. No core files or core doctypes are
ever edited — only Custom Fields/Doctypes, Roles, Custom DocPerm, fixtures,
and code inside this app.

### Development conventions (Task 1.4)

**Module layout**

```
gdl/gdl/
  api/          whitelisted REST endpoints, one file per portal
                (public.py, applicant.py, hr.py, panel.py, example.py)
  utils/        shared helpers (exceptions.py, logger.py)
  gdl/          the "Gdl" Frappe module - doctype/page/report/report
                definitions live here (this is a module folder, not a
                place for general Python scripts - see gotcha below)
  www/          portal pages (Jinja + Bootstrap, no SPA framework)
  public/js/    portal JS, including the shared gdl.call() API wrapper
  fixtures/     exported data (roles, permissions, master data) so a
                fresh site gets identical setup via `bench migrate`
```

**Naming conventions**
- Custom Doctypes: plain descriptive names, no app-prefix (module ownership
  already scopes them - e.g. "Interview Scorecard", not "GDL Interview Scorecard").
- Custom Fields added to standard doctypes (Job Opening, Job Applicant,
  User, ...): prefix the fieldname with `gdl_` to avoid collisions with
  core/other-app fields, e.g. `gdl_profile_completeness`.

**API convention**
- Whitelisted methods live in `gdl/gdl/api/<portal>.py`.
- Every method returns via `gdl.api.response.success(data, message)` or
  `.failure(message, data)` - never a raw/ad hoc dict.
- Frappe wraps whatever a whitelisted method returns under a top-level
  `"message"` key in the JSON response. The frontend never has to know
  this: call methods via the shared `gdl.call(method, args)` helper in
  `public/js/gdl_api.js`, which unwraps it and hands back
  `{success, data, message}` directly.
- See `gdl/gdl/api/example.py` (`ping`) for a full worked example.
- **Load-order gotcha:** Frappe's `web_include_js` (which is how `gdl_api.js`
  gets included) renders near the *end* of `<body>`, after a page's own
  inline `<script>` block. Any code that calls `gdl.call()`/`gdl.upload()`
  immediately when the page loads (not inside a later event handler) must be
  wrapped in `document.addEventListener("DOMContentLoaded", fn)`, or it'll
  fail with `gdl is not defined` - hit this for real in `dashboard.html` and
  `complete-profile.html`, both fixed the same way.

**Error handling**
- User-facing validation failures: `gdl.utils.exceptions.gdl_error(msg)` -
  raises (`frappe.throw` equivalent). Doesn't write to the Error Log unless
  you pass `exc=` (a caught exception) - routine bad input isn't logged.
- Non-fatal failures that shouldn't interrupt the caller (e.g. a
  notification email that failed to send): `gdl_log_error(msg, exc=...)` -
  logs only, via `frappe.log_error`.

**Logging**
- `gdl.utils.logger.get_logger("<area>")` wraps `frappe.logger()` with a
  consistent `gdl.<area>` tag (e.g. `gdl.applicant.registration`,
  `gdl.api.example`), so portal-specific log lines are traceable across
  all 4 portals.

**Gotcha:** `apps/gdl/gdl/` is the actual importable Python package root
(`import gdl` -> here). `apps/gdl/gdl/gdl/` is the *Frappe module* folder
matching `modules.txt` (`Gdl`), used for doctype/page/report scaffolding -
it is not on the general import path for arbitrary scripts. Put new
Python modules under `apps/gdl/gdl/`, not the nested `gdl/gdl/gdl/`.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch version-16
bench install-app gdl
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/gdl
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
