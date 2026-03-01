
import requests
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
import warnings
import re
import argparse
import csv
import sys

# Suppress the "Some characters could not be decoded" warning from BeautifulSoup
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')



def get_sitemap_urls(sitemap_url):
    urls = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(sitemap_url, headers=headers)
        if response.status_code >= 400:
            print(f"Error: Website returned status code {response.status_code} ({response.reason})")
            return []
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml-xml")

        if soup.find("sitemapindex"):
            print(f"Sitemap index detected: {sitemap_url}")
            for sitemap in soup.find_all("sitemap"):
                loc = sitemap.find("loc")
                if loc:
                    urls.extend(get_sitemap_urls(loc.text.strip()))
        else:
            for loc in soup.find_all("loc"):
                urls.append(loc.text.strip())
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sitemap: {e}")
    print("URLs Found: ", len(urls))
    return urls

def find_contact_links(url, search_string, silent=False, search_all=False):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers)
        if 400 <= response.status_code < 500:
            if not silent:
                print("Skip, URL: ", url, " Status Code: ", response.status_code, file=sys.stderr)
            return False
        response.raise_for_status()

        if "text/html" not in response.headers.get("Content-Type", "").lower():
            return False

        response.encoding = response.apparent_encoding
        if search_all:
            if re.search(search_string, response.text):
                return True
        else:
            soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.find_all("a", href=re.compile(search_string)):
                return True
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find links in a sitemap.")
    parser.add_argument("sitemap_url", help="The URL of the sitemap.")
    parser.add_argument("search_string", help="The string to search for in the links.")
    parser.add_argument("-s", "--silent", action="store_true", help="Suppress skip messages.")
    parser.add_argument("-a", "--all", action="store_true", help="Search the entire HTML text.")
    args = parser.parse_args()
    x=1
    
    urls = get_sitemap_urls(args.sitemap_url)

    if args.all:
        print("Searching website text")
    else:
        print("Searching links in the website text")

    writer = csv.writer(sys.stdout)
    writer.writerow(["Index", "URL", "Found Text"])

    for url in urls:
       
        if find_contact_links(url, args.search_string, args.silent, args.all):
            writer.writerow([x, url, args.search_string])
            x+=1
            