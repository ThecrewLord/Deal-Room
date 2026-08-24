# Deal Room Phase 4 — Sales Executive → Sales Manager

Implemented Phase 4 only. The workflow is:

Lead / Identified → Qualification → Pending Sales Manager Review → Approved or Rejected.

Approval requires an active, approved Sales Executive as Sales Owner. The creator and Sales Owner remain separate, and the assigned owner is added to OpportunityTeam for participation visibility. Reassignment is not implemented.

Notifications are persisted in the new `notifications` table. Phase 5/6 technical assignment and POC workflow changes are not introduced by this phase.
