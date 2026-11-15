# Programmable Tanks

A tabletop programming game: players build short programs from cards, then tanks run them autonomously on an 8×8 grid and fight. This repo holds the rules simulator, the experiments that tune the rules, and the browser match viewer.

- **Rules (current draft):** `docs/RULES-v0.5-draft.md`
- **Plan and decisions:** `docs/PLAN-2026-11.md`
- **Experiment record (October):** `docs/TANKS-V03-V04-NOTES.md`

## Files

- `tanksim.py`: duel rules engine. Every rule is a `Config` field.
- `tanksim_multi.py`: free-for-all engine (v0.1 cards only; free-for-all is out of the first edition).
- `experiments.py` … `experiments7.py`: experiments, each documented in its docstring. Raw outputs are in `results/`.
- `tank-match-viewer.html`: self-contained browser viewer and second rules engine (JavaScript). Published copy: https://claude.ai/artifact/XH46tiRNNpi3RK5DYYqvDW
- `tests/parity.py`: runs the same random duels through both engines and fails on any mismatch. Needs Node.

## The one rule for changes

Any rule change goes into both `tanksim.py` and the viewer's engine (between `ENGINE START` and `ENGINE END`), as a `Config` field that is off by default, and then this must pass:

```
python tests/parity.py 800 v5
PARITY_TEMPLATES=1 python tests/parity.py 800 v5
python tests/parity.py 600 v4
python tests/parity.py 600 v3
```

On Windows use `python` or `py`; set the environment variable with `set PARITY_TEMPLATES=1` (cmd) or `$env:PARITY_TEMPLATES=1` (PowerShell).
