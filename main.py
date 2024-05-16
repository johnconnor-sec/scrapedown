import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, unquote
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def get_domain(url):
    parsed = urlparse(url)
    return parsed.netloc

def same_domain(url, domain):
    return get_domain(url) == domain

def extract_links(session, url, domain):
    try:
        response = session.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Failed to retrieve {url}")
            return []
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if not is_valid_url(href):
                href = urljoin(url, href)
            if same_domain(href, domain):
                links.append(href)
        return links
    except Exception as e:
        print(f"Error extracting links from {url}: {e}")
        return []

def extract_text(session, url):
    try:
        response = session.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Failed to retrieve {url}")
            return ""
        soup = BeautifulSoup(response.content, 'html.parser')
        text = str(soup)
        return text
    except Exception as e:
        print(f"Error extracting text from {url}: {e}")
        return ""

def save_text_to_markdown(url, text, base_dir):
    parsed_url = urlparse(url)
    path = parsed_url.path.strip('/')
    path = unquote(path)
    filename = "index.md" if not path else os.path.basename(path) + ".md"
    directory = os.path.join(base_dir, os.path.dirname(path))
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_path = os.path.join(directory, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)

def process_page(session, url, domain, base_dir, depth):
    links = extract_links(session, url, domain)
    text = extract_text(session, url)
    save_text_to_markdown(url, text, base_dir)
    return (url, links, depth)

def crawl_and_scrape(start_url, base_dir, max_depth=3, max_workers=20):
    domain = get_domain(start_url)
    visited = set()
    to_visit = [(start_url, 0)]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while to_visit:
            futures = []
            for current_url, depth in to_visit:
                if depth > max_depth or current_url in visited:
                    continue
                visited.add(current_url)
                futures.append(executor.submit(process_page, requests.Session(), current_url, domain, base_dir, depth))

            to_visit = []
            for future in as_completed(futures):
                try:
                    url, links, depth = future.result()
                    print(f"Visited: {url}")
                    for link in links:
                        if link not in visited:
                            to_visit.append((link, depth + 1))
                except Exception as e:
                    print(f"Error processing page: {e}")
    print(f"Visited {len(visited)} pages.")
    return visited

# Example usage:
start_url = input("Enter the URL to start scraping: ")
if not start_url.startswith("https://") and not start_url.startswith("http://"):
    start_url = "https://" + start_url
base_dir = os.path.join(f"./scraped_{get_domain(start_url)}")
visited_pages = crawl_and_scrape(start_url, base_dir, max_depth=3)
print("Pages visited:", visited_pages)
