# Phase 3 API Reference

## Search
`GET /api/search`

Supports keyword search plus entity/type/stage/status/account/owner filters and pagination.

## Dashboard
`GET /api/dashboard`

Returns role-scoped analytics. Admin remains explicitly denied business dashboard access.

Important response groups:
- `pipeline_by_stage`
- `follow_ups`
- `activities`
- `operational`
- `revenue_intelligence` for Leadership/Sales Manager
- `opportunities_by_owner` for Leadership/Sales Manager
- `own_revenue` for Sales Executive

Existing Phase 2 endpoints remain the source of truth for workflow mutations.
