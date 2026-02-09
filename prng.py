"""
Отримання псевдовипадкових чисел для перестановки блоків
З LFSR дістається біти; з цього робиться randint(a, b)
"""

from dataclasses import dataclass
from lfsr import LFSR


@dataclass
class LfsrPrng:
    lfsr: LFSR

    def randint(self, a: int, b: int) -> int:
        """
        Рівномірне число в [a, b]
        Використовується rejection sampling, щоб не ловити модульний bias
        """
        if a > b:
            raise ValueError("a must be <= b")

        span = b - a + 1
        if span == 1:
            return a

        # Скільки біт треба, щоб покрити span
        bits = span.bit_length()

        # Rejection sampling: береться значення, поки воно не в межах
        while True:
            x = self.lfsr.randbits(bits)
            if x < span:
                return a + x
