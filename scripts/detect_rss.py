import requests
from bs4 import BeautifulSoup

with open("news.txt") as f:
    urls = [line.strip() for line in f if line.strip()]

for url in urls:
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        rss = soup.find("link", type="application/rss+xml")
        if rss:
            print(f"[RSS] {url} → {rss['href']}")
        else:
            print(f"[NO RSS] {url}")
    except Exception as e:
        print(f"[ERROR] {url}: {e}")