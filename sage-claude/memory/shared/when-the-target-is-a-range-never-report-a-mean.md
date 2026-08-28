---
id: when-the-target-is-a-range-never-report-a-mean
kind: rule
class: portable
status: live
---

**When the target is a range, chase the internal range and report minimums — never optimise or report a mean.**

- Qualifier: when the finding is aesthetic or perceptual, do not re-check it with the metric that misled you; ask what range the target has.
- Recogniser: one run made the mean-for-range error four times, walking a value straight through its minimum separation while every mean looked right.
- Falsifier: three range-targeted deliverables where the mean and the minimum select the same design.
