# A3 — Initial Lead Review + Full Regression Audit

## Root cause

The backend already authorizes the Deal Finder to create stakeholders while an opportunity is an editable Lead (`Lead`, `Draft`/`Rejected`, operational status `Active`). The frontend `OpportunityDetail.jsx` incorrectly rendered `StakeholderForm` only when the legacy `opportunity.status === "Open"` condition was true. The canonical A2/A3 operational state is `operational_status === "Active"`, so the Add Stakeholder control was hidden.

## A3 fixes

- Stakeholder form visibility now follows canonical `operational_status` plus Deal Finder, Lead, and Draft/Rejected checks.
- Sales Executive Lead-edit visibility is aligned with backend Draft/Rejected authorization.
- Lead submission visibility is aligned with backend Deal Finder authorization for Sales Executive, Sales Manager, and Leadership.
- Opportunity list Open Deals statistics and status filtering now use `outcome` and `operational_status`, avoiding the legacy `status === "Open"` mismatch.
- Sales Manager review approval fixed an undefined `state` variable that would fail when clicking Approve.
- Sales Manager review status badge uses canonical opportunity outcome/operational state.
- A3 lifecycle audit records for lifecycle change and Closed Lost now include `active_role`.
- Added a focused backend regression test proving the Deal Finder can add a stakeholder during editable Lead state, another Sales Executive cannot, and the Deal Finder cannot add one after submission.

## A4 boundary audit

A3 does not mutate Opportunity Value through generic update. `OpportunityService.update_opportunity()` rejects `estimated_value` and `final_revenue`; post-creation value changes continue through `OpportunityValueService`. Creation uses the existing A4 `record_initial_value()` hook. No new A3 value-history implementation was added.

## Verification performed

- All backend Python files syntax-compiled successfully.
- Static repository audit performed across Opportunity, Stakeholder, Authorization, Lifecycle, Value, Audit, frontend Opportunity Detail, Opportunities list, and Sales Manager Review.
- No new database migration was required for the stakeholder UI fix.
- Full pytest could not be executed in this environment because `marshmallow` is unavailable.
- The supplied frontend archive contains `src/` but no package manifest/node_modules, so a full frontend build could not be run here.
- PostgreSQL runtime/concurrency verification was not claimed as passed.

## Manual runtime verification required

Run in the actual project environment:

```bash
cd backend
flask db current
flask db upgrade
pytest -q
```

Then execute:

```text
Sales Executive Alice
→ Create Lead
→ Open Opportunity Detail
→ Add Stakeholder
→ Refresh
→ Submit Lead
→ Sales Manager Bob
→ Review
→ Approve + assign Charlie
→ verify Deal Finder remains Alice
→ verify Sales Owner becomes Charlie
→ verify lifecycle becomes Qualified
```

Also test zero stakeholders → Submit and confirm validation rejection.

## Out of scope

A4/A5 later domains, Accounts, advanced Stakeholder management, OEM, RFX, POC, Negotiations, Delivery, incentives, and Revenue Attribution were not implemented as part of this audit.
