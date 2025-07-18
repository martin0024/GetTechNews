import openai
import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


async def fetch_html(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        html = await page.content()
        await browser.close()
        return html


def generate_scraper(site_name, html):
    prompt = f"""
You are a Python developer. Generate a script that extracts article titles, publication dates (if available), and links from the following blog HTML page.

Return Python code that prints a list of dictionaries in this format:
[{{"title": ..., "link": ..., "date": ...}}, ...]

HTML:
{html[:4000]}  # Truncated for safety
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response["choices"][0]["message"]["content"]


if __name__ == "__main__":
    url = input("Enter the blog/news URL without RSS: ").strip()
    site_name = url.split("//")[-1].split("/")[0]

    html = asyncio.run(fetch_html(url))
    scraper_code = generate_scraper(site_name, html)

    os.makedirs("scrapers", exist_ok=True)
    with open(f"scrapers/{site_name}.py", "w", encoding="utf-8") as f:
        f.write(scraper_code)

    print(f"✅ Scraper for {site_name} saved to scrapers/{site_name}.py")