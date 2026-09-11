"""Final integration: original vectors, frozen hashes, delivered tests."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ARM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ARM / "work"))
from decoder import Decoder, FrameError


def main():
    output = []
    for line in (ARM / "evidence" / "frozen-sha256.txt").read_text().splitlines():
        digest, rel = line.split("  ", 1)
        actual = hashlib.sha256((ARM / rel).read_bytes()).hexdigest()
        assert actual == digest, (rel, actual, digest)
        output.append(f"SHA-256 unchanged: {actual}  {rel}")
    vectors = json.loads((ARM / "inputs" / "vectors.json").read_text())
    expected = [[b""], [b"a,b", b":\x00"], [b"\xc3\xa9"]]
    cases = 0
    for wire_hex, payloads in zip(vectors["valid_wire_hex"], expected):
        wire = bytes.fromhex(wire_hex)
        for size in vectors["chunk_sizes"]:
            decoder = Decoder()
            actual = []
            for offset in range(0, len(wire), size):
                actual.extend(decoder.feed(wire[offset:offset + size]))
            decoder.finish()
            assert actual == payloads
            cases += 1
    for category in ["invalid_wire_hex", "unfinished_wire_hex"]:
        for wire_hex in vectors[category]:
            decoder = Decoder()
            try:
                decoder.feed(bytes.fromhex(wire_hex))
                decoder.finish()
            except FrameError:
                pass
            else:
                raise AssertionError((category, wire_hex))
            try:
                decoder.feed(b"0:,")
            except FrameError:
                pass
            else:
                raise AssertionError("missing poisoning")
            decoder.reset()
            assert decoder.feed(b"0:,") == [b""]
            cases += 1
    output.append(f"Original vector integration: {cases} cases passed")
    result = subprocess.run([sys.executable, "-m", "unittest", "-v"], cwd=ARM / "work", capture_output=True, text=True)
    output.extend([f"Delivered stdlib suite exit code: {result.returncode}", result.stdout, result.stderr])
    rendered = "\n".join(output)
    (ARM / "evidence" / "final-check.txt").write_text(rendered)
    print(rendered)
    result.check_returncode()


if __name__ == "__main__":
    main()
