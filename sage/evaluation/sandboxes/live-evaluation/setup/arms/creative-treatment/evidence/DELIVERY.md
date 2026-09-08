# Echo Steps — frozen candidate; independent review pending

Deliverable: work/index.html (single self-contained local file).

SHA-256: 8b5abbf89ee581a6621f65c269adb4f9971075a059b12cd3bc58b250740a8f21.

The supplied direct keyboard flow passed at 1280x800 and 390x844: first Tab focused Start, Enter demonstrated the sequence, 2–4–1 succeeded, R restarted, 3 produced a visible mistake, R restarted, and 2–4–1 succeeded again. Focused runs observed ignored guesses during demonstration, native Enter activation of pads 2 and 4, individual demonstrations of 2 then 4 then 1, and the announced input phase. The source schedules the transition at 1650 ms. The frozen recorder does not timestamp that transition directly; temporal samples corroborate it without constituting an exact end-to-end duration measurement.

Both supplied-flow screenshots were actually inspected with view_image. Instructions, phase/progress text, numbered 2x2 pads, success messaging and Start/Restart focus are visible. The mobile layout fits the screen. Desktop game content fits; its decorative footer begins at the lower edge and continues below. scrollWidth equals innerWidth (1280 and 390), so no horizontal overflow was observed.

Local timing observations, Darwin 27.0.0 arm64, owned headless Google Chrome, Node v26.7.0, deviceScaleFactor 1, mobile emulation false:

| Viewport | Supplied-flow file load | Keyboard to two frames | Samples |
| --- | ---: | ---: | --- |
| 1280×800 | 55.286 ms | 29.055–41.048 ms | 1 navigation, 11 keys |
| 390×844 | 8.023 ms | 28.379–33.651 ms | 1 navigation, 11 keys |

Load means one local file navigation after the browser process already exists, awaiting readyState complete. Keyboard timing includes CDP keyDown/keyUp and two animation frames. No CPU/network throttle. The two viewports share one process per run; each run has a fresh owned profile. Other focused-run samples, exact original values and artifact hashes are retained in check-results.json. These observations do not establish general performance, population experience or monetary cost.

Primary evidence: browser-attempt-2/observations.json and both PNGs; browser-focused-1 and browser-demonstration-1 contain additional original observations. verify.mjs exited 0 and generated check-results.json. Restricted browser attempt 1 failed to expose an endpoint; its failure remains retained. Approved isolated escalation completed all three live runs.

Independent review is incomplete: native dispatch failed before creating a reviewer, reporting agent thread limit reached. No reviewer findings or successful review are claimed. intended-review-brief.txt retains the exact requested brief. The outer coordinator directed this actor to checkpoint and release so a fresh reviewer can be attempted outside this terminal actor. Candidate unchanged since the one build wave; no repairs performed.

Untested: screen-reader speech, physical touch/mouse, reduced-motion runtime emulation (CSS rule inspected), browsers/platforms/viewports beyond those specified. Effective model/effort, tokens and money are null. Requested coordinator routing was gpt-6-astra/high; requested but uncreated reviewer routing was gpt-5.6-sol/xhigh.

Sage state is a validated incomplete checkpoint, with its derived report under state/runs/echo-steps/report.md. Review was admitted before the native dispatch failed; the installed contract cannot close that delegated task without a real request handle and lifecycle. No handle or lifecycle has been fabricated. Remaining work: independent review, evidence-based finding dispositions and any focused repair, then final completion reconciliation.
