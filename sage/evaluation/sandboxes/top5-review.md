# Independent candidate review

Reviewer: native handle `/root/review`, fresh context, requested Sol/xhigh; effective identity unobserved. The reviewer received the frozen candidate, original proposal and user request, acceptance criteria and relevant standards. It did not receive the builder's disposition rationale and had read-only authority.

Initial state-helper freeze: `b32a89e8d65effeeb55dd37b46ee9c9313777694b4605160a522a4cc0aedf799`.

Initial compliance and quality verdicts: **fail pending three major fixes**.

| Finding | Evidence and falsifiable repair check |
| --- | --- |
| Application chronology | Selection and decision/admission targets were unordered sets, allowing a target predating the knowledge load. Require exact selection before target before application; test backward rejection and forward acceptance. |
| Superseded failures in working context | Every failed/not-tested bound attempt remained visible after a current pass. Root reproduced 49 obsolete failures after attempt 50 passed. Keep only the current active bound attempt in the working view and preserve full history behind an inventory locator. |
| Unbound continuation | A nonzero context offset did not require a digest. A newly opened finding could shift ordering between pages and be skipped. Require a current first-page digest for continuation; test missing/stale rejection and successful restarted enumeration. |

The root accepted all three findings and implemented focused repairs and regressions. It additionally exposed stale check obligations in generated reports and documented checkpoint locators for knowledge revalidation. The repaired candidate was frozen for a focused independent recheck.

Repaired state-helper freeze: `9f61d3082fdb03dcd5282b5d9640bab754325a2dbf48cb527de856748ea99898`.

The initial reviewer verified helper hashes, `git diff --check` and all 66 then-current focused tests. Its evaluation-suite run in `/private/tmp` passed 63 of 64; the remaining test requires its installation sandbox to lie beneath the repository evaluation tree. The root's correctly configured full gate passed all 133 final tests with no skips. This environment mismatch was not represented as a product regression or a reviewer full-suite pass.

The reviewer found no other material issues and accepted the scope treatment of conditional routing/matching/caching/promotion changes and the absence of generalized token-saving claims. The accounting utility remains an experimental reporter, not a native telemetry collector.

Focused recheck result: **compliance pass; quality pass; all three findings fixed; no new major defect**. The reviewer matched both supplied repaired freeze hashes, passed `git diff --check`, and independently ran all 13 improvement tests. It verified strict application chronology, current bound-attempt selection with complete history retained, and mandatory current pagination digests. It also approved the report's required-obligation state and the revalidation checkpoint guidance. Root final integration evidence is in `top5-final/report.json` and `top5-installed.json`.
