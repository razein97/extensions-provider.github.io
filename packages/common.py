

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


import logging
from datetime import datetime

class GitHubAPIClient:
    """GitHub API client with rate limit handling."""
    
    def __init__(self, token: Optional[str] = None):
        self.base_url = "https://api.github.com"
        self.token = token or os.getenv("GIT_TOKEN")
        self.session = requests.Session()
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
        
        if self.token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            })
            self.logger.info("GitHub API client initialized with token")
        else:
            self.logger.warning("No token provided - rate limits will be very restrictive!")
        
        # Track rate limit state
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self.request_count = 0
    
    def check_rate_limit(self) -> Dict[str, Any]:
        """Check current rate limit status."""
        self.logger.info("Checking rate limit status...")
        response = self.session.get(f"{self.base_url}/rate_limit")
        data = response.json()
        
        core = data['resources']['core']
        self.logger.info(f"Rate limit: {core['remaining']}/{core['limit']} remaining, "
                        f"resets at {datetime.fromtimestamp(core['reset']).strftime('%H:%M:%S')}")
        return data
    
    def update_rate_limit_from_headers(self, response: requests.Response) -> None:
        """Update rate limit state from response headers."""
        self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))
        
        if self.rate_limit_remaining < 100:
            reset_time = datetime.fromtimestamp(self.rate_limit_reset).strftime('%H:%M:%S')
            self.logger.warning(f"Rate limit low: {self.rate_limit_remaining} remaining (resets at {reset_time})")
    
    def wait_for_rate_limit_reset(self) -> None:
        """Wait until rate limit resets."""
        if self.rate_limit_reset:
            wait_time = self.rate_limit_reset - time.time() + 5
            if wait_time > 0:
                reset_time = datetime.fromtimestamp(self.rate_limit_reset).strftime('%H:%M:%S')
                self.logger.warning(f"Rate limit exhausted. Waiting {wait_time:.0f}s until {reset_time}")
                
                # Log progress every 30 seconds
                elapsed = 0
                while elapsed < wait_time:
                    sleep_duration = min(30, wait_time - elapsed)
                    time.sleep(sleep_duration)
                    elapsed += sleep_duration
                    if elapsed < wait_time:
                        remaining = wait_time - elapsed
                        self.logger.info(f"Still waiting... {remaining:.0f}s remaining")
    
    def check_before_request(self) -> None:
        """Check rate limit before making request and wait if needed."""
        if self.rate_limit_remaining is not None and self.rate_limit_remaining < 10:
            self.logger.warning(f"Only {self.rate_limit_remaining} requests remaining. Checking...")
            rate_limit_info = self.check_rate_limit()
            core_limit = rate_limit_info['resources']['core']
            
            if core_limit['remaining'] < 10:
                reset_time = core_limit['reset']
                wait_time = reset_time - time.time() + 5
                if wait_time > 0:
                    self.logger.warning(f"Preemptively waiting {wait_time:.0f}s...")
                    time.sleep(wait_time)
    
    def get(self, endpoint: str, params: Optional[Dict] = None, max_retries: int = 3) -> Dict[Any, Any]:
        """Make GET request with rate limit handling and retries."""
        url = endpoint
        self.request_count += 1
        
        self.logger.info(f"Request #{self.request_count}: {url}")
        
        for attempt in range(max_retries):
            try:
                # Check rate limit before request
                self.check_before_request()
                
                response = self.session.get(url, params=params, timeout=30)
                
                # Update rate limit tracking
                self.update_rate_limit_from_headers(response)
                
                # Handle rate limiting
                if response.status_code in (403, 429):
                    self.logger.error(f"Rate limited! Status {response.status_code}, attempt {attempt + 1}/{max_retries}")
                    
                    if 'X-RateLimit-Remaining' in response.headers:
                        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                        if remaining == 0:
                            self.wait_for_rate_limit_reset()
                            continue
                    
                    wait_time = min(2 ** attempt * 5, 60)
                    self.logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                
                if response.status_code == 404:
                    self.logger.warning(f"Resource not found: {url}")
                    return {}
                
                response.raise_for_status()
                self.logger.info(f"Request #{self.request_count} completed successfully")
                
                time.sleep(0.5)
                return response.json()
                
            except requests.exceptions.Timeout:
                self.logger.error(f"Timeout on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {}
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {}
        
        self.logger.error(f"Failed after {max_retries} attempts")
        return {}