"""Reviewer-supplied independent check, retained by coordinator after release."""
from itertools import product
from decoder import Decoder, FrameError

A, LIMIT = b"01:,a\x00", 2


def ref(w):
    state, n, digit, payload, frames = "length", 0, False, bytearray(), []
    for value in w:
        if state == "payload":
            payload.append(value)
            if len(payload) == n:
                state = "comma"
        elif state == "comma":
            if value != 44:
                return "feed-error", None
            frames.append(bytes(payload))
            state, n, digit, payload = "length", 0, False, bytearray()
        elif 48 <= value <= 57:
            if digit and n == 0:
                return "feed-error", None
            n = n * 10 + value - 48
            if n > LIMIT:
                return "feed-error", None
            digit = True
        elif value == 58 and digit:
            state = "comma" if n == 0 else "payload"
        else:
            return "feed-error", None
    return (("ok", frames) if state == "length" and not digit
            else ("finish-error", None))


def candidate(w, bytewise):
    d, frames = Decoder(LIMIT), []
    chunks = [bytes([b]) for b in w] if bytewise else [w]
    try:
        for chunk in chunks:
            frames.extend(d.feed(chunk))
    except FrameError:
        return "feed-error", None
    try:
        d.finish()
    except FrameError:
        return "finish-error", None
    return "ok", frames


checked = 0
for size in range(7):
    for values in product(A, repeat=size):
        wire = bytes(values)
        assert candidate(wire, False) == ref(wire)
        assert candidate(wire, True) == ref(wire)
        checked += 1

d = Decoder(3)
d.feed(b"1")
try:
    d.feed(memoryview(b":x,"))
except TypeError:
    pass
assert d.feed(b":x,") == [b"x"]

for bad in (b"3:abc;", b"01:x,", b"4"):
    d = Decoder(3)
    try:
        d.feed(bad)
        d.finish()
    except FrameError:
        pass
    for call in (lambda: d.feed(b""), d.finish):
        try:
            call()
            raise AssertionError("not poisoned")
        except FrameError:
            pass
    d.reset()
    assert d.feed(b"0:,") == [b""]

d = Decoder(1024)
try:
    d.feed(b"999999999999999999999999999999")
except FrameError:
    pass
assert d._length == 999 and not d._payload and d._poisoned

print(f"exhaustive_streams={checked}; modes=whole,bytewise; mismatches=0")
print("type_state=preserved; poison_reset=ok; oversize_rejected_at_digit=4; stored_length=999")
