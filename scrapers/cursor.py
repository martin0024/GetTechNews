import requests
from bs4 import BeautifulSoup
import json

url = "https://cursor.com/blog"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

articles = []
for article in soup.find_all('article'):
    title = article.find('h2').get_text(strip=True)
    link = article.find('a')['href']
    if not link.startswith('http'):
        link = url + link
    date = article.find('time')
    publication_date = date['datetime'] if date else None
    articles.append({
        'title': title,
        'link': link,
        'publication_date': publication_date
    })

print(json.dumps(articles, indent=2))