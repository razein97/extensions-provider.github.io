

import json
from typing import Any, Dict, List
import yaml


def parse_local_pkg(last_item_count: int, path: str)->List[Dict[Any, Any]]:
    with open(path) as stream:
        try:
            items = [];
            loaded_items = yaml.safe_load(stream);
            if loaded_items is not None and len(loaded_items) > 0:
                for idx, item in enumerate(loaded_items):
                    item['id'] = last_item_count + idx;
                    items.append(item)

            return items

        except yaml.YAMLError as exc:
            print(exc)
            return[]
        

def save_json(data: List[Dict[Any, Any]], filename: str) -> None:
 
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filename}")
    except IOError as e:
        print(f"Error saving file: {e}")