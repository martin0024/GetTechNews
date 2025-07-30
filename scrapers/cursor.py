import requests
from bs4 import BeautifulSoup
import json

url = "https://cursor.com/blog"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

articles = []
for article in soup.find_all('a', class_='relative justify-between'):
    title = article.find('h2').text.strip()
    link = article['href']
    full_link = f"https://cursor.com{link}"
    date = article.find('p', class_='text-sm')
    publication_date = date.text.strip() if date else None
    articles.append({
        'title': title,
        'link': full_link,
        'publication_date': publication_date
    })

print(json.dumps(articles, indent=2))