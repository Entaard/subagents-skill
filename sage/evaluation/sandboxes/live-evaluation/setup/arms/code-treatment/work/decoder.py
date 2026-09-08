"""Incremental decoder for length:payload, byte frames."""


class FrameError(ValueError):
    """Invalid or incomplete framing; reset the decoder before reuse."""


class Decoder:
    """Decode frames with a nonnegative maximum payload size in bytes."""

    def __init__(self, max_payload=1024):
        if isinstance(max_payload, bool) or not isinstance(max_payload, int):
            raise ValueError("max_payload must be a nonnegative integer")
        if max_payload < 0:
            raise ValueError("max_payload must be a nonnegative integer")
        self._max_payload = max_payload
        self.reset()

    def reset(self) -> None:
        """Discard pending data and errors, retaining the configured limit."""
        self._poisoned = False
        self._state = "length"
        self._length = 0
        self._has_digit = False
        self._payload = bytearray()

    def _fail(self, message):
        self._poisoned = True
        self._payload.clear()
        raise FrameError(message)

    def _check_healthy(self):
        if self._poisoned:
            raise FrameError("decoder is poisoned; call reset()")

    def feed(self, chunk: bytes) -> list[bytes]:
        """Return complete frames; argument errors leave parser state intact."""
        if not isinstance(chunk, bytes):
            raise TypeError("chunk must be bytes")
        self._check_healthy()
        frames = []
        offset = 0
        while offset < len(chunk):
            if self._state == "payload":
                count = min(self._length - len(self._payload), len(chunk) - offset)
                self._payload.extend(chunk[offset:offset + count])
                offset += count
                if len(self._payload) == self._length:
                    self._state = "comma"
                continue

            value = chunk[offset]
            offset += 1
            if self._state == "comma":
                if value != ord(","):
                    self._fail("expected comma after payload")
                frames.append(bytes(self._payload))
                self._payload.clear()
                self._state = "length"
                self._length = 0
                self._has_digit = False
            elif ord("0") <= value <= ord("9"):
                if self._has_digit and self._length == 0:
                    self._fail("leading zero in length")
                length = self._length * 10 + value - ord("0")
                if length > self._max_payload:
                    self._fail("payload length exceeds max_payload")
                self._length = length
                self._has_digit = True
            elif value == ord(":") and self._has_digit:
                self._state = "payload" if self._length else "comma"
            else:
                self._fail("expected ASCII decimal length followed by colon")
        return frames

    def finish(self) -> None:
        """Check for a clean boundary without closing the decoder."""
        self._check_healthy()
        if self._state != "length" or self._has_digit:
            self._fail("incomplete frame at end of stream")
