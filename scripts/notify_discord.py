import os
from discord_webhook import DiscordWebhook

with open(".env") as f:
    for line in f:
        if "DISCORD_WEBHOOK_URL" in line:
            webhook_url = line.split("=")[1].strip()

if os.path.exists("new_articles.txt"):
    with open("new_articles.txt") as f:
        content = f.read()
        if content.strip():
            webhook = DiscordWebhook(url=webhook_url, content=f"📰 New Articles Found:\n{content}")
            webhook.execute()
        else:
            print(f"[{site_id}] No new articles.")
        os.remove("new_articles.txt")