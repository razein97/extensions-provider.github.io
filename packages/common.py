

import json
import os
import time
from typing import Any, Dict, List, Optional
import requests
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


class GitHubAPIClient:
    """GitHub API client with rate limit handling."""
    
    def __init__(self, token: Optional[str] = None):
        self.base_url = "https://api.github.com"
        self.token = token or os.getenv("GIT_TOKEN")
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            })
        
        # Track rate limit state
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
    
    def check_rate_limit(self) -> Dict[str, Any]:
        """Check current rate limit status."""
        response = self.session.get(f"{self.base_url}/rate_limit")
        return response.json()
    
    def update_rate_limit_from_headers(self, response: requests.Response) -> None:
        """Update rate limit state from response headers."""
        self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))
    
    def wait_for_rate_limit_reset(self) -> None:
        """Wait until rate limit resets."""
        if self.rate_limit_reset:
            wait_time = self.rate_limit_reset - time.time() + 5  # Add 5s buffer
            if wait_time > 0:
                print(f"Rate limit reached. Waiting {wait_time:.0f} seconds...")
                time.sleep(wait_time)
    
    def check_before_request(self) -> None:
        """Check rate limit before making request and wait if needed."""
        if self.rate_limit_remaining is not None and self.rate_limit_remaining < 10:
            print(f"Only {self.rate_limit_remaining} requests remaining. Checking rate limit...")
            rate_limit_info = self.check_rate_limit()
            core_limit = rate_limit_info['resources']['core']
            
            if core_limit['remaining'] < 10:
                reset_time = core_limit['reset']
                wait_time = reset_time - time.time() + 5
                if wait_time > 0:
                    print(f"Preemptively waiting {wait_time:.0f} seconds before rate limit hits...")
                    time.sleep(wait_time)
    
    def get(self, endpoint: str, params: Optional[Dict] = None, max_retries: int = 3) -> Dict[Any, Any]:
        """
        Make GET request with rate limit handling and retries.
        
        Args:
            endpoint: API endpoint URL
            params: Query parameters
            max_retries: Maximum number of retry attempts
        """
        url = endpoint
        
        for attempt in range(max_retries):
            try:
                # Check rate limit before request
                self.check_before_request()
                
                response = self.session.get(url, params=params, timeout=30)
                
                # Update rate limit tracking
                self.update_rate_limit_from_headers(response)
                
                # Handle rate limiting (403 or 429)
                if response.status_code in (403, 429):
                    print(f"Rate limited (status {response.status_code}), attempt {attempt + 1}/{max_retries}")
                    
                    # Check if it's actually rate limiting
                    if 'X-RateLimit-Remaining' in response.headers:
                        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                        if remaining == 0:
                            self.wait_for_rate_limit_reset()
                            continue  # Retry after waiting
                    
                    # Generic wait and retry
                    wait_time = min(2 ** attempt * 5, 60)  # Exponential backoff, max 60s
                    print(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                
                # Handle other client errors
                if response.status_code == 404:
                    print(f"Resource not found: {url}")
                    return {}
                
                response.raise_for_status()
                
                # Add delay between successful requests
                time.sleep(0.5)  # Increased from 0.1 to 0.5 seconds
                
                return response.json()
                
            except requests.exceptions.Timeout:
                print(f"Timeout on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {}
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching data (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {}
        
        print(f"Failed after {max_retries} attempts")
        return {}