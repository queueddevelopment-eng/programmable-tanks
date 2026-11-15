# Status ledger, file map, open items

## Ledger (re-run the command; never quote a row as current without it)

| Claim | Verified | Command |
|---|---|---|
| Both engines agree on v0.5 rules | 2026-11-15: 800 + 622 (templates) + 600 (pits) duels, 0 mismatches | `python tests/parity.py 800 v5`; `PARITY_TEMPLATES=1 python tests/parity.py 800 v5`; `python tests/parity.py 600 v5 3 9` |
| Older rule sets unchanged | 2026-11-15: legacy and v0.4 `ok` | `python tests/fingerprints.py` |
| `main` pushed | 2026-11-15: `d911783` (code, docs, results) + the toolkit commit | `git log --oneline -3`; `git status -sb` |
| Stuck rounds 0% with the pathfinding clock | 2026-10-25, `results/results7c.txt` (K) | `python experiments7.py 60 K` (~15 min) |
| Card-language overtime stalls on some layouts | 2026-11-15, an engine check (passive programs on Pillars-and-pits draw at 5–5) | E2 will measure it |
| Viewer runs the v0.5 rules without errors | 2026-11-15, Playwright: kit round, dealt round with pit stops, both computer players | open the file; run a dealt round |

## File map

| Path | Owner agent | Notes |
|---|---|---|
| `tanksim.py` | rules-engineer | Python engine |
| `tank-match-viewer.html` ENGINE block (`// ==== ENGINE START` … `END ====`) | rules-engineer | JS engine, including `CARDS` and `RULESETS` |
| `tank-match-viewer.html` outside the block | viewer-developer | UI, deal mode, pit stops, computer opponent, board editor |
| `tanksim_multi.py` | — | free-for-all, v0.1, out of scope (k) |
| `experiments*.py` | sim-analyst | one question per file |
| `results/**` | sim-analyst (written by runs only) | the protect hook blocks hand edits |
| `tests/**` | rules-engineer | parity and fingerprints; `EXPECTED` changes only at an owner freeze |
| `docs/RULES-*`, `docs/PLAN-*`, `docs/TANKS-*`, `README.md`, `CLAUDE.md` (Current phase, Repo layout) | docs-writer | the owner syncs the rules draft, plan and notes to the claude.ai Project |
| `docs/playtest/**` | playtest-designer | to come in Phase 2 |
| `.claude/**` | the owner's decision; code-reviewer reviews; github-ops commits | toolkit |
| `.gitignore` | github-ops | |

## Open items

1. **E2:** card-language overtime stalls on some layouts. Blocks (m) being final.
2. **E1:** the debug rule under dealt hands. Blocks (e).
3. **E3, E4, E5**, then the v0.5 freeze: a fingerprint entry `v05()` and docs synced.
4. **Paper executability:** never timed. Phase 2's hand-execution sessions.
5. **Repo visibility:** the repo is public (the owner's call). Keep personal data out.
6. **CI:** none yet. The gate is run by hand. A GitHub Actions job running parity and fingerprints would make it automatic; that's a build task for the owner to approve.
7. The claude.ai Project copy of `TANKS-HANDOFF.md` is superseded on rules by the v0.5 draft. The owner updates it.
