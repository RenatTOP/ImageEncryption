"""
CLI для дешифрування відео покадрово
"""

import argparse

from config import (
    DEFAULT_LFSR_WIDTH,
    DEFAULT_LFSR_TAPS,
    DEFAULT_TILE_SIZE,
    DEFAULT_ROUNDS,
    DEFAULT_VIDEO_CODEC,
)
from video_pipeline import VideoJob, process_video


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Encrypted video path")
    ap.add_argument("output", help="Output decrypted video path")
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
    ap.add_argument("--codec", type=str, default=DEFAULT_VIDEO_CODEC)
    args = ap.parse_args()

    job = VideoJob(
        input_path=args.input,
        output_path=args.output,
        tile_size=args.tile_size,
        rounds=args.rounds,
        seed=args.seed,
        lfsr_width=DEFAULT_LFSR_WIDTH,
        lfsr_taps=DEFAULT_LFSR_TAPS,
        no_transform=args.no_transform,
        mode="decrypt",
        codec=args.codec,
    )
    process_video(job)


if __name__ == "__main__":
    main()
