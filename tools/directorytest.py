#!/usr/bin/env python3
"""The directory server's list limit, without a network.

    python3 tools/directorytest.py

net/directory.py's handler called with a socket that records what it
sends and a clock set by hand. Checked: a list for every request up to
the burst, then LIST_RATE a second; each address its own bucket; an
idle address's bucket forgotten; a full list of 16 sessions still one
datagram under 1472 bytes.
"""
import contextlib
import importlib.util
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('directory', os.path.join(ROOT, 'net', 'directory.py'))
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class Sock:
    def __init__(self):
        self.sent = []

    def sendto(self, data, addr):
        self.sent.append((data, addr))


def lists(sock, addr, n, now):
    before = len(sock.sent)
    for _ in range(n):
        d.handle(sock, d.MAGIC + b'L', addr, now)
    return sum(1 for data, to in sock.sent[before:] if to == addr and data[4:5] == b'S')


def main():
    sock = Sock()
    a, b = ('198.51.100.7', 5000), ('203.0.113.9', 5000)
    t = 1000.0
    assert lists(sock, a, 100, t) == d.LIST_BURST, 'the burst'
    assert lists(sock, a, 1, t) == 0, 'past the burst'
    assert lists(sock, b, 5, t) == 5, 'another address held by the first'
    assert lists(sock, a, 100, t + 1) == d.LIST_RATE, 'the rate'
    for k in range(40):                           # a game searching: every 400 ms
        assert lists(sock, a, 1, t + 2 + k * 0.4) == 1, 'a searching game refused'
    d.expire(t + 100)
    assert not d.lists, 'idle buckets kept'
    with contextlib.redirect_stdout(io.StringIO()):     # the server's own log lines
        for k in range(16):
            guid = bytes([k]) * 16
            d.handle(sock, d.MAGIC + b'H' + guid + bytes(d.RECORD), ('192.0.2.%d' % (k + 1), 6000), t + 100)
    sock.sent.clear()
    assert lists(sock, a, 1, t + 100) == 1
    data = sock.sent[-1][0]
    assert data[5] == d.LIST_MAX and len(data) <= 1472, 'the full list'
    print('directory: lists held to %d/s per address after %d, %d bytes at the most'
          % (d.LIST_RATE, d.LIST_BURST, len(data)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
