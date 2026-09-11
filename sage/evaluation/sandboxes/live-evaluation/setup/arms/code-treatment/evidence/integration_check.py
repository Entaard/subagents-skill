"""Independent whole-stream grammar and README integration checks."""
import itertools
from pathlib import Path
from decoder import Decoder, FrameError


def reference(wire):
    frames = []
    while wire:
        colon = wire.find(b":")
        if colon < 1:
            raise ValueError
        header = wire[:colon]
        if any(c < 48 or c > 57 for c in header) or len(header) > 1 and header[0] == 48:
            raise ValueError
        length = int(header)
        if length > 2 or len(wire) < colon + length + 2 or wire[colon + length + 1] != 44:
            raise ValueError
        frames.append(wire[colon + 1:colon + length + 1])
        wire = wire[colon + length + 2:]
    return frames


cases = 0
for size in range(6):
    for raw in itertools.product(b"012:a,?", repeat=size):
        wire = bytes(raw)
        try:
            expected = reference(wire)
        except ValueError:
            expected = None
        for split in range(len(wire) + 1):
            decoder = Decoder(2)
            try:
                actual = decoder.feed(wire[:split]) + decoder.feed(wire[split:])
                decoder.finish()
            except FrameError:
                actual = None
            assert actual == expected, (wire, split, actual, expected)
            cases += 1
print(f"PASS: {cases} exhaustive wire/split cases match independent whole-stream grammar, max_payload=2")

readme = Path("README.md").read_text()
example = readme.split("```python\n", 1)[1].split("```", 1)[0]
exec(compile(example, "README.md usage example", "exec"))
print("PASS: README usage example executes successfully")
