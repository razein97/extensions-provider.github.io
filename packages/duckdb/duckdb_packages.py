
from typing import Any, Dict, List
import requests
import yaml
import base64

from packages.common import parse_local_pkg, save_json, GitHubAPIClient


def fetch_duckdb_packages():
    # All extensions are hosted on github hence we need to visit the repo in order to get the extension details
    duckdb_git_tree = "https://api.github.com/repos/duckdb/community-extensions/git/trees/86761d118e803aeafd02ad4aac735d95fa81d301";
    client = GitHubAPIClient();
      # Check initial rate limit
    client.check_rate_limit()
    # Check if token exists
    if not client.token:
        print("ERROR: No token found!")
        exit(1)
    try:
        tree_json:Dict[Any, Any] = client.get(duckdb_git_tree);

        tree: List[Dict[Any, Any]] = tree_json['tree'];

        parsed_data : List[Dict[Any, Any]] = [];

        for branch in tree:
            stem_url = branch['url'];
            try:
                leaf_json= client.get(stem_url);
                leaves: List[Dict[Any, Any]] = leaf_json['tree'];
                for leaf in leaves:
                    if leaf['path'] == "description.yml":   
                        try:
                            binary_url = leaf['url'];
                            base64_json = client.get(binary_url);
                            # remove the \n in the content
                            base_64_content:str = base64_json["content"];
                            replaced_content = base_64_content.replace("\\n", '');
                            decoded =  base64.b64decode(replaced_content);
                            item = yaml.safe_load(decoded);
                            ext = item['extension'];
                            if item is not None:
                                ready_item:Dict[Any, Any] = {};
                                count = len(parsed_data);
                                repo = item.get('repo', '');
                                repo_name = repo.get('github', '');
                                repository = f"https://github.com/{repo_name}"

                                ready_item.update({
                                    'id':count, 
                                    'fullname': repo_name,
                                    'name': ext.get('name', ''),
                                    'version': str(ext.get('version', '')),
                                    'homepage': "",
                                    'repository': repository,
                                    'authors': ext.get("maintainers", ''),
                                    'license': ext.get('license') or ext.get('licence', ''),
                                    "description": ext.get('description', ''),
                                    'keywords': '',
                                    'symbols': [],
                                    'assets':{}
                                    });
                        
                                parsed_data.append(ready_item);

                        except requests.exceptions.RequestException as e:
                            print(f"Error fetching data: {e}")
                            return {}                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching data: {e}")
                return {}


        items_len = len(parsed_data);
        parsed_local_items = parse_local_pkg(items_len, './packages/duckdb/packages.yaml');
        joined_list = parsed_data + parsed_local_items;
        save_json(joined_list, "./json/duckdb.json")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return {}





