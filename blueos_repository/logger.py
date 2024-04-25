import dataclasses
import json
from enum import StrEnum
from typing import Dict, List, Optional

from docker.models.limit import RateLimit
from utils import EnhancedJSONEncoder


class LogEntryStatus(StrEnum):
    """
    Enum for log status
    """

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclasses.dataclass
class LogEntry:
    """
    Represents a log entry in the manifest log

    Attributes:
        status (str): The status of the log entry.
        message (str): The message of the log entry.
    """

    status: LogEntryStatus
    message: str


@dataclasses.dataclass
class ManifestLog:
    """
    Represents the data logged during the consolidation process
    """

    start_docker_rate_limit: Optional[RateLimit] = None
    final_docker_rate_limit: Optional[RateLimit] = None

    extensions: Dict[str, List[LogEntry]] = dataclasses.field(default_factory=dict)


class Logger:
    """
    Simple logger class to consolidate logs and generate a manifest.log
    """

    log_buffer: ManifestLog = ManifestLog()

    @staticmethod
    def start_docker_rate_limit(rate_limit: RateLimit) -> None:
        """
        Log the initial Docker rate limit
        """

        Logger.log_buffer.start_docker_rate_limit = rate_limit

    @staticmethod
    def final_docker_rate_limit(rate_limit: RateLimit) -> None:
        """
        Log the final Docker rate limit
        """

        Logger.log_buffer.final_docker_rate_limit = rate_limit

    @staticmethod
    def _check_and_init_entry(entry: str) -> None:
        """
        Check if an entry exists in the log buffer, if not create it

        Args:
            entry (str): The entry identifier.
        """

        if entry not in Logger.log_buffer.extensions:
            Logger.log_buffer.extensions[entry] = []

    @staticmethod
    def log(entry: str, message: str, level: LogEntryStatus) -> None:
        Logger._check_and_init_entry(entry)
        Logger.log_buffer.extensions[entry].append(LogEntry(level, message))

    @staticmethod
    def info(entry: str, message: str) -> None:
        Logger.log(entry, message, LogEntryStatus.INFO)

    @staticmethod
    def warning(entry: str, message: str) -> None:
        Logger.log(entry, message, LogEntryStatus.WARNING)

    @staticmethod
    def error(entry: str, message: str) -> None:
        Logger.log(entry, message, LogEntryStatus.ERROR)

    @staticmethod
    def dump(file_name: str) -> None:
        """
        Dump the log buffer to a file

        Args:
            file_name (str): The file name to dump the log buffer
        """

        with open(file_name, "w") as log_file:
            log_file.write(
                json.dumps(dataclasses.asdict(Logger.log_buffer), indent=4, sort_keys=True, cls=EnhancedJSONEncoder)
            )
