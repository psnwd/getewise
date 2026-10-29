# Adding a gateway

1. `cp -r templates/gateway-skill skills/<slug>` (slug = lowercase gateway name).
2. Gather docs (use a browser if the site blocks fetching). One reference file per topic: checkout, recurring, server API, SDKs, sandbox/test data, account/fees, troubleshooting.
3. Write `SKILL.md`:
   - `name` = slug; a "pushy" `description` listing gateway name, domains, param names, error codes.
   - Routing table to references; 5-10 core rules (signing, webhook verification, URLs, plan gates).
4. Put runnable helpers in `scripts/` and test them against a known vector.
5. Code examples: keep one `code-*.md` per concern; mark anything not run against the real API.
6. Evals: 3 cases in `evals/<slug>/<case>/` (`prompt.md`, `case.yaml`, `graders/NN-*.md`). Include one non-code support question and one gotcha the model usually misses.
7. Run each case with and without the skill, grade, save the summary to `docs/benchmarks/<slug>-iteration-N.md`.
8. Add a row to the README table and tick your local ROADMAP (it is gitignored).

Keep gateway-specific facts inside its own skill; cross-gateway guidance belongs in a shared skill later.
9. Add the skill to `.claude-plugin/marketplace.json` (in the bundle's `skills` list and as its own entry), run `python scripts/package.py`, then `python scripts/verify.py`. CI runs the same check on every PR.
