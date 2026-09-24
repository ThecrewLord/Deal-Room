# A1 Implementation Report — Authorization, Leadership, and Roles

## Scope

A1 implements the platform/security layer only. Opportunity lifecycle, Deal Finder, value/revenue, accounts, stakeholders, OEM, POC, Delivery Project, and other later-phase business workflows are intentionally outside this change.

## Canonical roles

The backend canonical vocabulary is exactly:

1. Leadership
2. Admin
3. Sales Manager
4. Sales Executive
5. Pre-Sales Manager
6. Solution Engineer
7. Delivery Manager
8. DevOps Engineer
9. Data Analyst

`Delivery` is retired. It remains only as an isolated legacy constant for migration compatibility and is not accepted by canonical role validation or JWT active-role validation.

## Authorization model

- `AuthorizationService.current_context()` is the authoritative request context.
- The JWT supplies identity, active role, and `auth_version`; the server reloads the user and verifies approval, active/revoked status, current auth version, canonical active role, and actual role membership.
- Exactly one active role governs a session. Stored secondary roles are never unioned into the active permission set.
- Leadership is a distinct root governance role, not an `Admin` Boolean or permission shortcut.
- Admin is a delegated system-administration role and is denied business pipeline/opportunity/dashboard visibility.
- Admin visibility excludes Leadership and Admin identities.
- Leadership may assign any canonical role, including Leadership and Admin.
- Admin may assign ordinary roles. Assignment of Admin is separately gated by the explicit `MANAGE_ADMINS` delegation capability granted by Leadership.
- Admin cannot assign Leadership, self-elevate, or manage privileged Leadership/Admin identities.

## Security invariants

### First user

Signup takes a PostgreSQL transaction-scoped advisory lock before checking the user count. The first committed user receives Leadership and approval; subsequent users remain pending unless approved through administration. This closes the initial root-user race.

### Last Leadership

Leadership role mutations and access revocation use the same security serialization boundary. Before removing Leadership or revoking a Leadership account, the service checks for another active approved Leadership account. The invariant is enforced server-side and transactionally; it is not a frontend-only check.

### Session invalidation

Security-sensitive role/access/manager changes increment `auth_version` in the same transaction as the mutation. Existing access/refresh tokens therefore fail the central authorization-context check after the mutation.

### Manager hierarchy

Manager assignment validates active/approved status, required manager role, self-management, and organizational cycles. Role changes and revocation are blocked when they would leave existing direct reports with invalid manager relationships.

## Database changes

Migration `i0j1k2l3m4n5_phase1_leadership_and_admin_delegation.py`:

- creates `user_system_permissions` with a unique `(user_id, permission)` constraint;
- creates indexes for user and permission lookup;
- migrates legacy `Delivery` role rows to the already-canonical Solution Engineer role, removing duplicates safely.

No Boolean `is_leadership` or `is_admin` field was introduced.

## Audit

Existing `ActivityService` / `AuditLog` infrastructure is reused for approvals, role additions/removals, Leadership assignment/removal protection, access revocation, manager changes, and Admin delegation changes.

## API contract

Existing auth routes are retained. Security-sensitive operations remain explicit:

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/select-role`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `GET /api/auth/admin/pending`
- `GET /api/auth/admin/users`
- `POST /api/auth/admin/approve/<user_id>`
- `POST /api/auth/admin/users/<user_id>/roles`
- `PATCH|POST /api/auth/admin/users/<user_id>/manager`
- `POST /api/auth/admin/users/<user_id>/admin-delegation`
- `POST /api/auth/admin/revoke/<user_id>`

`401` is used for unauthenticated/stale sessions, `403` for authenticated authorization failures, `400` for invalid input, and `409` for optimistic-concurrency/state conflicts.

## Tests and verification

`tests/test_phase1_roles.py` contains 15 A1-focused tests, including canonical roles, first-user behavior, active-role isolation, stale tokens, Leadership/Admin authorization, Admin business denial, manager hierarchy, legacy JWT rejection, Admin delegation, and a PostgreSQL concurrency test.

The environment used for this implementation does not contain the required Python dependencies and has no PostgreSQL test database. Therefore the full pytest suite could not be executed here. `compileall` succeeds. The PostgreSQL concurrency test is explicitly marked to require `TEST_POSTGRES_URL` and must be run in CI/integration infrastructure before production acceptance.

## Remaining risks / follow-up

- The repository still contains later-phase legacy references to the old `Delivery` terminology in historical tests/constants. They are not canonical authorization values, but later phases should remove or explicitly quarantine those references.
- Full PostgreSQL concurrency verification remains an environment/CI requirement.
- A1 does not implement later-phase business authorization rules; Person B must use the central authorization context/policy instead of introducing route-local role checks.
