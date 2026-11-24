# P2 API and Metrics Reference

## POC Team Assignment

`GET /api/v2/delivery-manager/poc-assignments?search=&status=all`

Returns opportunities in the open POC stage with an active POC cycle or an existing canonical team that needs to remain manageable between cycles. `status` supports `all`, `assigned`, and `unassigned`.

Initial assignment:

`POST /api/v2/pocs/{poc_id}/team`

```json
{
  "member_ids": [12, 18],
  "expected_version": 3
}
```

`expected_version` is optional for backward compatibility with existing callers; new P2 UI sends it. A POC team is limited to one or two active, approved DevOps Engineer/Data Analyst users.

Explicit reassignment:

`PUT /api/v2/opportunity/{opportunity_id}/poc-team`

```json
{
  "member_ids": [12, 18],
  "expected_version": 7
}
```

Here `expected_version` is the opportunity row version. Reassignment changes the canonical opportunity team, synchronizes an active Draft/In Progress POC snapshot, and does not mutate completed POC-cycle records. Reassignment is blocked while a POC is Submitted and awaiting completion.

## Delivery Team Assignment

`GET /api/v2/delivery-manager/delivery-assignments?search=&status=all`

Returns active delivery projects within the active Delivery Manager's scope. POC-team members are suggestions, not automatically treated as confirmed delivery membership.

`PUT /api/v2/delivery-project/{project_id}/members`

```json
{
  "member_ids": [12, 18],
  "expected_version": 4
}
```

A non-empty eligible team is required. Updates to completed projects and writes by a Delivery Manager to another manager's project are rejected.

## Performance endpoints

- `GET /api/delivery-manager/team-performance`
- `GET /api/delivery-manager/team-performance/{employee_id}`

Only an active, approved Delivery Manager can access these endpoints. The individual endpoint additionally checks that the requested employee is within that manager's computed scope.

## Counting conventions

- Assigned opportunity count is distinct by opportunity ID.
- Active delivery work is an active project-member assignment not marked done.
- Completed work is the number of eligible assignment rows completed in the current calendar month.
- Overdue work is `null` because no delivery due-date field exists in the supplied model; the UI labels it “Not tracked”.
- Pipeline value is unweighted and not a probability forecast.
