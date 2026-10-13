# Phase 3 Internal Gap Matrix

| Domain | Existing | Phase 3 status | Action / finding |
|---|---|---|---|
| Authentication / active role | Complete in Phase 1/2 | Preserved | No replacement |
| Lifecycle | Complete/frozen | Preserved | No new stages/transitions |
| Global Search | Partial: Opportunity/Account/POC | Improved | 8 entity types + filters + pagination |
| Search authorization | Present | Improved | Central scope + restricted projections |
| Dashboards | Common backend + partial role UI | Improved | Role-specific KPIs and analytics data |
| Weighted forecast | Existing probability calculation | Open decision | No approved stage mapping found |
| Revenue | Phase 2 value/final revenue/attribution | Extended | Dashboard revenue intelligence |
| Stalled opportunities | Existing metric | Preserved/extended | Operational dashboard visibility |
| FollowUps | Phase 2 domain | Extended | Dashboard due/overdue/upcoming/completed counts |
| Activities | Phase 2 domain | Extended | Dashboard authorized activity count |
| Notifications | Existing framework | Preserved | No second system introduced |
| Audit/history | Existing logs/history | Partial | Existing history preserved; first-class audit timeline still open |
| Opportunity timeline | Not a first-class API/UI | Open | Candidate after Phase 3 certification |
| Opportunity detail | Existing Phase 2 detail | Preserved | No destructive redesign |
| Closed UX | Existing locked state | Preserved | No post-close mutation changes |
| Security audit | Phase 1/2 controls | Partial | Static review done; live IDOR/concurrency tests blocked by environment |
| Input validation | Existing write validation | Review required | Phase 3 live endpoint fuzz/validation pass still required |
| Query performance | Existing indexes | Review required | PostgreSQL EXPLAIN not run in uploaded environment |
| Pagination | Existing list endpoints mixed | Partial | Search now paginated; broader list endpoint audit remains |
| API consistency | Mixed legacy/current endpoints | Partial | Search contract improved; legacy endpoint audit remains |
| Legacy code | Compatibility references remain | Review required | Historical vs runtime classification needed |
| Seed/reset | Existing Phase 2 support | Not re-certified | Requires normal DB environment |
| Frontend UX | Shared component system | Improved | Role KPI coverage/search response compatibility |
| Production build | Not available in upload | Blocked | Frontend package lacks package.json/node_modules |
| Full regression | 57/0/1 reported by source prompt | Not re-certified | Local environment missing Python dependencies |
