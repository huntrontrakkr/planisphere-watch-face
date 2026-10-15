"""A small random number generator the watch's C carries too (xorshift32), so the prototype and the watch scatter
the weather's clouds, rain and snow alike."""


class Rng:
    def __init__(self, seed):
        x = (int(seed) ^ 0x9E3779B9) & 0xFFFFFFFF
        self.x = x or 1
        for _ in range(4):
            self.next32()

    def next32(self):
        x = self.x
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
        self.x = x
        return x

    def random(self):
        """0 <= u < 1, in 24 bits."""
        return (self.next32() >> 8) / 16777216.0

    def uniform(self, a, b):
        return a + (b - a) * self.random()

    def integers(self, a, b):
        """a <= n < b."""
        return a + (((self.next32() >> 8) * (b - a)) >> 24)

    def choice(self, n, p):
        """An index 0..n-1, by the weights p (summing to 1)."""
        u, acc = self.random(), 0.0
        for i in range(n):
            acc += p[i]
            if u < acc:
                return i
        return n - 1
