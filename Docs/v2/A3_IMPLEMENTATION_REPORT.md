# Deal Room v2 — A3 Implementation Report

## Scope

A3 implements Deal Finder semantics, Lead creation, pre-submission validation, Sales Manager initial review, Sales Executive assignment, initial closure, optimistic concurrency, audit/notification integration, and the minimum frontend flow.

## Architecture discovered before A3

- `Opportunity.created_by` already represented the creator and was distinct from `sales_owner_id`; it is retained as the persisted **Deal Finder** field rather than introducing a redundant column.
- `Opportunity.sales_owner_id` represents the assigned Sales Executive and is independent from Deal Finder.
- A2 already owns `lifecycle_stage`, `outcome`, `operational_status`, `review_status`, `row_version`, stage history, optimistic compare-and-swap, and closed-state protection.
- Existing opportunity mutation routes included explicit lifecycle/closure actions plus a generic `PUT /api/opportunities/<id>`. The generic update path was hardened so state/security fields remain server controlled.
- Existing Account and Stakeholder models were reused; A3 does not create a parallel Account or Stakeholder domain.
- Existing `ActivityService`/`AuditLog` and `NotificationService`/`Notification` infrastructure are reused.

## Deal Finder model

`Opportunity.created_by` is the immutable Deal Finder. The API also exposes it as `deal_finder_id` and `deal_finder` for v2 clarity. Creation always derives the field from the authenticated active-role context; clients cannot supply it. `sales_owner_id` is a separate field assigned during approval.

No generic update schema accepts Deal Finder, lifecycle, outcome, operational status, account, or Sales Owner as arbitrary fields.

## Lead workflow

```text
Create
  ↓
Lead / Open / Active / Draft
  ↓
Submit
  ↓
Lead / Open / Active / Pending Sales Manager Review
  ├── Reject → Lead / Open / Active / Rejected
  ├── Approve + Sales Executive → Qualified / Open / Active / Approved
  ├── Close Won → Lead / Closed Won / Closed
  └── Close Lost → Lead / Closed Lost / Closed
```

Approval calls `LifecycleTransitionService.approve_lead()`; A3 never directly assigns `lifecycle_stage = Qualified` as a workflow mutation.

## Creation contract

Required server-side:

- existing active canonical `account_id`
- `opportunity_name`
- non-negative `estimated_value` (the existing field used for initial Opportunity Value)

Optional initial fields remain supported where already part of the opportunity contract. `pain_points` was added as a first-class opportunity field because it is required before submission.

Client-provided lifecycle/outcome/status/Deal Finder values are not accepted.

## Submission contract

The Deal Finder may submit only while the opportunity is an open Lead in Draft/Rejected review state. Submission requires:

- description
- pain points
- at least one Stakeholder

Submission does not qualify the opportunity. It increments `row_version`, audits the action, and queues Sales Manager review notifications using the existing notification infrastructure.

## Initial review

Sales Manager and Leadership can review pending Leads. Approval:

1. checks Lead + pending review + open state + expected `row_version`;
2. validates the target user is an active, approved Sales Executive;
3. applies permitted review edits only;
4. assigns `sales_owner_id`;
5. calls A2 to move `Lead -> Qualified`;
6. records stage history and audit;
7. queues the existing Sales Executive assignment notification;
8. commits atomically.

A Sales Manager who is also the Deal Finder may approve their own Lead; there is no blanket creator/approver prohibition.

Reject is a review-state mutation only. It never sets Closed Lost.

## Initial closure

A3 uses the existing A2 closure methods. For a Lead, closure is restricted to pending Sales Manager review. Sales Manager and Leadership can close Won/Lost without Sales Executive assignment. Closed Lost requires a standard reason and requires explanation when the reason is `Other`. Closed opportunities remain locked by A2.

## Concurrency

A3 uses `row_version`, not `auth_version`.

- Submission checks the expected version and performs a compare-and-swap update.
- Approval loads with row locking and uses A2's versioned state update.
- Review edits and assignment are inside the same transaction as approval.
- A stale approval is rejected as a `TransitionConflict`, mapped by the HTTP controller to `409 Conflict`.

## Audit / notifications

Reused infrastructure records at least:

- opportunity creation / Deal Finder assignment
- Lead submission
- Lead rejection
- Lead approval
- Sales Executive assignment
- initial closure through the existing A2 closure audit
- review-stage field edits

Existing notification infrastructure is used for Sales Manager review and Sales Executive assignment.

## API contract

Existing explicit endpoints are retained:

- `POST /api/opportunities`
- `POST /api/opportunities/<id>/submit-lead`
- `POST /api/opportunities/<id>/review`
- `POST /api/opportunities/<id>/close-won`
- `POST /api/opportunities/<id>/close-lost`
- `PUT /api/opportunities/<id>` for permitted ordinary/review fields only, with `expected_version`

The review payload supports `APPROVE`/`REJECT`, Sales Executive assignment, expected version, and permitted Lead review fields. The request-body role is never trusted.

## Person B integration contract

### Accounts

A3 references an existing canonical Account only. It validates existence and active status. There is no inline Account creation. Account duplicate prevention, archive/ban lifecycle, and master-data CRUD remain outside A3.

### Stakeholders

A3 does not create stakeholder records automatically. Before Lead submission it queries the existing Stakeholder relation and requires at least one row. Person B can continue to manage Stakeholder details without changing Deal Finder semantics.

### Immutable participation boundary

`created_by` / `deal_finder_id` is read-only after opportunity creation. Person B domains must not overwrite it.

## Known limitations / deferred work

- The repository currently has no separate general-purpose domain-event bus; A3 therefore reuses the existing audit and notification infrastructure as the event boundary.
- `estimated_value` remains the existing opportunity value field. A4 should add value history without changing Deal Finder/Sales Owner ownership semantics.
- Final Revenue is not implemented in A3.
- Account banned-state handling is deferred to the Account domain because the current Account model has no `banned` field.
- Delivery Project creation is not implemented; it remains later-phase work.
- PostgreSQL-specific concurrency verification could not be executed in this isolated artifact environment because required Python packages are not installed and external package installation is unavailable.
