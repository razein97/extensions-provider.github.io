from typing import Any, Dict, List
import requests

from packages.common import parse_local_pkg, save_json


def fetch_sqlite_packages():
    sql_pkg_url = "https://sqlpkg.org/data/packages.json"
    
    try:
        response = requests.get(sql_pkg_url, timeout=10)
        response.raise_for_status()  # Raise exception for bad status codes
        sql_pkg_json: List[Dict[Any, Any]] = response.json();

        items_len = len(sql_pkg_json);
        parsed_local_items = parse_local_pkg(items_len, "./packages/sqlite/packages.yaml");
        joined_list = sql_pkg_json + parsed_local_items;
        save_json(joined_list, "./json/sqlite.json")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return {}



