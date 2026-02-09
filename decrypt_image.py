"""
CLI для дешифрування статичної картинки
"""

import argparse
import cv2

from config import (
    DEFAULT_LFSR_WIDTH,
    DEFAULT_LFSR_TAPS,
    DEFAULT_TILE_SIZE,
    DEFAULT_ROUNDS,
)
from cipher import decrypt_image


def main() -> None:
    ap = argparse.ArgumentParser(description="Block-based image decryption")
    ap.add_argument("input", help="Encrypted image path")
    ap.add_argument("output", help="Decrypted image path")
    ap.add_argument("--seed", type=int, required=True, help="Same seed as encryption")
    ap.add_argument(
        "--tile-size", type=int, default=DEFAULT_TILE_SIZE, help="Block size in pixels"
    )
    ap.add_argument(
        "--rounds", type=int, default=DEFAULT_ROUNDS, help="Number of shuffle rounds"
    )
    ap.add_argument(
        "--no-transform", action="store_true", help="Disable rotate/flip transform"
    )

    args = ap.parse_args()

    img = cv2.imread(args.input, cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError("Cannot read input image")

    dec = decrypt_image(
        img=img,
        seed=args.seed,
        width=DEFAULT_LFSR_WIDTH,
        taps=DEFAULT_LFSR_TAPS,
        tile_size=args.tile_size,
        rounds=args.rounds,
        use_tile_transform=not args.no_transform,
    )

    ok = cv2.imwrite(args.output, dec)
    if not ok:
        raise RuntimeError("Cannot write output image")


if __name__ == "__main__":
    main()
