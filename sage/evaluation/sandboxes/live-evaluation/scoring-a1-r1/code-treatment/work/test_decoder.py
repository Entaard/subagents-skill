import itertools
import json
from pathlib import Path
import random
import unittest

from decoder import Decoder, FrameError


def encode(payload):
    return str(len(payload)).encode("ascii") + b":" + payload + b","


class DecoderTests(unittest.TestCase):
    def assert_poisoned(self, decoder):
        for operation in (lambda: decoder.feed(b""), lambda: decoder.feed(b"0:,"), decoder.finish):
            with self.assertRaises(FrameError):
                operation()

    def test_every_single_split_and_bytewise_binary(self):
        payloads = [b"", b"a,b", b":\0", "é".encode(), bytes(range(256)), b"last"]
        wire = b"".join(map(encode, payloads))
        for split in range(len(wire) + 1):
            with self.subTest(split=split):
                decoder = Decoder()
                self.assertEqual(decoder.feed(wire[:split]) + decoder.feed(wire[split:]), payloads)
                self.assertIsNone(decoder.finish())
        decoder = Decoder()
        self.assertEqual([p for value in wire for p in decoder.feed(bytes([value]))], payloads)
        decoder.finish()

    def test_all_partitions_of_short_stream(self):
        wire = b"0:,2::,,"
        for cuts in itertools.product((False, True), repeat=len(wire) - 1):
            decoder = Decoder()
            frames = []
            start = 0
            for end, cut in enumerate(cuts, 1):
                if cut:
                    frames.extend(decoder.feed(wire[start:end]))
                    self.assertEqual(decoder.feed(b""), [])
                    start = end
            frames.extend(decoder.feed(wire[start:]))
            self.assertEqual(frames, [b"", b":,"])
            decoder.finish()

    def test_deterministic_random_chunking(self):
        rng = random.Random(7541)
        for _ in range(100):
            payloads = [bytes(rng.randrange(256) for _ in range(rng.randrange(65)))
                        for _ in range(rng.randrange(1, 15))]
            wire = b"".join(map(encode, payloads))
            decoder = Decoder(64)
            got = []
            offset = 0
            while offset < len(wire):
                size = rng.randrange(1, 18)
                got.extend(decoder.feed(wire[offset:offset + size]))
                offset += size
            self.assertEqual(got, payloads)
            decoder.finish()

    def test_raw_vectors(self):
        path = Path(__file__).resolve().parents[1] / "inputs" / "vectors.json"
        data = json.loads(path.read_text())
        expected = [[b""], [b"a,b", b":\0"], ["é".encode()]]
        for wire_hex, payloads in zip(data["valid_wire_hex"], expected):
            wire = bytes.fromhex(wire_hex)
            for size in data["chunk_sizes"]:
                decoder = Decoder()
                self.assertEqual([p for i in range(0, len(wire), size)
                                  for p in decoder.feed(wire[i:i + size])], payloads)
                decoder.finish()
        for wire_hex in data["invalid_wire_hex"]:
            with self.assertRaises(FrameError):
                Decoder().feed(bytes.fromhex(wire_hex))
        for wire_hex in data["unfinished_wire_hex"]:
            decoder = Decoder()
            decoder.feed(bytes.fromhex(wire_hex))
            with self.assertRaises(FrameError):
                decoder.finish()

    def test_malformed_and_reset(self):
        malformed = [b":", b"00", b"01", b"+1", b"-1", b" 1", b"1 ", b"\n",
                     b"x", b"\xff", b"1:a;", b"0:x", b"1:a,,", b"0:,x"]
        for wire in malformed:
            for split in range(len(wire) + 1):
                with self.subTest(wire=wire, split=split):
                    decoder = Decoder()
                    with self.assertRaises(FrameError):
                        decoder.feed(wire[:split])
                        decoder.feed(wire[split:])
                    self.assert_poisoned(decoder)
                    self.assertIsNone(decoder.reset())
                    self.assertEqual(decoder.feed(b"1:z,"), [b"z"])
                    decoder.finish()

    def test_each_incomplete_prefix_and_poisoning(self):
        wire = b"12:abcdefghijkl,"
        for end in range(1, len(wire)):
            decoder = Decoder()
            self.assertEqual(decoder.feed(wire[:end]), [])
            with self.assertRaises(FrameError):
                decoder.finish()
            self.assert_poisoned(decoder)
            decoder.reset()
            self.assertEqual(decoder.feed(b"0:,"), [b""])

    def test_limit_enforced_before_colon(self):
        for limit, prefix in [(0, b"1"), (9, b"10"), (1024, b"1025"), (100, b"999")]:
            decoder = Decoder(limit)
            decoder.feed(prefix[:-1])
            with self.assertRaises(FrameError):
                decoder.feed(prefix[-1:])
            self.assert_poisoned(decoder)
        with self.assertRaises(FrameError):
            Decoder().feed(b"9" * 100_000)
        self.assertEqual(Decoder(0).feed(b"0:,0:,"), [b"", b""])
        self.assertEqual(Decoder(3).feed(b"3:abc,"), [b"abc"])
        self.assertEqual(Decoder().feed(encode(b"x" * 1024)), [b"x" * 1024])
        decoder = Decoder(0)
        decoder.reset()
        with self.assertRaises(FrameError):
            decoder.feed(b"1")

    def test_constructor_validation(self):
        for value in [True, False, -1, 1.0, "1", None, b"1", [], object()]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                Decoder(value)
        for value in [0, 1, 1024, 10 ** 100]:
            Decoder(value).finish()

    def test_type_errors_preserve_each_partial_state(self):
        for split in range(len(b"2:ab,")):
            for invalid in ["", bytearray(), memoryview(b""), None, 1, [], object()]:
                decoder = Decoder()
                decoder.feed(b"2:ab,"[:split])
                with self.assertRaises(TypeError):
                    decoder.feed(invalid)
                self.assertEqual(decoder.feed(b"2:ab,"[split:]), [b"ab"])
                decoder.finish()

    def test_finish_stays_open_and_reset_discards_partial(self):
        decoder = Decoder()
        for _ in range(3):
            self.assertIsNone(decoder.finish())
            self.assertEqual(decoder.feed(b""), [])
            self.assertEqual(decoder.feed(b"1:a,"), [b"a"])
        decoder.feed(b"10:partial")
        decoder.reset()
        self.assertEqual(decoder.feed(b"1:b,"), [b"b"])
        decoder.finish()


if __name__ == "__main__":
    unittest.main()
