# -*- coding: utf-8 -*-
"""Pure-Python RFC 8032 Ed25519 signature verification."""

import hashlib


_P = 2**255 - 19
_L = 2**252 + 27742317777372353535851937790883648493
_D = (-121665 * pow(121666, _P - 2, _P)) % _P
_SQRT_M1 = pow(2, (_P - 1) // 4, _P)
_IDENTITY = (0, 1, 1, 0)


class Ed25519VerifyError(ValueError):
    """The supplied Ed25519 verification input is inadmissible."""


def _is_identity(point: tuple[int, int, int, int]) -> bool:
    x, y, z, _t = point
    return x % _P == 0 and (y - z) % _P == 0


def _add(
    left: tuple[int, int, int, int],
    right: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    x1, y1, z1, t1 = left
    x2, y2, z2, t2 = right
    a = ((y1 - x1) * (y2 - x2)) % _P
    b = ((y1 + x1) * (y2 + x2)) % _P
    c = (2 * _D * t1 * t2) % _P
    d = (2 * z1 * z2) % _P
    e = (b - a) % _P
    f = (d - c) % _P
    g = (d + c) % _P
    h = (b + a) % _P
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _double(point: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x, y, z, _t = point
    a = x * x % _P
    b = y * y % _P
    c = 2 * z * z % _P
    d = -a % _P
    e = ((x + y) * (x + y) - a - b) % _P
    g = (d + b) % _P
    f = (g - c) % _P
    h = (d - b) % _P
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _scalar_multiply(
    point: tuple[int, int, int, int], scalar: int,
) -> tuple[int, int, int, int]:
    result = _IDENTITY
    addend = point
    while scalar:
        if scalar & 1:
            result = _add(result, addend)
        addend = _double(addend)
        scalar >>= 1
    return result


def _equal(
    left: tuple[int, int, int, int],
    right: tuple[int, int, int, int],
) -> bool:
    x1, y1, z1, _t1 = left
    x2, y2, z2, _t2 = right
    return (
        (x1 * z2 - x2 * z1) % _P == 0
        and (y1 * z2 - y2 * z1) % _P == 0
    )


def _decode_point(encoded: bytes, error: str) -> tuple[int, int, int, int]:
    value = int.from_bytes(encoded, "little")
    sign = value >> 255
    y = value & ((1 << 255) - 1)
    if y >= _P:
        raise Ed25519VerifyError(error)

    y_squared = y * y % _P
    denominator = (_D * y_squared + 1) % _P
    x_squared = (y_squared - 1) * pow(denominator, _P - 2, _P) % _P
    x = pow(x_squared, (_P + 3) // 8, _P)
    if x * x % _P != x_squared:
        x = x * _SQRT_M1 % _P
    if x * x % _P != x_squared:
        raise Ed25519VerifyError(error)
    if x == 0 and sign:
        raise Ed25519VerifyError(error)
    if (x & 1) != sign:
        x = (-x) % _P
    # Unreachable after the parity flip; not counted as an independent barrier.
    if (x & 1) != sign:
        raise Ed25519VerifyError(error)
    # Redundant for reachable inputs after square-root checks; not an independent barrier.
    if (-x * x + y_squared - 1 - _D * x * x * y_squared) % _P:
        raise Ed25519VerifyError(error)
    return (x, y, 1, x * y % _P)


_BASE = _decode_point(bytes.fromhex("58" + "66" * 31), "point")


def verify(public_key: bytes, message: bytes, signature: bytes) -> None:
    """Verify an Ed25519 signature or raise :class:`Ed25519VerifyError`."""
    if type(public_key) is not bytes or len(public_key) != 32:
        raise Ed25519VerifyError("key")
    if type(message) is not bytes:
        raise Ed25519VerifyError("message")
    if type(signature) is not bytes or len(signature) != 64:
        raise Ed25519VerifyError("signature")

    encoded_r = signature[:32]
    encoded_s = signature[32:]
    s = int.from_bytes(encoded_s, "little")
    if s >= _L:
        raise Ed25519VerifyError("S")

    public_point = _decode_point(public_key, "key")
    if _is_identity(public_point):
        raise Ed25519VerifyError("identity")
    if not _is_identity(_scalar_multiply(public_point, _L)):
        raise Ed25519VerifyError("subgroup")
    r_point = _decode_point(encoded_r, "R")
    if _is_identity(r_point):
        raise Ed25519VerifyError("R identity")
    if not _is_identity(_scalar_multiply(r_point, _L)):
        raise Ed25519VerifyError("R subgroup")

    challenge = int.from_bytes(
        hashlib.sha512(encoded_r + public_key + message).digest(), "little"
    ) % _L
    left = _scalar_multiply(_scalar_multiply(_BASE, s), 8)
    right = _add(
        _scalar_multiply(r_point, 8),
        _scalar_multiply(_scalar_multiply(public_point, challenge), 8),
    )
    if not _equal(left, right):
        raise Ed25519VerifyError("equation")
