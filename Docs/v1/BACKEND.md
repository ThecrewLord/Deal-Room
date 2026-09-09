# Deal Room — Backend & Connectivity

## 1. Backend stack

The project backend is described as:

- Python
- Flask
- Flask REST API
- SQLAlchemy / SQL data layer
- PostgreSQL development database
- environment-driven database configuration
- role/permission constants
- automated tests

## 2. Backend responsibilities

The backend is the system-of-record boundary between the frontend and database.

```text
Frontend
   |
   | REST requests
   v
Flask routes/controllers
   |
   +--> authentication
   +--> authorization
   +--> validation
   +--> workflow/service logic
   +--> dashboard calculations
   +--> audit/history
   |
   v
SQLAlchemy models
   |
   v
PostgreSQL
```

## 3. Model areas

The seed code currently imports these application models:

### Auth
- `User`
- `UserRole`

### Account
- `Account`
- `Contact`
- `OEMPartner`

### Opportunity
- `StageMaster`
- `Opportunity`
- `OpportunityTeam`
- `Stakeholder`
- `StageHistory`
- `POCTracker`

### POC
- `Poc`

### System
- `Tag`
- `AuditLog`
- `Notification`

## 4. Configuration

The seed scripts read:
- `DATABASE_URL`
- optionally `SEED_DATABASE_URL`
- optionally `SEED_DATA_FILE`

The development seed dataset is expected at:

```text
backend/seed_data/Deal_Room_Seed_Dataset.xlsx
```

The seed loader is intended to be idempotent and does not drop/truncate/delete records.

## 5. Seed connectivity

```text
Deal_Room_Seed_Dataset.xlsx
        |
        v
seed_data_*.py
        |
        +--> accounts
        +--> opportunities
        +--> contacts
        +--> OEM partners
        +--> stakeholders
        +--> opportunity teams
        +--> stage history
        +--> POC tracker
        +--> audit/activity
        |
        v
PostgreSQL
```

The workbook is treated as the source of truth for business/test records, while Python retains application identities and canonical pipeline-stage metadata.

## 6. Important implementation behavior

Opportunity seeding assigns:
- account
- stage
- estimated value
- probability
- expected close date
- status
- active state
- creator
- sales owner

Closed Won / Closed Lost are mapped to closed status and inactive state in the seed logic.

Stakeholders are associated to an opportunity and keyed by opportunity + email during idempotent seeding.

Contacts can be derived from stakeholder rows and attached to the account.

Opportunity team membership is deliberately used to create visibility boundaries for authorization testing.

## 7. Backend risks

### Duplicate POC models

There are both `POCTracker` and `Poc`. The seed code explicitly describes `Poc` as a legacy/separate table and notes that it is not linked with a SQL foreign key in one version.

This is a major architecture cleanup item because two POC representations can diverge.

### Seed-script proliferation

There are multiple historical variants:
- `seed_test_data.py`
- `seed_test_data_existing_users.py`
- `seed_test_data_updated.py`
- `seed_data_fixed.py`
- `seed_data_corrected.py`

Only one should be the canonical entry point.

### Activity vs audit ambiguity

The seed code maps workbook activity information into the existing audit architecture in some versions. This needs an explicit distinction between:
- business activity timeline
- security/audit log

## 8. Frontend-to-backend contract

The frontend should depend on stable API contracts, not SQL model details.

Recommended contract pattern:

```text
UI action
 -> API request
 -> authorization
 -> validation
 -> workflow rule
 -> database transaction
 -> audit/history
 -> structured response
 -> frontend state refresh
```

For mutations, the API should return enough information for the frontend to update its state without guessing.

## 9. Concurrency contract

For optimistic concurrency, mutation requests should carry a version / last-known revision.

A stale request should return a clear conflict response rather than silently overwrite newer data.

The frontend should then:
1. show a conflict message,
2. refresh the record,
3. let the user reconcile their changes.
