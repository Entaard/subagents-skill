## Independent read-only recheck

Hashes verified:

- Preserved original: `8b5abbf89ee581a6621f65c269adb4f9971075a059b12cd3bc58b250740a8f21`
- Frozen repaired candidate: `3daf1331277df84d6f9abe9e18576a872fc6e564aa6d4e621d815b649cc667c0`

### Original finding 1: performance platform metadata absent

**Disposition: Resolved, with a preserved provenance limitation.**

The original falsifiable fix check is satisfied:

- `evidence/platform-metadata.json:4-6` records macOS 27.0/build 26A5425a, Darwin 27.0.0, arm64, Google Chrome installed version 152.0.7977.82, and Node.js v26.7.0.
- `evidence/platform-metadata.json:7` precisely describes the owned-headless/fresh-profile/network-blocked method, device scale factor, lack of throttling, post-process-start local-file load timing, and CDP key-to-two-frame timing.
- `evidence/platform-metadata.json:8` explicitly records one navigation and 11 keyboard samples at each of 1280×800 and 390×844.
- The primary uninstrumented run retains the scoped disclaimer at `evidence/browser-repair-main/observations.json:2-3` and contains exactly 11 input measurements per viewport.
- Repaired-run measurements are:
  - 1280×800: wall load 53.664 ms, Navigation Timing duration 5.3 ms, 11 key-to-two-frame samples spanning 21.855–38.442 ms.
  - 390×844: wall load 7.298 ms, Navigation Timing duration 4.5 ms, 11 samples spanning 24.849–33.136 ms.

The evidence does not overgeneralize these measurements.

Remaining limitation: `platform-metadata.json:2,5,10` explicitly states that Chrome 152.0.7977.82 is the installed application version observed immediately before the repair runs, not a contemporaneous browser-process protocol version; `runtimeProtocolVersion` is null. This is appropriately preserved and does not negate the platform/method/sample-count repair.

### Original finding 2: terminal pads remain enabled and silently inert

**Disposition: Resolved.**

The diff is narrowly limited to terminal-state handling:

- `work/index.html:145-150` adds `finishRound(result)`, which records whether a pad held focus, disables all four native pad buttons, and moves focus to Restart when necessary.
- Mistake and success now call that helper at `work/index.html:182-195`.
- No sequence, timing, status-copy, styling, or input-handler behavior was otherwise changed.

The falsifiable fix check is directly supported:

- After success, all pads are reported disabled at both viewports: `browser-repair-disabled/observations.json:37-40` and `148-151`.
- After a mistake, all pads are likewise disabled: `browser-repair-disabled/observations.json:61-64` and `172-175`.
- Subsequent Tab actions never focus a pad in either terminal state: `browser-repair-disabled/observations.json:43-52,67-76` and `154-163,178-187`.
- When a focused Pad 1 produces a mistake, focus transfers to Restart at both viewports: `browser-repair-focus/observations.json:25-34` and `100-109`.
- When focused Pad 1 completes the correct sequence, focus again transfers to Restart: `browser-repair-focus/observations.json:55-64` and `130-139`.
- During the input phase, pads remain enabled and keyboard-operable, demonstrated by Pad 1 receiving focus and Enter activating it in the same records.

### Diagnostic evidence integrity

`make-disabled-probe.mjs:4-20` reads the frozen repaired candidate, calculates its SHA-256, and appends only a non-focusable `<output>` plus mutation observers that read pad-disabled attributes and phase text. The embedded probe source hash is `3daf1331277df84d6f9abe9e18576a872fc6e564aa6d4e621d815b649cc667c0`, matching the independently recomputed repaired-candidate hash.

The diagnostic instrumentation does affect layout: its unbroken JSON output causes `scrollWidth: 773` at the 390-pixel viewport (`browser-repair-disabled/observations.json:214-222`; `browser-repair-focus/observations.json:142-150`). This is a probe-created artifact, not candidate overflow. The appended output is not focusable and does not alter controls or handlers, so the disabled-state and focus observations remain useful. Probe screenshots or overflow metrics must not be treated as visual evidence for the real candidate.

### Regression check

No material regression was found in the repaired candidate:

- The uninstrumented `browser-repair-main` run still records the complete required flow at both viewports: Start, successful `2-4-1`, restart, wrong `3`, restart, and successful `2-4-1`.
- Its metrics report `scrollWidth === innerWidth` at both 1280 and 390 (`observations.json:80-88,167-175`).
- I actually viewed both repaired real-candidate screenshots. The 1280×800 composition remains balanced and fully readable. The 390×844 layout remains clean, complete, and free of visible horizontal clipping. Restart has a strong visible focus ring in both, terminal success text and progress remain intact, and disabling the pads does not dim or erase the final non-color feedback.

### Recheck limitations and identity

- Disabled-state evidence is source/hash-bound probe evidence; the uninstrumented main harness does not itself record DOM `disabled` properties.
- This bounded recheck did not newly exercise screen readers, reduced-motion emulation, or pointer/touch input.
- Requested routing: `gpt-5.6-sol/xhigh`.
- Effective identity: `null`.
- Tokens: `null`.
- Money: `null`.

RELEASE: read-only recheck complete; no writes or external effects
