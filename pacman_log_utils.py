import sqlite3
import re
from datetime import datetime
from dataclasses import dataclass
from typing import Iterator
from pathlib import Path

import sqlcommands as sqlcmd


# Constants

LOG_PATTERN = re.compile(
    r"\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+\-]\d{4})\] "  # timestamp_str
    r"\[ALPM] "
    r"(installed|upgraded|removed) "  # action
    r"([^ ]+) "  # package_name
    r"\((.*)\)$"  # versions
)
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

# Helpers


def ask_to_console(question: str) -> bool:
    answer = input(question).lower()
    if (answer in ['y', 'yes', '']):
        print("Continuing...")
        return True
    else:
        print("Aborting operation.")
        return False


# Database interactions
# TODO : Feature to read only lines after a certain date for subsequent runs.
# TODO : (WIP) Batch processing.
# TODO : BUG: multiple entries caused by first being installed as dependency,
# then installed explicitly

@dataclass  # TODO : should be frozen
class LogFeatures:
    package_name: str
    action: str
    version: str
    timestamp: datetime


def prepare_db(db_path: Path) -> None:
    """Creates a SQLite database and log table if not exist."""
    if db_path.is_file():
        print(f"Database '{db_path}' already exists.")
        question = "Do you want to write to the existing database? [Y/n]: "
        answered_yes = ask_to_console(question)
        if not answered_yes:
            exit()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sqlcmd.CREATE_TABLE)
    print(f"Database '{db_path}' created.")


def record_installed(entries: list[LogFeatures], db_path: Path) -> None:
    """Called to write into the db if a package was installed"""
    is_installed = True
    is_dependency = False  # TODO not yet implemented
    repacked_entry = [(
        entry.package_name,
        entry.version,
        entry.timestamp,
        entry.timestamp,
        is_installed,
        is_dependency
    ) for entry in entries]
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany(sqlcmd.INSERT_INSTALLED, repacked_entry)


def record_removed(entries: list[LogFeatures], db_path: Path) -> None:
    """Called to write into the db if a package was removed"""
    is_installed = False
    repacked_entry = [(
        is_installed,
        entry.timestamp,
        entry.package_name,
        entry.timestamp
    ) for entry in entries]
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany(sqlcmd.UPDATE_REMOVED, repacked_entry)


def record_upgraded(entries: list[LogFeatures], db_path: Path) -> None:
    """Called to write into the db if a package was upgraded"""
    repacked_entry = [(
        entry.version,
        entry.timestamp,
        entry.package_name,
        True,
    ) for entry in entries]
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany(sqlcmd.UPDATE_UPGRADED, repacked_entry)


# Parser


def parse_log_entry(line: str) -> LogFeatures | None:
    # TODO: DeprecationWarning: The default datetime adapter is deprecated
    # as of Python 3.12; see the sqlite3 documentation for
    # suggested replacement recipes
    """Parses /var/log/pacman.log according to this format
    [%YYYY-%MM-%ddT%hh:%mm:%ss%t] [ALPM] action package-name (version)
    (https://doc.qt.io/qt-6/qml-qtqml-qt.html#formatDateTime-method)
    """
    match = LOG_PATTERN.search(line)
    if match is None:
        return None
    timestamp_str, action, package_name, versions = match.groups()
    timestamp = datetime.strptime(timestamp_str, TIMESTAMP_FORMAT)
    version = versions.split("-> ", 1)[1] if "-> " in versions else versions

    return LogFeatures(package_name, action, version, timestamp)


# Main Process Lines


def collect_log_in_batch(
    log_path: Path,
    batch_size: int = 500
) -> Iterator[list[LogFeatures]]:
    """Reads the log entries in batches"""
    batch_entries = []
    with open(log_path, 'r') as log_file:
        for count, line in enumerate(log_file, 1):
            entry = parse_log_entry(line)
            if entry is None:
                continue
            batch_entries.append(entry)
            if count % batch_size == 0:
                yield batch_entries
                batch_entries = []
        if batch_entries is not None:
            yield batch_entries


def process_log_file(log_path: Path, db_path: Path):
    """
    Collects the features of each line within the log file to memory.
    Handles writting to db based on the action
    taken by pacman: "installed", "updated", or "removed".
    """
    for batch in collect_log_in_batch(log_path):
        record_installed(
            [entry for entry in batch if entry.action == "installed"],
            db_path
        )
        record_removed(
            [entry for entry in batch if entry.action == "removed"],
            db_path
        )
        record_upgraded(
            [entry for entry in batch if entry.action == "upgraded"],
            db_path
        )
