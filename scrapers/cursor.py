import requests
from bs4 import BeautifulSoup
import json

url = "https://cursor.com/blog"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

articles = []
for article in soup.find_all('a', class_='relative'):
    title = article.find('h2').text if article.find('h2') else None
    link = article['href'] if article['href'].startswith('http') else f"https://cursor.com{article['href']}"
    date = article.find('p', class_='text-sm').text if article.find('p', class_='text-sm') else None
    articles.append({"title": title, "link": link, "date": date})

print(json.dumps(articles, indent=2))