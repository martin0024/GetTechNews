from xml.etree.ElementTree import Element, SubElement, tostring
import json, os, datetime

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