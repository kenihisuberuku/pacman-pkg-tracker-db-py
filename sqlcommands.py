CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    installed_on TEXT NOT NULL,
    last_modified TEXT NOT NULL,
    is_installed BOOLEAN NOT NULL,
    is_dependency BOOLEAN NOT NULL
)
"""

INSERT_INSTALLED = """
    INSERT OR REPLACE INTO packages (
        name,
        version,
        installed_on,
        last_modified,
        is_installed,
        is_dependency
    )
    VALUES (?, ?, ?, ?, ?, ?)
"""

UPDATE_REMOVED = """
    UPDATE packages
    SET (version, is_installed, last_modified) = (?, ?, ?)
    WHERE name=?
"""

UPDATE_UPGRADED = """
    UPDATE packages
    SET version=?, last_modified=?
    WHERE name=?
"""
