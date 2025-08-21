import logging
from concurrent.futures.thread import ThreadPoolExecutor

from FileScanner import IScannerLogger

from AppLogger import AppLogger
from Hardlinker import Hardlinker

source: str = r"test\source"
target: str = r"test\target"
source_file = r"test\source_file\新建文本文档.txt"
target_file = r"test\target_file\A\新建文本文档.txt"
logger: IScannerLogger = AppLogger("HardlinkerLogger", level=logging.DEBUG)
with ThreadPoolExecutor(max_workers=10) as executor:
    linker: Hardlinker = Hardlinker(source_file, target_file, executor, logger)
    linker.hardlink()

