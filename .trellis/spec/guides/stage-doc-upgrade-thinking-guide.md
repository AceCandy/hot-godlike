# Stage Documentation Upgrade Thinking Guide

> **Purpose**: Keep stage brief upgrades synchronized across product docs, workflow, task state, and verification records.

---

## When To Use

Use this guide when upgrading a route-level brief, such as `docs/prd/m5-*-brief.md`, into a detailed contract plus backend/frontend PRDs.

This is a documentation workflow guide, not a replacement for backend/frontend code-specs.

---

## Upgrade Checklist

After creating or updating a stage contract / PRD set:

- [ ] Add or update the shared contract under `docs/contracts/`.
- [ ] Add or update backend and frontend PRDs under `docs/prd/`.
- [ ] Update `prd.md` section `13.10` with the new contract and PRD paths.
- [ ] Update the matching stage section in `prd.md` so it references the detailed docs, not only the brief.
- [ ] Update `workflow.md` startup commands for the stage.
- [ ] Update `workflow.md` contract / PRD lists.
- [ ] Update `workflow.md` current-stage table from brief-only to `已具备详细 PRD，待确认编码入口`.
- [ ] Update `.trellis/tasks/<task>/progress.md` current conclusion, completed items, next steps, recovery rules, and do-not-repeat rules.
- [ ] Update `.trellis/tasks/<task>/task.json` `relatedFiles` and `notes`.

---

## Required Verification

Run checks that prove synchronization, not just file existence:

- [ ] Contract / backend PRD / frontend PRD cover `workflow.md` 8.3 required sections.
- [ ] `task.json`, `implement.jsonl`, and `check.jsonl` parse successfully.
- [ ] Every `task.json.relatedFiles` path exists.
- [ ] `prd.md`, `workflow.md`, `progress.md`, and `task.json` all contain the new contract and PRD paths.
- [ ] Old brief-only recovery hints are gone for the upgraded stage.
- [ ] Core boundary terms are searchable across the new docs.
- [ ] Touched docs have no trailing whitespace.
- [ ] Git root / commit readiness is checked; if not a Git repository, record the blocker in `progress.md`.

---

## Wrong vs Correct

### Wrong

- Create `docs/contracts/<stage>.md` and PRDs.
- Say in chat that the stage is done.
- Leave `workflow.md`, `progress.md`, or `task.json` saying the stage is still brief-only.

### Correct

- Create or update the detailed docs.
- Synchronize all indexes and recovery docs.
- Run section, index, stale-status, relatedFiles, boundary, whitespace, and Git-root checks.
- Write the successful checks into `progress.md`.

---

## Python Runner Note

If `python3` points to a broken Homebrew interpreter and Trellis scripts fail before running, retry Trellis scripts with `/usr/bin/python3` and record the environment blocker in `progress.md`. Do not edit shell configuration as part of a documentation upgrade unless explicitly requested.
