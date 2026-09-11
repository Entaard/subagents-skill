"""Incremental decoding of decimal-length, colon, payload, comma frames."""


class FrameError(ValueError):
    """Malformed or incomplete framing, or use of a poisoned decoder."""


class Decoder:
    """Decode bytes incrementally; reset is required after a framing error."""

    def __init__(self, max_payload=1024):
        if isinstance(max_payload, bool) or not isinstance(max_payload, int) or max_payload < 0:
            raise ValueError("max_payload must be a nonnegative integer")
        self._max_payload = max_payload
        self.reset()

    def reset(self) -> None:
        """Discard all buffered data and errors, retaining the payload limit."""
        self._poisoned = False
        self._start_frame()

    def _start_frame(self):
        self._phase = "length"
        self._length = 0
        self._has_digit = False
        self._payload = bytearray()

    def _fail(self, message):
        self._poisoned = True
        self._start_frame()
        raise FrameError(message)

    def _check_healthy(self):
        if self._poisoned:
            raise FrameError("decoder is poisoned; call reset()")

    def feed(self, chunk: bytes) -> list[bytes]:
        """Return frames completed by this chunk; TypeError preserves state."""
        if not isinstance(chunk, bytes):
            raise TypeError("chunk must be bytes")
        self._check_healthy()
        frames = []
        offset = 0
        while offset < len(chunk):
            if self._phase == "payload":
                count = min(self._length - len(self._payload), len(chunk) - offset)
                self._payload.extend(chunk[offset:offset + count])
                offset += count
                if len(self._payload) == self._length:
                    self._phase = "comma"
                continue

            byte = chunk[offset]
            offset += 1
            if self._phase == "comma":
                if byte != 44:
                    self._fail("expected comma after payload")
                frames.append(bytes(self._payload))
                self._start_frame()
            elif 48 <= byte <= 57:
                if self._has_digit and self._length == 0:
                    self._fail("leading zero in length")
                digit = byte - 48
                # Compare before multiplication so even the temporary length
                # never exceeds the configured limit. No header is retained.
                if self._length > (self._max_payload - digit) // 10:
                    self._fail("payload length exceeds max_payload")
                self._length = self._length * 10 + digit
                self._has_digit = True
            elif byte == 58 and self._has_digit:
                self._phase = "payload" if self._length else "comma"
            else:
                self._fail("expected an ASCII decimal length followed by colon")
        return frames

    def finish(self) -> None:
        """Validate a clean frame boundary without closing the decoder."""
        self._check_healthy()
        if self._phase != "length" or self._has_digit:
            self._fail("incomplete frame at end of stream")
