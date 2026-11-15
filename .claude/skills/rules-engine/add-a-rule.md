# Checklist: adding or changing a rule

A rule is done when every box is ticked in one change. code-reviewer works through this list.

1. **Accepted proposal.** game-designer's proposal, with the owner's acceptance and its date. It names the Config field, its off value, and the rules-draft wording. No proposal → stop.
2. **Locked-decision check.**
   - (b) no second card-language exception;
   - (d) nothing random once a round runs;
   - (e) the debug rule is untouched or explicitly re-decided;
   - (a) layouts stay rotationally symmetric.
3. **Python:** a new `Config` field with its default **off**, and a comment saying what turns it on and which version introduced it. The new branch is guarded by the field. With the field off, the old code path runs unchanged.
4. **JS, same change:** the camelCase key read as `R.<key>` inside the ENGINE block only, in the same evaluation order as Python (see the tick order in `SKILL.md`). Turn it on in the ruleset that adopts it (`RULESETS.v4` for v0.5 today), not in older rulesets.
5. **Parity coverage:**
   - set the field in the right `tests/parity.py` mode (or add a mode and document it in the module docstring);
   - make sure the harness passes it to the JS rules object (`m.rules = {...}`);
   - add a coverage count to `COVER` so the run prints how many matchups triggered it;
   - if random programs rarely trigger it, add template programs (`TEMPLATES`).
6. **Run the gate** (CLAUDE.md Commands): every parity line `0 mismatches`, with the new rule's coverage count above zero. Then `python tests/fingerprints.py`, all `ok`.
7. **Direct edge cases**, a few lines each, output quoted:
   - the rule at the rail's wrap point;
   - the rule on the tick a tank is destroyed;
   - both tanks triggering it on the same tick;
   - a pit-stop reload mid-effect;
   - a stunned tank.
8. **Viewer surface** (viewer-developer): a new card needs an entry in `CARDS` (label, kind, tooltip) inside the ENGINE block (rules-engineer adds it, since `CARDS` is engine data). The UI needs log lines in `describe`, any badge, and the rules summary text.
9. **Docs** (docs-writer): the `docs/RULES-v0.5-draft.md` card text or tick-order line, the deck table if counts changed, and `config.md` in this skill.
10. **Fingerprints:** never edit `EXPECTED`. A new entry is added only when the owner declares a rule-set freeze (the v0.5 freeze adds `v05()`), and the old entries stay.
