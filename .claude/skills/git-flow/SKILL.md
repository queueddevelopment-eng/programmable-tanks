---
name: git-flow
description: Programmable Tanks' git conventions - a solo repo with main always green and pushed, Conventional Commits with this repo's scopes (engine, viewer, experiments, results, tests, docs, playtest, toolkit, build), the Co-Authored-By trailer taken from the session's attribution reminder, what is never committed, the pre-commit gate, and gh one-liners. The repo is public. Loads on "commit", "commit message", "branch", "push", "PR", "what not to commit".
when_to_use: Before writing a commit, cutting a branch, pushing, or opening a pull request.
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash(git status*), Bash(git log --oneline*), Bash(git diff --stat), Bash(gh run list*), Bash(gh pr list*), Bash(gh pr view*)
---

# git-flow

A solo project built by its owner with Claude. Light on ceremony, strict about what lands in history. `CLAUDE.md` wins.

**Repo:** `queueddevelopment-eng/programmable-tanks`, branch `main`, **public**.

## Flow

- Work lands on `main` after the gate passes. Push after each verified commit.
- Branch (`feat/…`, `fix/…`, `exp/…`, `docs/…`) only for multi-session work or when the owner asks for a PR.
- Never force-push `main`. Never rewrite pushed history.

## Message

```
type(scope): what changed, imperative, ≤ 72 chars

Why it changed, and what verified it (gate output summarised: "parity v5 800/0,
templates 622/0, pits 600/0; fingerprints ok"). Decision letters if relevant.

<trailer lines exactly as the session's attribution reminder gives them>
```

- **Types:** `feat`, `fix`, `exp` (a new experiment or run), `refactor`, `test`, `docs`, `chore`, `build`.
- **Scopes:**
  - `engine`: either engine, or both;
  - `viewer`: UI outside the ENGINE block;
  - `experiments`;
  - `results`;
  - `tests`;
  - `docs`;
  - `playtest`;
  - `toolkit`: `.claude/` and CLAUDE.md;
  - `build`.
- A rule change and its docs ride in one commit. Experiment code and its results file ride together.

## Never committed

- `__pycache__/`, `*.pyc`;
- `.claude/settings.local.json`, `.claude/agent-memory-local/`, `.claude/worktrees/`;
- scratch scripts;
- screenshots, unless the owner asks for them;
- anything personal: emails, playtesters' names, content from other projects. The repo is public.

## Tracked on purpose

- `results/*.txt`: the evidence behind the docs' numbers.
- `.claude/agent-memory/**`: tracked memory, no personal data.
- `docs/**`.
- The published viewer's source, `tank-match-viewer.html`.

## Pre-commit

1. code-reviewer's verdict (or the owner skipped review).
2. The gate for any rule change (CLAUDE.md Commands), with the output summarised in the body.
3. `git status` shows only the intended files.

## gh

`gh run list --limit 5` (no CI yet). In Claude Code cloud sessions, `gh` GraphQL is unavailable; use REST paths (`gh api repos/queueddevelopment-eng/programmable-tanks/...`).
