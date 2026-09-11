import itertools
import random
import unittest

from decoder import Decoder, FrameError


def encode(payloads):
    return b"".join(str(len(p)).encode("ascii") + b":" + p + b"," for p in payloads)


class DecoderTests(unittest.TestCase):
    def decode_chunks(self, chunks, expected, limit=1024):
        decoder = Decoder(limit)
        result = []
        for chunk in chunks:
            self.assertEqual(decoder.feed(b""), [])
            result.extend(decoder.feed(chunk))
        self.assertIsNone(decoder.finish())
        self.assertEqual(result, expected)

    def test_every_single_split_binary_and_concatenation(self):
        payloads = [b"", b"a,b", b":\0", "é🙂".encode(), bytes(range(256)), b""]
        wire = encode(payloads)
        for split in range(len(wire) + 1):
            with self.subTest(split=split):
                self.decode_chunks([wire[:split], wire[split:]], payloads)
        self.decode_chunks([bytes([byte]) for byte in wire], payloads)

    def test_every_partition_of_short_stream(self):
        payloads = [b"", b":,"]
        wire = encode(payloads)
        for cuts in itertools.product([False, True], repeat=len(wire) - 1):
            boundaries = [0] + [i + 1 for i, cut in enumerate(cuts) if cut] + [len(wire)]
            self.decode_chunks([wire[a:b] for a, b in zip(boundaries, boundaries[1:])], payloads)

    def test_seeded_arbitrary_chunks(self):
        rng = random.Random(2026)
        payloads = [bytes(rng.randrange(256) for _ in range(rng.randrange(80))) for _ in range(100)]
        wire = encode(payloads)
        chunks = []
        while wire:
            size = rng.randrange(1, 37)
            chunks.append(wire[:size])
            wire = wire[size:]
        self.decode_chunks(chunks, payloads)

    def test_emits_only_after_comma(self):
        decoder = Decoder()
        self.assertEqual(decoder.feed(b"3:abc"), [])
        self.assertEqual(decoder.feed(b",0:,2:x"), [b"abc", b""])
        self.assertEqual(decoder.feed(b"y,"), [b"xy"])
        decoder.finish()

    def assert_poisoned_then_reset(self, decoder):
        for chunk in [b"", b"0:,"]:
            with self.assertRaises(FrameError):
                decoder.feed(chunk)
        with self.assertRaises(FrameError):
            decoder.finish()
        self.assertIsNone(decoder.reset())
        self.assertEqual(decoder.feed(b"0:,"), [b""])
        decoder.finish()

    def test_malformed_at_every_split(self):
        invalid = [b":", b"01", b"00", b"+1", b"-1", b" 1", b"\t1", b"1\n", b"x",
                   b"\xff", b"1\xff", b"1.0", b"0:;", b"1:a;", b"1:a:", b"1:a,,"]
        for wire in invalid:
            for split in range(len(wire) + 1):
                with self.subTest(wire=wire, split=split):
                    decoder = Decoder()
                    with self.assertRaises(FrameError):
                        decoder.feed(wire[:split])
                        decoder.feed(wire[split:])
                    self.assert_poisoned_then_reset(decoder)

    def test_every_proper_frame_prefix_is_truncated(self):
        for wire in [b"0:,", b"12:hello,world!,"]:
            for stop in range(1, len(wire)):
                with self.subTest(wire=wire, stop=stop):
                    decoder = Decoder()
                    decoder.feed(wire[:stop])
                    with self.assertRaises(FrameError):
                        decoder.finish()
                    self.assert_poisoned_then_reset(decoder)

    def test_finish_boundary_does_not_close(self):
        decoder = Decoder()
        decoder.finish()
        decoder.finish()
        self.assertEqual(decoder.feed(b"1:a,"), [b"a"])
        decoder.finish()
        self.assertEqual(decoder.feed(b"1:b,"), [b"b"])
        decoder.finish()

    def test_constructor_validation(self):
        for limit in [-1, True, False, 1.0, "1", None, b"1", [], {}]:
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                Decoder(limit)
        for limit in [0, 1, 1024, 10 ** 100]:
            Decoder(limit).finish()
        self.assertTrue(issubclass(FrameError, ValueError))

    def test_limit_zero_and_exact_limit(self):
        self.decode_chunks([b"0:,0:,"], [b"", b""], limit=0)
        self.decode_chunks([b"3:abc,"], [b"abc"], limit=3)
        self.decode_chunks([encode([b"x" * 1024])], [b"x" * 1024])
        decoder = Decoder(0)
        with self.assertRaises(FrameError):
            decoder.feed(b"1")
        self.assert_poisoned_then_reset(decoder)

    def test_oversize_immediately_without_colon(self):
        for limit, prefix, last in [(1024, b"102", b"5"), (99, b"99", b"0"), (9, b"", b"9" * 100000)]:
            with self.subTest(limit=limit):
                decoder = Decoder(limit)
                self.assertEqual(decoder.feed(prefix), [])
                with self.assertRaises(FrameError):
                    decoder.feed(last)
                self.assert_poisoned_then_reset(decoder)

    def test_type_errors_preserve_every_phase(self):
        wire = b"3:abc,"
        for split in range(len(wire)):
            for invalid in [None, "", bytearray(b"x"), memoryview(b"x"), 123, [], True]:
                with self.subTest(split=split, invalid=invalid):
                    decoder = Decoder()
                    decoder.feed(wire[:split])
                    with self.assertRaises(TypeError):
                        decoder.feed(invalid)
                    self.assertEqual(decoder.feed(wire[split:]), [b"abc"])
                    decoder.finish()

    def test_type_error_does_not_unpoison(self):
        decoder = Decoder()
        with self.assertRaises(FrameError):
            decoder.feed(b"x")
        with self.assertRaises(TypeError):
            decoder.feed("0:,")
        self.assert_poisoned_then_reset(decoder)

    def test_reset_discards_partial_data_and_preserves_limit(self):
        decoder = Decoder(3)
        for prefix in [b"2", b"2:", b"2:a", b"2:ab"]:
            decoder.feed(prefix)
            decoder.reset()
            self.assertEqual(decoder.feed(b"1:x,"), [b"x"])
        decoder.reset()
        decoder.reset()
        with self.assertRaises(FrameError):
            decoder.feed(b"4")


if __name__ == "__main__":
    unittest.main()
