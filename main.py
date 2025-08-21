import logging
from concurrent.futures.thread import ThreadPoolExecutor

from FileScanner import IScannerLogger

from AppLogger import AppLogger
from Hardlinker import Hardlinker


def main():
    source: str = input("输入源文件/夹: ")
    target: str = input("输入目标文件/夹: ")

    logger: IScannerLogger = AppLogger("HardlinkerLogger", level=logging.DEBUG)
    with ThreadPoolExecutor(max_workers=10) as executor:
        linker: Hardlinker = Hardlinker(source, target, executor, logger)
        linker.hardlink()

if __name__ == "__main__":
    main()
