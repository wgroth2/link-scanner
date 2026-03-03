
# Copyright 2026 Bill Roth
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests
from bs4 import BeautifulSoup
import warnings
import re
import argparse
import csv
import sys
import logging

# Suppress the "Some characters could not be decoded" warning from BeautifulSoup
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

logger = logging.getLogger(__name__)


def get_sitemap_urls(sitemap_url, timeout=10):
    """
    Fetches the sitemap from the provided URL.
    If a sitemap index is detected, it recursively fetches child sitemaps.
    Returns a list of all URLs found in the sitemap(s).
    """
    urls = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(sitemap_url, headers=headers, timeout=timeout)
        if response.status_code >= 400:
            logger.error(f"Error: Website returned status code {response.status_code} ({response.reason})")
            return None
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml-xml")

        # Check for valid sitemap root tags
        is_index = soup.find("sitemapindex")
        is_urlset = soup.find("urlset")

        if not is_index and not is_urlset:
            return None

        if is_index:
            logger.info(f"Sitemap index detected: {sitemap_url}")
            for sitemap in soup.find_all("sitemap"):
                loc = sitemap.find("loc")
                if loc:
                    child_urls = get_sitemap_urls(loc.text.strip(), timeout=timeout)
                    if child_urls:
                        urls.extend(child_urls)
        else:
            # Standard sitemap, extract URLs from <url> tags
            for url_tag in soup.find_all("url"):
                loc = url_tag.find("loc")
                if loc:
                    urls.append(loc.text.strip())
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching sitemap: {e}")
        return None
    logger.info(f"URLs Found: {len(urls)}")
    return urls

def find_contact_links(url, search_string, silent=False, search_all=False, timeout=10):
    """
    Scans a single URL for the search_string.
    If search_all is True, searches the entire HTML text.
    Otherwise, searches only within the href attributes of <a> tags.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        # Skip 400-level errors (client errors) silently if requested
        if 400 <= response.status_code < 500:
            if not silent:
                logger.warning(f"Skip, URL: {url} Status Code: {response.status_code}")
            return False
        response.raise_for_status()

        # Ensure we are processing HTML content
        if "text/html" not in response.headers.get("Content-Type", "").lower():
            return False

        response.encoding = response.apparent_encoding
        if search_all:
            # Search the entire raw HTML text
            if re.search(search_string, response.text):
                return True
        else:
            # Parse HTML and search only in link hrefs
            soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.find_all("a", href=re.compile(search_string)):
                return True
    except requests.exceptions.Timeout:
        print(f"Timeout fetching {url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Exiting.")
        sys.exit(0)
    return False

if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Find links in a sitemap.")
    parser.add_argument("sitemap_url", help="The URL of the sitemap.")
    parser.add_argument("search_string", help="The string to search for in the links.")
    parser.add_argument("-s", "--silent", action="store_true", help="Suppress skip messages.")
    parser.add_argument("-a", "--all", action="store_true", help="Search the entire HTML text.")
    parser.add_argument("-t", "--timeout", type=int, default=10, help="Request timeout in seconds.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging to stdout.")
    parser.add_argument("-u", "--url", action="store_true", help="Print the URL as it is being scanned.")
    args = parser.parse_args()

    # Configure logging based on debug flag
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        stream=sys.stdout
    )

    x=1
    
    urls = get_sitemap_urls(args.sitemap_url, timeout=args.timeout)

    if urls is None:
        print(f"Error: The URL '{args.sitemap_url}' is not a valid sitemap or could not be reached.", file=sys.stderr)
        sys.exit(1)

    # Print status message based on search mode
    if args.all:
        print("Searching website text")
    else:
        print("Searching links in the website text")

    # Initialize CSV writer
    writer = csv.writer(sys.stdout)
    writer.writerow(["Index", "URL", "Found Text"])

    # Iterate through URLs and scan them
    for url in urls:
        if args.url:
            print(f"Scanning: {url}")

        if find_contact_links(url, args.search_string, args.silent, args.all, timeout=args.timeout):
            writer.writerow([x, url + " ", args.search_string])
            x+=1
            