from pathlib import Path
import re

documents = [
    Path("sage/README.md"),
    Path("sage/ARCHITECTURE.md"),
    *Path("sage/docs").glob("*.md"),
    *Path("sage/skills").rglob("*.md"),
]
checked = 0
broken = []
for document in documents:
    for raw in re.findall(r"\[[^]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
        link = raw.split("#", 1)[0]
        if not link or "://" in link:
            continue
        checked += 1
        if not (document.parent / link).exists():
            broken.append(f"{document}:{link}")
assert not broken, broken
print(f"links_ok={checked}")
