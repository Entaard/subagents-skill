"""Reviewer-authored executable checks, preserved by the coordinator."""
import hashlib
import itertools
import json
import random
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
sys.path.insert(0, 'work')
from decoder import Decoder, FrameError

counts = {}
def counted(name):
    counts[name] = counts.get(name, 0) + 1

def raises(kind, fn, *args):
    try:
        fn(*args)
    except kind:
        return
    except Exception as exc:
        raise AssertionError((kind, type(exc), args)) from exc
    raise AssertionError(('expected', kind, args))

def poison_and_reset(decoder):
    raises(FrameError, decoder.feed, b'')
    raises(FrameError, decoder.feed, b'0:,')
    raises(FrameError, decoder.finish)
    raises(TypeError, decoder.feed, '0:,')
    raises(FrameError, decoder.finish)
    assert decoder.reset() is None
    assert decoder.feed(b'0:,') == [b'']
    assert decoder.finish() is None

def oracle(data, limit):
    frames, pos = [], 0
    while pos < len(data):
        digits = b''
        while pos < len(data) and 48 <= data[pos] <= 57:
            digits += data[pos:pos + 1]
            pos += 1
            if (len(digits) > 1 and digits.startswith(b'0')) or int(digits) > limit:
                return 'bad', frames
        if pos == len(data):
            return 'partial', frames
        if not digits or data[pos:pos + 1] != b':':
            return 'bad', frames
        pos += 1
        size = int(digits)
        if len(data) - pos <= size:
            return 'partial', frames
        if data[pos + size:pos + size + 1] != b',':
            return 'bad', frames
        frames.append(data[pos:pos + size])
        pos += size + 1
    return 'boundary', frames

def check_chunks(chunks, limit=1024):
    decoder, accumulated, emitted = Decoder(limit), b'', []
    for chunk in chunks:
        assert decoder.feed(b'') == []
        accumulated += chunk
        state, expected = oracle(accumulated, limit)
        if state == 'bad':
            raises(FrameError, decoder.feed, chunk)
            poison_and_reset(decoder)
            return
        got = decoder.feed(chunk)
        assert isinstance(got, list) and all(type(p) is bytes for p in got)
        emitted.extend(got)
        assert emitted == expected, (chunks, expected, emitted)
    state, expected = oracle(accumulated, limit)
    if state == 'partial':
        raises(FrameError, decoder.finish)
        poison_and_reset(decoder)
    else:
        assert state == 'boundary' and emitted == expected
        assert decoder.finish() is None
        assert decoder.finish() is None
        assert decoder.feed(b'0:,') == [b'']
        assert decoder.finish() is None

vectors = json.loads(Path('inputs/vectors.json').read_text())
for category in ['valid_wire_hex', 'invalid_wire_hex', 'unfinished_wire_hex']:
    for encoded in vectors[category]:
        wire = bytes.fromhex(encoded)
        for size in vectors['chunk_sizes']:
            check_chunks([wire[i:i + size] for i in range(0, len(wire), size)])
            counted('raw_vector_chunkings')
        if category == 'valid_wire_hex':
            for mask in range(1 << (len(wire) - 1)):
                boundaries = [0] + [i for i in range(1, len(wire)) if mask & (1 << (i - 1))] + [len(wire)]
                check_chunks([wire[a:b] for a, b in zip(boundaries, boundaries[1:])])
                counted('raw_valid_all_partitions')

alphabet = b'012:,x\xff'
for length in range(6):
    for values in itertools.product(alphabet, repeat=length):
        wire = bytes(values)
        for cut in range(length + 1):
            check_chunks([wire[:cut], wire[cut:]], 2)
            counted('exhaustive_short_split_cases')

payloads = [b'', bytes(range(256)), 'é🙂'.encode(), b'\x00,:\xff', b'', b'x' * 1024]
wire = b''.join(str(len(p)).encode() + b':' + p + b',' for p in payloads)
for cut in range(len(wire) + 1):
    check_chunks([wire[:cut], wire[cut:]])
    counted('binary_every_single_split')
check_chunks([wire[i:i + 1] for i in range(len(wire))])
rng = random.Random(728113)
for _ in range(200):
    chunks, pos = [], 0
    while pos < len(wire):
        step = rng.randrange(1, 50)
        chunks.append(wire[pos:pos + step])
        pos += step
    check_chunks(chunks)
    counted('binary_random_chunkings')

for byte in range(256):
    for wire in [bytes([byte]), b'1' + bytes([byte]), b'0:' + bytes([byte]), b'1:x' + bytes([byte])]:
        check_chunks([wire[:1], wire[1:]])
        counted('all_byte_header_and_terminator_cases')

wire = b'12:hello,world!,'
invalid = [None, '', bytearray(), memoryview(b''), 0, 1.0, True, [], {}, object()]
for cut in range(len(wire) + 1):
    for value in invalid:
        decoder = Decoder()
        before = decoder.feed(wire[:cut])
        raises(TypeError, decoder.feed, value)
        after = decoder.feed(wire[cut:])
        assert before + after == [b'hello,world!']
        assert decoder.finish() is None
        counted('typeerror_preserves_states')
    decoder = Decoder(12)
    decoder.feed(wire[:cut])
    assert decoder.reset() is None
    assert decoder.reset() is None
    assert decoder.feed(b'1:z,') == [b'z']
    raises(FrameError, decoder.feed, b'13')
    poison_and_reset(decoder)
    counted('reset_at_every_frame_prefix')

for value in [-1, -(10 ** 100), True, False, 0.0, 1.5, float('nan'), float('inf'), '0', b'0', None, [], {}, set(), 0j, Decimal(0), Fraction(0)]:
    raises(ValueError, Decoder, value)
    counted('invalid_constructors')
class IntegerSubclass(int):
    pass
for limit in [0, 1, 1024, 10 ** 100, IntegerSubclass(3)]:
    assert Decoder(limit).finish() is None
    counted('valid_constructors')
assert issubclass(FrameError, ValueError)
for limit in list(range(128)) + [255, 999, 1024, 10000, 10 ** 100]:
    decoder = Decoder(limit)
    header = str(limit + 1).encode()
    for end in range(1, len(header) + 1):
        if int(header[:end]) <= limit:
            assert decoder.feed(header[end - 1:end]) == []
        else:
            raises(FrameError, decoder.feed, header[end - 1:end])
            poison_and_reset(decoder)
            break
    else:
        raise AssertionError(('oversize was accepted', limit))
    counted('earliest_oversize_digit')

import decoder as module
module_file = module.__file__
def traced_oversize(wire):
    decoder, events = Decoder(9), []
    def trace(frame, event, arg):
        if frame.f_code.co_filename == module_file and event == 'line':
            events.append(frame.f_lineno)
        return trace
    sys.settrace(trace)
    try:
        raises(FrameError, decoder.feed, wire)
    finally:
        sys.settrace(None)
    return events
short_trace = traced_oversize(b'99')
long_trace = traced_oversize(b'9' * 1000000)
assert short_trace == long_trace
print('oversize execution: identical %d decoder line events for 2-byte and 1000000-byte headers' % len(short_trace))
for name in sorted(counts):
    print('%s: %d PASS' % (name, counts[name]))
for name in ['prompt.txt', 'checks.json', 'inputs/vectors.json', 'work/decoder.py', 'work/test_decoder.py', 'work/README.md']:
    print('SHA256 %s %s' % (name, hashlib.sha256(Path(name).read_bytes()).hexdigest()))
print('INDEPENDENT REVIEW CHECKS: PASS')
