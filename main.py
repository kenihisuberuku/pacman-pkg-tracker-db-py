import pacman_log_utils as utils
from pathlib import Path


def main() -> None:
    # TODO : Path is still hardcoded.
    CURR_PATH = Path("__file__").parent
    DB_NAME = "pacman-pkgs.db"
    DB_PATH = CURR_PATH / DB_NAME
    LOG_NAME = "pacman.log"
    utils.prepare_db(DB_PATH)
    print("Processing database...")
    with open(LOG_NAME, 'r') as log_file:
        utils.process_log_file(log_file, DB_PATH)
    print("Completed.")


if __name__ == "__main__":
    main()
