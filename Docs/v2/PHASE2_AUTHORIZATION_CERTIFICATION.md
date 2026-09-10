# Phase 2 Authorization Certification

Authorization remains centralized in `AuthorizationService`; controllers do not become the security boundary.

## Implemented policy
- Admin is still excluded from business-data access.
- Leadership governs account status and OEM master data.
- All approved non-Admin business roles can view/create canonical Accounts.
- Account archive/ban is Leadership-only.
- Stakeholder creation/tag management follows relationship and active-role checks; Sales Executive cannot edit stakeholder identity fields.
- Closed Opportunities remain locked.
- OEM contact fields are emitted only for Leadership.
- OEM association authority is stage/relationship aware.
- POC team assignment is Delivery Manager/Leadership only.
- POC submission requires actual POC-team membership.
- Delivery Project membership is Delivery Manager/Leadership; member completion is self-only.
- Follow-Up mutation respects owner/creator/manager/Leadership relationships.

## Remaining certification limitation
Direct API authorization tests are present in the Phase 2 test suite, but full execution requires the project's installed Python dependencies and a PostgreSQL environment for database-specific constraints/concurrency verification.
