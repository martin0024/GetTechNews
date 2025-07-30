from bs4 import BeautifulSoup
import json
import requests

url = "https://www.anthropic.com/news"
response = requests.get(url)
html = response.text

soup = BeautifulSoup(html, "html.parser")

articles = []

featured_cards = soup.find_all("a", class_="FeaturedCard_featuredCard__dMSxb")
for card in featured_cards:
    if card.find("h4") and "Press inquiries" in card.get_text():
        continue
    
    link = card.get("href")
    if link and link.startswith("/news/"):
        title_elem = card.find("div", class_="FeaturedCard_heading__U_YwE")
        if title_elem:
            title = title_elem.get_text(strip=True)
            full_link = f"https://anthropic.com{link}"
            articles.append({
                "title": title,
                "link": full_link,
                "date": None
            })

post_cards = soup.find_all("a", class_="PostCard_post-card__z_Sqq")
for card in post_cards:
    link = card.get("href")
    if link and link.startswith("/news/"):
        title_elem = card.find("h3", class_="PostCard_post-heading__Ob1pu")
        date_elem = card.find("div", class_="PostList_post-date__djrOA")
        
        if title_elem:
            title = title_elem.get_text(strip=True)
            full_link = f"https://anthropic.com{link}"
            date = date_elem.get_text(strip=True) if date_elem else None
            
            articles.append({
                "title": title,
                "link": full_link,
                "date": date
            })

seen_links = set()
unique_articles = []
for article in articles:
    if article["link"] not in seen_links:
        seen_links.add(article["link"])
        unique_articles.append(article)

print(json.dumps(unique_articles, indent=2))