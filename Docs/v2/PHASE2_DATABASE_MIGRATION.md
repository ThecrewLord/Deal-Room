# Phase 2 Database Migration

Migration: `p2a3b4c5d6e7_phase2_business_domains.py`

Down revision: `f7a8b9c0d1e2`

## Changes
- Adds `accounts.canonical_name` and `accounts.status`.
- Backfills canonical account identity using trimmed, lower-cased, repeated-whitespace-normalized names.
- Replaces display-name uniqueness with canonical-name uniqueness.
- Renames stakeholder identity columns to V2 terminology and adds `company` and `is_decision_maker`.
- Creates fixed stakeholder tag link storage and the transactional Decision Maker unique index.
- Adds V2 POC input/result links and submission metadata to `poc_tracker`.
- Creates `poc_team_members`.
- Creates `opportunity_oems`.
- Creates `rfx_contexts` and `negotiation_contexts`.
- Creates `delivery_projects` and `delivery_project_members`.
- Creates `activities` and `follow_ups`.
- Removes the disposable duplicate `poc` aggregate.

## Integrity
Business-history foreign keys use RESTRICT where deletion could damage history. Delivery project membership uses CASCADE only from a project to its membership rows. Canonical identity and Decision Maker constraints are database-authoritative.

## Important
The migration is intentionally one-way for V2 development cutover. Apply it to a clean Phase 1 database before running the deterministic V2 reset/seed.
