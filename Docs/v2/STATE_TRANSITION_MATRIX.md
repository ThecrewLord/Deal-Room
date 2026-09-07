# Deal Room v2 State Transition Matrix

**Status:** FROZEN --- Phase 2

## 1. State dimensions

Lifecycle: `Lead -> Qualified -> RFX -> POC -> Negotiations -> Delivery`

Outcome: `Open | Closed Won | Closed Lost`

Operational status: `Active | Stalled | Closed`

Stage, outcome, and operational status must not be collapsed into one
uncontrolled field.

## 2. Main transitions

  -----------------------------------------------------------------------
  From              To                Trigger           Conditions
  ----------------- ----------------- ----------------- -----------------
  New               Lead              Authorized Deal   Required creation
                                      Finder            fields valid

  Lead              Qualified         Sales Manager     Approval + Sales
                                                        Exec assigned

  Qualified         RFX               Pre-Sales / SE /  Authorized actor
                                      Leadership        

  RFX               POC               Pre-Sales / SE /  Required POC
                                      Leadership        input link

  POC               Negotiations      Pre-Sales / SE /  Valid POC
                                      Leadership        context/result

  Negotiations      Delivery          Pre-Sales Manager Final Closed Won
                                                        approval
  -----------------------------------------------------------------------

## 3. Lead review

Deal Finder submits Lead.

Sales Manager chooses:

### Approve

Requires Sales Executive assignment.

Result: `Lead -> Qualified`

### Closed Won

Sales Executive assignment not required.

Result: `Lead -> Closed Won`

### Closed Lost

Sales Executive assignment not required.

Reason required.

Result: `Lead -> Closed Lost`

### Reject

Result: `Sales Manager Review -> Lead`

Reject is not Closed Lost. The rejection is audited.

## 4. Qualified -\> RFX

Allowed: - Pre-Sales Manager - authorized Solution Engineer - Leadership

Denied: - Sales Manager - Sales Executive - Delivery roles - Admin

## 5. RFX -\> POC

Requires: - authorized actor - required Drive link - Drive permission
disclaimer

Deal Room does not verify Drive permissions.

## 6. POC request

POC request is an action while stage = POC.

Required: - success metrics - exit criteria - input Drive link

Result: - create POC request - notify Delivery Manager - remain in POC

## 7. POC assignment

Delivery Manager assigns up to two: - DevOps Engineer - Data Analyst

The POC team is the default suggested selection.

Suggestion does not equal automatic assignment.

## 8. POC execution

Delivery member: - views authorized information - works externally -
uploads output externally - supplies view link - submits result

Submission: - creates historical POC result - notifies Solution
Engineer - does not overwrite older POCs

## 9. Multiple POCs

Allowed while stage = POC:

`POC #1 -> result -> POC #2 -> result -> ...`

Historical POCs remain immutable.

`POC -> RFX` is not allowed in v2.

## 10. POC -\> Negotiations

Allowed: - Pre-Sales Manager - authorized Solution Engineer - Leadership

Must be based on valid POC context rather than arbitrary stage ID
assignment.

## 11. Negotiations

Negotiations is mandatory between POC and Delivery.

Documents are optional. NDA is a suggestion, not a mandatory field.

## 12. Negotiations -\> Delivery

Flow:

`Negotiations -> Pre-Sales Manager final approval`

Options:

### Approve Closed Won

`Negotiations -> Delivery`

### Close Lost

`Negotiations -> Closed Lost`

Sales Manager is not the final approver.

## 13. Early closure

### Closed Won

  Stage          Sales Mgr   Pre-Sales Mgr   SE    Leadership
  -------------- ----------- --------------- ----- ------------
  Lead           Y           ---             ---   Y
  Qualified      N           Y               C     Y
  RFX            N           Y               C     Y
  POC            N           Y               C     Y
  Negotiations   N           Y               C     Y

C = SE requires Pre-Sales Manager approval.

### Closed Lost

  Stage          Sales Mgr   Pre-Sales Mgr   SE    Leadership
  -------------- ----------- --------------- ----- ------------
  Lead           Y           ---             ---   Y
  Qualified      N           Y               Y     Y
  RFX            N           Y               Y     Y
  POC            N           Y               Y     Y
  Negotiations   N           Y               Y     Y

Sales Executive, Admin, and Delivery roles cannot close.

## 14. Closed Lost

Required: - standard reason

If standard reason = Other: - explanation mandatory

Otherwise: - explanation optional

Result: - outcome = Closed Lost - operational status = Closed -
opportunity locked

## 15. Solution Engineer Closed Won

Flow:

`SE -> Closed Won request -> Pre-Sales Manager`

Pre-Sales Manager: - Approve -\> Closed Won - Reject -\> prior open
stage

Rejection is audited.

## 16. Delivery

Once final Closed Won approval is complete:

`Negotiations -> Delivery`

Delivery Manager receives the project.

Delivery employees may mark their work Done.

Delivery Manager may mark the project Done at any time.

Manager completion is authoritative and is not blocked by employee Done
clicks.

## 17. Operational status

Active: - Active -\> Stalled - Active -\> Closed

Stalled: - Stalled -\> Active - Stalled -\> Closed

Closed: - terminal for normal users

Status changes should be audited.

## 18. Reopening

Normal users cannot reopen.

Leadership is reserved for future reopen capability.

POC -\> RFX reopening is future scope and is not implemented.

## 19. Forbidden transitions

Reject: - Lead -\> RFX - Lead -\> POC - Lead -\> Negotiations -
Qualified -\> POC - Qualified -\> Negotiations - RFX -\> Negotiations -
RFX -\> Delivery - POC -\> Delivery - Negotiations -\> RFX - Delivery
-\> previous stage - Closed -\> any stage - Sales Executive -\> stage
transition - Delivery -\> stage transition - Admin -\> stage transition

## 20. Atomicity

Every transition must atomically validate: - authorization - current
state - concurrency/version - mutation - history - audit -
event/notification

Partial workflow commits are forbidden.
