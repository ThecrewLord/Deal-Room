# Deal Room — PLAN

## 1. Purpose

Deal Room is intended to turn an informal commercial motion into one auditable workspace for opportunity management, stakeholder coverage, pipeline execution, and disciplined POC execution.

The agreed scope is deliberately narrow:

1. Accounts & opportunities
2. Pipeline + activities
3. Stakeholders + POCs
4. OEM / partner registry
5. Pipeline dashboard
6. Role-aware access and workflow enforcement
7. Auditable workflow/history

The project should prioritize reliability and proof over adding new features.

## 2. Target operating flow

```text
Account
  -> Opportunity
      -> Pipeline stage progression
      -> Stakeholders
      -> Activities / history
      -> POC / technical evaluation
      -> Proposal / Negotiation
      -> Closed Won / Closed Lost

Users / roles
  -> authorization
  -> opportunity visibility
  -> workflow permissions
  -> approval gates

Opportunity data
  -> dashboard
  -> weighted forecast
  -> conversion / pipeline metrics
  -> stalled / ageing signals
```

## 3. Workflow decisions captured during the project

- Sales -> Sales Manager approval -> Pre-Sales handoff is an explicit handoff trigger.
- Closing Won/Lost requires the opportunity owner plus manager approval.
- Concurrent editing uses optimistic concurrency.
- POC progression must respect mandatory exit criteria / success metrics.
- Opportunity stage changes and important actions should remain auditable.
- Closed Won and Closed Lost must be represented consistently in stage, status, and dashboard metrics.
- Stakeholder coverage should eventually support power-vs-interest and economic-buyer gap mapping.

## 4. Definition-of-done / quality bar

The project corpus was targeted at:

- 80+ accounts
- 150+ opportunities across approximately 24 months and edge cases
- 30+ POCs
- realistic stakeholder coverage, with the stated target of 3–6 stakeholders per opportunity
- meaningful automated test coverage
- weighted forecast and conversion logic
- POC exit-criteria / success-metric enforcement
- data provenance documentation

## 5. Execution strategy

### Phase A — Core product
- Authentication and role-aware workspace
- Accounts
- Opportunities
- Pipeline stages
- Opportunity detail
- Stakeholders
- Activities/history
- POC tracking
- OEM registry
- Dashboard

### Phase B — Workflow enforcement
- Stage transition rules
- Sales Manager approval
- Pre-Sales handoff
- Owner + manager close approval
- POC gates
- Opportunity visibility
- Optimistic concurrency

### Phase C — Hardening
- Stakeholder create/update verification
- Closed Won/Lost counter verification
- Full-corpus reconciliation
- Role-by-role regression
- concurrency testing
- POC download verification

### Phase D — Explicit remaining quality requirements
- Stakeholder power-vs-interest / buyer-gap mapping
- Historical POC missing-exit-criteria flag
- Configurable stage-specific stalled thresholds
- Data provenance (`sources.md` or equivalent)

## 6. Current priority

Do not expand scope until the remaining workflow and data-quality gaps are proven closed.

The recovery sequence established in the project is:

1. Close functional verification.
2. Close explicit quality requirements.
3. Prove the result with reconciliation, concurrency testing, and role-by-role regression.
