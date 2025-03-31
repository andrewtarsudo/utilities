# -*- coding: utf-8 -*-
from rich import print

# def hash_file(file: StrPath):
#     with open(file, "rb") as f:
#         _hash = md5()
#
#         while True:
#             data: bytes = f.read(2048)
#
#             if not data:
#                 break
#
#             _hash.update(data)
#
#         result: bytes = _hash.digest()
#
#     return result
#
#
# def concatenate_files(files: Iterable[StrPath]):
#     unified_file: Path = Path(__file__).with_name("joined_file.txt")
#
#     with open(unified_file, "ab") as uf:
#         for file in files:
#             with open(file, "rb") as f:
#                 data = f.read()
#
#             uf.write(data)
#             uf.write(b"\n")
#
#     return unified_file
#
#
# def timer(func: Callable):
#     @wraps
#     def wrapper(*args, **kwargs):
#         start_time: int = perf_counter_ns()
#
#         result = func(*args, **kwargs)
#
#         end_time: int = perf_counter_ns()
#
#         print(f"Функция {func.__name__}, время выполнения: {end_time - start_time}")
#
#         return result
#
#     return wrapper
#
#
# @timer
# def hypothesis_a(files: Iterable[StrPath]) -> bytes:
#     """Try to join files into the single one and get its hash."""
#     unified_file: Path = concatenate_files(*files)
#     return hash_file(unified_file)
#
#
# @timer
# def hypothesis_b(files: Iterable[StrPath]) -> bytes:
#     """Try to get hashes of all files and then hash of hashes."""
#     hashes: list[bytes] = [hash_file(file) for file in files]
#     return md5(b"".join(hashes)).digest()
#
#
# if __name__ == '__main__':
#     _files: list[Path] = [item for item in Path(r"C:\Users\tarasov-a\PycharmProjects\hlr_hss\content\common\provisioning").iterdir() if item.is_file()]
#     _files.extend([file for file in Path(r"C:\Users\tarasov-a\PycharmProjects\hlr_hss\content\common\provisioning\entities").iterdir()])
#
#     hash_a: bytes = hypothesis_a(_files)
#     hash_b: bytes = hypothesis_b(_files)
#
#     print(hash_a)
#     print(hash_b)

from concurrent.futures import ProcessPoolExecutor
import hashlib
import os
import random
import string
import time


def generate_test_files(n_files, file_size):
    """Генерирует n_files файлов размером file_size байт"""
    for i in range(n_files):
        filename = f"test_{i}.txt"
        with open(filename, "w") as f:
            f.write(
                "".join(random.choice(string.ascii_letters) for _ in range(file_size))
            )


def hash_concatenated_files(files):
    """Хеширование объединенного буфера"""
    buffer = b"".join(open(file, "rb").read() for file in files)
    return hashlib.md5(buffer).hexdigest()


def hash_separate_files_parallel(files):
    """Параллельное хеширование каждого файла"""
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = [executor.submit(hash_file, file) for file in files]
        hashes = [future.result() for future in futures]
    return hashlib.md5(" ".join(hashes).encode()).hexdigest()


def hash_file(file):
    """Хеширование одного файла"""
    return hashlib.md5(open(file, "rb").read()).hexdigest()


def measure_time(func, files):
    """Измеряет время выполнения функции func"""
    start_time = time.time()
    result = func(files)
    end_time = time.time()
    return end_time - start_time, result


def run_experiment(n_files, file_size):
    """Запуск эксперимента"""
    filenames = [f"test_{i}.txt" for i in range(n_files)]
    concat_time, concat_result = measure_time(hash_concatenated_files, filenames)
    parallel_time, parallel_result = measure_time(
        hash_separate_files_parallel, filenames
    )
    return concat_time, parallel_time, concat_result, parallel_result


def main():
    n_files = 50  # Количество файлов
    file_size = 1024 * 1024  # Размер файла в байтах (1 МБ)

    generate_test_files(n_files, file_size)

    results = run_experiment(n_files, file_size)

    print(f"Time for concatenated files: {results[0]:.4f} seconds")
    print(f"Time for parallel separate files: {results[1]:.4f} seconds")
    print(f"Concatenated result: {results[2]}")
    print(f"Parallel result: {results[3]}")


if __name__ == "__main__":
    main()
