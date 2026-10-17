"""Integer trigonometry and the projection in integers, as the watch has them (plan_math.c isin_q30, plan_render.c
project_u), bit for bit: angles in 2^-20 of a turn (1.24 seconds of arc), sines in Q30, positions in 1/256 pixel.
Python's >> floors negative numbers as the watch's arithmetic shifts do."""
import math
import struct

TURN, QUARTER = 1 << 20, 1 << 18
_Q = (1686629681, -693597962, 85565130, -5017110, 162088)   # sin(pi x / 2) on 0..1, Q30, odd powers


def f32(x):
    """x as the watch's single precision has it."""
    return struct.unpack("<f", struct.pack("<f", x))[0]


def floor_half(x):
    """floor(x + 0.5): the rounding the watch uses here (pyf_floor(x + 0.5f))."""
    return math.floor(x + 0.5)


def isin_q30(a):
    a &= TURN - 1
    q, f = a >> 18, a & (QUARTER - 1)
    if q & 1:
        f = QUARTER - f
    x = f << 12
    x2 = (x * x) >> 30
    acc = _Q[4]
    for k in (3, 2, 1, 0):
        acc = _Q[k] + ((x2 * acc) >> 30)
    s = (x * acc) >> 30
    return -s if q >= 2 else s


def icos_q30(a):
    return isin_q30(a + QUARTER)


def isqrt32(v):
    return math.isqrt(v)


_A = (2734205957, -909566774, 529544042, -318951500, 144429673, -32182182)   # atan z, z 0..1, in brad, Q14


def atan_q(z):
    """atan of z (Q16, 0..1) in 2^-20 of a turn."""
    z2 = (z * z) >> 16
    acc = _A[5]
    for k in (4, 3, 2, 1, 0):
        acc = _A[k] + ((z2 * acc) >> 16)
    return (z * acc) >> 30


def iatan2_brad(y, x):
    ax, ay = abs(x), abs(y)
    if not ax and not ay:
        return 0
    a = atan_q((ay << 16) // ax) if ay <= ax else QUARTER - atan_q((ax << 16) // ay)
    if x < 0:
        a = TURN // 2 - a
    return -a if y < 0 else a


def iasin_brad(s):
    s15 = max(-32768, min(32768, s >> 15))
    return iatan2_brad(s15, isqrt32((1 << 30) - s15 * s15))


def lst20(lst):
    """The sidereal time (degrees, as the watch holds it in single precision) in 2^-20 of a turn."""
    return floor_half(f32(f32(lst) * f32(1048576.0 / 360))) & (TURN - 1)


def kq(k):
    """The projection's scale: pixels per 65535th of a half turn, Q16 of Q8 (from the watch's single-precision k)."""
    return floor_half(f32(f32(k) * f32(180.0 * 256 * 65536 / 65535)))


def project_u(ra20, colat_u, lst20_, south, kq_, cxq, cyq):
    """(x, y) in 1/256 pixel of a point ra20 (2^-20 turn) and colat_u (65535ths of a half turn) from the pole."""
    h = (lst20_ - ra20) & (TURN - 1)
    if south:
        h = (-h) & (TURN - 1)
    rho = (colat_u * kq_) >> 16
    return cxq + ((rho * isin_q30(h)) >> 30), cyq + ((rho * icos_q30(h)) >> 30)
