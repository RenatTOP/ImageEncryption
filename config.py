# Параметри LFSR:
# width = кількість бітів у регістрі
# taps = позиції бітів, які XOR-яться для feedback (типова форма Fibonacci LFSR)
DEFAULT_LFSR_WIDTH = 16
DEFAULT_LFSR_TAPS = (16, 14, 13, 11)  # 16-бітний поліном

# Для відео: дефолтний codec для вихідного файлу.
DEFAULT_VIDEO_CODEC = "mp4v"  # 'FFV1' для MKV, 'mp4v' для MP4 ...

DEFAULT_TILE_SIZE = 64  # розмір блоку в пікселях
DEFAULT_ROUNDS = 3  # кількість раундів перемішування
