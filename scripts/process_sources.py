import os
import json
import feedparser
import asyncio
import subprocess
from discord_webhook import DiscordWebhook
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from xml.etree.ElementTree import Element, SubElement, tostring
import datetime
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            html = await page.content()
            logging.info(f"Fetched HTML for {url}")
            logging.info(f"HTML length: {len(html)} characters")
            await browser.close()
            return html
    except Exception as e:
        log_error(f"Playwright failed for {url}: {e}")
        return ""

async def generate_scraper(site_name, html, url):
    try:
        prompt = f"""You are a Python developer. Generate ONLY the Python code with no explanation or markdown formatting.

Create a Python script that:
- Uses the `requests` library to fetch HTML from the target URL: {url}
- Uses `BeautifulSoup` to parse the HTML
- Extracts all articles from the page, getting the title, link (full URL), and publication date if available
- Outputs the extracted data as JSON using: print(json.dumps(articles, indent=2))

Return ONLY the Python code, no explanation, no markdown blocks, no comments explaining what the code does.

HTML structure sample:
{html[:8000]}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a code generator. Return only Python code with no explanation, no markdown formatting, no code blocks. The code should be ready to execute directly."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        code = response.choices[0].message.content.strip()
        
        if code.startswith("```python"):
            code = code[9:]
        if code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        
        lines = code.split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                start_idx = i
                break
        
        if start_idx > 0:
            code = '\n'.join(lines[start_idx:])
        
        return code.strip()
    except Exception as e:
        log_error(f"OpenAI generation failed for {site_name}: {e}")
        return None

def commit_scraper(name):
    logging.info(f"Committing scraper for {name}")
    try:
        subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"])
        subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"])
        subprocess.run(["git", "add", f"scrapers/{name}.py"])
        subprocess.run(["git", "add", f"feeds/seen_{name}.json"])
        subprocess.run(["git", "commit", "-m", f"🤖 Add scraper and seen file for {name}"], check=False)
        subprocess.run(["git", "push"], check=False)
    except Exception as e:
        log_error(f"Git commit failed for {name}: {e}")

def commit_seen(name):
    logging.info(f"Committing seen articles for {name}")
    try:
        subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"])
        subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"])
        subprocess.run(["git", "add", f"feeds/seen_{name}.json"])
        subprocess.run(["git", "commit", "-m", f"🤖 Update seen articles for {name}"], check=False)
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
            logging.info(f"Processing RSS feed for {name} from {rss_url}")
            try:
                feed = feedparser.parse(rss_url)
                if feed.entries:
                    logging.info(f"[{name}] Latest: {feed.entries[0].title}")
                    latests = feed.entries[:10]
                    seen_path = f"feeds/seen_{name}.json"
                    logging.info(f"[{name}] Seen articles file: {seen_path}")
                    seen = []
                    if os.path.exists(seen_path):
                        logging.info(f"[{name}] Seen articles file found.")
                        with open(seen_path) as f:
                            seen = json.load(f)
                    
                    new_articles_found = False
                    for latest in latests:
                        if latest.link not in seen:
                            logging.info(f"[NEW] {latest.title}")
                            seen.append(latest.link)
                            new_articles_found = True
                            notify_discord(f"📰 New article on {name.title()}: {latest.title} → {latest.link}")
                    
                    if new_articles_found:
                        with open(seen_path, "w") as f:
                            json.dump(seen, f, indent=2)
                        commit_seen(name)
                        logging.info(f"Saving RSS feed for {name}")
                        logging.info(f"Saving RSS feed for {name} to feeds/{name}.xml")
            except Exception as e:
                log_error(f"RSS parsing failed for {name}: {e}")
        else:
            logging.info(f"Processing scraper for {name} from {url}")
            scraper_path = f"scrapers/{name}.py"
            if not os.path.exists(scraper_path):
                logging.info(f"Generating scraper for {name}")
                html = await fetch_html(url)
                logging.info(f"Found HTML for {name}, generating scraper code")
                code = await generate_scraper(name, html, url)
                if code:
                    logging.info(f"Writing scraper code for {name} to {scraper_path}")
                    with open(scraper_path, "w") as f:
                        f.write(code)
                    
                    seen_path = f"feeds/seen_{name}.json"
                    if not os.path.exists(seen_path):
                        with open(seen_path, "w") as f:
                            json.dump([], f)
                    
                    commit_scraper(name)

            try:
                result = subprocess.run(
                    ["python", f"scrapers/{name}.py"], 
                    capture_output=True, 
                    text=True, 
                    cwd=os.getcwd()
                )
                if result.returncode != 0:
                    log_error(f"Scraper execution failed for {name}: {result.stderr}")
                    continue
                
                articles = json.loads(result.stdout)
                logging.info(f"Scraper for {name} returned {len(articles)} articles")
                seen_path = f"feeds/seen_{name}.json"
                seen = []
                if os.path.exists(seen_path):
                    logging.info(f"Seen articles file found for {name}.")
                    logging.info(f"Loading seen articles from {seen_path}")
                    with open(seen_path) as f:
                        seen = json.load(f)
                
                new_articles_found = False
                for article in articles:
                    logging.info(f"Processing article: {article['title']}")
                    if article['link'] not in seen:
                        seen.append(article['link'])
                        new_articles_found = True
                        notify_discord(f"📰 New article on {name.title()}: {article['title']} → {article['link']}")
                
                if new_articles_found:
                    with open(seen_path, "w") as f:
                        json.dump(seen, f, indent=2)
                    commit_seen(name)
                
                save_rss(name, url, articles)
            except Exception as e:
                log_error(f"Scraper failed for {name}: {e}")

if __name__ == "__main__":
    asyncio.run(main())