# Gallery byte-stream decoder

Dependency-free Python 3.9+ decoder for `length:payload,` frames. Length is the
ASCII decimal **byte count**; payload bytes may contain any value. Zero is valid;
leading zeroes, signs, whitespace and other length characters are invalid.

```python
from decoder import Decoder, FrameError

decoder = Decoder(max_payload=1024)
assert decoder.feed(b"3:a,") == []
assert decoder.feed(b"b,0:,2:\xc3") == [b"a,b", b""]
assert decoder.feed(b"\xa9,") == ["é".encode("utf-8")]
decoder.finish()  # Call at end of input to reject a truncated frame.
```

`feed(bytes)` returns complete payloads in order. Chunks may split anywhere;
empty chunks are harmless on a healthy decoder. `finish()` accepts a clean
boundary and permits further input. `reset()` discards buffered bytes and errors
while retaining the configured limit.

Malformed, oversized or truncated framing raises `FrameError` (a `ValueError`)
and poisons the decoder. Subsequent byte feeds, including empty ones, and
`finish()` raise `FrameError` until `reset()`. If a chunk contains complete frames
followed by an error, that call raises and returns no frames. Previously returned
frames remain valid.

Non-`bytes` chunks always raise `TypeError` without changing state (including
existing poisoning). The constructor requires a nonnegative integer limit;
booleans and non-integers raise `ValueError`. Oversize lengths are rejected as
soon as a digit proves they exceed the limit, even before a colon arrives.
The decoder stores no header string and buffers at most one permitted payload;
the returned list naturally occupies space for all completed frames in a call.

Run the standard-library tests from this directory:

```sh
python3 -m unittest -v
```
