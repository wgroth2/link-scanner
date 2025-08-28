
import requests
from bs4 import BeautifulSoup
import re
import argparse

def get_sitemap_urls(sitemap_url):
    urls = []
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "xml")
        for loc in soup.find_all("loc"):
            urls.append(loc.text.strip())
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sitemap: {e}")
    print("URLs Found: ", len(urls))
    return urls

def find_contact_links(url, search_string):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        for link in soup.find_all("a", href=re.compile(search_string)):
            return True
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find links in a sitemap.")
    parser.add_argument("sitemap_url", help="The URL of the sitemap.")
    parser.add_argument("search_string", help="The string to search for in the links.")
    args = parser.parse_args()
    x=0
    
    urls = get_sitemap_urls(args.sitemap_url)
    for url in urls:
       
        if find_contact_links(url, args.search_string):
            print(x,": ", url, " has the text ", args.search_string)
            x+=1
