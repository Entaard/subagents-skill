# Archived pre-rebuild Sage

This directory is an inert, recoverable copy of the legacy Sage implementation selected from Git commit `c816a6250d0df74e6cbfa9b2a672a2fc15110deb`. It is evidence and historical source, not an active fallback, import root, installer input, or skill reference.

The archive was extracted with `git archive` from explicit baseline paths. `SHA256SUMS` lists all 186 extracted files and their content hashes. It intentionally covers the legacy policy, runtime, schemas/fixtures, libraries, knowledge seed, phase documentation/evaluation, scripts/tests, and the legacy references that previously sat under the active skill trees. The original deleted promotion references—`promotion-contract.md`, `source-manifest.json`, and `workflow.md`—are present here exactly as stored in the baseline commit.

The mixed active directories were not copied wholesale. Rebuilt entrypoints, helpers, tests, verification files, reviews, and evidence remain outside this archive. In particular, the active lifecycle helper is the narrow installer implementation; the archived `scripts/sage-lifecycle.py` and `scripts/generate-skill-bundle.py` cannot be reached by the active wrappers.

Verify the retained bytes from this directory with:

```sh
shasum -a 256 -c SHA256SUMS
```
