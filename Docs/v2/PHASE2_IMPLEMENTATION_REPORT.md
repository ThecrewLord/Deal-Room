# Phase 2 Implementation Report

## Scope
Implemented the Phase 2 V2 business-domain foundation across Accounts, Stakeholders/tags, OEMs and Opportunity–OEM associations, RFX context, the authoritative `poc_tracker` POC aggregate, POC team assignment/submission, Negotiations context, Delivery Project, Activities, Follow-ups, Phase 2 notifications, centralized authorization hooks, migrations, deterministic seed/reset support, frontend routes/pages, and certification tests.

## Key invariants
- Account canonical identity is normalized and database-unique across Active, Archived and Banned states.
- Archived accounts cannot be reactivated; Banned accounts cannot be used for new Opportunities and return exactly `this account is banned`.
- Stakeholder V2 fields are `name`, `job_title`, `email`, `phone`, `company`, and fixed tags.
- Decision Maker is represented transactionally by a partial unique index per Opportunity.
- Employees receive OEM names/products but the backend omits contact person, email and phone.
- OEM master mutation is Leadership-only.
- RFX → POC requires a stored Google Drive link; the application does not verify Drive permissions.
- `poc_tracker` is the authoritative POC aggregate; the duplicate `poc` table is removed by the Phase 2 migration.
- POC execution roles are DevOps Engineer and Data Analyst, with at most two members.
- Negotiations remains mandatory before the final Delivery transition.
- Closed Won creates a separate Delivery Project aggregate.
- Activities are separate from AuditLog; Follow-ups are separate lightweight business records.
- Phase 1 lifecycle, closure, Deal Finder, Final Revenue, row-version and active-role architecture remain the authoritative foundation.

## Certification status
The implementation source was compiled successfully with Python `compileall` and AST parsing. Full pytest execution in the supplied sandbox was blocked because the sandbox did not have the project's runtime dependencies installed (`flask_jwt_extended` and other application packages). The frontend source bundle did not include its package manifest, so a production frontend build could not be executed from the supplied frontend archive.

Therefore this report does **not** claim Phase 2 final certification.
