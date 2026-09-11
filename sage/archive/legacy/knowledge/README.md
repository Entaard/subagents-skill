# Promoted knowledge source

Global promotion writes validated `KnowledgeRecordProjection/v1` records under `active/`. The generated `index.json` is the source index installed by `sage/install.sh`. Runtime tasks read only the installed validated index; they never search this directory as a substitute for installation and never read closed-run logs from here.

The index exposes recognizer and qualifier metadata for selection but omits rule and falsifier text. The runtime fetches full records only for explicitly selected stable IDs, and the index input-manifest hash binds those entries to their validated projections and locators.
