import sqlite3, re
from datetime import datetime
from dataclasses import dataclass
from typing import TextIO
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
# TODO : Batch processing, writting each line to db is slow af.

@dataclass # TODO : should be frozen
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


def record_installed(entry: LogFeatures, db_path: Path) -> None:
    """Called to write into the db if a package was installed"""
    is_installed = True
    is_dependency = False  # TODO not yet implemented
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            sqlcmd.INSERT_INSTALLED, (
                entry.package_name,
                entry.version,
                entry.timestamp,
                entry.timestamp,
                is_installed,
                is_dependency
            )
        )


def record_removed(entry: LogFeatures, db_path: Path) -> None:
    """Called to write into the db if a package was removed"""
    is_installed = False
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            sqlcmd.UPDATE_REMOVED,
            (
                entry.version,
                is_installed,
                entry.timestamp,
                entry.package_name,
            )
        )


def record_upgraded(entry: LogFeatures, db_path: Path) -> None:
    """Called to write into the db if a package was upgraded"""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            sqlcmd.UPDATE_UPGRADED,
            (
                entry.version,
                entry.timestamp,
                entry.package_name,
            )
        )


# Parser


def parse_log_entry(line: str) -> LogFeatures | None:
# TODO: DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
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


def collect_log_files(log_file: TextIO, db_path: Path) -> None:
    """
    Collects the features of each line within the log file to memory.
    Handles writting to db based on the action
    taken by pacman: "installed", "updated", or "removed".
    """
    installed_entries = []
    upgraded_entries = []
    removed_entries = []
    
    for line in log_file:
        entry = parse_log_entry(line)
        if entry is None:
            continue
        if entry.action == "installed":
            installed_entries.append(entry)
        elif entry.action == "upgraded":
            upgraded_entries.append(entry)
        elif entry.action == "removed":
            removed_entries.append(entry)
        else:
            print("Parsing error!")
            return None
    
    record_installed(installed_entries)
    record_upgraded(upgraded_entries)
    record_removed(removed_entries)