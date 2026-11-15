# Programmable Tanks AI toolkit (`.claude/`)

The project-scoped Claude Code toolkit for Programmable Tanks: specialised agents, skills, tracked agent memory, shared settings and two hooks. It encodes how work is done here, so any session starts from the same rules:
- one card-language rule set;
- two engines kept in exact step;
- every rule a default-off `Config` field;
- simulator numbers as directional evidence with pass lines written first;
- human playtests as the final referee;
- the staging plan.

Start with [`CLAUDE.md`](../CLAUDE.md) for the rules themselves; it wins wherever this file disagrees. Locked decisions are cited as letters (a)–(n); `skills/project-map/decisions.md` says where each is stated and enforced.

The layout follows the owner's other toolkits (origami-mask-designer, 2026-10). It's sized smaller on purpose: this is a rules-design project with two small engines, not an application with an API and clients.

## Agents (`agents/`)

Delegated automatically when a task matches an agent's description, or invoked by name ("use the sim-analyst agent to …"). After adding or renaming an agent, run `/agents` or restart the session so it registers.

| Agent | Model | Tools | Preloaded skills | Owns |
|---|---|---|---|---|
| project-manager | inherit | Read, Grep, Glob, Bash | project-map, git-flow | Plans one-agent tasks with pass lines and a definition of done, delegates by name, reports honest status against the staging plan; inspects, never edits |
| game-designer | opus | Read, Grep, Glob, WebFetch, WebSearch | project-map, rules-engine, experiment-method | Rule proposals and experiment briefs checked against (a)–(n), with paper cost; never codes |
| rules-engineer | inherit | engineer set | rules-engine | `tanksim.py`, the viewer's ENGINE block, `tests/**`; both engines in step, the gate green |
| sim-analyst | inherit | engineer set | experiment-method, rules-engine | `experiments*.py`, `results/**`, the proxies; runs experiments on paired seeds and reports verdicts against the pass line |
| viewer-developer | inherit | engineer set | rules-engine, playtest-protocol | `tank-match-viewer.html` outside the ENGINE block: UI, deal mode, pit stops, computer opponent, board editor, text, themes |
| playtest-designer | inherit | Read, Grep, Glob, Edit, Write | playtest-protocol, project-map | `docs/playtest/**`: session protocol, observer and tick sheets, quick reference, the print-and-play kit spec, paper executability, debriefs |
| tabletop-sme | opus | Read, Grep, Glob, WebFetch, WebSearch | project-map, playtest-protocol | Verdicts on balance, luck versus skill, clarity, downtime, components and print-on-demand cost, comparable games; advisory, never edits |
| docs-writer | sonnet | Read, Grep, Glob, Edit, Write | project-map | `CLAUDE.md` Current phase and Repo layout, `README.md`, `docs/RULES-*`, `docs/PLAN-*`, `docs/TANKS-*`, this file |
| code-reviewer | inherit, plan mode | Read, Grep, Glob, Bash | review-checklist, project-map, rules-engine | Diff review against (a)–(n), parity, fingerprints, docs sync, the public-repo rule; never edits or commits |
| github-ops | haiku | Bash, Read, Grep, Glob | git-flow | Commits with the trailer, push to `origin main`, `gh`; owns `.gitignore` |

The *engineer set* is `Read, Grep, Glob, Edit, Write, Bash`, named explicitly so no agent inherits MCP tool schemas (the owner's 2026-10-22 rule from the origami toolkit). Advisory agents (game-designer, tabletop-sme) and project-manager never edit repo files. `memory: project` lets them write their own memory files, so that rule rests on their prompts and the hooks, not on their tool lists.

### Parked (`parked/agents/`)

Files here aren't loaded. To restore one: `git mv .claude/parked/agents/<name>.md .claude/agents/`, delete its parked note, and add its row above.

| Agent | Parked | Owns |
|---|---|---|
| hardware-engineer | 2026-11-15, until staging step 5 (decision (h)) | The first electronic tank: MCU, motors, line sensors, IR shooting and hit attribution, program entry (NFC console or printed codes), battery, the passive-board alternative, the BOM |

## Skills (`skills/`)

Invoke a user-invocable skill as `/<name>`. Background skills load when an agent that lists them runs. A skill is a map, never a second authority. The larger skills are split into a short `SKILL.md` map plus detail files read on demand.

| Skill | Carries | User-invocable |
|---|---|---|
| project-map | What exists; the staging position. `decisions.md`: (a)–(n) with where each is stated and enforced, owner decisions by date. `ledger.md`: status claims with commands, the file map with owners, open items | yes |
| rules-engine | Both engines side by side, the tick order as coded, card semantics (statements, skips, loops, the spent rule, Otherwise), the parity harness. `config.md`: every Config field with its JS key and v0.5 value. `add-a-rule.md`: the checklist | no |
| experiment-method | The loop (pass line first, paired seeds, smoke test, rule-fired check), proxies and their biases, metric definitions, noise and runtimes, file conventions. `past-experiments.md`: every experiment and its verdict | yes |
| review-checklist | Ten ordered review items with runnable checks; blocking versus non-blocking | yes |
| git-flow | Scopes, message shape, the trailer, never-committed list, pre-commit, gh notes; the repo is public | yes |
| playtest-protocol | Two session kinds, the script, observer sheet, tick sheet, quick reference, findings table, the step-3 gate | yes |
| tune-agents | Cost checklist after a session-limit hit; model tiers; propose, never make, a model move | yes |

## Memory (`agent-memory/`)

Tracked in git, one folder per agent with a `MEMORY.md` index. Seeded: `project-manager` (the owner's 2026-11-15 answers and the status at toolkit creation). Machine-local notes go in `.claude/agent-memory-local/` (gitignored). **The repo is public:** no personal data in memory.

## Hooks (`hooks/`) and settings

`settings.json` pre-allows the read-only commands (the gate, git and gh reads, WebSearch) and wires two hooks. Both run via `python -c` with a `runpy` shim, which works in Git Bash, PowerShell and Linux, and does nothing if the file is missing.

- `protect.py` (PreToolUse, blocks):
  - hand edits to `results/**` (rerun the experiment instead);
  - any edit that changes or removes an existing expected fingerprint in `tests/fingerprints.py` (f). Adding a new entry at a freeze is allowed.
- `guard.py` (PostToolUse, nudges):
  - an edit to `tanksim.py` or the viewer's ENGINE block → mirror it and run the gate (g);
  - a `Config` bool defaulting to True (f);
  - randomness inside `play()` or the ENGINE block (d);
  - an `experiments*.py` without a pass line in its docstring;
  - an edit to a doc with a claude.ai Project copy → tell the owner to sync;
  - an email address written anywhere (the repo is public).

Hooks fire only on edits made through Claude Code. Changes made elsewhere haven't been checked.
