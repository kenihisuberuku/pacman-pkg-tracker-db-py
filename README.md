## Pacman Package Tracker

A simple ~~and somewhat useless~~ script to parse Pacman log files (`/var/log/pacman.log`) and store it in a local SQLite database.

### Features

- Stores the modifications done (installation, removal, update) on a package, version, and timestamp from each log entry.
- COMING SOON! Shows the packages that are not explicitly installed (dependency).
- COMING SOON! Updates the DB for subsequent runs.

## Requires
Python 3.12

## Usage
Quickstart
1. Clone this repo.
2. Read the PIPFILE and make sure you have the appropriate version or run this using `pipenv`.
```bash
pipenv install
```
3. Copy your pacman logs to the same directory of `main,py`.
```bash
cp /var/log/pacman.log /path/to/main.py
```
4. Run the script
```bash
cd /path/to/main.py
python main.py
```
