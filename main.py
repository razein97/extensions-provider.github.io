import base64
import os
import time
from typing import Any, Dict, Optional

import requests
from packages.duckdb.duckdb_packages import fetch_duckdb_packages
from packages.sqlite.sqlite_packages import fetch_sqlite_packages;

class GitHubAPIClient:
    """GitHub API client with rate limit handling."""
    
    def __init__(self, token: Optional[str] = None):
        self.base_url = "https://api.github.com"
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            })
    
    def check_rate_limit(self) -> Dict[str, Any]:
        """Check current rate limit status."""
        response = self.session.get(f"{self.base_url}/rate_limit")
        return response.json()
    
    def wait_if_rate_limited(self, response: requests.Response) -> None:
        """
        Check rate limit headers and wait if necessary.
        
        Args:
            response: Response object from requests
        """
        remaining = int(response.headers.get('X-RateLimit-Remaining', 1))
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        
        if remaining == 0:
            wait_time = reset_time - time.time() + 10  # Add 10s buffer
            if wait_time > 0:
                print(f"Rate limit reached. Waiting {wait_time:.0f} seconds...")
                time.sleep(wait_time)
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[Any, Any]:
    
        url = endpoint
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            # Check and handle rate limiting
            self.wait_if_rate_limited(response)
            
            # Handle 403 (rate limit exceeded)
            if response.status_code == 403:
                rate_limit_info = self.check_rate_limit()
                core_limit = rate_limit_info['resources']['core']
                reset_time = core_limit['reset'] - time.time()
                print(f"Rate limited. Resets in {reset_time:.0f} seconds")
                time.sleep(reset_time + 10)
                # Retry request
                response = self.session.get(url, params=params, timeout=10)
            
            response.raise_for_status()
            
            # Add small delay between requests to be nice
            time.sleep(0.1)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return {}


def main():
    fetch_sqlite_packages()
    fetch_duckdb_packages()


if __name__ == "__main__":
    main()