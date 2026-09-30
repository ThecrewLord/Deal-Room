# Deal Room — DESIGN

## 1. Architecture

```text
+---------------------------+
| React / Vite Frontend     |
|                           |
| Role-aware workspace      |
| Opportunity UI            |
| POC UI                    |
| Dashboard                 |
+-------------+-------------+
              |
              | HTTP / REST
              v
+---------------------------+
| Flask REST API            |
|                           |
| Authentication            |
| Authorization             |
| Validation                |
| Workflow rules            |
| Dashboard calculations    |
| Audit/history             |
+-------------+-------------+
              |
              v
+---------------------------+
| SQL / SQLAlchemy          |
|                           |
| Users / roles             |
| Accounts / contacts       |
| Opportunities             |
| Stakeholders              |
| POCs                      |
| Activities / audit        |
| Partners / tags           |
+---------------------------+
```

The project progress material describes the application as React/Vite -> Flask REST API -> SQL, with workflow rules, authorization and validation owned by the API layer.

## 2. Frontend design

The frontend is role-aware and centered around the opportunity workflow.

Known UI areas include:
- dashboard
- opportunities / pipeline
- opportunity detail
- stakeholder management
- POC tracking
- activity/history
- administrative / role-aware areas

The opportunity page became the preferred visual reference for the other pages: later frontend work focused on alignment and making other pages visually consistent with the opportunity page.

## 3. Backend design

The Flask API is responsible for:
- authentication
- role checks
- opportunity visibility
- CRUD validation
- stage progression
- POC lifecycle
- stakeholder operations
- activity/history
- dashboard data
- concurrency protection

The API should remain the authoritative enforcement layer. The frontend may hide or disable controls, but must not be the only place where business rules are enforced.

## 4. Workflow model

### Opportunity lifecycle

```text
Lead / Identified
      |
Qualification
      |
Discovery
      |
POC / Technical Evaluation
      |
Proposal
      |
Negotiation
      |
Closed Won / Closed Lost
```

The exact canonical stage set is maintained by the backend stage constants / `StageMaster` data rather than by the seed business dataset alone.

### POC

A POC has explicit:
- objective
- success metric
- exit criteria
- target / planned dates
- status
- failure condition
- stakeholder signoff
- outcome / outcome notes

The project intentionally treats POC discipline as a core differentiator rather than a generic checklist.

## 5. Approval model

The intended control flow is:

```text
Sales execution
    |
    v
Sales Manager approval
    |
    v
Pre-Sales handoff
```

For closing:

```text
Opportunity owner requests closure
        |
        v
Manager approval
        |
        +--> Closed Won
        |
        +--> Closed Lost
```

This should be implemented and tested server-side.

## 6. Concurrency

The selected design is optimistic concurrency.

The principle is:

```text
Read opportunity version
      |
      v
User edits
      |
      v
Update only if version is unchanged
      |
  +---+---+
  |       |
 match   changed
  |       |
 save    reject with conflict
```

This prevents silent last-write-wins overwrites.

## 7. Dashboard design

The dashboard is intended to provide:
- total opportunities
- pipeline / value views
- weighted forecast
- conversion logic
- stage distribution
- Closed Won / Closed Lost visibility
- ageing / stalled signals
- POC signals where applicable

Weighted forecast is conceptually based on opportunity value multiplied by probability. The exact production formula should remain centralized and documented rather than duplicated across frontend components.

## 8. Design principles

- API is authoritative.
- Workflow state should be explicit, not inferred from UI state.
- Closed status and closed stage must remain consistent.
- History should be append-oriented/auditable.
- Seed data should be idempotent.
- Business data should come from the workbook/source dataset where possible.
- Test scaffolding should not be mistaken for production business data.
- Legacy schema should not be allowed to create two competing sources of truth.
