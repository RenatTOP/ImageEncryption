"""
Fibonacci LFSR
Має стан (register), на кожному кроці робить feedback XOR із taps і зсувається

- seed не може бути 0, бо тоді LFSR залипне назавжди у нулях
"""

from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass
class LFSR:
    width: int
    taps: Tuple[int, ...]
    state: int

    def __post_init__(self) -> None:
        # Маска щоб стан ніколи не виходив за width бітів
        self._mask = (1 << self.width) - 1

        if self.state == 0:
            raise ValueError(
                "LFSR seed/state must be non-zero (otherwise it locks at 0)."
            )

        # Обрізається стан під width, якщо раптом дали більше
        self.state &= self._mask

        # Перевірка taps: вони мають бути в межах 1..width
        for t in self.taps:
            if not (1 <= t <= self.width):
                raise ValueError(f"Invalid tap position {t} for width={self.width}")

    def step_bit(self) -> int:
        """
        Робить 1 крок LFSR і повертає вихідний біт (LSB до зсуву)
        """
        out_bit = self.state & 1  # береться молодший біт як "output"

        # feedback = XOR вибраних бітів taps
        fb = 0
        for t in self.taps:
            # t=1 означає LSB, t=width означає MSB
            fb ^= (self.state >> (t - 1)) & 1

        # Зсув вправо, а feedback у MSB
        self.state = (self.state >> 1) | (fb << (self.width - 1))
        self.state &= self._mask  # щоб не вийти за width бітів

        return out_bit

    def randbits(self, n: int) -> int:
        """
        Генерує n псевдовипадкових бітів, склеєних у int
        """
        x = 0
        for i in range(n):
            x |= self.step_bit() << i
        return x
