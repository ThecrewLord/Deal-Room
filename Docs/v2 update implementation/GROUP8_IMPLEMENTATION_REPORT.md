# Group 8 Implementation Report — Closure Workflow + Closure Approval

## STATUS
Implemented Group 8 against the supplied backend snapshot. Runtime pytest/migration verification was not available in this execution environment because Flask is not installed here. `compileall` passes.

## 1. CURRENT CLOSURE ARCHITECTURE
The existing authoritative closure engine is `LifecycleTransitionService`. The existing `ClosedWonRequest` model/table was retained and evolved into the single closure-request mechanism.

## 2. CLOSURE MODEL USED
`ClosedWonRequest` remains the model/table for compatibility, but now represents both `Closed Won` and `Closed Lost` requests. Multiple terminal requests are preserved instead of overwriting prior request history.

## 3. CLOSURE REQUEST CHANGES
Added `POST /api/opportunities/<id>/request-closure`.
- Assigned Solution Engineer only.
- Qualified/RFX only for the no-POC request workflow.
- Supports Closed Won and Closed Lost.
- Closed Lost requires reason; `Other` requires explanation.
- Request does not change outcome, operational status, or lifecycle stage.
- Opportunity row_version is incremented atomically.

## 4. PSM APPROVAL CHANGES
Added generic approve/reject routes using the same lifecycle service.
- PSM only.
- Pending request required.
- Duplicate/already-processed requests rejected.
- Rejection leaves opportunity Open and at the same lifecycle stage.
- Approval invokes the existing authoritative closure mutation.

## 5. CLOSED WON CHANGES
PSM approval invokes `_close_won_locked`.
Existing behavior is preserved: Closed Won remains an outcome; Negotiations -> Delivery remains the already-established closure semantics. Delivery Project creation and Delivery Manager notification reuse the existing aggregate/service.

## 6. CLOSED LOST CHANGES
PSM approval invokes `_close_lost_locked` using the reason/explanation captured in the request. Existing direct closure behavior remains available under the frozen authorization matrix.

## 7. AUTHORIZATION CHANGES
Added explicit no-POC closure request authorization for an assigned Solution Engineer in Qualified/RFX. Added explicit PSM closure-request review authorization. Existing direct-close authorization was not broadly redesigned.

## 8. CONCURRENCY CHANGES
Closure request creation and approval validate the existing Opportunity `row_version`. Closure requests increment Opportunity `row_version`, and stale approval attempts return the existing conflict path.

## 9. AUDIT CHANGES
Uses existing `ActivityService`/AuditLog architecture for request created, request approved/rejected, and actual Closed Won/Closed Lost mutations.

## 10. NOTIFICATION CHANGES
Reuses `NotificationService`. Added generic closure request/approval/rejection notification types. Closed Won continues to reuse the existing Delivery Project creation notification to the Delivery Manager.

## 11. DELIVERY HANDOFF CHANGES
No new Delivery Project implementation. Existing `Phase2Service.create_delivery_project` remains authoritative and POC members remain suggested only.

## 12. OBSOLETE ENDPOINTS
Kept: existing `request-closed-won`, `approve-closed-won`, and `reject-closed-won` as compatibility facades.
Modified: they delegate to the same authoritative Group 8 service.
Added: generic `request-closure`, `approve-closure`, and `reject-closure`.
Removed: none, because caller compatibility was preserved and there is no competing implementation.

## 13. FILES CHANGED
- app/auth/authorization.py
- app/api/opportunity_routes.py
- app/controllers/opportunity_controller.py
- app/models/opportunity/closed_won_request.py
- app/models/opportunity/opportunity.py
- app/schemas/opportunity_schema.py
- app/services/lifecycle_transition_service.py
- app/services/notification_service.py

## 14. FILES ADDED
- migrations/versions/7f8e9d0c1b2a_group8_closure_workflow.py
- tests/test_group8_closure_workflow.py
- GROUP8_IMPLEMENTATION_REPORT.md

## 15. FILES REMOVED
None.

## 16. DATABASE/MIGRATION CHANGES
The existing `closed_won_requests` table is evolved:
- removes the one-request-per-opportunity unique constraint
- adds requested_outcome
- adds requested_reason
- adds requested_explanation
- adds a check constraint for Closed Won/Closed Lost

The baseline migration was not modified.

## 17. TESTS ADDED/UPDATED
Focused Group 8 tests cover:
- assigned SE request
- Qualified/RFX boundary
- Closed Lost reason/Other validation
- unassigned SE
- cross-opportunity IDOR
- PSM rejection
- PSM Closed Won approval
- PSM Closed Lost approval
- self/non-PSM approval denial
- stale version
- duplicate processing
- repeated request history
- Delivery Manager notification

## 18. TEST RESULTS
PASS:
- Python AST parsing
- `python -m compileall -q app tests`

FAIL:
- Focused pytest could not be collected in this execution environment because Flask is not installed.

SKIPPED:
- Full pytest/migration verification pending execution in the project's existing `.venv`.

## 19. SECURITY TEST RESULTS
Static implementation review covers:
- assigned-SE requirement
- cross-opportunity IDOR
- PSM-only approval
- self-approval denial
- closed-record mutation rejection through the existing lifecycle authority
- client-controlled outcome/state fields rejected by existing update schema
- stale opportunity row_version conflicts
- duplicate pending/processed request protection

## 20. KNOWN ISSUES
The runtime test environment used for implementation lacks Flask, so test execution and Alembic execution must be performed in the project's existing `.venv`.

## 21. ITEMS INTENTIONALLY LEFT FOR OTHER GROUPS
Groups 1-7, Group 9, POC history/repeat/submission redesign, RFX cleanup, and broad legacy cleanup were not implemented.

The existing Negotiations -> Delivery behavior was preserved rather than reinterpreted, because the supplied Group 8 specification explicitly instructs the implementation to retain the already-confirmed current behavior when the documents conflict.
