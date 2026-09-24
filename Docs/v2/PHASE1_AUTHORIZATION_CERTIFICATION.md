# Deal Room V2 — Phase 1 Authorization Certification

## Active-role model

Authorization is evaluated using the authenticated user, selected active role, resource, relationship/scope, lifecycle stage, operational status, requested action, field permission, and expected version. The backend reloads authoritative user/resource state and rejects stale `auth_version` or invalid active roles.

## Leadership

Leadership has company-wide business opportunity visibility and retains root system governance.

## Admin

Admin is an access administrator, not a business user. Business Opportunity queries return no records for Admin. Admin cannot create Leads or perform lifecycle/closure operations. Other Admin identities remain Leadership-only visibility.

## Deal Finder

Eligible roles:

- Leadership
- Sales Manager
- Sales Executive
- Pre-Sales Manager
- Solution Engineer
- Delivery Manager
- DevOps Engineer
- Data Analyst

Admin is excluded. Deal Finder is derived from the authenticated actor and cannot be changed through generic updates or client-supplied ownership input.

## Lifecycle authority

| Action | Authorized active roles |
|---|---|
| Lead -> Qualified | Sales Manager / Leadership through approval action |
| Qualified -> RFX | Pre-Sales Manager / assigned Solution Engineer / Leadership |
| RFX -> POC | Pre-Sales Manager / assigned Solution Engineer / Leadership |
| POC -> Negotiations | Pre-Sales Manager / assigned Solution Engineer / Leadership |
| Negotiations -> Delivery | Pre-Sales Manager / Leadership through explicit Closed Won approval |

Generic lifecycle transition cannot execute Negotiations -> Delivery.

## Closure

- Initial Lead Closed Won/Lost: Sales Manager or Leadership.
- Qualified onward Closed Won/Lost: Pre-Sales Manager or Leadership.
- Assigned Solution Engineer may close Lost.
- Solution Engineer Closed Won is request/approval based and cannot bypass Pre-Sales Manager approval.
- Closed opportunities are locked.

## Concurrency

Sensitive mutations require integer `row_version`. Stale versions produce conflict semantics and successful mutations increment the version exactly once.

## Certification status

Static certification completed. Full runtime certification requires the project's installed dependency set and PostgreSQL environment.
