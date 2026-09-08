# Gallery kiosk frame decoder

Dependency-free Python 3.9+ module. Each wire frame is an ASCII decimal byte
length, a colon, that many arbitrary bytes, and a comma. Zero-length payloads
are valid. Lengths cannot have leading zeroes, signs, whitespace, or nondigits.

```python
from decoder import Decoder, FrameError

decoder = Decoder(max_payload=1024)
assert decoder.feed(b"3:a,") == []
assert decoder.feed(b"b,0:,2:\xc3") == [b"a,b", b""]
assert decoder.feed(b"\xa9,") == ["é".encode("utf-8")]
decoder.finish()  # Validate the stream ends at a complete frame boundary.
assert decoder.feed(b"1:x,") == [b"x"]  # finish() does not close the decoder.
```

Call `feed(bytes)` for each received chunk, including empty chunks, and
`finish()` at end of input. Chunk boundaries can fall anywhere. Payload bytes
are returned unchanged, with no text decoding. Only complete frames with a
valid trailing comma are returned.

`max_payload` defaults to 1024 bytes and must be a nonnegative integer;
booleans and other types raise `ValueError`. Oversize lengths fail at the first
digit that exceeds the limit. The parser stores an integer length, never a
growing header string, and buffers at most one payload up to the limit.
Returned frames and the caller's input chunk consume additional memory.

Malformed framing or an incomplete frame at `finish()` raises
`FrameError(ValueError)` and poisons the decoder. Subsequent byte feeds and
`finish()` raise `FrameError` until `reset()` discards all pending state.
Reset retains the configured limit. A non-bytes argument to `feed()` raises
`TypeError` without changing existing state.

If a chunk contains valid frames followed by malformed framing, the call
raises and does not return the earlier frames from that same call. Previously
returned frames are unaffected.

Run the standard-library tests from this directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v
```

The raw-vector test reads the preserved `../inputs/vectors.json` fixture.
Tests also cover every single split of a binary stream, all partitions of a
short stream, deterministic random chunking, invalid and truncated frames,
limits, poisoned state, recovery, and argument-error state preservation.
