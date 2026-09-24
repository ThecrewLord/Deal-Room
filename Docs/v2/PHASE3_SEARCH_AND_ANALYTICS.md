# Phase 3 Search and Analytics

## Search
Endpoint: `GET /api/search`

Parameters:
- `q` — 2–100 characters
- `type` — opportunity, account, stakeholder, oem, activity, follow-up, delivery-project, poc
- `stage`
- `status`
- `account_id`
- `owner_id`
- `page` (1-based)
- `page_size` (1–50)

The response is `{items, page, page_size, total, has_next}`.

Every opportunity-derived entity is constrained by `AuthorizationService.opportunity_query`. Account search is constrained by `AuthorizationService.account_query`. The projection deliberately omits restricted OEM contact fields.

## Analytics
The dashboard now exposes actual database-derived values for:
- pipeline value
- weighted forecast
- open/closed counts
- conversion rate
- lifecycle funnel
- stalled opportunities
- active POCs
- follow-up due/overdue/upcoming/completed counts
- activity count
- active delivery projects where the model supports that scope
- closed-won revenue
- Sales Executive sourced/participation reporting for Leadership/Sales Manager
- open pipeline by Sales Owner

## Forecast decision status
The uploaded V2 material does not define an approved stage-to-probability mapping. The current implementation therefore continues to use the existing `Opportunity.probability` value in the weighted calculation rather than inventing new percentages. This is an **INFERRED / MISSING DECISION** item, not a newly invented Phase 3 business rule.
