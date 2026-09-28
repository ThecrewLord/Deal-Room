# Deal Room — TODO

## P0 — Must close before calling the build complete

- [ ] Verify stakeholder create/update end-to-end.
- [ ] Verify Closed Won dashboard counter.
- [ ] Verify Closed Lost dashboard counter.
- [ ] Verify Closed Won/Lost updates stage + status + `is_active` consistently.
- [ ] Verify owner + manager close approval.
- [ ] Verify Sales -> Sales Manager approval -> Pre-Sales handoff trigger.
- [ ] Run optimistic concurrency test with two simultaneous editors.
- [ ] Run role-by-role regression.
- [ ] Run full-corpus data reconciliation.

## P1 — Explicit definition-of-done gaps

- [ ] Implement stakeholder power-vs-interest mapping.
- [ ] Implement economic-buyer gap detection.
- [ ] Flag historical POCs with missing exit criteria.
- [ ] Make stalled thresholds configurable per stage.
- [ ] Add/document data provenance with URL, licence and date.
- [ ] Verify POC download against real records.

## P1 — Data-model cleanup

- [ ] Decide whether `POCTracker` or `Poc` is the canonical POC model.
- [ ] If `Poc` is legacy, migrate/remove its production dependency.
- [ ] Decide whether stakeholder and contact are intentionally separate entities.
- [ ] Define the canonical source for activity history vs `AuditLog`.
- [ ] Confirm whether `Notification` is production-used and document its lifecycle.
- [ ] Document every foreign key and cascade behavior.
- [ ] Add database-level uniqueness constraints where application-level `get_or_create` is currently relied upon.

## P1 — API cleanup

- [ ] Inventory every registered route.
- [ ] Mark each route as UI-used, test-only, seed-only, legacy or unused.
- [ ] Remove or deprecate duplicate/legacy endpoints.
- [ ] Ensure every mutation endpoint enforces authorization server-side.
- [ ] Standardize error responses.
- [ ] Standardize conflict response for optimistic concurrency.
- [ ] Standardize pagination/filtering semantics.
- [ ] Ensure dashboard metrics have one authoritative implementation.

## P2 — Frontend cleanup

- [ ] Remove duplicated API calls and derived calculations.
- [ ] Centralize API client behavior.
- [ ] Centralize auth/session state.
- [ ] Centralize stage/status constants.
- [ ] Ensure UI never independently decides whether a transition is allowed.
- [ ] Align remaining pages with the opportunity-page visual system.
- [ ] Fix empty administrative/dashboard states where they are still present.
- [ ] Add loading, empty, error and conflict states consistently.

## P2 — Testing

- [ ] API tests for every opportunity mutation.
- [ ] Stakeholder CRUD tests.
- [ ] Closed Won/Lost tests.
- [ ] Approval workflow tests.
- [ ] Permission matrix tests.
- [ ] Optimistic concurrency tests.
- [ ] Dashboard aggregation tests.
- [ ] Seed idempotency test.
- [ ] Legacy POC regression test.
- [ ] Frontend integration tests for stakeholder and closure flows.

## P3 — Documentation

- [ ] Keep `PLAN.md` synchronized with actual scope.
- [ ] Keep `DESIGN.md` synchronized with architecture.
- [ ] Maintain endpoint inventory.
- [ ] Maintain database ERD/schema documentation.
- [ ] Maintain `sources.md`.
- [ ] Add runbook for local setup.
- [ ] Add deployment/configuration documentation.
