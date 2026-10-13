# Phase 2 API Reference

## Accounts
- `GET /api/accounts`
- `GET /api/accounts/<account_id>`
- `POST /api/accounts`
- `POST /api/accounts/<account_id>/archive` — Leadership
- `POST /api/accounts/<account_id>/ban` — Leadership
- `DELETE /api/accounts/<account_id>/duplicate` — restricted Leadership duplicate cleanup

## Stakeholders
- `GET /api/stakeholder`
- `GET /api/stakeholder/<id>`
- `GET /api/stakeholder/opportunity/<opportunity_id>`
- `POST /api/stakeholder`
- `PUT /api/stakeholder/<id>`
- `DELETE /api/stakeholder/<id>`

## OEM
Existing `/api/oem/` and `/api/oem/<id>` endpoints now enforce backend redaction and Leadership-only master mutation.

## Phase 2 collaboration endpoints
- `GET /api/v2/tags`
- `GET /api/v2/oem/<opportunity_id>`
- `PUT /api/v2/opportunity/<opportunity_id>/oems`
- `GET /api/v2/opportunity/<opportunity_id>/rfx`
- `PUT /api/v2/opportunity/<opportunity_id>/rfx`
- `POST /api/v2/opportunity/<opportunity_id>/pocs`
- `GET /api/v2/pocs/<poc_id>`
- `POST /api/v2/pocs/<poc_id>/team`
- `POST /api/v2/pocs/<poc_id>/submit`
- `GET /api/v2/opportunity/<opportunity_id>/negotiations`
- `PUT /api/v2/opportunity/<opportunity_id>/negotiations`
- `GET /api/v2/opportunity/<opportunity_id>/delivery-project`
- `PUT /api/v2/delivery-project/<id>/members`
- `POST /api/v2/delivery-project/<id>/complete`
- `POST /api/v2/delivery-project-members/<id>/done`
- `GET /api/v2/opportunity/<opportunity_id>/activities`
- `POST /api/v2/opportunity/<opportunity_id>/activities`
- `GET /api/v2/opportunity/<opportunity_id>/follow-ups`
- `POST /api/v2/opportunity/<opportunity_id>/follow-ups`
- `POST /api/v2/follow-ups/<id>/complete`

Authentication is JWT + server-side active-role validation. Resource/relationship authorization is evaluated in the service layer.
