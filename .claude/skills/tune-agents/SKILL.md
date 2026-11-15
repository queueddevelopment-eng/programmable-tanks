---
name: tune-agents
description: Checklist for cutting the cost of a Programmable Tanks session after a session-limit hit or high usage - read the usage breakdown's signals, apply the spawn and read rules, review the model tiers, and propose (never make) a model move. Adapted from the owner's origami-mask-designer toolkit (2026-10-22 decision).
when_to_use: After the session limit is hit, or when usage runs high; before a long fan-out; when someone asks which agent runs on which model.
user-invocable: true
allowed-tools: Read, Grep, Glob
---

# Tune agents

`CLAUDE.md` "Agent economy" wins; this is a procedure. A model move is the owner's decision.

## 1. Read the usage breakdown

Ask the owner to paste it. Read four signals: the share inside subagents, the share above 150k context, the share from tool results over 10k tokens, and the per-agent shares.

## 2. Apply the rules

- Never resume an agent past about 100k tokens for a small fix. Spawn fresh with a tight brief and a memory file.
- At most two agents at once.
- Narrow reads:
  - Never read `tank-match-viewer.html` (69 KB) whole; Grep, then offset and limit.
  - Never read a results file whole.
  - Experiments run in the background and only their verdict section is read.
- Bounded reports (about 300 words, `file` and symbol).
- `/compact` at each slice boundary. A new session after two slices or past ~150k.

## 3. Current model tiers (read the frontmatters to confirm)

| Tier | Agents |
|---|---|
| haiku | github-ops |
| sonnet | docs-writer |
| opus | game-designer, tabletop-sme |
| inherit (session model) | project-manager, rules-engineer, sim-analyst, viewer-developer, playtest-designer, code-reviewer |

## 4. Propose a move; don't make it

To move an agent to another tier, write the proposal with the evidence (its share of usage, mechanical versus judgement work, the saving) and send it to the owner. A `model:` edit is a `toolkit` commit.
