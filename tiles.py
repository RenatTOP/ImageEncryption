"""
Операції з фрагментами зображення (tiles):
- pad_to_grid: додається бордер, щоб картинка ділилась на grid без остачі
- split_tiles: ріжеться на блоки
- merge_tiles: збирається назад
- compute_edges: рахує межі блоків для довільного розміру і кількості блоків
- pad_to_tile_size: паддінг до кратності tile_size
- unpad_tile_size: прибирає паддінг, доданий pad_to_tile_size
"""

from typing import List, Tuple
import numpy as np
import cv2


def pad_to_grid(
    img: np.ndarray, rows: int, cols: int
) -> Tuple[np.ndarray, Tuple[int, int]]:
    """
    Додає padding справа/знизу, щоб (H % rows == 0) і (W % cols == 0)
    Повертає:
      - padded image
      - (pad_h, pad_w) щоб потім можна було обрізати назад
    """
    h, w = img.shape[:2]

    # Скільки треба додати до кратності
    pad_h = (rows - (h % rows)) % rows
    pad_w = (cols - (w % cols)) % cols

    if pad_h == 0 and pad_w == 0:
        return img, (0, 0)

    # BORDER_REFLECT: більш м’яко ніж чорні смуги
    padded = cv2.copyMakeBorder(img, 0, pad_h, 0, pad_w, borderType=cv2.BORDER_REFLECT)
    return padded, (pad_h, pad_w)


def split_tiles(img: np.ndarray, rows: int, cols: int) -> List[np.ndarray]:
    """
    Ріже зображення на rows*cols блоків (список)
    Порядок: row-major (зліва направо, зверху вниз)
    """
    h, w = img.shape[:2]
    tile_h = h // rows
    tile_w = w // cols

    tiles: List[np.ndarray] = []
    for r in range(rows):
        for c in range(cols):
            y0 = r * tile_h
            y1 = (r + 1) * tile_h
            x0 = c * tile_w
            x1 = (c + 1) * tile_w

            # .copy() важливо, щоб tile став незалежним об'єктом у пам’яті
            tiles.append(img[y0:y1, x0:x1].copy())

    return tiles


def merge_tiles(tiles: List[np.ndarray], rows: int, cols: int) -> np.ndarray:
    """
    Збирає tiles назад у картинку
    Очікує tiles у тому ж row-major порядку, що і split_tiles
    """
    if len(tiles) != rows * cols:
        raise ValueError("tiles length must be rows*cols")

    # Склеюється по рядках: кожен рядок = hstack, потім vstack
    rows_imgs = []
    idx = 0
    for r in range(rows):
        row_tiles = tiles[idx : idx + cols]
        idx += cols
        rows_imgs.append(np.hstack(row_tiles))

    return np.vstack(rows_imgs)


def compute_edges(n: int, size: int) -> List[int]:
    """
    Рахує межі так, щоб покрити весь size і розподілити "залишок" рівномірно
    Наприклад, size=10, n=3 -> [0, 3, 7, 10] (блоки 3,4,3)
    """
    edges = [0]
    base = size // n
    rem = size % n  # скільки пікселів зайвих
    acc = 0
    for i in range(n):
        step = base + (1 if i < rem else 0)  # першим rem блокам дається +1
        acc += step
        edges.append(acc)
    edges[-1] = size  # щоб не було проблем з округленням
    return edges


def pad_to_tile_size(
    img: np.ndarray, tile_size: int
) -> Tuple[np.ndarray, Tuple[int, int]]:
    """
    Паддінг справа/знизу так, щоб H і W стали кратні tile_size
    Повертає padded та (pad_h, pad_w) для зворотного unpad
    """
    h, w = img.shape[:2]
    pad_h = (tile_size - (h % tile_size)) % tile_size
    pad_w = (tile_size - (w % tile_size)) % tile_size

    if pad_h == 0 and pad_w == 0:
        return img, (0, 0)

    padded = cv2.copyMakeBorder(img, 0, pad_h, 0, pad_w, borderType=cv2.BORDER_REFLECT)
    return padded, (pad_h, pad_w)


def unpad_tile_size(img: np.ndarray, pad_h: int, pad_w: int) -> np.ndarray:
    """
    Прибирає паддінг, який додається з pad_to_tile_size
    """
    if pad_h == 0 and pad_w == 0:
        return img
    h, w = img.shape[:2]
    return img[: h - pad_h, : w - pad_w]
