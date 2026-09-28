# Deal Room Documentation Pack

Generated: 31 Aug 2026

## Files

1. `PLAN.md` — product plan, workflow, quality bar and execution phases.
2. `DESIGN.md` — architecture and workflow design.
3. `WHAT_WE_HAVE_MADE.md` — current build/readout.
4. `TODO.md` — prioritized remaining work.
5. `BACKEND.md` — backend responsibilities and frontend/API/database connectivity.
6. `DATABASE.md` — tables, dependencies and relationship model.
7. `PLANNED_VS_MADE.md` — planned requirements versus current implementation.
8. `OPEN_ENDPOINTS_AND_CODE.md` — endpoint/code review checklist and clarity gaps.

## Evidence basis

This pack was synthesized from the Deal Room project discussion and accessible project artifacts, including the 27 Aug progress/readout material and the seed-data implementations. The progress material describes the architecture as React/Vite + Flask REST API + SQL and reports core workflows as working while keeping several items in verification/hardening. The seed implementations provide concrete evidence for the current model inventory, import behavior, closed-stage mapping, POC duplication, and idempotent seed strategy.

The uploaded backend/frontend ZIPs were not accessible in the active runtime during this generation, so `OPEN_ENDPOINTS_AND_CODE.md` intentionally labels route-level findings as items requiring repository-level verification rather than pretending to have scanned files that could not be read.
