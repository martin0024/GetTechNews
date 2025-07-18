import os
import json
import feedparser
import asyncio
import subprocess
from discord_webhook import DiscordWebhook
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import openai
from xml.etree.ElementTree import Element, SubElement, tostring
import datetime

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

with open("news.json") as f:
    sources = json.load(f)

os.makedirs("feeds", exist_ok=True)
os.makedirs("scrapers", exist_ok=True)

def log_error(msg):
    print(f"[ERROR] {msg}")
    try:
        webhook = DiscordWebhook(url=WEBHOOK_URL, content=f"⚠️ Error: {msg}")
        webhook.execute()
    except:
        pass

async def fetch_html(url):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            html = await page.content()
            await browser.close()
            return html
    except Exception as e:
        log_error(f"Playwright failed for {url}: {e}")
        return ""

def generate_scraper(site_name, html):
    try:
        prompt = f"""
You are a Python developer. Generate a script that extracts article titles, publication dates (if available), and links from the following blog HTML page.
Return Python code that prints a list of dictionaries like:
[{{"title": ..., "link": ..., "date": ...}}, ...]

HTML:
{html[:4000]}
"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        log_error(f"OpenAI generation failed for {site_name}: {e}")
        return None

def commit_scraper(name):
    try:
        subprocess.run(["git", "config", "--global", "user.name", "github-actions"])
        subprocess.run(["git", "config", "--global", "user.email", "github-actions@github.com"])
        subprocess.run(["git", "add", f"scrapers/{name}.py"])
        subprocess.run(["git", "commit", "-m", f"🤖 Add scraper for {name}"], check=False)
        subprocess.run(["git", "push"], check=False)
    except Exception as e:
        log_error(f"Git commit failed for {name}: {e}")

def build_rss(articles, site, url):
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = site
    SubElement(channel, "link").text = url
    SubElement(channel, "description").text = f"{site} custom RSS feed"
    for a in articles:
        item = SubElement(channel, "item")
        SubElement(item, "title").text = a["title"]
        SubElement(item, "link").text = a["link"]
        SubElement(item, "pubDate").text = a.get("date", str(datetime.datetime.utcnow()))
    return tostring(rss, encoding="utf-8")

def save_rss(site, url, articles):
    data = build_rss(articles, site, url)
    path = f"feeds/{site}.xml"
    with open(path, "wb") as f:
        f.write(data)

def notify_discord(content):
    webhook = DiscordWebhook(url=WEBHOOK_URL, content=content)
    webhook.execute()

async def main():
    for source in sources:
        name = source["name"].lower()
        url = source["url"]
        rss_url = source.get("rss")

        if rss_url:
            try:
                feed = feedparser.parse(rss_url)
                if feed.entries:
                    latest = feed.entries[0]
                    seen_path = f"feeds/seen_{name}.json"
                    seen = []
                    if os.path.exists(seen_path):
                        with open(seen_path) as f:
                            seen = json.load(f)
                    if latest.link not in seen:
                        seen.append(latest.link)
                        with open(seen_path, "w") as f:
                            json.dump(seen, f, indent=2)
                        notify_discord(f"📰 New article on {name.title()}: {latest.title} → {latest.link}")
            except Exception as e:
                log_error(f"RSS parsing failed for {name}: {e}")
        else:
            scraper_path = f"scrapers/{name}.py"
            if not os.path.exists(scraper_path):
                html = await fetch_html(url)
                code = generate_scraper(name, html)
                if code:
                    with open(scraper_path, "w") as f:
                        f.write(code)
                    commit_scraper(name)

            try:
                result = os.popen(f"python scrapers/{name}.py").read()
                articles = json.loads(result)
                seen_path = f"feeds/seen_{name}.json"
                seen = []
                if os.path.exists(seen_path):
                    with open(seen_path) as f:
                        seen = json.load(f)
                for article in articles:
                    if article['link'] not in seen:
                        seen.append(article['link'])
                        notify_discord(f"📰 New article on {name.title()}: {article['title']} → {article['link']}")
                with open(seen_path, "w") as f:
                    json.dump(seen, f, indent=2)
                save_rss(name, url, articles)
            except Exception as e:
                log_error(f"Scraper failed for {name}: {e}")

if __name__ == "__main__":
    asyncio.run(main())