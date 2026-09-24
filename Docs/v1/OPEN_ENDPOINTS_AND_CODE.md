# Deal Room — Open Endpoints, Redundant Code & Clarity Required

> **Important:** This document is a review checklist, not a claim that every item below is definitely unused. The current repository snapshot was not successfully mounted into the analysis runtime, so endpoint-level conclusions should be confirmed against the actual route registry. The findings below combine the project history with the accessible seed/model evidence.

## 1. Endpoint inventory that must be produced

Run a route inventory and classify every endpoint as:

```text
ACTIVE_UI
ACTIVE_INTERNAL
TEST_ONLY
SEED_ONLY
LEGACY
UNUSED
DUPLICATE
DEPRECATED
```

At minimum inspect route groups for:

- auth/login/session
- users/roles
- accounts
- contacts
- opportunities
- opportunity teams
- stages
- stakeholders
- POCs
- POC download/export
- stage history/activity
- dashboard/metrics
- OEM partners
- tags
- notifications
- audit logs

## 2. Endpoint questions that need clarity

### Opportunity mutations
- Does every update enforce optimistic concurrency?
- Does every update enforce opportunity visibility?
- Are stage transitions validated by backend rules?
- Can a client directly set `status` to Closed Won/Lost?
- Can a client directly set `is_active`?
- If stage and status disagree, which one wins?

### Close endpoints
- Is there one canonical close endpoint?
- Is Closed Won different from Closed Lost only by payload?
- Is manager approval stored as an auditable event?
- Can a user bypass the approval endpoint and call a generic opportunity PATCH?

### Stakeholders
- Is stakeholder creation available through more than one route?
- Is email uniqueness enforced at DB level?
- Does update preserve the opportunity association?
- Does the endpoint expose power/influence data that the UI does not yet use?

### POC
- Which endpoint owns POC state: `POCTracker` or legacy `Poc`?
- Are download/export routes reading the same source of truth as the POC screen?
- Can users update outcome without satisfying signoff/exit criteria?

### Dashboard
- Are counts calculated in one backend service?
- Is frontend code recalculating Closed Won/Lost counts?
- Are dashboard totals based on status, stage, or `is_active`?
- Is weighted forecast calculated once or duplicated?

## 3. Redundant / suspicious code areas

### Multiple seed scripts

Observed variants include:
- `seed_test_data.py`
- `seed_test_data_existing_users.py`
- `seed_test_data_updated.py`
- `seed_data_fixed.py`
- `seed_data_corrected.py`

**Problem:** multiple executable definitions of seed behavior make it unclear which one is canonical.

**Action:** retain one canonical seed command and move old versions to an archive/history directory or delete them after preserving Git history.

### Duplicate POC models

`POCTracker` and `Poc` both exist.

**Problem:** two APIs can eventually update two different records.

**Action:** choose one canonical model.

### Repeated model-column introspection

The seed scripts use helpers such as `model_columns()` and `set_if_present()` to tolerate schema differences.

This is useful during migration, but dangerous as a permanent pattern because it can hide schema drift.

**Action:** replace compatibility probing with explicit schema contracts after the migration stabilizes.

### Seed-time notification suppression

The seed code intentionally avoids manufacturing notifications so that application workflow services remain responsible for notifications.

This is correct for test integrity, but it means notification behavior needs its own tests.

### Contacts derived from stakeholders

This is practical for importing data, but it can create duplicate conceptual identities if the application treats Contact and Stakeholder as separate people.

**Action:** define whether Stakeholder references Contact or duplicates contact identity.

## 4. Code smells to search for

Search the repository for:

```text
TODO
FIXME
HACK
TEMP
LEGACY
DEPRECATED
console.log
print(
alert(
setTimeout(
fetch(
axios.
useEffect(
localStorage
```

Then classify each result rather than deleting blindly.

## 5. Frontend-specific duplication to inspect

- repeated fetch calls for the same opportunity
- repeated dashboard calculations
- local copies of stage/status constants
- permission checks implemented independently in multiple components
- duplicate form validation
- stale state after mutation
- mutations that do not refresh related counters
- optimistic UI updates without rollback on 409 conflict
- generic error handling that hides 409/403/422 differences

## 6. Backend-specific duplication to inspect

- generic opportunity PATCH that bypasses workflow services
- separate close endpoints plus generic update paths
- duplicated authorization decorators/helpers
- stage validation duplicated in routes and services
- dashboard SQL duplicated across endpoints
- audit logging duplicated manually in every route
- notification creation duplicated across services
- old API aliases retained without a deprecation plan

## 7. Clarity decisions required

### A. Status vs stage

Define:

```text
stage = business pipeline position
status = lifecycle state
is_active = query/visibility convenience
```

Then define exactly which transitions update all three.

### B. Owner vs opportunity-team role

The seed code correctly notes that opportunity-team `role` is not the same thing as a user's system role.

Document the distinction explicitly:

```text
UserRole
  = application authorization role

OpportunityTeam.role
  = role on a particular opportunity
```

### C. Activity vs audit

Separate business timeline events from security/audit events.

### D. POCTracker vs Poc

One must become canonical.

### E. Contact vs Stakeholder

Decide whether stakeholder is an opportunity-specific role assigned to a contact.

### F. Approval state

Document where pending/approved/rejected close or handoff requests live.

## 8. Immediate cleanup sequence

1. Export all registered Flask routes.
2. Map every frontend API call to an endpoint.
3. Mark unmatched endpoints.
4. Map every endpoint to its service/model.
5. Identify duplicate mutation paths.
6. Remove/deprecate bypass paths.
7. Select canonical POC model.
8. Centralize dashboard calculations.
9. Add DB constraints for identity/uniqueness.
10. Re-run role and concurrency tests.

## 9. Security-critical rule

Do not rely on the frontend to enforce workflow.

A hidden/disabled button is not authorization.

The backend must reject:
- unauthorized opportunity access
- unauthorized stage changes
- unauthorized stakeholder mutation
- unauthorized close actions
- unauthorized approval actions
- stale concurrent updates

## 10. Exit criterion for this review

This document should be considered complete only after the actual route registry and frontend API client are compared.

The final endpoint table should have:

| Endpoint | Method | Consumer | Auth | Role rule | Service | DB tables | Status |
|---|---|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

