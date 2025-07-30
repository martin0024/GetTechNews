# GetTechNews

Get the latest tech news from various sources and deliver it to your Discord channel via webhook.

## 🚀 Quick Start

### 1. Fork the Repository
Start by forking this repository to your own GitHub account.

### 2. Configure Secrets
In your forked repository:
1. Navigate to **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"** and add the following:
   - `OPENAI_API_KEY`: Your OpenAI API key (required for generating scrapers)
   - `DISCORD_WEBHOOK_URL`: Your Discord webhook URL (for notifications)

### 3. Run the Workflow
1. Go to the **Actions** tab in your repository
2. Select the **News Monitor** workflow
3. Click **"Run workflow"** to start monitoring

The system will automatically check for new articles every hour.

## 🛠️ How It Works

The system follows this process for each news source:

1. **Check Source Type**: Reads `news.json` to determine if a source has an RSS feed or needs scraping
2. **RSS Processing**: For sources with RSS feeds, it parses the feed directly
3. **Scraper Generation**: For sources without RSS:
   - Fetches the website's HTML structure using Playwright
   - Uses OpenAI GPT to generate a custom scraper based on the HTML
   - Creates a Python script to extract articles
4. **Article Processing**: 
   - Extracts title, link, and publication date
   - Checks against previously seen articles to avoid duplicates
   - Stores new articles in the `feeds/` directory
5. **Notifications**: Sends new articles to Discord via webhook
6. **RSS Generation**: Creates custom RSS feeds for all sources

## Adding New Sources

Edit `news.json` to add or modify news sources:

```json
[
  {
    "name": "OpenAI",
    "url": "https://openai.com/news",
    "rss": "https://openai.com/news/rss.xml"
  },
  {
    "name": "Anthropic", 
    "url": "https://www.anthropic.com/news",
    "rss": null
  }
]
```

- **name**: Display name for the source
- **url**: Website URL to scrape
- **rss**: RSS feed URL (set to `null` if not available)

## Contributing

Contributions are welcome, feel free to submit a pull request.

## License

This project is open source and available under the MIT License. 

Made with ❤️ by Martin