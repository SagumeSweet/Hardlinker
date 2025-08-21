import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from FileScanner import IProcesser, BaseProcessResult, FolderScanner, IScannerLogger


class Hardlinker:
    def __init__(self, source: Path | str, target: Path | str, executor: ThreadPoolExecutor, logger: IScannerLogger, retry_count: int = 3) -> None:
        self._source: Path = Path(source)
        self._target: Path = Path(target)
        self.logger: IScannerLogger = logger
        self._executor: ThreadPoolExecutor = executor
        self.retry_count: int = retry_count

    def _create_dir_hardlink(self, source_file: Path) -> None:
        relative_file_path: Path = source_file.relative_to(self._source)
        target_file_path: Path = self._target / relative_file_path
        target_file_path.parent.mkdir(parents=True, exist_ok=True)
        target_file_path.hardlink_to(source_file)

    def _create_file_hardlink(self) -> None:
        if not self._target.parent.exists():
            self._target.parent.mkdir(parents=True, exist_ok=True)
        self._target.hardlink_to(self._source)

    def _try_to_create_hardlink(self, source_file: Path, create_hardlink_func: Callable[[], None], count=0) -> None:
        """尝试创建硬链接"""
        self.logger.debug(f"Attempting to create hard link for {source_file.resolve()}")
        try:
            create_hardlink_func()
            self.logger.info(f"Created hard link for {source_file.resolve()}")
        except PermissionError:
            time.sleep(3)
            if count < self.retry_count:
                self.logger.warning(f"PermissionError: Failed to create hard link for {source_file.resolve()}, retrying... (Attempt {count + 1}/{self.retry_count})")
                self._try_to_create_hardlink(source_file, create_hardlink_func, count + 1)
            else:
                raise PermissionError(f"Failed to create hard link for {source_file.resolve()} after {self.retry_count} attempts.")

    def hardlink(self):
        try_to_create_hardlink_func = self._try_to_create_hardlink
        create_dir_hardlink_func = self._create_dir_hardlink

        class HardLinkProcessResult(BaseProcessResult):
            def __init__(self, data: list) -> None:
                super().__init__(data)

            def _add(self, other: "BaseProcessResult") -> "BaseProcessResult":
                new_list: list = self._data.copy()
                new_list.extend(other.data)
                return HardLinkProcessResult(new_list)

            def _iadd(self, other: "BaseProcessResult") -> None:
                self._data.extend(other.data)

        class HardLinkProcess(IProcesser):
            def process(self, path: Path) -> BaseProcessResult:
                """处理数据，返回处理结果"""

                def do() -> None:
                    create_dir_hardlink_func(path)

                try_to_create_hardlink_func(path, do)
                process_result = HardLinkProcessResult([path])
                return process_result

            @property
            def empty_process_result(self) -> BaseProcessResult:
                """返回一个空的处理结果"""
                return HardLinkProcessResult([])

        if self._source.is_dir():
            self.logger.info(f"Creating hard links for directory: {self._source.resolve()} to {self._target.resolve()}")
            processer = HardLinkProcess()
            scanner = FolderScanner(self._source, self._executor, self.logger, processer)
            result = scanner.scan()
            self.logger.info(f"Created hard links for {len(result.data)} files in directory {self._source.resolve()}")
        elif self._source.is_file():
            self.logger.info(f"Creating hard link for file: {self._source.resolve()} to {self._target.resolve()}")
            try_to_create_hardlink_func(self._source, self._create_file_hardlink)
            self.logger.info(f"Created hard link for file {self._source.resolve()} to {self._target.resolve()}")
