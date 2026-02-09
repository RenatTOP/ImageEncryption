"""
Ядро шифру:
- будується permutation table з seed через LFSR
- переставляються блоки
- для дешифрування береться інверсна перестановка
"""

import math
from typing import List
import cv2
import numpy as np

from lfsr import LFSR
from prng import LfsrPrng
from tiles import pad_to_tile_size, unpad_tile_size, split_tiles, merge_tiles


def build_permutation(
    n: int, seed: int, width: int, taps: tuple[int, ...]
) -> List[int]:
    """
    Створює перестановку індексів [0..n-1] використовуючи LFSR як PRNG
    Реалізація: Fisher-Yates shuffle
    """
    lfsr = LFSR(width=width, taps=taps, state=seed)
    rng = LfsrPrng(lfsr)

    perm = list(range(n))

    # Fisher-Yates: проходиться справа наліво і міняємо місцями з випадковим індексом
    for i in range(n - 1, 0, -1):
        j = rng.randint(0, i)
        perm[i], perm[j] = perm[j], perm[i]

    return perm


def invert_permutation(perm: List[int]) -> List[int]:
    """
    Інверсія перестановки:
    inv[perm[i]] = i
    """
    inv = [0] * len(perm)
    for i, p in enumerate(perm):
        inv[p] = i
    return inv


def apply_permutation(tiles: List[np.ndarray], perm: List[int]) -> List[np.ndarray]:
    """
    Повертає новий список tiles, де tile з індексу i переходить в позицію perm[i]
    """
    if len(tiles) != len(perm):
        raise ValueError("tiles and perm must have same length")

    out = [None] * len(tiles)
    for i, p in enumerate(perm):
        out[p] = tiles[i]
    return out  # type: ignore


def transform_tile(tile: np.ndarray, code: int) -> np.ndarray:
    """
    code 0..7: 8 варіантів (4 повороти * optional flip)
    """
    t = tile
    rot = code & 3  # 0..3
    flip = (code >> 2) & 1

    if rot == 1:
        t = cv2.rotate(t, cv2.ROTATE_90_CLOCKWISE)
    elif rot == 2:
        t = cv2.rotate(t, cv2.ROTATE_180)
    elif rot == 3:
        t = cv2.rotate(t, cv2.ROTATE_90_COUNTERCLOCKWISE)

    if flip:
        t = cv2.flip(t, 1)  # горизонтальний flip
    return t


def inverse_transform_tile(tile: np.ndarray, code: int) -> np.ndarray:
    """
    Інверсія для transform_tile (8 варіантів: 4 повороти * optional flip)
    Порядок операцій при інверсії зворотний
    Якщо в encrypt було: rotate -> flip,
    то тут має бути: flip -> rotate_back
    """
    t = tile
    rot = code & 3  # 0..3
    flip = (code >> 2) & 1  # 0/1

    # 1) спочатку відміняється flip
    if flip:
        t = cv2.flip(t, 1)

    # 2) потім відміняється rotate
    # rotate_back = (4 - rot) % 4
    if rot == 1:
        t = cv2.rotate(t, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif rot == 2:
        t = cv2.rotate(t, cv2.ROTATE_180)
    elif rot == 3:
        t = cv2.rotate(t, cv2.ROTATE_90_CLOCKWISE)

    return t


def encrypt_image(
    img: np.ndarray,
    seed: int,
    width: int,
    taps: tuple[int, ...],
    tile_size: int | None = None,
    rounds: int = 1,
    use_tile_transform: bool = True,
) -> np.ndarray:
    """
    Шифрує зображення, використовуючи перестановки та трансформації блоків
    """

    # Якщо tile_size заданий, паддинг до кратності tile_size
    if tile_size is not None and tile_size > 0:
        padded, (pad_h, pad_w) = pad_to_tile_size(img, tile_size)

        # rows/cols рахується строго по padded розміру, щоб не було проблем з неповними блоками
        h_pad, w_pad = padded.shape[:2]
        rows = h_pad // tile_size
        cols = w_pad // tile_size
    else:
        # якщо без tile_size
        padded = img
        pad_h = pad_w = 0

    tiles = split_tiles(padded, rows, cols)

    out_tiles = tiles
    for r in range(max(1, rounds)):
        # transform
        if use_tile_transform:
            lfsr = LFSR(width=width, taps=taps, state=(seed ^ (r + 1) * 0xBEEF))
            codes = [lfsr.randbits(3) for _ in range(len(out_tiles))]
            out_tiles = [transform_tile(t, codes[i]) for i, t in enumerate(out_tiles)]

        # permutation
        perm = build_permutation(
            n=len(out_tiles), seed=(seed ^ (r + 1) * 0x9E37), width=width, taps=taps
        )
        out_tiles = apply_permutation(out_tiles, perm)

    encrypted = merge_tiles(out_tiles, rows, cols)

    # Повертається оригінальний розмір
    if tile_size is not None and tile_size > 0:
        encrypted = unpad_tile_size(encrypted, pad_h, pad_w)

    return encrypted


def decrypt_image(
    img: np.ndarray,
    seed: int,
    width: int,
    taps: tuple[int, ...],
    tile_size: int | None = None,
    rounds: int = 1,
    use_tile_transform: bool = True,
) -> np.ndarray:
    """
    Дешифрує зображення, використовуючи інверсні перестановки та трансформації блоків
    """

    # Якщо tile_size заданий, паддинг до кратності tile_size
    if tile_size is not None and tile_size > 0:
        padded, (pad_h, pad_w) = pad_to_tile_size(img, tile_size)
        h_pad, w_pad = padded.shape[:2]
        rows = h_pad // tile_size
        cols = w_pad // tile_size
    else:
        padded = img
        pad_h = pad_w = 0

    tiles = split_tiles(padded, rows, cols)
    out_tiles = tiles

    # Раунди відкочуються назад
    for r in reversed(range(max(1, rounds))):
        # inverse permutation
        perm = build_permutation(
            n=len(out_tiles), seed=(seed ^ (r + 1) * 0x9E37), width=width, taps=taps
        )
        inv = invert_permutation(perm)
        out_tiles = apply_permutation(out_tiles, inv)

        # inverse transform
        if use_tile_transform:
            lfsr = LFSR(width=width, taps=taps, state=(seed ^ (r + 1) * 0xBEEF))
            codes = [lfsr.randbits(3) for _ in range(len(out_tiles))]
            out_tiles = [
                inverse_transform_tile(t, codes[i]) for i, t in enumerate(out_tiles)
            ]

    decrypted = merge_tiles(out_tiles, rows, cols)

    # Повертається оригінальний розмір
    if tile_size is not None and tile_size > 0:
        decrypted = unpad_tile_size(decrypted, pad_h, pad_w)

    return decrypted
