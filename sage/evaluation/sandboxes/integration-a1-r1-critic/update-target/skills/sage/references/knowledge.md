# Promoted knowledge retrieval

Read before the first knowledge query, when a material cue changes, or when recording retrieval feedback. Main Sage reads only an active immutable generation through the helper. It never searches closed-run logs, writes a generation, promotes an observation, or edits itself.

Resolve all paths explicitly. Use `sage/scripts/sage_knowledge.py` in this checkout or the installed sibling `<target-root>/sage/bin/sage_knowledge.py`. Set `STORE` to `<explicit-state-root>/knowledge`; use the configured state root or the absolute expansion of the standard `~/.codex/sage`, never the task repository.

After qualification and before final planning, write a cue JSON object whose arrays capture only observed `task`, `domain`, `artifact`, `environment`, `risk`, `operation`, and `failure` values. Normal retrieval omits `include_non_supported` or sets it false. Set it true only when provisional/contested guidance is worth examining with status and counterevidence attached.

```text
python3 SAGE_KNOWLEDGE retrieve --store-dir STORE --cues cues.json --limit 3
```

The result contains `generation_id`, `cue_fingerprint`, `retrieval_status`, and bounded `matches`. A fresh empty store returns `generation_id: "none"`, `no_match`, and `[]`; `none` is reserved and is recorded unchanged in state. Each match contains exact ID/revision/status/reason and the rule, qualifier, falsifier, support rationale, evidence summary, and counterevidence.

Apply a match only inside its qualifier after comparing it with the current user instruction and current task evidence. Those current inputs outrank promoted knowledge. Treat `provisional` and `contested` as warnings with limits, not supported defaults. Never apply `refuted` or `retired` records; the helper excludes them.

Append one `knowledge.selected` event using exactly the returned generation, fingerprint, retrieval status, and match ID/revision/status/reason, plus the normalized input cues (including `include_non_supported` when true). This includes no-match. Before a retry or material decision, re-query only if the active generation, an observed cue, or retrieval policy changed. An unchanged generation/fingerprint is recorded as `unchanged` without reloading exact revisions; otherwise deduplicate revisions and re-check all prior statuses and qualifiers.

After use, append `knowledge.feedback` for every loaded revision: `useful`, `neutral`, `misleading`, or `not_exercised`, with evidence IDs and any missed recognizers. Feedback is an observation for a later explicit `$sage-promote` run. Selection/use frequency may suggest bounded cue, qualifier, index, or rule refinement; it is never evidence that the rule is true.
