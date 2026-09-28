# Phase 2 Remaining Scope / Gap Audit

## Known environment validation gaps
1. Full pytest certification must be run in the project environment with all requirements installed.
2. PostgreSQL-specific migration, partial unique index and concurrent-write tests must be executed against the real project database.
3. Frontend production build must be run from the repository that contains the package manifest/build configuration.
4. The frontend POC/Delivery management UX should be exercised end-to-end with real seeded users; the supplied source archive was not accompanied by a package manifest.
5. A full browser workflow should verify all Phase 2 controls against the backend rather than treating UI visibility as authorization.

## Deliberately not implemented
- Google Drive permission verification
- full CRM
- full project management
- stage skipping or POC → RFX reopening
- incentive/commission calculations
- employee access to OEM contact details
- generic Delivery employee role
- unrestricted CRUD
- normal deletion of submitted POCs

## Certification rule
Phase 2 must not be declared complete until the required PostgreSQL, API security, cross-domain, seed/reset and frontend build checks pass in the project's normal runtime environment.
