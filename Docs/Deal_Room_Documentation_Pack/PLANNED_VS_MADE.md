# Deal Room — Planned vs Made

## Executive summary

The product direction is largely implemented. The gap is not primarily missing screens; it is **workflow enforcement, data-model cleanliness, and proof**.

The 27 Aug project readout explicitly characterized the build as AMBER: core workflows were working, while hardening/verification and several explicit quality requirements remained.

## Comparison

| Area | Planned / required | Made / current assessment |
|---|---|---|
| Accounts | Account management | Implemented / seeded |
| Opportunities | Full opportunity lifecycle | Implemented |
| Pipeline | Stage progression | Implemented |
| Activities | Activity/history visibility | Implemented substantially |
| Stakeholders | Create/manage stakeholders | Implemented; verification needed |
| Stakeholder intelligence | Power-vs-interest + buyer gap | **Not complete** |
| POCs | Structured POC tracking | Implemented |
| POC discipline | Exit criteria / success metric | Implemented substantially |
| POC quality | Flag historical missing exit criteria | **Not complete** |
| POC download | Export/download | Implemented; verify live |
| OEM registry | Partner registry | Implemented |
| Dashboard | Pipeline + weighted forecast | Implemented |
| Win/Loss metrics | Closed Won/Lost counters | Implemented but recently exposed as a verification issue |
| Stall detection | Stage-specific configurable thresholds | **Not complete** |
| Data provenance | URL/licence/date source record | **Not complete** |
| RBAC | Role-aware access | Implemented |
| Concurrency | Optimistic concurrency | Strategy implemented; live proof required |
| Close control | Owner + manager approval | Required; verify end-to-end |
| Handoff | Sales -> Manager approval -> Pre-Sales | Required; verify end-to-end |
| Auditability | Stage/history/audit trail | Implemented substantially |
| Corpus | 80+ accounts, 150+ opportunities, 30+ POCs | Reported as above minimum target |
| Automated tests | Significant coverage | Reported as present |
| UI consistency | Opportunity page as design reference | Partially addressed; remaining alignment work |

## The biggest architectural difference

The planned system is a **workflow-enforcing commercial system**.

Parts of the current implementation can still behave like a conventional CRUD application unless the API is the single authoritative enforcement point.

That distinction matters most for:
- closing
- stage transitions
- approvals
- POC gates
- permissions
- concurrent editing

## The biggest data difference

The schema contains legacy/parallel representations, particularly around POCs.

The planned model should have one source of truth.

The current code has both `POCTracker` and `Poc`, with seed logic explicitly treating `Poc` as legacy/separate.

## The biggest quality difference

The planned definition of done requires evidence, not only code.

The remaining work therefore should be measured by:
- test cases passing
- live role-by-role behavior
- full-corpus reconciliation
- conflict behavior
- dashboard totals matching database reality
- data-quality flags being visible

## What should NOT be added now

Do not add new product scope until the current gaps are closed.

The project recovery plan explicitly favored keeping scope frozen and spending the remaining cycle on hardening, verification and evidence.
