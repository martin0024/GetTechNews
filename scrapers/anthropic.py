```python
from bs4 import BeautifulSoup

html_content = """
<!-- Your HTML content goes here -->
"""

soup = BeautifulSoup(html_content, 'html.parser')
articles = []

for article in soup.find_all('article'):
    title_tag = article.find('h2')
    link_tag = article.find('a', href=True)
    date_tag = article.find('time')

    title = title_tag.get_text(strip=True) if title_tag else None
    link = link_tag['href'] if link_tag else None
    date = date_tag.get('datetime', date_tag.get_text(strip=True)) if date_tag else None

    articles.append({
        "title": title,
        "link": link,
        "date": date
    })

print(articles)
```