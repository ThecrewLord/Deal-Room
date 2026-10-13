# Deal Room — Database & Relationships

## 1. Current model inventory

The application code references these real tables/models:

| Domain | Model/Table | Main purpose |
|---|---|---|
| Auth | User | Application identity |
| Auth | UserRole | User-to-role assignment |
| Account | Account | Customer/company account |
| Account | Contact | Account contact |
| Account | OEMPartner | Partner/OEM relationship |
| Opportunity | StageMaster | Canonical pipeline stages |
| Opportunity | Opportunity | Core commercial opportunity |
| Opportunity | OpportunityTeam | Opportunity visibility/team membership |
| Opportunity | Stakeholder | Opportunity stakeholders |
| Opportunity | StageHistory | Stage-change history |
| Opportunity | POCTracker | Current POC tracking model |
| POC | Poc | Legacy/separate POC model |
| System | Tag | Tag metadata |
| System | AuditLog | Auditable actions/history |
| System | Notification | Workflow notifications |

## 2. Core relationship graph

```text
User
 ├──< UserRole
 ├──< Opportunity (created_by)
 ├──< Opportunity (sales_owner_id)
 ├──< OpportunityTeam >── Opportunity
 ├──< StageHistory
 └──< AuditLog

Account
 ├──< Contact
 ├──< OEMPartner
 └──< Opportunity

StageMaster
 ├──< Opportunity
 └──< StageHistory

Opportunity
 ├──< OpportunityTeam >── User
 ├──< Stakeholder
 ├──< StageHistory >── StageMaster
 ├──< POCTracker
 ├──< Poc  [legacy/separate representation]
 └──< AuditLog

System metadata
 ├── Tag
 ├── AuditLog
 └── Notification
```

## 3. Dependency order

For creation/import, the practical dependency chain is:

```text
Users / Roles
      |
      +------------------+
      |                  |
      v                  v
Accounts             StageMaster
      |                  |
      +--------+---------+
               |
               v
          Opportunities
          /     |               /      |               v       v        v
 Contacts  Stakeholders  OpportunityTeam
                                         v
                 POCTracker

Opportunity -> StageHistory
Opportunity -> AuditLog
Opportunity -> Notifications
```

OEM partners depend on accounts.

Contacts depend on accounts.

Opportunities depend on accounts and stages, and normally reference users for creator/owner.

Stakeholders depend on opportunities.

Opportunity teams depend on opportunities and users.

Stage history depends on opportunities, stages and the acting user.

POC records depend on opportunities.

## 4. Data provenance / import behavior

The seed documentation states that the workbook is the source of truth for:
- Accounts
- Opportunities
- Stakeholders
- POC_Tracker
- Activity_Log
- OEM_Partners

Python is intentionally used for application test identities and canonical stages rather than hard-coding the business corpus.

## 5. Important schema mismatch

The workbook contains an external POC identifier, but the current `POCTracker` schema does not have a dedicated external `poc_id` in the seed logic. The importer therefore uses opportunity + start date to identify an existing tracker.

This is a fragile mapping and should be resolved by adding a stable external/source identifier if the workbook remains an authoritative import source.

## 6. POC duplication

The database contains both:
- `POCTracker`
- `Poc`

The seed code explicitly calls the latter legacy/separate.

This creates the most obvious competing-source-of-truth risk in the current model.

**Decision required:** select one canonical POC table and migrate/deprecate the other.

## 7. Stakeholder vs Contact

A stakeholder is opportunity-specific.

A contact is account-specific.

This distinction can be valid:

```text
Account
  |
  +--> Contact
         |
         +--> may participate in an Opportunity as Stakeholder
```

However, the current seed process derives contacts from stakeholder rows. The system should define whether a stakeholder is:
- a reference to a reusable contact, or
- a separate opportunity-role record.

A normalized design would usually separate identity/contact data from opportunity-specific role/influence data.

## 8. Audit vs activity

The project has `AuditLog`, while the business dataset has an `Activity_Log`.

These should not automatically be treated as the same thing.

Recommended distinction:

- **Activity:** sales/business event visible in opportunity timeline.
- **Audit log:** security/system record of who changed what and when.

## 9. Database integrity checks to add

- [ ] Foreign-key constraints for all relationship columns.
- [ ] Unique `(opportunity_id, email)` for stakeholders if that is the intended identity rule.
- [ ] Unique opportunity-team membership.
- [ ] Unique stage names.
- [ ] Stable external IDs for imported business records.
- [ ] Check constraints for probability range.
- [ ] Consistent closed-stage/status rules.
- [ ] Version/revision column for optimistic concurrency.
- [ ] Explicit cascade rules.
