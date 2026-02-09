"""
Пайплайн для відео:
- читається кадри через OpenCV
- для кожного кадру робиться encrypt/decrypt
- пишеться у новий файл
"""

from dataclasses import dataclass
import cv2

from cipher import encrypt_image, decrypt_image


@dataclass
class VideoJob:
    input_path: str
    output_path: str
    tile_size: int
    rounds: int
    seed: int
    lfsr_width: int
    lfsr_taps: tuple[int, ...]
    no_transform: bool = False
    mode: str = "encrypt"  # "encrypt" / "decrypt"
    codec: str = "mp4v"


def process_video(job: VideoJob) -> None:
    cap = cv2.VideoCapture(job.input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open input video: {job.input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    # Беремо розмір кадру з вхідного відео
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Налаштовуємо writer
    fourcc = cv2.VideoWriter_fourcc(*job.codec)
    writer = cv2.VideoWriter(job.output_path, fourcc, fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError(f"Cannot open output video for writing: {job.output_path}")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if job.mode == "encrypt":
            out = encrypt_image(
                img=frame,
                seed=job.seed,
                width=job.lfsr_width,
                taps=job.lfsr_taps,
                tile_size=job.tile_size,
                rounds=job.rounds,
                use_tile_transform=not job.no_transform,
            )
        elif job.mode == "decrypt":
            # Відео-дешифр зазвичай потребує того ж grid і seed.
            # pad_h/pad_w тут = 0, бо в відео-пайплайні зберігається розмір кадру.
            out = decrypt_image(
                img=frame,
                seed=job.seed,
                width=job.lfsr_width,
                taps=job.lfsr_taps,
                tile_size=job.tile_size,
                rounds=job.rounds,
                use_tile_transform=not job.no_transform,
            )
        else:
            raise ValueError("job.mode must be 'encrypt' or 'decrypt'")

        # writer очікує кадр того ж розміру, що й оголошений (w,h).
        # Якщо encrypt_image додає padding, розміри можуть змінитись.
        if out.shape[0] != h or out.shape[1] != w:
            out = cv2.resize(out, (w, h), interpolation=cv2.INTER_NEAREST)

        writer.write(out)

    cap.release()
    writer.release()
