from typing import Any, Dict, Optional

import requests
from packages.duckdb.duckdb_packages import fetch_duckdb_packages
from packages.sqlite.sqlite_packages import fetch_sqlite_packages;



def main():
    fetch_sqlite_packages()
    fetch_duckdb_packages()


if __name__ == "__main__":
    main()