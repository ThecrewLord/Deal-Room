# Deal Room v2 — Decisions Required Before Implementation

This is intentionally limited to conflicts or material omissions in the frozen v2 artifacts. It is not a list of implementation preferences. Resolved decisions are retained below as an implementation record; only the final open item blocks v2 application code.

## D1 — What does “Closed Won -> Delivery” mean operationally?

**Conflict.** The model says `Closed Won` is an outcome and that closed opportunities are locked ([DEAL_ROOM_V2_SPEC.md](DEAL_ROOM_V2_SPEC.md) §§8, 14; [STATE_TRANSITION_MATRIX.md](STATE_TRANSITION_MATRIX.md) §§1, 14). Yet the final gate says “Approve Closed Won -> Delivery” and represents the result as `Negotiations -> Delivery` ([DEAL_ROOM_V2_SPEC.md](DEAL_ROOM_V2_SPEC.md) §13; [STATE_TRANSITION_MATRIX.md](STATE_TRANSITION_MATRIX.md) §§12, 16). Delivery users must then be able to assign people and mark work done.

Those rules cannot all be represented by a single terminal `closed` state without an exception: a terminal, locked closed opportunity cannot also accept normal delivery assignment/completion mutations.

**Resolved (user, 2026-09-04).** `Closed Won` is terminal for the opportunity, locks it, snapshots Final Revenue, and automatically creates a distinct Delivery Project for the Delivery Manager. The project is a separate system/aggregate. Only Delivery Manager, assigned delivery employees, and Leadership interact with it; other business roles do not. This is option 2.

## D2 — Which action produces Closed Won outside the final Negotiations gate?

**Conflict.** The transition matrix permits a Pre-Sales Manager to close won from `Qualified`, `RFX`, and `POC`, and permits a Solution Engineer to submit a Closed Won request from those stages ([STATE_TRANSITION_MATRIX.md](STATE_TRANSITION_MATRIX.md) §§13, 15). Separately, the normal final gate says Pre-Sales approval results in `Negotiations -> Delivery` (§12). The specification says final revenue is set “when opportunity becomes Closed Won” ([DEAL_ROOM_V2_SPEC.md](DEAL_ROOM_V2_SPEC.md) §18).

**Resolved (user, 2026-09-04).** Closed Won may occur from any open opportunity stage. It always creates the separate Delivery Project, including before Negotiations. A pre-Negotiations win has no POC-team suggestion; the Delivery Manager assigns the project team directly.

## D3 — At which transition is the required RFX Google Drive link captured?

**Conflict.** “RFX” says its required Drive link is used for POC documentation ([DEAL_ROOM_V2_SPEC.md](DEAL_ROOM_V2_SPEC.md) §10), while the transition matrix makes the link a condition of `RFX -> POC` ([STATE_TRANSITION_MATRIX.md](STATE_TRANSITION_MATRIX.md) §5). The authorization matrix calls it “Supply POC input link” and allows it conditionally for Pre-Sales Manager, Solution Engineer, and Leadership ([AUTHORIZATION_MATRIX.md](AUTHORIZATION_MATRIX.md) §9).

**Resolved (user, 2026-09-04).** Require/capture the RFX Drive link only when moving `RFX -> POC`. Store it on the opportunity’s RFX context; it persists across subsequent POC cycles unless an authorized Solution Engineer updates it. The app displays access guidance and does not verify Drive permissions. Each POC request still has its own required input Drive link.

## D4 — Define Deal Finder eligibility and post-creation Lead ownership

**Omission.** The authorization matrix marks lead creation `C` for every business role ([AUTHORIZATION_MATRIX.md](AUTHORIZATION_MATRIX.md) §4), and the specification calls the actor an “authorized Deal Finder,” but neither defines the eligibility rule nor who can edit a draft/rejected Lead. It also explicitly allows a Sales Manager who is the Deal Finder to review their own Lead.

**Resolved (user, 2026-09-04).** Every approved active role except Admin is eligible to act as Deal Finder and create a Lead. Every such employee can see/add central accounts and select existing OEM partners for the opportunity they create. Sales Manager has no reject/rework action: the only negative initial-review outcome is Closed Lost, which is terminal and permits no subsequent action. The self-review exception remains as frozen.

## D5 — Define who assigns Solution Engineers and when

**Omission.** V2 authorizes “assigned” Solution Engineers to view/change stages and request POCs ([AUTHORIZATION_MATRIX.md](AUTHORIZATION_MATRIX.md) §§1, 8–9), but does not say who creates, changes, or ends that participation or when it must exist. The older application has a Pre-Sales Manager technical-assignment queue, but that is not frozen v2 behavior.

**Resolved (user, 2026-09-04).** Pre-Sales Manager assigns Solution Engineers. The assignment is immutable in normal operations. Only departure from the company or Admin access revocation returns the opportunity to Pre-Sales Manager for reassignment. Retain assignment history; do not overwrite it.

## D6 — Define canonical-account duplicate matching and archive reuse

**Omission.** Duplicate prevention must include archived accounts ([DEAL_ROOM_V2_SPEC.md](DEAL_ROOM_V2_SPEC.md) §5), but the frozen artifacts do not define equivalence. Exact case-insensitive equality will not prevent the stated `Acme Ltd` / `ACME Limited` / `Acme Pvt Ltd` examples, while aggressive fuzzy matching can block legitimate companies.

**Resolved (user, 2026-09-04).** An archived account cannot be reactivated. It remains in the directory/history. Physical deletion is permitted only to resolve a duplicate account. Leadership can also ban an account: it remains visible in the list with a red status and cannot be selected for a new opportunity; attempted creation must return exactly: `this account is banned`.

**Implementation note:** deterministic canonical-name matching remains required to identify duplicates. Use a normalized unique key across active, archived, and banned rows; do not use fuzzy matching as an automatic delete decision.

## D7 — Define OEM attachment authority for non-Leadership employees

**Ambiguity.** Leadership alone CRUDs OEM master data ([DEAL_ROOM_V2_SPEC.md](DEAL_ROOM_V2_SPEC.md) §16), while the authorization matrix says employees can conditionally “Attach multiple OEMs” ([AUTHORIZATION_MATRIX.md](AUTHORIZATION_MATRIX.md) §12). It does not name the eligible roles, resource scope, lifecycle stages, or detach rules.

**Resolved (user, 2026-09-04).** Existing OEMs may be attached during Deal Finder opportunity creation, by Sales Manager during initial review, and after that only by Pre-Sales Manager, assigned Solution Engineer, or Leadership. Preserve association history and prohibit mutation on a closed opportunity.

## D8 — Define the delivery-work unit and assignment invariants

**Omission.** V2 says the Delivery Manager assigns/reassigns delivery members and individuals mark their own work Done ([DEAL_ROOM_V2_SPEC.md](DEAL_ROOM_V2_SPEC.md) §15; [AUTHORIZATION_MATRIX.md](AUTHORIZATION_MATRIX.md) §10), but it does not define whether the assigned object is one project-level team membership, named work items, or one completion flag per employee. It also says the POC team is suggested as the delivery team although POC members are DevOps/Data roles and may be zero, one, or two.

**Resolved (user, 2026-09-04).** A Delivery Project may have any number of delivery members. Its POC team appears preselected as proposed members; Delivery Manager may remove any/all before approving the project team. The manager then assigns the final team. Retain the lightweight project/member-completion model—do not introduce a work-item engine.

## D9 — Define which stakeholder actions remain allowed after closure and during draft Lead

**Ambiguity.** The stakeholder table grants a number of conditional actions but does not express lifecycle constraints ([AUTHORIZATION_MATRIX.md](AUTHORIZATION_MATRIX.md) §11), while closed opportunities are stated to be locked ([DEAL_ROOM_V2_SPEC.md](DEAL_ROOM_V2_SPEC.md) §14).

**Resolved (user, 2026-09-04).** All stakeholder and tag mutations are denied after Closed Won or Closed Lost. The remaining role permissions follow the frozen authorization matrix.
