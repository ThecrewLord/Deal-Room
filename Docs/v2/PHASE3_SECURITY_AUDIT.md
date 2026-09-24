# Phase 3 Security Audit

## Preserved controls
- JWT authentication and database-backed session/auth-version validation.
- Active-role enforcement from the JWT plus current database role membership.
- Admin has no business opportunity visibility.
- Search applies backend authorization before returning records.
- OEM search projection excludes contact person, email and phone.
- Closed opportunity mutation controls remain in the existing services.
- Opportunity value changes retain row-version concurrency and append-only value history.

## Findings from static audit
### 1. Search coverage was incomplete — FIXED
The previous search service only supported Opportunity, Account and POC. It now covers the Phase 3 entity vocabulary.

### 2. Role-specific dashboard coverage was incomplete — FIXED in UI
The backend already returned common metrics, but the frontend rendered no KPI set for Leadership, Delivery Manager, DevOps Engineer or Data Analyst. Role-specific KPI branches were added.

### 3. ActivityService naming is misleading — OPEN
`ActivityService.log()` writes `AuditLog` records, while Phase 2 business Activities are stored in the separate `activities` table. This does not currently merge the domains, but the naming should be clarified in a future cleanup.

### 4. Legacy compatibility references remain — OPEN / intentional
The repository still contains compatibility references such as legacy Delivery aliases, `delivery_ids`, `influence_level`, `poc_tracker`, and historical Rejected states. They must not be removed blindly because some are historical migration/compatibility structures. Active runtime usage should be reviewed separately.

## Not certified in this environment
Direct IDOR, privilege-escalation, closed-record mutation, concurrency, PostgreSQL EXPLAIN/index behaviour and full API integration tests could not be executed because the uploaded environment does not include an installed Python dependency environment and external package installation is unavailable.
