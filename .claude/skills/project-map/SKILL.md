---
name: project-map
description: Map of Programmable Tanks - the locked decisions (a)-(n) with where each is stated and enforced, the owner's dated decisions, the file map with owner agents, the staging plan and where the project stands on it, the status ledger with a command per claim, and the open items. Loads on "locked decision", "is this allowed", "who owns", "where does X live", "status", "what is verified", "which step", "open items".
when_to_use: Before designing, planning, reviewing or documenting a change; when deciding who owns a file; when a status claim must be checked against reality, not a doc.
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash(git status -sb), Bash(git log --oneline -10), Bash(python tests/parity.py*), Bash(python tests/fingerprints.py)
---

# Project map

`CLAUDE.md` is the source of truth. This skill is a map, not a second authority: if they disagree, CLAUDE.md wins and this file is stale (tell docs-writer). Verified 2026-11-15 at the first commit on `main`.

## What exists

- **Rules:** the v0.5 draft, in both engines and in `docs/RULES-v0.5-draft.md`:
  - chassis + a dealt hand of 5 from a 47-card shared deck;
  - two pit stops;
  - pits, Breach, Raise wall (behind);
  - Hunt avoids walls and pits;
  - Otherwise;
  - specials with the spent rule;
  - optional pickups;
  - a 10-tick shot clock, where the leader attacks, with card-language overtime.
- **Measurement:** seven experiment files, the results of the October runs, the parity harness and the fingerprints.
- **The playable viewer**, published as a claude.ai artifact.
- **Nobody but the owner has played.** No round has been run by hand on paper.

## Staging plan position

Step 1 (simulator tuning), Phase 1 of `docs/PLAN-2026-11.md`. Next: E2 and E1, then E3, E4 and E5, then the v0.5 freeze, then Phase 2 (the playtest kit and 5+ sessions).

## Detail

| File | Read when |
|---|---|
| `decisions.md` | Is something allowed? Each decision (a)–(n): its text, where it's stated, how it's enforced, and the owner decisions with dates |
| `ledger.md` | Status claims and the command that verifies each; the file map with owner agents; open items |
