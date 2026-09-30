---
id: an-alt-agent-can-be-listed-and-not-dispatchable
kind: rule
class: portable
status: live
---

**An alt agent in the live agent list is not proof the lane works: the model behind it can be gone, and a lane that is off looks exactly like a lane that is broken.** Probe before you plan around it — one one-line dispatch asking only for the `MODEL-FAMILY:` line — and let a `model_not_found` fall that seat to its in-family agent at once, never after a second full brief.

- Qualifier: the corpus rule that alt availability is a live-session fact still holds; this adds the state it does not name — listed, and not dispatchable. One 404 says a name did not resolve, never why or how widely, so it settles nothing about the other roles. A clean vendor check narrows the cause to "not the vendor" and no further: a lane can be switched off, and that leaves no filesystem trace for a grep of the alt files or the conf to find.
- Recogniser: an alt dispatch returning HTTP 404 `model_not_found` while the agent type is in the live list; a plan that wrote "vendor lineup change" as the cause of such a 404.
- Falsifier: three sessions on one machine in which every listed alt agent dispatches without a model error after a listing an earlier session on that machine found dead — the listing then did track dispatchability.
