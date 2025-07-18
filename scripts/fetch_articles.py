import os, feedparser, json

with open("news.txt") as f:
    urls = [line.strip() for line in f if line.strip()]

for url in urls:
    site_id = url.split("//")[-1].split("/")[0]
    feed_path = f"feeds/{site_id}.xml"

    if os.path.exists(feed_path):
        feed = feedparser.parse(feed_path)
        latest = feed.entries[0] if feed.entries else None
        if latest:
            print(f"[{site_id}] Latest: {latest.title}")
            with open(f"feeds/seen_{site_id}.json", "r+") as f:
                seen = json.load(f)
                if latest.link not in seen:
                    seen.append(latest.link)
                    f.seek(0)
                    json.dump(seen, f, indent=2)
                    print(f"[NEW] {latest.title}")
                    with open("new_articles.txt", "a") as nf:
                        nf.write(f"{site_id}: {latest.title} → {latest.link}\n")
