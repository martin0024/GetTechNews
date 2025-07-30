import asyncio
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.winamax.fr/news")
        await page.wait_for_selector("#latest-news")
        content = await page.content()
        await browser.close()

        soup = BeautifulSoup(content, 'html.parser')
        articles = []
        for item in soup.select('.news-item'):
            title = item.select_one('.news-title a').get_text(strip=True)
            link = "https://www.winamax.fr" + item.select_one('.news-title a')['href']
            date = item.select_one('.news-details .date').get_text(strip=True) if item.select_one('.news-details .date') else None
            articles.append({"title": title, "link": link, "date": date})

        print(json.dumps(articles, indent=2))

asyncio.run(run())