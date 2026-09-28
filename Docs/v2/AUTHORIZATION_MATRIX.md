# Deal Room v2 Authorization Matrix

**Status:** FROZEN --- Phase 2

Legend: Y = allowed, N = denied, C = conditional, V = view-only.

## 1. Core resource visibility

  --------------------------------------------------------------------------------------------------------------------
  Resource         Leadership   Admin   Sales Mgr    Sales Exec   Pre-Sales    Solution Eng Delivery Mgr DevOps/Data
                                                                  Mgr                                    
  ---------------- ------------ ------- ------------ ------------ ------------ ------------ ------------ -------------
  System           Y            Y\*     N            N            N            N            N            N
  administration                                                                                         

  Other Admin      Y            N       N            N            N            N            N            N
  identities                                                                                             

  Business         Y            N       Team         Authorized   Assigned     Assigned     Delivery     Assigned
  pipeline                                                                                  scope        scope

  Central Accounts Y            N       Y            Y            Y            Y            Y            Y

  Opportunity      Y            N       Team         Authorized   Assigned     Assigned     Assigned     Assigned
  details                                                                                                scope

  POC records      Y            N       Authorized   Authorized   Authorized   Assigned     Assigned     Assigned
                                                     view                                                

  OEM names        Y            N       Authorized   Authorized   Authorized   Authorized   Authorized   Authorized

  OEM contacts     Y            N       N            N            N            N            N            N

  Company          Y            N       Team         Own scope    Relevant     Relevant     Delivery     Own scope
  performance                                                     scope        scope        scope        
  --------------------------------------------------------------------------------------------------------------------

\* Admin privileges are delegated by Leadership and remain
system-administration privileges.

## 2. System administration

  Action                          Leadership   Admin            Other roles
  ------------------------------- ------------ ---------------- -------------
  Approve/revoke users            Y            C                N
  Assign normal business roles    Y            C                N
  Assign Admin                    Y            C if delegated   N
  Assign Leadership               Y            N                N
  View other Admins               Y            N                N
  Remove/demote last Leadership   N            N                N
  Grant self Admin/Leadership     N            N                N

## 3. Accounts

  Action                           Leadership   Admin   Employees
  -------------------------------- ------------ ------- -----------
  Search                           Y            N       Y
  View canonical company details   Y            N       Y
  Add account                      Y            N       Y
  Edit canonical account           Y            N       N
  Archive                          Y            N       N
  Physical delete                  N\*          N       N

\*Prefer archival where historical references exist.

## 4. Opportunity creation

  -------------------------------------------------------------------------------------
  Action        Leadership   Admin    Sales    Sales    Pre-Sales   SE       Delivery
                                      Mgr      Exec                          
  ------------- ------------ -------- -------- -------- ----------- -------- ----------
  Create Lead   Y            N        C        C        C           C        C

  Set initial   Y            N        C        C        C           C        C
  value                                                                      

  Add           Y            N        C        C        C           C        C
  description                                                                

  Add initial   Y            N        C        C        C           C        C
  stakeholder                                                                

  Add pain      Y            N        C        C        C           C        C
  points                                                                     

  Submit for    Y            N        C        C        N           N        N
  Sales Manager                                                              
  -------------------------------------------------------------------------------------

Business-role eligibility and Deal Finder recording are enforced
server-side.

## 5. Initial Sales Manager review

  Action                   Sales Mgr   Leadership   Others
  ------------------------ ----------- ------------ --------
  Review                   Y           Y            N
  Edit permitted details   Y           Y            N
  Assign Sales Exec        Y           Y            N
  Approve                  Y           Y            N
  Close Won immediately    Y           Y            N
  Close Lost immediately   Y           Y            N

Approval requires Sales Executive assignment. Direct closure does not.

## 6. Post-Qualified fields

  ---------------------------------------------------------------------------
  Field/action   Sales Exec  Sales Mgr   Pre-Sales   SE          Leadership
                                         Mgr                     
  -------------- ----------- ----------- ----------- ----------- ------------
  Stage          N           N           C           C           Y

  Description    N           N           Y           Y           Y

  Opportunity    N           N           Y           N           Y
  Value                                                          

  Add            Y           C           C           C           Y
  stakeholder                                                    

  Edit           N           C           C           C           Y
  stakeholder                                                    

  Close          N           N           Y           C\*         Y
  ---------------------------------------------------------------------------

\*C = Solution Engineer Closed Won requires Pre-Sales Manager approval.

## 7. Value/revenue

After creation, current Opportunity Value may be modified only by: -
Sales Manager - Pre-Sales Manager - Leadership

Each change requires old/new value, reason, actor, timestamp.

Final Revenue is created at Closed Won and is immutable for ordinary
users.

## 8. Stage authority

After Qualified:

  -----------------------------------------------------------------------------------
  Action         Pre-Sales   SE         Leadership   Sales Mgr  Sales Exec Delivery
                 Mgr                                                       
  -------------- ----------- ---------- ------------ ---------- ---------- ----------
  Qualified -\>  Y           Y          Y            N          N          N
  RFX                                                                      

  RFX -\> POC    Y           Y          Y            N          N          N

  POC -\>        Y           Y          Y            N          N          N
  Negotiations                                                             

  Negotiations   Y\*         N/C        Y            N          N          N
  -\> Delivery                                                             

  POC -\> RFX    N           N          N            N          N          N
  -----------------------------------------------------------------------------------

\*Final Delivery transition requires Pre-Sales Manager approval.

## 9. POC

  --------------------------------------------------------------------------
  Action      Pre-Sales   SE          Delivery    DevOps/Data   Leadership
              Mgr                     Mgr                       
  ----------- ----------- ----------- ----------- ------------- ------------
  Request POC Y           Y           N           N             Y

  Define      C           Y           N           N             Y
  success                                                       
  metrics                                                       

  Define exit C           Y           N           N             Y
  criteria                                                      

  Supply POC  C           Y           N           N             Y
  input link                                                    

  Assign POC  Y           N           Y           N             Y
  team                                                          

  Execute POC N           N           C           Y             C

  Submit      N           N           C           Y             C
  result                                                        

  Edit        N           N           N           N             N
  submitted                                                     
  result                                                        

  Review      Y           Y           N           N             Y
  result                                                        

  Create      Y           Y           N           N             Y
  another POC                                                   

  Delete POC  N           N           N           N             N
  --------------------------------------------------------------------------

## 10. Delivery

  Action                               Delivery Mgr   DevOps/Data   Leadership
  ------------------------------------ -------------- ------------- ------------
  View project                         Y              Y             Y
  Assign/reassign team                 Y              N             Y
  Use POC team as default suggestion   Y              N             Y
  Mark own work Done                   N              Y             Y
  Mark project Done                    Y              N             Y
  Change Opportunity stage             N              N             Y
  Close Opportunity                    N              N             Y

## 11. Stakeholders

  ----------------------------------------------------------------------------------
  Action        Leadership   Sales Mgr  Sales Exec Pre-Sales   SE         Delivery
  ------------- ------------ ---------- ---------- ----------- ---------- ----------
  View          Y            Y          Y          Y           Y          Y
  authorized                                                              
  stakeholder                                                             

  Add           Y            C          Y          C           C          C

  Edit          Y            C          N          C           C          C

  Set tags      Y            C          Y          C           C          C

  Set Decision  Y            C          Y          C           C          C
  Maker                                                                   

  Create second N            N          N          N           N          N
  Decision                                                                
  Maker                                                                   
  ----------------------------------------------------------------------------------

## 12. OEM

  Action                                    Leadership   Employees   Admin
  ----------------------------------------- ------------ ----------- -------
  View OEM name on authorized opportunity   Y            Y           N
  View OEM contact details                  Y            N           N
  Create/edit/archive OEM master            Y            N           N
  Attach multiple OEMs                      Y            C           N

## 13. Closure

### Initial Lead review

-   Sales Manager: Closed Won/Lost
-   Leadership: Closed Won/Lost
-   Sales Executive: denied
-   Admin: denied

### Qualified onward

-   Pre-Sales Manager: Closed Won/Lost
-   Leadership: Closed Won/Lost
-   Solution Engineer: Closed Lost; Closed Won with Pre-Sales approval
-   Sales Manager: denied
-   Sales Executive: denied
-   Delivery: denied
-   Admin: denied

### Final Negotiations gate

Pre-Sales Manager approves Closed Won -\> Delivery or closes Lost.

## 14. Closed state

Closed opportunities: - cannot be edited by ordinary users - cannot
change stage - cannot mutate POC - cannot reassign - cannot change
value - cannot change stakeholders

Leadership is reserved for future reopen authority.

## 15. Enforcement rule

Every protected mutation must validate: 1. authentication 2. active role
3. resource visibility 4. relationship/team scope 5. stage/status 6.
field-level permission 7. optimistic concurrency 8. atomic mutation 9.
audit 10. notification/event where required

Never trust client-supplied role, ownership, stage, user IDs, or generic
update payloads.
