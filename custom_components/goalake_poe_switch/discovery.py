"""Multicast discovery of switches (UDP 239.0.0.100:10086).

Protocol as the vendor app uses it: a JSON request {"cmd":"calludp","syn":<8 random characters>,
"data":{"callcmd":"search"}} is encrypted, base64 encoded and sent with a trailing CR LF to the multicast
group. Every switch answers with the same kind of encrypted message whose "data" holds its description.
The 16 byte key is a constant of the vendor protocol (every device uses it); this is obfuscation, not
security, and nothing secret travels over this channel (no password).

The code is independent of Home Assistant so that it can be tested and probed on its own.
"""

from __future__ import annotations

import base64
import json
import secrets
import socket
import string
import struct
import time
from typing import Any

GROUP = "239.0.0.100"
PORT = 10086
KEY = b"EpumTpjli6zIxL1I"

_DELTA = 0x9E3779B9
_ROUNDS = 32
_MASK = 0xFFFFFFFF
_BYTE_TABLE = b"qazwsxedc"


def _key_words(key: bytes) -> list[int]:
    return list(struct.unpack("<4I", key))


def _encrypt_block(v0: int, v1: int, k: list[int]) -> tuple[int, int]:
    total = 0
    for _ in range(_ROUNDS):
        total = (total + _DELTA) & _MASK
        v0 = (v0 + ((((v1 << 4) + k[0]) ^ (v1 + total) ^ ((v1 >> 5) + k[1])) & _MASK)) & _MASK
        v1 = (v1 + ((((v0 << 4) + k[2]) ^ (v0 + total) ^ ((v0 >> 5) + k[3])) & _MASK)) & _MASK
    return v0, v1


def _decrypt_block(v0: int, v1: int, k: list[int]) -> tuple[int, int]:
    total = (_ROUNDS * _DELTA) & _MASK
    for _ in range(_ROUNDS):
        v1 = (v1 - ((((v0 << 4) + k[2]) ^ (v0 + total) ^ ((v0 >> 5) + k[3])) & _MASK)) & _MASK
        v0 = (v0 - ((((v1 << 4) + k[0]) ^ (v1 + total) ^ ((v1 >> 5) + k[1])) & _MASK)) & _MASK
        total = (total - _DELTA) & _MASK
    return v0, v1


def _tail_delta(index: int, k: list[int]) -> int:
    """The amount added to (or removed from) a trailing byte, 32 times, at absolute byte position `index`."""
    m = _BYTE_TABLE[index % 8]
    return ((((m << 2) + k[index % 4]) ^ ((m >> 3) + k[index % 4])) * _ROUNDS) & 0xFF


def encrypt(data: bytes, key: bytes = KEY) -> str:
    """Encrypt and base64 encode. Full 8 byte blocks use a TEA variant, the rest is done byte by byte."""
    k = _key_words(key)
    whole = len(data) - len(data) % 8
    out = bytearray()
    for i in range(0, whole, 8):
        v0, v1 = struct.unpack("<2I", data[i : i + 8])
        out += struct.pack("<2I", *_encrypt_block(v0, v1, k))
    for i in range(whole, len(data)):
        out.append((data[i] + _tail_delta(i, k)) & 0xFF)
    return base64.b64encode(bytes(out)).decode()


def decrypt(text: str, key: bytes = KEY) -> bytes | None:
    """Inverse of encrypt; None when the text is not valid base64."""
    try:
        raw = base64.b64decode(text, validate=True)
    except ValueError:
        return None
    k = _key_words(key)
    whole = len(raw) - len(raw) % 8
    out = bytearray()
    for i in range(0, whole, 8):
        v0, v1 = struct.unpack("<2I", raw[i : i + 8])
        out += struct.pack("<2I", *_decrypt_block(v0, v1, k))
    for i in range(whole, len(raw)):
        out.append((raw[i] - _tail_delta(i, k)) & 0xFF)
    return bytes(out)


def new_syn() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


def build_search(syn: str) -> bytes:
    request = {"cmd": "calludp", "syn": syn, "data": {"callcmd": "search"}}
    return (encrypt(json.dumps(request, separators=(",", ":")).encode()) + "\r\n").encode()


def parse_reply(packet: bytes, syn: str) -> dict[str, Any] | None:
    """The device description of a reply to our search, or None for anything else."""
    text = packet.decode("ascii", "ignore").strip()
    plain = decrypt(text)
    if plain is None:
        return None
    try:
        message = json.loads(plain.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(message, dict) or message.get("ack") != "calludp" or message.get("syn") != syn:
        return None
    data = message.get("data")
    return data if isinstance(data, dict) else None


def discover(interface_ip: str | None = None, timeout: float = 3.0, ttl: int = 2) -> list[dict[str, Any]]:
    """Send one search and collect the answers for `timeout` seconds (blocking, run it in an executor).

    `interface_ip` selects the network interface by its IPv4 address; None lets the system choose.
    """
    syn = new_syn()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    found: dict[str, dict[str, Any]] = {}
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        sock.bind(("", 0))
        iface = socket.inet_aton(interface_ip) if interface_ip else socket.inet_aton("0.0.0.0")
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, iface)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(GROUP) + iface)
        sock.sendto(build_search(syn), (GROUP, PORT))
        deadline = time.monotonic() + timeout
        while (remaining := deadline - time.monotonic()) > 0:
            sock.settimeout(remaining)
            try:
                packet, addr = sock.recvfrom(2048)
            except (TimeoutError, socket.timeout):
                break
            device = parse_reply(packet, syn)
            if device:
                device.setdefault("ip", addr[0])
                found[str(device.get("sn") or addr[0])] = device
    finally:
        sock.close()
    return list(found.values())
